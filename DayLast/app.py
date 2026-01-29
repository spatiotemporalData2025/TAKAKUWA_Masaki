import threading
import time
import requests
import numpy as np
import csv
import os
from datetime import datetime
from fastapi import FastAPI, Request, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sklearn.cluster import DBSCAN

# --- 安全装置: R-treeがインストールされていなくても動くようにする ---
try:
    from rtree import index
    HAS_RTREE = True
except (ImportError, OSError):
    print("Warning: R-tree library not found. Using simple list search fallback.")
    HAS_RTREE = False

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# --- データ管理クラス ---
class DataStore:
    def __init__(self):
        self.stations = {}  # {id: station_data}
        self.lock = threading.Lock()
        
        # アルゴリズム用データ構造
        self.rtree_idx = index.Index() if HAS_RTREE else None
        self.empty_stations_coords = [] # DBSCAN用: 空っぽのステーションの座標リスト
        
        # Space Saving法 (簡易実装: 変動があったステーションをカウント)
        self.activity_counter = {} 
        self.MAX_COUNTERS = 50 # 追跡する最大数

    def update_data(self, new_stations):
        """APIから取得したデータで更新し、アルゴリズム用インデックスを再構築"""
        with self.lock:
            current_coords = []
            empty_coords = []
            
            # R-treeの再構築（簡略化のため毎回作り直し）
            if HAS_RTREE:
                self.rtree_idx = index.Index()

            for i, st in enumerate(new_stations):
                sid = st['id']
                lat = st['latitude']
                lon = st['longitude']
                free = st['free_bikes']
                
                # Space Saving: 前回のデータと比較して変動があればカウント
                if sid in self.stations:
                    prev_free = self.stations[sid]['free_bikes']
                    if prev_free != free:
                        self._increment_counter(st['name'])
                
                # ステーション保存
                self.stations[sid] = st
                
                # R-treeへ挿入
                if HAS_RTREE:
                    self.rtree_idx.insert(i, (lon, lat, lon, lat), obj=st)
                
                # DBSCAN用: 「自転車が0台」のステーション座標を集める
                if free == 0:
                    empty_coords.append([lat, lon])

            self.empty_stations_coords = np.array(empty_coords)

    def _increment_counter(self, name):
        """Space Saving Algorithm (簡易版)"""
        if name in self.activity_counter:
            self.activity_counter[name] += 1
        elif len(self.activity_counter) < self.MAX_COUNTERS:
            self.activity_counter[name] = 1
        else:
            # カウンタがいっぱいの時、最小値を減らす（省略版: 最小を削除して入替）
            min_key = min(self.activity_counter, key=self.activity_counter.get)
            self.activity_counter.pop(min_key)
            self.activity_counter[name] = 1

    def search_bounds(self, min_x, min_y, max_x, max_y):
        """R-treeを使って範囲検索"""
        with self.lock:
            if HAS_RTREE:
                results = list(self.rtree_idx.intersection((min_x, min_y, max_x, max_y), objects=True))
                return [item.object for item in results]
            else:
                # フォールバック: 全探索
                res = []
                for st in self.stations.values():
                    if min_y <= st['latitude'] <= max_y and min_x <= st['longitude'] <= max_x:
                        res.append(st)
                return res

    def get_clusters(self):
        """DBSCANで「自転車ゼロ」密集地帯を検出"""
        with self.lock:
            if len(self.empty_stations_coords) < 3:
                return []
            
            # 半径約500m (0.005度くらい) 以内に3つ以上空っぽステーションがあればクラスタとみなす
            db = DBSCAN(eps=0.005, min_samples=3).fit(self.empty_stations_coords)
            labels = db.labels_
            
            # 結果整形
            clusters = []
            for coord, label in zip(self.empty_stations_coords, labels):
                if label != -1: # ノイズ以外
                    clusters.append({
                        "lat": coord[0],
                        "lon": coord[1],
                        "cluster_id": int(label)
                    })
            return clusters

    def get_ranking(self):
        """利用頻度ランキングを返す"""
        with self.lock:
            return sorted(self.activity_counter.items(), key=lambda x: x[1], reverse=True)[:10]

store = DataStore()

# --- バックグラウンド: データ取得ループ ---
def poll_citybikes():
    # 東京のドコモ・バイクシェア（千代田区、中央区、港区、新宿区、文京区、江東区、品川区、目黒区、大田区、渋谷区）
    NETWORK_ID = 'docomo-cycle-tokyo' 
    API_URL = f"http://api.citybik.es/v2/networks/{NETWORK_ID}"
    
    # CSVファイルの初期化（ヘッダーがなければ作成）
    csv_file = "bike_log.csv"
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'station_name', 'free_bikes', 'latitude', 'longitude'])
    
    while True:
        try:
            resp = requests.get(API_URL)
            data = resp.json()
            stations = data['network']['stations']
            store.update_data(stations)
            
            # データロギング: CSV追記
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                for st in stations:
                    writer.writerow([
                        current_time,
                        st['name'],
                        st['free_bikes'],
                        st['latitude'],
                        st['longitude']
                    ])
            
            print(f"Updated {len(stations)} stations data.")
        except Exception as e:
            print(f"Error fetching data: {e}")
        
        time.sleep(30) # 30秒ごとに更新

# --- API ---

@app.on_event("startup")
def start_background_task():
    t = threading.Thread(target=poll_citybikes, daemon=True)
    t.start()

@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/search")
def search_stations(
    min_lon: float = Query(...), min_lat: float = Query(...),
    max_lon: float = Query(...), max_lat: float = Query(...)
):
    """地図の表示範囲内のステーションを返す (R-tree使用)"""
    stations = store.search_bounds(min_lon, min_lat, max_lon, max_lat)
    return {"stations": stations}

@app.get("/api/analysis")
def analysis():
    """分析結果（クラスタとランキング）を返す"""
    clusters = store.get_clusters()
    ranking = store.get_ranking()
    return {"clusters": clusters, "ranking": ranking}