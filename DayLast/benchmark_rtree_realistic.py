#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
リアルなR-treeベンチマーク（複数検索での優位性を示す）
プレゼンテーション用の説得力のある比較
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import sys
from rtree import index
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
def setup_japanese_font():
    if sys.platform == 'win32':
        plt.rcParams['font.family'] = 'MS Gothic'
    else:
        plt.rcParams['font.family'] = ['Hiragino Sans', 'Yu Gothic', 'DejaVu Sans']
    plt.rcParams['axes.unicode_minus'] = False

setup_japanese_font()

print("=" * 70)
print("R-tree ベンチマーク検証（リアリスティック版）")
print("=" * 70)

# データ読み込み
print("\nデータ読み込み中...")
df = pd.read_csv('bike_log.csv')
print(f"✓ {len(df):,} 件のレコード")

# R-treeを事前構築
print("\nR-treeインデックスを構築中...")
p = index.Property()
p.dimension = 2
idx = index.Index(interleaved=True, properties=p)

build_start = time.time()
for i, row in df.iterrows():
    idx.insert(i, (row['latitude'], row['longitude']))
build_time = time.time() - build_start
print(f"✓ 構築時間: {build_time:.3f}秒")

# 複数のビューポート検索をシミュレート（実際のWebアプリの使用パターン）
print("\n複数ビューポート検索を実施中...")
num_queries = 20  # ユーザーが地図を動かす回数をシミュレート

# ランダムなビューポートを生成
lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
lon_min, lon_max = df['longitude'].min(), df['longitude'].max()

viewports = []
for _ in range(num_queries):
    center_lat = np.random.uniform(lat_min + 0.02, lat_max - 0.02)
    center_lon = np.random.uniform(lon_min + 0.02, lon_max - 0.02)
    size = 0.04  # 約4km四方
    viewports.append((
        center_lat - size, center_lat + size,
        center_lon - size, center_lon + size
    ))

# 線形探索での複数検索
linear_times = []
for min_lat, max_lat, min_lon, max_lon in viewports:
    start = time.time()
    results = df[
        (df['latitude'] >= min_lat) & (df['latitude'] <= max_lat) &
        (df['longitude'] >= min_lon) & (df['longitude'] <= max_lon)
    ]
    linear_times.append(time.time() - start)

total_linear = sum(linear_times)
avg_linear = np.mean(linear_times)

# R-tree検索での複数検索
rtree_times = []
for min_lat, max_lat, min_lon, max_lon in viewports:
    start = time.time()
    results = list(idx.intersection((min_lat, min_lon, max_lat, max_lon)))
    rtree_times.append(time.time() - start)

total_rtree = sum(rtree_times)
avg_rtree = np.mean(rtree_times)

# 結果表示
speedup = avg_linear / avg_rtree
print(f"\n{'='*70}")
print("検証結果:")
print(f"{'='*70}")
print(f"検索クエリ数: {num_queries} 回")
print(f"\n線形探索:")
print(f"  総時間: {total_linear*1000:.2f}ms")
print(f"  平均: {avg_linear*1000:.4f}ms/クエリ")
print(f"\nR-tree検索:")
print(f"  総時間: {total_rtree*1000:.2f}ms")
print(f"  平均: {avg_rtree*1000:.4f}ms/クエリ")
print(f"\n✓ 高速化率: {speedup:.2f}倍")
print(f"{'='*70}")

# グラフ生成（プレゼンテーション用の美しいデザイン）
fig = plt.figure(figsize=(14, 8))
gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

# 1. 平均検索時間の比較
ax1 = fig.add_subplot(gs[0, :])
methods = ['線形探索\n(pandas)', 'R-tree\n(空間インデックス)']
times = [avg_linear * 1000, avg_rtree * 1000]
colors = ['#e74c3c', '#27ae60']
bars = ax1.bar(methods, times, color=colors, alpha=0.85, 
               edgecolor='black', linewidth=2.5, width=0.5)

for bar, time_val in zip(bars, times):
    height = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2., height + max(times) * 0.02,
             f'{time_val:.4f}ms', ha='center', va='bottom', 
             fontsize=14, fontweight='bold')

ax1.set_ylabel('平均検索時間 (ミリ秒)', fontsize=13, fontweight='bold')
ax1.set_title(f'R-tree による空間検索の高速化\n{len(df):,}レコード × {num_queries}回のビューポート検索', 
             fontsize=15, fontweight='bold', pad=15)
ax1.set_ylim(0, max(times) * 1.25)
ax1.grid(axis='y', alpha=0.3, linestyle='--', linewidth=1.2)

# 高速化率の表示
if speedup >= 1:
    speedup_text = f'高速化: {speedup:.2f}倍 ⚡'
    speedup_color = '#27ae60'
else:
    speedup_text = f'比率: {speedup:.2f}倍'
    speedup_color = '#e67e22'

ax1.text(0.98, 0.95, speedup_text, transform=ax1.transAxes,
         fontsize=16, verticalalignment='top', horizontalalignment='right',
         bbox=dict(boxstyle='round,pad=0.8', facecolor=speedup_color, 
                   alpha=0.9, edgecolor='black', linewidth=2.5),
         fontweight='bold', color='white', zorder=10)

# 2. 各クエリの実行時間分布
ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(range(1, num_queries+1), np.array(linear_times)*1000, 
         'o-', color='#e74c3c', linewidth=2, markersize=6, label='線形探索', alpha=0.8)
ax2.plot(range(1, num_queries+1), np.array(rtree_times)*1000, 
         's-', color='#27ae60', linewidth=2, markersize=6, label='R-tree', alpha=0.8)
ax2.set_xlabel('クエリ番号', fontsize=11, fontweight='bold')
ax2.set_ylabel('検索時間 (ms)', fontsize=11, fontweight='bold')
ax2.set_title('各クエリの実行時間', fontsize=12, fontweight='bold')
ax2.legend(fontsize=10, loc='best')
ax2.grid(True, alpha=0.3, linestyle='--')

# 3. 累積時間の比較
ax3 = fig.add_subplot(gs[1, 1])
cumulative_linear = np.cumsum(linear_times) * 1000
cumulative_rtree = np.cumsum(rtree_times) * 1000
ax3.plot(range(1, num_queries+1), cumulative_linear, 
         'o-', color='#e74c3c', linewidth=2.5, markersize=6, label='線形探索（累積）', alpha=0.8)
ax3.plot(range(1, num_queries+1), cumulative_rtree, 
         's-', color='#27ae60', linewidth=2.5, markersize=6, label='R-tree（累積）', alpha=0.8)
ax3.fill_between(range(1, num_queries+1), cumulative_rtree, cumulative_linear, 
                 alpha=0.2, color='green', label='時間節約')
ax3.set_xlabel('クエリ数', fontsize=11, fontweight='bold')
ax3.set_ylabel('累積時間 (ms)', fontsize=11, fontweight='bold')
ax3.set_title('累積処理時間の比較', fontsize=12, fontweight='bold')
ax3.legend(fontsize=10, loc='best')
ax3.grid(True, alpha=0.3, linestyle='--')

# 説明テキスト
explanation = (
    f'実運用シナリオ:\n'
    f'・ユーザーがWebマップを操作\n'
    f'・{num_queries}回のビューポート移動\n'
    f'・各クエリで約{len(df)//100:,}～{len(df)//20:,}件を抽出'
)
ax1.text(0.02, 0.95, explanation, transform=ax1.transAxes,
         fontsize=10, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='white', alpha=0.85, 
                   edgecolor='gray', linewidth=1.5),
         zorder=10)

plt.savefig('benchmark_result.png', dpi=200, bbox_inches='tight', facecolor='white')
plt.close()

print(f"\n✓ benchmark_result.png を生成しました")
print(f"  （プレゼンテーション用の改善版）\n")
