from fastapi import FastAPI, Query
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from pydantic import BaseModel
from rtree import index
import requests
import time
from typing import List, Optional, Tuple, Dict
import math
from pathlib import Path
from datetime import datetime
import json
try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発用。必要に応じて制限
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- storage settings ---
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# --- OSM/Overpass を使って無料の POI を取得 ---
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]


def _overpass_request(query: str, timeout_s: int = 60, retries: int = 2) -> dict:
    """Call Overpass with retries and endpoint fallback. Uses POST as recommended.
    Returns parsed JSON or raises on final failure.
    """
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        for base in OVERPASS_URLS:
            try:
                r = requests.post(base, data={"data": query}, timeout=timeout_s)
                r.raise_for_status()
                return r.json()
            except Exception as e:  # noqa: BLE001 keep broad for network issues
                last_err = e
                # brief backoff between endpoints
                time.sleep(0.2)
        # exponential backoff between attempts
        time.sleep(0.6 * (2 ** attempt))
    # If all fail, raise
    raise last_err or RuntimeError("Overpass request failed")

# サポートするカテゴリ（OSMタグ）
SUPPORTED_AMENITIES = {
    "cafe", "restaurant", "bar", "pub", "fast_food", "biergarten",
    "ice_cream", "food_court", "library"
}


class Recommendation(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    lat: float
    lon: float


class RecommendResponse(BaseModel):
    midpoint: Tuple[float, float]
    recommendations: List[Recommendation]


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _safe_stem(name: str) -> str:
    # very simple sanitizer for filename stem
    return "".join(c for c in name if c.isalnum() or c in ("-", "_", ".")) or "dataset"


def _save_payload(data: dict, prefix: str = "dataset", fmt: str = "json", name: Optional[str] = None) -> Path:
    stem = _safe_stem(name) if name else f"{prefix}_{_timestamp()}"
    if fmt.lower() in ("yaml", "yml"):
        if yaml is None:
            raise HTTPException(status_code=400, detail="YAML is not available on server (PyYAML not installed)")
        path = DATA_DIR / f"{stem}.yaml"
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)
        return path
    # default json
    path = DATA_DIR / f"{stem}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def fetch_pois(lat: float, lon: float, category: str, radius_m: int) -> List[dict]:
    """Overpass APIで中点周辺のPOIを取得。nodes/ways/relationsを 'out geom' で取得し、
    ways/relations は幾何から重心を推定して座標化する。"""
    # amenity タグのみ対応（無料・汎用）
    if category not in SUPPORTED_AMENITIES:
        category = "cafe"

    # 軽量化のため 'out center' を使用（ways/relations に center を付与）
    query = f"""
    [out:json][timeout:60];
    (
        node["amenity"="{category}"](around:{radius_m},{lat},{lon});
        way["amenity"="{category}"](around:{radius_m},{lat},{lon});
        relation["amenity"="{category}"](around:{radius_m},{lat},{lon});
    );
    out center;
    """
    data = _overpass_request(query, timeout_s=60, retries=2)

    pois: List[dict] = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name") or "Unnamed"
        amenity = tags.get("amenity")

        lat_i = None
        lon_i = None
        # ノード: 座標をそのまま
        if "lat" in el and "lon" in el:
            lat_i, lon_i = float(el["lat"]), float(el["lon"])
        # ウェイ/リレーション: center を利用（'out center'）
        if (lat_i is None or lon_i is None) and "center" in el and el["center"]:
            lat_i = float(el["center"].get("lat"))
            lon_i = float(el["center"].get("lon"))
        if lat_i is None or lon_i is None:
            continue

        pois.append({
            "id": el.get("id"),
            "name": name,
            "category": amenity,
            "lat": float(lat_i),
            "lon": float(lon_i),
        })
    return pois


def _polygon_centroid(latlon: List[Tuple[float, float]]) -> Tuple[float, float]:
    """多角形（閉じた経緯度列）の重心を計算（平面近似）。ざっくりだがPOI位置の改善に有効。"""
    # 2D平面に投影してから計算（小地域前提）
    # x=lon, y=lat として多角形の重心を求める
    area = 0.0
    cx = 0.0
    cy = 0.0
    pts = [(p[1], p[0]) for p in latlon]  # (x=lon, y=lat)
    for i in range(len(pts) - 1):
        x0, y0 = pts[i]
        x1, y1 = pts[i + 1]
        cross = x0 * y1 - x1 * y0
        area += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross
    if abs(area) < 1e-9:
        # 面積ゼロ（線状等）の場合は単純平均
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (sum(ys) / len(ys), sum(xs) / len(xs))
    area *= 0.5
    cx /= (6.0 * area)
    cy /= (6.0 * area)
    return (cy, cx)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def build_rtree(pois: List[dict]) -> Tuple[index.Index, List[dict]]:
    """POI を R-tree にインデックス。"""
    idx = index.Index()
    for i, p in enumerate(pois):
        # 点を最小矩形として登録（lon, lat, lon, lat）
        idx.insert(i, (p["lon"], p["lat"], p["lon"], p["lat"]))
    return idx, pois


@app.get("/recommend", response_model=RecommendResponse)
def recommend(
    lat1: float = Query(..., description="Person A latitude"),
    lon1: float = Query(..., description="Person A longitude"),
    lat2: float = Query(..., description="Person B latitude"),
    lon2: float = Query(..., description="Person B longitude"),
    category: str = Query("cafe", description="OSM amenity category, e.g., cafe, restaurant"),
    limit: int = Query(10, ge=1, le=50),
    radius_m: Optional[int] = Query(None, ge=100, le=10000, description="Search radius in meters; default auto"),
    save: bool = Query(False, description="If true, save the response on server"),
    fmt: Optional[str] = Query("json", description="Save format json|yaml (when save=true)"),
    name: Optional[str] = Query(None, description="Optional file name (without extension) when saving")
):
    """
    二人の中間地点から、指定カテゴリのスポットをR-treeで近い順に返す。
    戻り値は座標と簡易メタデータのみ（距離は返さない）。
    """
    # 中間地点
    mid_lat = (lat1 + lat2) / 2.0
    mid_lon = (lon1 + lon2) / 2.0

    # 半径: 二人間の距離の半分 + 400m を基準（800m〜3000mの範囲にクランプ）
    auto_r = int(_haversine_m(lat1, lon1, lat2, lon2) / 2 + 400)
    r_m = radius_m or max(800, min(3000, auto_r))

    try:
        pois = fetch_pois(mid_lat, mid_lon, category, r_m)
    except Exception as e:
        # Overpass障害時は 200 で空配列を返し、クライアントで再試行可能にする
        # ログだけ残す
        print(f"Overpass error: {e}")
        return {"midpoint": (mid_lat, mid_lon), "recommendations": []}
    if not pois:
        return {"midpoint": (mid_lat, mid_lon), "recommendations": []}

    # 名前と近接で重複除去
    deduped: List[dict] = []
    seen: Dict[str, List[Tuple[float, float]]] = {}
    for p in pois:
        key = (p.get("name") or "Unnamed").strip().lower()
        lst = seen.setdefault(key, [])
        # 30m 以内に同名があるならスキップ
        if any(_haversine_m(p["lat"], p["lon"], la, lo) < 30 for (la, lo) in lst):
            continue
        lst.append((p["lat"], p["lon"]))
        deduped.append(p)

    idx, items = build_rtree(deduped)
    # R-tree で最近傍 k 件
    k = min(limit, len(items))
    nearest_ids = list(idx.nearest((mid_lon, mid_lat, mid_lon, mid_lat), k))

    recs = []
    for i in nearest_ids:
        p = items[i]
        # 距離は返さず、座標とカテゴリ/名前のみ
        recs.append({
            "id": int(p["id"]),
            "name": p["name"],
            "category": p.get("category"),
            "lat": p["lat"],
            "lon": p["lon"],
        })
    result = {"midpoint": (mid_lat, mid_lon), "recommendations": recs}
    if save:
        try:
            saved = _save_payload(
                data={
                    "type": "recommend",
                    "params": {
                        "lat1": lat1, "lon1": lon1, "lat2": lat2, "lon2": lon2,
                        "category": category, "limit": limit, "radius_m": r_m,
                    },
                    "result": result,
                },
                prefix="recommend",
                fmt=(fmt or "json"),
                name=name,
            )
            # expose location in header-like field
            return JSONResponse(content=result, headers={"X-Saved-Path": str(saved.name)})
        except HTTPException:
            raise
        except Exception as e:  # pragma: no cover
            print(f"Save error: {e}")
            # still return result
            return result
    return result


class BBoxResponse(BaseModel):
    bbox: Tuple[float, float, float, float]
    pois: List[Recommendation]


@app.get("/search_bbox", response_model=BBoxResponse)
def search_bbox(
    min_lat: float = Query(..., description="South latitude"),
    min_lon: float = Query(..., description="West longitude"),
    max_lat: float = Query(..., description="North latitude"),
    max_lon: float = Query(..., description="East longitude"),
    category: str = Query("cafe", description="OSM amenity category"),
    save: bool = Query(False, description="If true, save the response on server"),
    fmt: Optional[str] = Query("json", description="Save format json|yaml (when save=true)"),
    name: Optional[str] = Query(None, description="Optional file name (without extension) when saving"),
):
    """
    指定した矩形範囲（bbox）内の指定カテゴリのPOIを全件取得して返す。
    """
    if category not in SUPPORTED_AMENITIES:
        category = "cafe"

    # Overpass bbox は (south, west, north, east) の順
    query = f"""
    [out:json][timeout:60];
    (
        node["amenity"="{category}"]({min_lat},{min_lon},{max_lat},{max_lon});
        way["amenity"="{category}"]({min_lat},{min_lon},{max_lat},{max_lon});
        relation["amenity"="{category}"]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out center;
    """
    try:
        data = _overpass_request(query, timeout_s=60, retries=2)
    except Exception as e:
        print(f"Overpass error: {e}")
        return {"bbox": (min_lat, min_lon, max_lat, max_lon), "pois": []}

    pois: List[dict] = []
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        name = tags.get("name") or "Unnamed"
        amenity = tags.get("amenity")

        lat_i = None
        lon_i = None
        if "lat" in el and "lon" in el:
            lat_i, lon_i = float(el["lat"]), float(el["lon"])
        if (lat_i is None or lon_i is None) and "center" in el and el["center"]:
            lat_i = float(el["center"].get("lat"))
            lon_i = float(el["center"].get("lon"))
        if lat_i is None or lon_i is None:
            continue

        pois.append({
            "id": el.get("id"),
            "name": name,
            "category": amenity,
            "lat": float(lat_i),
            "lon": float(lon_i),
        })

    # 型整形
    out_items = [Recommendation(id=int(p["id"]), name=p["name"], category=p.get("category"), lat=p["lat"], lon=p["lon"]) for p in pois]
    result = {"bbox": (min_lat, min_lon, max_lat, max_lon), "pois": out_items}
    if save:
        try:
            # convert pydantic models to plain dicts where needed
            serializable = {
                "type": "search_bbox",
                "params": {
                    "min_lat": min_lat, "min_lon": min_lon, "max_lat": max_lat, "max_lon": max_lon,
                    "category": category,
                },
                "result": {
                    "bbox": result["bbox"],
                    "pois": [r.model_dump() if hasattr(r, "model_dump") else r.dict() for r in out_items],
                },
            }
            saved = _save_payload(serializable, prefix="bbox", fmt=(fmt or "json"), name=name)
            return JSONResponse(content=result, headers={"X-Saved-Path": str(saved.name)})
        except HTTPException:
            raise
        except Exception as e:  # pragma: no cover
            print(f"Save error: {e}")
            return result
    return result


# --- Explicit save/list APIs ---
class SaveBody(BaseModel):
    data: dict
    format: Optional[str] = "json"  # json | yaml
    name: Optional[str] = None


@app.post("/data/save")
def save_dataset(body: SaveBody):
    path = _save_payload(body.data, prefix="dataset", fmt=(body.format or "json"), name=body.name)
    return {"ok": True, "file": path.name}


@app.get("/data/list")
def list_datasets():
    items = []
    for p in sorted(DATA_DIR.glob("*.*")):
        if p.suffix.lower() not in (".json", ".yaml", ".yml"):
            continue
        stat = p.stat()
        items.append({
            "file": p.name,
            "size": stat.st_size,
            "modified": datetime.utcfromtimestamp(stat.st_mtime).strftime("%Y-%m-%dT%H:%M:%SZ"),
        })
    return {"items": items}


@app.get("/data/{file_name}")
def get_dataset(file_name: str):
    safe = _safe_stem(file_name)
    # allow extensions
    for ext in (".json", ".yaml", ".yml"):
        cand = DATA_DIR / (safe if safe.endswith(ext) else safe + ext)
        if cand.exists():
            if cand.suffix == ".json":
                with cand.open("r", encoding="utf-8") as f:
                    return JSONResponse(json.load(f))
            # YAML -> plain text for easy download/inspection
            return FileResponse(path=str(cand), media_type="text/yaml")
    raise HTTPException(status_code=404, detail="file not found")
