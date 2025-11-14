"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import Map from "../components/Map";

type ApiResponse = {
  midpoint: [number, number];
  recommendations: { id: number; name: string; category?: string; lat: number; lon: number }[];
};

export default function Home() {
  const [lat1, setLat1] = useState<string>("35.690921");
  const [lon1, setLon1] = useState<string>("139.700257");
  const [lat2, setLat2] = useState<string>("35.729503");
  const [lon2, setLon2] = useState<string>("139.7109");
  const [category, setCategory] = useState<string>("cafe");
  const [data, setData] = useState<ApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [basemap, setBasemap] = useState<"osm" | "gsi">("osm");
  const [showRail, setShowRail] = useState(true);
  // 標高表示は削除
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [mode, setMode] = useState<"midpoint" | "bbox">("midpoint");
  const [widthM, setWidthM] = useState<string>("10000");  // 10km
  const [heightM, setHeightM] = useState<string>("10000"); // 10km
  const [bboxRect, setBboxRect] = useState<[number, number, number, number] | undefined>(undefined);
  const [page, setPage] = useState<number>(1);
  const pageSize = 10;
  const [toast, setToast] = useState<string>("");
  const [saving, setSaving] = useState<boolean>(false);
  const [lastSavedCount, setLastSavedCount] = useState<number | null>(null);
  const dragTimer = useRef<number | undefined>(undefined);

  const fetchRecs = useCallback(async (override?: { aLat: number; aLon: number; bLat: number; bLon: number }) => {
    setLoading(true);
    setError(null);
    try {
      const aLat = override?.aLat ?? parseFloat(lat1);
      const aLon = override?.aLon ?? parseFloat(lon1);
      const bLat = override?.bLat ?? parseFloat(lat2);
      const bLon = override?.bLon ?? parseFloat(lon2);
      const lats = [aLat, bLat];
      const lons = [aLon, bLon];
      if (lats.some((v) => Number.isNaN(v) || v < -90 || v > 90) || lons.some((v) => Number.isNaN(v) || v < -180 || v > 180)) {
        throw new Error("座標が不正です (-90..90, -180..180)");
      }
      const midLat = (aLat + bLat) / 2;
      const midLon = (aLon + bLon) / 2;
      if (mode === "midpoint") {
        const params = new URLSearchParams({
          lat1: String(aLat),
          lon1: String(aLon),
          lat2: String(bLat),
          lon2: String(bLon),
          category,
          limit: "10",
        });
        const res = await fetch(`http://127.0.0.1:8000/recommend?${params.toString()}`);
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as ApiResponse;
        setData(json);
        setSelectedId(null);
        setBboxRect(undefined);
  setPage(1);
      } else {
        // bbox モード（中心は A/B の中間地点。幅/高さは [m]）
        const w = parseFloat(widthM);
        const h = parseFloat(heightM);
        if ([w, h].some((m) => Number.isNaN(m) || m <= 0)) {
          throw new Error("幅/高さ(メートル)は正の数を入力してください");
        }
        // メートル→度換算（概算）。緯度1度≈111,320m、経度1度≈111,320*cos(緯度)
        const latDegPerM = 1 / 111320;
        const cosLat = Math.cos((midLat * Math.PI) / 180);
        const lonDegPerM = 1 / (111320 * (cosLat || 1e-6));
        const dLat = (h / 2) * latDegPerM;
        const dLon = (w / 2) * lonDegPerM;
        const min_lat = midLat - dLat;
        const max_lat = midLat + dLat;
        const min_lon = midLon - dLon;
        const max_lon = midLon + dLon;

        const params = new URLSearchParams({
          min_lat: String(min_lat),
          min_lon: String(min_lon),
          max_lat: String(max_lat),
          max_lon: String(max_lon),
          category,
        });
        const res = await fetch(`http://127.0.0.1:8000/search_bbox?${params.toString()}`);
        if (!res.ok) throw new Error(`API ${res.status}`);
        const json = (await res.json()) as { bbox: [number, number, number, number]; pois: ApiResponse["recommendations"] };
        setBboxRect([min_lat, min_lon, max_lat, max_lon]);
        setData({ midpoint: [midLat, midLon], recommendations: json.pois });
        setSelectedId(null);
  setPage(1);
      }
    } catch (e: any) {
      setError(e.message ?? "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  }, [category, mode, widthM, heightM, lat1, lon1, lat2, lon2]);

  // ドラッグ終了でA/B更新 → 再検索
  const handlePersonADrag = useCallback((lat: number, lon: number) => {
    setLat1(lat.toFixed(6));
    setLon1(lon.toFixed(6));
    const bLat = parseFloat(lat2);
    const bLon = parseFloat(lon2);
    if (dragTimer.current) window.clearTimeout(dragTimer.current);
    dragTimer.current = window.setTimeout(() => {
      fetchRecs({ aLat: lat, aLon: lon, bLat, bLon });
    }, 150);
  }, [fetchRecs, lat2, lon2]);

  const handlePersonBDrag = useCallback((lat: number, lon: number) => {
    setLat2(lat.toFixed(6));
    setLon2(lon.toFixed(6));
    const aLat = parseFloat(lat1);
    const aLon = parseFloat(lon1);
    if (dragTimer.current) window.clearTimeout(dragTimer.current);
    dragTimer.current = window.setTimeout(() => {
      fetchRecs({ aLat, aLon, bLat: lat, bLon: lon });
    }, 150);
  }, [fetchRecs, lat1, lon1]);

  // 共有URL: 初回にクエリ文字列を解析して状態を復元し、その内容で検索
  useEffect(() => {
    const applyFromQuery = () => {
      try {
        const q = new URLSearchParams(window.location.search);
        const qLat1 = q.get('lat1');
        const qLon1 = q.get('lon1');
        const qLat2 = q.get('lat2');
        const qLon2 = q.get('lon2');
        const qCat  = q.get('category');
        const qMode = q.get('mode');
        const qBasemap = q.get('basemap');
        const qRail = q.get('rail');
        const qW = q.get('widthM');
        const qH = q.get('heightM');

        const next = {
          lat1: qLat1 ?? lat1,
          lon1: qLon1 ?? lon1,
          lat2: qLat2 ?? lat2,
          lon2: qLon2 ?? lon2,
          category: qCat ?? category,
          mode: (qMode === 'bbox' || qMode === 'midpoint') ? (qMode as 'bbox'|'midpoint') : mode,
          basemap: (qBasemap === 'gsi' || qBasemap === 'osm') ? (qBasemap as 'gsi'|'osm') : basemap,
          showRail: qRail ? qRail === '1' : showRail,
          widthM: qW ?? widthM,
          heightM: qH ?? heightM,
        };
        // set states
        setLat1(next.lat1);
        setLon1(next.lon1);
        setLat2(next.lat2);
        setLon2(next.lon2);
        setCategory(next.category);
        setMode(next.mode);
        setBasemap(next.basemap);
        setShowRail(next.showRail);
        if (next.mode === 'bbox') {
          setWidthM(next.widthM);
          setHeightM(next.heightM);
        }
        // kick fetch with parsed values
        const aLat = parseFloat(next.lat1);
        const aLon = parseFloat(next.lon1);
        const bLat = parseFloat(next.lat2);
        const bLon = parseFloat(next.lon2);
        fetchRecs({ aLat, aLon, bLat, bLon });
      } catch {
        // フォールバック: 既定で検索
        fetchRecs();
      }
    };
    applyFromQuery();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 共有URL: 状態→クエリへ反映（シェアしやすいように常時同期）
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const q = new URLSearchParams();
    q.set('lat1', parseFloat(lat1).toFixed(6));
    q.set('lon1', parseFloat(lon1).toFixed(6));
    q.set('lat2', parseFloat(lat2).toFixed(6));
    q.set('lon2', parseFloat(lon2).toFixed(6));
    q.set('category', category);
    q.set('mode', mode);
    q.set('basemap', basemap);
    q.set('rail', showRail ? '1' : '0');
    if (mode === 'bbox') {
      q.set('widthM', widthM);
      q.set('heightM', heightM);
    }
    const url = `${location.pathname}?${q.toString()}`;
    window.history.replaceState(null, '', url);
  }, [lat1, lon1, lat2, lon2, category, mode, widthM, heightM, basemap, showRail]);

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <div>
            <div className="title">二人の中間地点からおすすめスポット</div>
            <div className="subtitle">OSM/Overpass × R-tree × MapLibre — 軽量で美しい地図体験</div>
          </div>
          <Link href="/benchmark" style={{ color: '#007aff', textDecoration: 'none' }}>⚡ ベンチマーク →</Link>
        </div>

        <div className="grid cols-3 items-start">
          <div className="card">
            <h2>Person A</h2>
            <div className="field">
              <input className="input" placeholder="lat" value={lat1} onChange={(e) => setLat1(e.target.value)} />
              <input className="input" placeholder="lon" value={lon1} onChange={(e) => setLon1(e.target.value)} />
            </div>
          </div>
          <div className="card">
            <h2>Person B</h2>
            <div className="field">
              <input className="input" placeholder="lat" value={lat2} onChange={(e) => setLat2(e.target.value)} />
              <input className="input" placeholder="lon" value={lon2} onChange={(e) => setLon2(e.target.value)} />
            </div>
          </div>
          <div className="card">
            <h2>検索設定</h2>
            <div className="row">
              <label>モード:</label>
              <select className="select" value={mode} onChange={(e) => setMode(e.target.value as any)}>
                <option value="midpoint">中間地点</option>
                <option value="bbox">矩形（BBOX）</option>
              </select>
              <label>カテゴリ:</label>
              <select className="select" value={category} onChange={(e) => setCategory(e.target.value)}>
          <option value="cafe">cafe</option>
          <option value="restaurant">restaurant</option>
          <option value="bar">bar</option>
          <option value="pub">pub</option>
          <option value="fast_food">fast_food</option>
          <option value="ice_cream">ice_cream</option>
          <option value="library">library</option>
        </select>
              <label className="ml-4">ベースマップ:</label>
              <select className="select" value={basemap} onChange={(e) => setBasemap(e.target.value as any)}>
          <option value="osm">OSM</option>
          <option value="gsi">地理院（標準地図）</option>
        </select>
              <label className="row">
                <input className="checkbox" type="checkbox" checked={showRail} onChange={(e) => setShowRail(e.target.checked)} />
                鉄道路線
              </label>
              <button className="btn btn-primary" onClick={() => fetchRecs()} disabled={loading} title="検索を実行">
                {loading ? "検索中..." : "検索"}
              </button>
              {data && (
                <>
                  <button
                    className="btn"
                    disabled={saving}
                    onClick={async () => {
                      try {
                        setSaving(true);
                        const count = data?.recommendations?.length ?? 0;
                        const ts = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 15);
                        const base = mode === 'bbox' ? 'bbox' : 'recommend';
                        const name = `${base}_${count}items_${ts}`;
                        const body = {
                          data: {
                            type: mode === 'bbox' ? 'search_bbox' : 'recommend',
                            params: mode === 'bbox' ? {
                              lat1: parseFloat(lat1), lon1: parseFloat(lon1), lat2: parseFloat(lat2), lon2: parseFloat(lon2),
                              category,
                              bbox: bboxRect ?? null,
                            } : {
                              lat1: parseFloat(lat1), lon1: parseFloat(lon1), lat2: parseFloat(lat2), lon2: parseFloat(lon2),
                              category,
                            },
                            result: data,
                          },
                          format: 'json',
                          name,
                        };
                        const res = await fetch('http://127.0.0.1:8000/data/save', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify(body),
                        });
                        if (!res.ok) throw new Error(`save ${res.status}`);
                        const json = await res.json();
                        setLastSavedCount(count);
                        setToast(`保存しました (${count}件): ${json.file}`);
                        setTimeout(() => setToast(''), 1500);
                      } catch (e: any) {
                        setToast(`保存に失敗: ${e?.message ?? e}`);
                        setTimeout(() => setToast(''), 1800);
                      } finally {
                        setSaving(false);
                      }
                    }}
                    title="結果をJSONで保存"
                    style={{ marginLeft: 8 }}
                  >JSON保存</button>
                  <button
                    className="btn"
                    disabled={saving}
                    onClick={async () => {
                      try {
                        setSaving(true);
                        const count = data?.recommendations?.length ?? 0;
                        const ts = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(0, 15);
                        const base = mode === 'bbox' ? 'bbox' : 'recommend';
                        const name = `${base}_${count}items_${ts}`;
                        const body = {
                          data: {
                            type: mode === 'bbox' ? 'search_bbox' : 'recommend',
                            params: mode === 'bbox' ? {
                              lat1: parseFloat(lat1), lon1: parseFloat(lon1), lat2: parseFloat(lat2), lon2: parseFloat(lon2),
                              category,
                              bbox: bboxRect ?? null,
                            } : {
                              lat1: parseFloat(lat1), lon1: parseFloat(lon1), lat2: parseFloat(lat2), lon2: parseFloat(lon2),
                              category,
                            },
                            result: data,
                          },
                          format: 'yaml',
                          name,
                        } as any;
                        const res = await fetch('http://127.0.0.1:8000/data/save', {
                          method: 'POST',
                          headers: { 'Content-Type': 'application/json' },
                          body: JSON.stringify(body),
                        });
                        if (!res.ok) {
                          const text = await res.text();
                          throw new Error(text || `save ${res.status}`);
                        }
                        const json = await res.json();
                        setToast(`保存しました (${count}件): ${json.file}`);
                        setTimeout(() => setToast(''), 1500);
                      } catch (e: any) {
                        setToast(`保存に失敗: ${e?.message ?? e}`);
                        setTimeout(() => setToast(''), 1800);
                      } finally {
                        setSaving(false);
                      }
                    }}
                    title="結果をYAMLで保存"
                    style={{ marginLeft: 6 }}
                  >YAML保存</button>
                  {lastSavedCount !== null && (
                    <span className="hint" style={{ marginLeft: 10 }}>
                      最新保存件数: {lastSavedCount}件
                    </span>
                  )}
                </>
              )}
            </div>
            {error && <p className="hint" style={{ color: '#ff6b6b' }}>{error}</p>}
            {mode === "bbox" && (
              <div style={{ marginTop: 12 }}>
                <div className="row subtle" title="中心は A と B の中間地点を自動採用します">
                  <span className="badge">中心</span>
                  <span className="mono">A/B の中間地点が自動計算されます</span>
                </div>
                <div className="row" style={{ marginTop: 10, gap: 8 }}>
                  <div className="chip-group">
                    <button type="button" className="chip" onClick={() => { setWidthM("5000"); setHeightM("5000"); }}>5km 四方</button>
                    <button type="button" className="chip" onClick={() => { setWidthM("10000"); setHeightM("10000"); }}>10km 四方</button>
                    <button type="button" className="chip" onClick={() => { setWidthM("20000"); setHeightM("20000"); }}>20km 四方</button>
                  </div>
                </div>
                <div className="row" style={{ marginTop: 8 }}>
                  <input className="input" placeholder="幅 (m) 例: 10000" value={widthM} onChange={(e) => setWidthM(e.target.value)} />
                  <input className="input" placeholder="高さ (m) 例: 10000" value={heightM} onChange={(e) => setHeightM(e.target.value)} />
                </div>
                {/* ドラッグON/OFFの表示は不要のため非表示 */}
                <p className="hint" style={{ marginTop: 6 }}>A/B の中間地点を中心に、幅/高さ(メートル)から矩形を自動算出します。例: 幅=10000, 高さ=10000 で約10km四方。</p>
              </div>
            )}
          </div>
        </div>

      {data && (
        <>
          <hr className="divider" />
          {(() => { const aLat = parseFloat(lat1); const aLon = parseFloat(lon1); const bLat = parseFloat(lat2); const bLon = parseFloat(lon2); const midLat = (aLat + bLat)/2; const midLon = (aLon + bLon)/2; return (<div className="hint">📍 中間地点: {midLat.toFixed(5)}, {midLon.toFixed(5)}</div>); })()}
          <Map
            midpoint={(() => { const aLat = parseFloat(lat1); const aLon = parseFloat(lon1); const bLat = parseFloat(lat2); const bLon = parseFloat(lon2); return [(aLat + bLat)/2, (aLon + bLon)/2] as [number, number]; })()}
            pois={data.recommendations}
            personA={[parseFloat(lat1), parseFloat(lon1)]}
            personB={[parseFloat(lat2), parseFloat(lon2)]}
            basemap={basemap}
            showRail={showRail}
            bboxRect={bboxRect}
            enableDraw={mode === 'bbox'}
            loading={loading}
            onPersonADrag={handlePersonADrag}
            onPersonBDrag={handlePersonBDrag}
            enableCluster={mode === 'bbox'}
            onBBoxDrawn={(bbox) => {
              // bbox = [minLat, minLon, maxLat, maxLon]; update width/height(m) to reflect draw result
              const [minLat, minLon, maxLat, maxLon] = bbox;
              const midLat = (parseFloat(lat1) + parseFloat(lat2)) / 2;
              const latDegPerM = 1 / 111320;
              const cosLat = Math.cos((midLat * Math.PI) / 180);
              const lonDegPerM = 1 / (111320 * (cosLat || 1e-6));
              const hM = Math.abs(maxLat - minLat) / latDegPerM;
              const wM = Math.abs(maxLon - minLon) / lonDegPerM;
              setWidthM(String(Math.round(wM)));
              setHeightM(String(Math.round(hM)));
              setBboxRect(bbox);
              // Optional: auto-trigger search for newly drawn bbox
              fetchRecs();
            }}
            toolbar={true}
            onResetBBox={() => {
              setBboxRect(undefined);
            }}
            onRecenter={() => {
              // no-op, handled inside Map for flyTo
            }}
          />
          <div className="grid cols-2" style={{ marginTop: 16 }}>
            <div>
              <div className="section-title">おすすめスポット</div>
              <ul className="list" style={{ display: 'grid', gap: 8 }}>
                {(mode === 'bbox' ? data.recommendations : data.recommendations.slice((page-1)*pageSize, page*pageSize)).map((p) => (
                  <li
                    key={p.id}
                    className={`list-item ${selectedId === p.id ? "active" : ""}`}
                    onMouseEnter={() => setSelectedId(p.id)}
                    onMouseLeave={() => setSelectedId((prev) => (prev === p.id ? null : prev))}
                    onClick={() => {
                      setSelectedId(p.id);
                      // Mapへ選択イベントを通知
                      const evt = new CustomEvent("poi-select", { detail: { id: p.id } });
                      window.dispatchEvent(evt);
                    }}
                    title="地図上でハイライト"
                  >
                    <div className="name">{p.name} {p.category ? `(${p.category})` : ""}</div>
                    <div className="meta">lat: {p.lat.toFixed(6)}, lon: {p.lon.toFixed(6)}
                      <button className="chip" style={{ marginLeft: 8 }} onClick={(e) => {
                        e.stopPropagation();
                        const text = `${p.lat.toFixed(6)}, ${p.lon.toFixed(6)}`;
                        navigator.clipboard.writeText(text).then(() => {
                          setToast("座標をコピーしました");
                          setTimeout(() => setToast(""), 1400);
                        });
                      }}>コピー</button>
                    </div>
                  </li>
                ))}
                {data.recommendations.length === 0 && <li className="hint">該当スポットが見つかりませんでした</li>}
              </ul>
              {mode !== 'bbox' && data.recommendations.length > pageSize && (
                <div className="row" style={{ justifyContent: 'space-between', marginTop: 10 }}>
                  <button className="btn" disabled={page===1} onClick={() => setPage((p)=>Math.max(1,p-1))}>前へ</button>
                  <div className="hint">{page} / {Math.ceil(data.recommendations.length / pageSize)}</div>
                  <button className="btn" disabled={page >= Math.ceil(data.recommendations.length / pageSize)} onClick={() => setPage((p)=>p+1)}>次へ</button>
                </div>
              )}
            </div>
            <div>
              <div className="section-title">ヒント</div>
              <ul className="hint" style={{ paddingLeft: 18, marginTop: 6 }}>
                <li>カテゴリを変更すると候補が増減します。</li>
                <li>A/Bの距離が離れすぎる場合は検索半径を自動的に調整します。</li>
                <li>駅・路線や地形のオーバーレイを切り替えて見やすい表示にできます。</li>
              </ul>
            </div>
          </div>
        </>
      )}
      {/* Toast */}
      {toast && (
        <div style={{ position: 'fixed', bottom: 20, right: 20, background: '#111214', color: '#fff', padding: '10px 12px', borderRadius: 10, boxShadow: '0 6px 16px rgba(0,0,0,0.2)' }}>{toast}</div>
      )}
      </div>
    </div>
  );
}
