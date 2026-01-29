import random
import time
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo']
matplotlib.rcParams['axes.unicode_minus'] = False

# R-tree インポート（エラーハンドリング付き）
try:
    from rtree import index
    HAS_RTREE = True
except (ImportError, OSError):
    print("Error: rtree library not found. Please install: pip install rtree")
    HAS_RTREE = False
    exit(1)

# ランダムデータ生成（10万件）
print("10万件のランダムデータを生成中...")
NUM_POINTS = 100000
data_points = []
for i in range(NUM_POINTS):
    lat = random.uniform(35.6, 35.75)  # 東京周辺
    lon = random.uniform(139.7, 139.85)
    data_points.append((i, lat, lon))

print(f"{NUM_POINTS}件のデータ生成完了\n")

# R-treeインデックス構築
print("R-treeインデックスを構築中...")
rtree_idx = index.Index()
for point_id, lat, lon in data_points:
    rtree_idx.insert(point_id, (lon, lat, lon, lat))
print("R-treeインデックス構築完了\n")

# ベンチマーク: 100回の検索範囲を生成
NUM_SEARCHES = 100
search_ranges = []
for _ in range(NUM_SEARCHES):
    center_lat = random.uniform(35.6, 35.75)
    center_lon = random.uniform(139.7, 139.85)
    radius = random.uniform(0.01, 0.05)  # 約1〜5km
    min_lat = center_lat - radius
    max_lat = center_lat + radius
    min_lon = center_lon - radius
    max_lon = center_lon + radius
    search_ranges.append((min_lat, max_lat, min_lon, max_lon))

print(f"{NUM_SEARCHES}個の検索範囲を生成完了\n")

# === 方法A: 線形探索（リスト全走査） ===
print("【方法A】線形探索でベンチマーク実行中...")
linear_times = []
for min_lat, max_lat, min_lon, max_lon in search_ranges:
    start = time.perf_counter()
    results = []
    for point_id, lat, lon in data_points:
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            results.append(point_id)
    elapsed = time.perf_counter() - start
    linear_times.append(elapsed)

avg_linear = sum(linear_times) / len(linear_times)
print(f"線形探索の平均時間: {avg_linear*1000:.3f} ms\n")

# === 方法B: R-tree検索 ===
print("【方法B】R-treeでベンチマーク実行中...")
rtree_times = []
for min_lat, max_lat, min_lon, max_lon in search_ranges:
    start = time.perf_counter()
    results = list(rtree_idx.intersection((min_lon, min_lat, max_lon, max_lat)))
    elapsed = time.perf_counter() - start
    rtree_times.append(elapsed)

avg_rtree = sum(rtree_times) / len(rtree_times)
print(f"R-tree検索の平均時間: {avg_rtree*1000:.3f} ms\n")

# 結果比較
speedup = avg_linear / avg_rtree if avg_rtree > 0 else float('inf')
print("=" * 50)
print(f"【結果】R-treeは線形探索の約 {speedup:.1f}倍 高速！")
print("=" * 50)

# 棒グラフ作成
plt.figure(figsize=(10, 6))
methods = ['線形探索\n(リスト全走査)', 'R-tree\n(空間インデックス)']
times = [avg_linear * 1000, avg_rtree * 1000]  # ミリ秒に変換
colors = ['#e74c3c', '#2ecc71']

bars = plt.bar(methods, times, color=colors, width=0.5)
plt.ylabel('平均検索時間 (ms)', fontsize=12)
plt.title('R-tree vs 線形探索 性能比較\n(10万件のデータ、100回の検索)', fontsize=14)
plt.grid(axis='y', alpha=0.3)

# 棒グラフに数値表示
for bar, time_val in zip(bars, times):
    height = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2., height,
             f'{time_val:.3f} ms', ha='center', va='bottom', fontsize=11)

# 速度向上率をアノテーション
plt.text(0.5, max(times)*0.8, f'R-treeは約{speedup:.1f}倍高速', 
         ha='center', fontsize=14, fontweight='bold', 
         bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))

plt.tight_layout()
plt.savefig('benchmark_result.png', dpi=150)
print("\nbenchmark_result.png を保存しました。")
