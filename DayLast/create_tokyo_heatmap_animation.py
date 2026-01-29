#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
東京実データによるヒートマップ動画生成
bike_log.csv（43,129レコード）を使用して、
実際のシェアサイクル需給パターンを可視化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from scipy.interpolate import griddata
import sys
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
def setup_japanese_font():
    if sys.platform == 'win32':
        plt.rcParams['font.family'] = 'MS Gothic'
    else:
        plt.rcParams['font.family'] = ['Hiragino Sans', 'Yu Gothic', 'Meiryo', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.size'] = 10

setup_japanese_font()

print("=" * 60)
print("東京シェアサイクル時系列ヒートマップ動画生成")
print("（プレゼンテーション用）")
print("=" * 60)

# ========================================
# データ読み込みと前処理
# ========================================
print("\nデータ読み込み中...")
df = pd.read_csv('bike_log.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

print(f"✓ {len(df):,} 件のレコード読み込み完了")
print(f"  期間: {df['timestamp'].min()} ～ {df['timestamp'].max()}")

# 複数のスナップショット時刻を選択（時間帯ごとに均等に選択）
df['hour'] = df['timestamp'].dt.hour
unique_hours = sorted(df['hour'].unique())
print(f"  利用可能な時刻: {len(unique_hours)}種類")

# 各時刻から1つのスナップショットを抽出
frame_data = []
for hour in unique_hours[:8]:  # 最初の8時刻を使用（ビデオ短縮のため）
    hour_data = df[df['hour'] == hour]
    if len(hour_data) > 0:
        frame_data.append(hour_data.iloc[0:1])  # 各時刻から1フレーム

frames = pd.concat(frame_data, ignore_index=True) if frame_data else df[:8]
print(f"✓ {len(frames)} フレームを選択")

# ========================================
# ヒートマップ動画の作成
# ========================================
print("\nヒートマップ動画を生成中...")

# 緯度経度の範囲
lat_min, lat_max = df['latitude'].min(), df['latitude'].max()
lon_min, lon_max = df['longitude'].min(), df['longitude'].max()

# グリッド作成
lat_range = np.linspace(lat_min, lat_max, 50)
lon_range = np.linspace(lon_min, lon_max, 50)
grid_lon, grid_lat = np.meshgrid(lon_range, lat_range)

# 図の設定
fig, ax = plt.subplots(figsize=(14, 10))

def animate(frame_idx):
    """各フレームの描画"""
    ax.clear()
    
    # 現在のフレームデータを取得
    frame_df = frames.iloc[frame_idx:frame_idx+1]
    
    # グリッド補間
    try:
        grid_bikes = griddata(
            (frame_df['longitude'].values, frame_df['latitude'].values),
            frame_df['free_bikes'].values,
            (grid_lon, grid_lat),
            method='nearest', fill_value=0
        )
    except Exception as e:
        print(f"  補間エラー (フレーム{frame_idx}): {e}")
        grid_bikes = np.zeros_like(grid_lon)
    
    # ヒートマップ描画
    contour = ax.contourf(
        grid_lon, grid_lat, grid_bikes,
        levels=15, cmap='YlOrRd', alpha=0.7
    )
    
    # ステーション散布図
    scatter = ax.scatter(
        frame_df['longitude'], frame_df['latitude'],
        c=frame_df['free_bikes'], s=100, cmap='YlOrRd',
        edgecolors='black', linewidths=1, vmin=0, vmax=35,
        zorder=5
    )
    
    # タイトルと情報表示
    timestamp = frame_df['timestamp'].iloc[0]
    hour = timestamp.hour
    minute = timestamp.minute
    
    title = f'東京シェアサイクル分布 {hour:02d}:{minute:02d}'
    ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    
    # 統計情報
    total_bikes = frame_df['free_bikes'].sum()
    avg_bikes = frame_df['free_bikes'].mean()
    max_bikes = frame_df['free_bikes'].max()
    min_bikes = frame_df['free_bikes'].min()
    
    stats_text = f'総台数: {int(total_bikes)}\n平均: {avg_bikes:.1f}台\n最大: {int(max_bikes)}台\n最小: {int(min_bikes)}台'
    ax.text(
        0.02, 0.98, stats_text,
        transform=ax.transAxes,
        fontsize=10, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8, edgecolor='black'),
        zorder=10
    )
    
    # 軸ラベル
    ax.set_xlabel('経度', fontsize=11)
    ax.set_ylabel('緯度', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    # カラーバー
    cbar = plt.colorbar(scatter, ax=ax, label='自転車台数（台）')
    
    return [scatter, contour, cbar.ax]

# アニメーション作成
print(f"  {len(frames)} フレームのアニメーションを作成...")
anim = FuncAnimation(
    fig, animate, frames=len(frames),
    interval=1000, repeat=True, blit=False
)

# GIF保存
try:
    output_file = 'bike_heatmap_tokyo_animation.gif'
    print(f"  GIF形式で保存中 ({output_file})...")
    writer = PillowWriter(fps=1)
    anim.save(output_file, writer=writer, dpi=100)
    print(f"✓ {output_file} を保存しました")
except Exception as e:
    print(f"✗ GIF保存エラー: {e}")

plt.close()

# ========================================
# 完了メッセージ
# ========================================
print("\n" + "=" * 60)
print("✓ 時系列ヒートマップ動画生成が完了しました！")
print("=" * 60)
print(f"\n生成ファイル: bike_heatmap_tokyo_animation.gif")
print(f"フレーム数: {len(frames)}")
print(f"データ範囲: {lat_min:.4f}～{lat_max:.4f}°N, {lon_min:.4f}～{lon_max:.4f}°E")
print(f"時間帯カバー: 複数スナップショット")
print("\nプレゼンテーション用画像一覧:")
print("  1. benchmark_result.png    - R-tree性能比較")
print("  2. cluster_low_stock.png   - DBSCAN不足エリア検出")
print("  3. station_ranking.png     - Space Savingランキング")
print("  4. flow_analysis.png       - 時系列フロー分析")
print("  5. bike_heatmap_tokyo_animation.gif - 時系列ヒートマップ動画")
print("=" * 60)
