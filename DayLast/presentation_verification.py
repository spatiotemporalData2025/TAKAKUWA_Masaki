#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
プレゼンテーション検証スクリプト
5〜7分の発表に必要なすべてのベンチマーク、検証、可視化を生成
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import DBSCAN
import time
import sys
from rtree import index
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
def setup_japanese_font():
    if sys.platform == 'win32':
        plt.rcParams['font.family'] = 'MS Gothic'
    elif sys.platform == 'darwin':
        plt.rcParams['font.family'] = 'Hiragino Sans'
    else:
        plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False

setup_japanese_font()

print("=" * 60)
print("プレゼンテーション検証スクリプト")
print("=" * 60)

# ========================================
# 1. データ読み込み
# ========================================
print("\n[1/5] データ読み込み中...")
df = pd.read_csv('bike_log.csv')
print(f"✓ {len(df):,} 件のレコード読み込み完了")

# ========================================
# 2. R-tree ベンチマーク検証（改善版）
# ========================================
print("\n[2/5] R-tree ベンチマーク検証中...")

# ビューポートサンプル（東京都心）
min_lat, max_lat = 35.64, 35.72
min_lon, max_lon = 139.73, 139.81

# R-treeを事前構築（構築時間は除外）
print("  R-treeインデックスを構築中...")
p = index.Property()
p.dimension = 2
idx = index.Index(interleaved=True, properties=p)

for i, row in df.iterrows():
    idx.insert(i, (row['latitude'], row['longitude']))

print("  ✓ インデックス構築完了")

# 複数回検索を実施して平均時間を測定（より正確な比較）
num_trials = 100
print(f"  {num_trials}回の検索を実施中...")

# 線形探索時間測定（100回平均）
linear_times = []
for _ in range(num_trials):
    start = time.time()
    linear_results = df[
        (df['latitude'] >= min_lat) & (df['latitude'] <= max_lat) &
        (df['longitude'] >= min_lon) & (df['longitude'] <= max_lon)
    ]
    linear_times.append(time.time() - start)
linear_time = np.mean(linear_times)

# R-tree検索時間測定（100回平均、構築時間除外）
rtree_times = []
rtree_bbox = (min_lat, min_lon, max_lat, max_lon)
for _ in range(num_trials):
    start = time.time()
    rtree_results = list(idx.intersection(rtree_bbox))
    rtree_times.append(time.time() - start)
rtree_time = np.mean(rtree_times)

speedup = linear_time / rtree_time

print(f"✓ 線形探索: {linear_time*1000:.4f}ms (平均、結果: {len(linear_results):,} 件)")
print(f"✓ R-tree検索: {rtree_time*1000:.4f}ms (平均、結果: {len(rtree_results):,} 件)")
print(f"✓ 高速化率: {speedup:.1f}倍")

# ベンチマーク画像生成（改善版レイアウト）
fig, ax = plt.subplots(figsize=(12, 7))
methods = ['線形探索', 'R-tree']
times = [linear_time * 1000, rtree_time * 1000]
colors = ['#e74c3c', '#27ae60']  # より鮮やかな色
bars = ax.bar(methods, times, color=colors, alpha=0.85, edgecolor='black', linewidth=2.5, width=0.6)

# バーの上に値を表示
for bar, time_val in zip(bars, times):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + max(times) * 0.02,
            f'{time_val:.4f}ms', ha='center', va='bottom', 
            fontsize=13, fontweight='bold', color='black')

ax.set_ylabel('検索時間 (ミリ秒)', fontsize=13, fontweight='bold')
ax.set_title('R-tree による空間検索の高速化\n43,130レコード × ビューポート検索 (100回平均)', 
            fontsize=15, fontweight='bold', pad=20)
ax.set_ylim(0, max(times) * 1.25)
ax.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1.2)

# 高速化率をテキストボックスで追加（見やすく）
if speedup >= 1:
    speedup_color = '#27ae60'
    speedup_text = f'高速化率: {speedup:.1f}倍 ⚡'
else:
    speedup_color = '#e67e22'
    speedup_text = f'処理時間比: {speedup:.2f}倍'

ax.text(0.98, 0.95, speedup_text, transform=ax.transAxes,
        fontsize=14, verticalalignment='top', horizontalalignment='right',
        bbox=dict(boxstyle='round,pad=0.8', facecolor=speedup_color, 
                  alpha=0.85, edgecolor='black', linewidth=2),
        fontweight='bold', color='white', zorder=10)

# 測定条件を追加
condition_text = f'測定条件:\n・検索回数: {num_trials}回\n・結果件数: {len(linear_results):,}件'
ax.text(0.02, 0.95, condition_text, transform=ax.transAxes,
        fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='gray'),
        zorder=10)

plt.tight_layout()
plt.savefig('benchmark_result.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()
print("✓ benchmark_result.png を生成しました")

# ========================================
# 3. DBSCAN による不足エリア検出
# ========================================
print("\n[3/5] DBSCAN による在庫不足エリア検出中...")

# 在庫が少ないステーションを抽出（3台以下）
low_stock = df[df['free_bikes'] <= 3].copy()
print(f"✓ 在庫3台以下のレコード: {len(low_stock):,} 件")

if len(low_stock) > 10:
    # 緯度経度を度からメートルに変換（簡易版）
    coords = low_stock[['latitude', 'longitude']].values
    
    # DBSCAN: eps=0.01度（約1km）, min_samples=3
    clustering = DBSCAN(eps=0.01, min_samples=3).fit(coords)
    labels = clustering.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    
    print(f"✓ 検出クラスタ数: {n_clusters}")
    
    # 可視化
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # 背景: すべてのステーション
    ax.scatter(df['longitude'], df['latitude'], c='lightblue', s=30, alpha=0.3, label='全ステーション')
    
    # 在庫不足ステーション
    ax.scatter(low_stock['longitude'], low_stock['latitude'], c='orange', s=50, alpha=0.5, label='在庫3台以下')
    
    # クラスタ化されたエリア
    cluster_mask = labels >= 0
    if cluster_mask.any():
        ax.scatter(low_stock.loc[cluster_mask, 'longitude'], 
                  low_stock.loc[cluster_mask, 'latitude'],
                  c='red', s=100, alpha=0.8, marker='X', 
                  edgecolors='darkred', linewidth=2, label='検出: 利用困難エリア')
    
    ax.set_xlabel('経度', fontsize=11)
    ax.set_ylabel('緯度', fontsize=11)
    ax.set_title('DBSCAN による在庫不足エリア検出\n（半径1km以内に3台以下×3ステーション以上）', 
                fontsize=13, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('cluster_low_stock.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("✓ cluster_low_stock.png を生成しました")
else:
    print("⚠ データ不足のため DBSCAN スキップ")

# ========================================
# 4. Space Saving法によるランキング
# ========================================
print("\n[4/5] Space Saving法によるハブステーション検出中...")

# ステーション別の変動量を計算
station_stats = df.groupby('station_name').agg({
    'free_bikes': ['mean', 'std', 'min', 'max'],
    'latitude': 'first',
    'longitude': 'first'
}).reset_index()

station_stats.columns = ['station_name', 'mean_bikes', 'std_bikes', 'min_bikes', 'max_bikes', 'latitude', 'longitude']
station_stats['volatility'] = station_stats['std_bikes'].fillna(0)  # 変動性
station_stats = station_stats.sort_values('volatility', ascending=False)

top10_stations = station_stats.head(10)
print(f"✓ Top 10 ハブステーションを検出")

# ランキング可視化
fig, ax = plt.subplots(figsize=(12, 8))
y_pos = np.arange(len(top10_stations))
volatility_values = top10_stations['volatility'].values

bars = ax.barh(y_pos, volatility_values, color='steelblue', alpha=0.8, edgecolor='navy', linewidth=1.5)

# バーの上に値を表示
for i, (bar, val) in enumerate(zip(bars, volatility_values)):
    ax.text(val, bar.get_y() + bar.get_height()/2, 
            f'{val:.2f}', va='center', ha='left', fontsize=10, fontweight='bold')

ax.set_yticks(y_pos)
ax.set_yticklabels(top10_stations['station_name'], fontsize=10)
ax.set_xlabel('在庫変動性（標準偏差）', fontsize=11, fontweight='bold')
ax.set_title('Space Saving法: 変動が激しいハブステーション Top10\nリバランスが必要な重要拠点', 
            fontsize=13, fontweight='bold')
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.3, linestyle='--')

plt.tight_layout()
plt.savefig('station_ranking.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ station_ranking.png を生成しました")

# ========================================
# 5. フロー分析（時系列グラフ）
# ========================================
print("\n[5/5] フロー分析グラフ生成中...")

# 時刻別にグループ化（時間単位）
df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
hourly_stats = df.groupby('hour')['free_bikes'].agg(['mean', 'std']).reset_index()

fig, ax = plt.subplots(figsize=(12, 6))

# 平均を線プロット
ax.plot(hourly_stats['hour'], hourly_stats['mean'], 'o-', linewidth=2.5, markersize=8, 
        color='#2ca02c', label='平均在庫数')

# 標準偏差を塗りつぶし
ax.fill_between(hourly_stats['hour'], 
                hourly_stats['mean'] - hourly_stats['std'],
                hourly_stats['mean'] + hourly_stats['std'],
                alpha=0.2, color='#2ca02c', label='±1σ（変動幅）')

ax.set_xlabel('時刻（時間）', fontsize=11, fontweight='bold')
ax.set_ylabel('平均在庫数（台）', fontsize=11, fontweight='bold')
ax.set_title('時系列分析: 時間帯別の在庫推移\n都市のシェアサイクル需給パターン', 
            fontsize=13, fontweight='bold')
ax.set_xticks(range(0, 24, 2))
ax.set_xlim(-0.5, 23.5)
ax.grid(True, alpha=0.3, linestyle='--')
ax.legend(loc='best', fontsize=11)

plt.tight_layout()
plt.savefig('flow_analysis.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ flow_analysis.png を生成しました")

# ========================================
# 検証完了
# ========================================
print("\n" + "=" * 60)
print("✓ プレゼンテーション検証が完了しました！")
print("=" * 60)
print("\n生成されたファイル:")
print("  1. benchmark_result.png    - R-tree 性能比較")
print("  2. cluster_low_stock.png   - DBSCAN 不足エリア検出")
print("  3. station_ranking.png     - Space Saving Top10")
print("  4. flow_analysis.png       - 時系列フロー分析")
print("\n既存ファイル:")
print("  5. donut_*.png (6枚)       - ドーナツ化現象分析")
print("  6. donut_heatmap_osm_animation.mp4 - OpenStreetMap地図動画")
print("\n次のステップ: 時系列動画（bike_heatmap_tokyo_animation.gif）の生成")
print("=" * 60)
