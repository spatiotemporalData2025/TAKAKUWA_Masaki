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
df = pd.read_csv('bike_log_donut.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

print(f"✓ {len(df):,} 件のレコード読み込み完了")
print(f"  期間: {df['timestamp'].min()} ～ {df['timestamp'].max()}")

# 時刻ごとにグループ化（1時間ごとのフレームを作成）
df['hour'] = df['timestamp'].dt.hour
unique_hours = sorted(df['hour'].unique())
print(f"  利用可能な時刻: {len(unique_hours)}種類")

# 1時間ごとのスナップショットを抽出（24フレーム）
frame_data = []
for hour in unique_hours:
    hour_data = df[df['hour'] == hour]
    if len(hour_data) > 0:
        # 各時間の最初のタイムスタンプのデータを使用
        first_timestamp = hour_data['timestamp'].min()
        frame_data.append(hour_data[hour_data['timestamp'] == first_timestamp])

frames = pd.concat(frame_data, ignore_index=True) if frame_data else df
print(f"✓ {len(unique_hours)} フレームを選択（1時間ごと）")

# ========================================
# ヒートマップ動画の作成
# ========================================
print("\nヒートマップ動画を生成中...")

# 緯度経度の範囲（マージンを追加）
lat_min, lat_max = df['latitude'].min() - 0.01, df['latitude'].max() + 0.01
lon_min, lon_max = df['longitude'].min() - 0.01, df['longitude'].max() + 0.01

# グリッド作成（密なグリッドでスムーズなヒートマップ）
lat_range = np.linspace(lat_min, lat_max, 100)
lon_range = np.linspace(lon_min, lon_max, 100)
grid_lon, grid_lat = np.meshgrid(lon_range, lat_range)

# 図の設定
fig, ax = plt.subplots(figsize=(14, 10))

def animate(frame_idx):
    """各フレームの描画"""
    ax.clear()
    
    # 現在のフレームのタイムスタンプを取得
    frame_timestamps = frames['timestamp'].unique()
    current_timestamp = frame_timestamps[frame_idx]
    frame_df = frames[frames['timestamp'] == current_timestamp]
    
    # グリッド補間（cubic → linear で安定性向上）
    try:
        grid_bikes = griddata(
            (frame_df['longitude'].values, frame_df['latitude'].values),
            frame_df['free_bikes'].values,
            (grid_lon, grid_lat),
            method='cubic', fill_value=0
        )
        grid_bikes = np.clip(grid_bikes, 0, None)
    except Exception as e:
        # cubic失敗時はlinearにフォールバック
        grid_bikes = griddata(
            (frame_df['longitude'].values, frame_df['latitude'].values),
            frame_df['free_bikes'].values,
            (grid_lon, grid_lat),
            method='linear', fill_value=0
        )
    
    # ヒートマップ描画（半透明）
    contour = ax.contourf(
        grid_lon, grid_lat, grid_bikes,
        levels=20, cmap='YlOrRd', alpha=0.6, vmin=0, vmax=35
    )
    
    # ステーション散布図（エリア別色分け）
    if 'area_type' in frame_df.columns:
        downtown = frame_df[frame_df['area_type'] == 'downtown']
        suburb = frame_df[frame_df['area_type'] == 'suburb']
        
        if len(downtown) > 0:
            ax.scatter(downtown['longitude'], downtown['latitude'],
                      c=downtown['free_bikes'], s=200, cmap='Reds',
                      edgecolors='black', linewidths=2, vmin=0, vmax=35,
                      marker='s', label='都心部', alpha=0.9, zorder=5)
        
        if len(suburb) > 0:
            ax.scatter(suburb['longitude'], suburb['latitude'],
                      c=suburb['free_bikes'], s=200, cmap='Blues',
                      edgecolors='black', linewidths=2, vmin=0, vmax=35,
                      marker='o', label='郊外部', alpha=0.9, zorder=5)
    else:
        scatter = ax.scatter(
            frame_df['longitude'], frame_df['latitude'],
            c=frame_df['free_bikes'], s=150, cmap='YlOrRd',
            edgecolors='black', linewidths=1.5, vmin=0, vmax=35,
            zorder=5
        )
    
    # タイトルと情報表示
    hour = current_timestamp.hour
    minute = current_timestamp.minute
    
    title = f'東京シェアサイクル分布 {hour:02d}:{minute:02d}'
    ax.set_title(title, fontsize=16, fontweight='bold', pad=15)
    
    # 統計情報
    total_bikes = frame_df['free_bikes'].sum()
    avg_bikes = frame_df['free_bikes'].mean()
    
    stats_text = f'総台数: {int(total_bikes)}\n平均: {avg_bikes:.1f}台'
    ax.text(
        0.02, 0.98, stats_text,
        transform=ax.transAxes,
        fontsize=11, verticalalignment='top',
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.85, edgecolor='black'),
        zorder=10
    )
    
    # 軸ラベル
    ax.set_xlabel('経度', fontsize=11)
    ax.set_ylabel('緯度', fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(lon_min, lon_max)
    ax.set_ylim(lat_min, lat_max)
    
    # 凡例
    if 'area_type' in frame_df.columns:
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
    return []

# アニメーション作成
print(f"  {len(unique_hours)} フレームのアニメーションを作成...")
anim = FuncAnimation(
    fig, animate, frames=len(unique_hours),
    interval=500, repeat=True, blit=False
)

# GIF保存
try:
    output_file = 'bike_heatmap_tokyo_animation.gif'
    print(f"  GIF形式で保存中 ({output_file})...")
    writer = PillowWriter(fps=2)
    anim.save(output_file, writer=writer, dpi=120)
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
print(f"フレーム数: {len(unique_hours)}")
print(f"データ範囲: {lat_min:.4f}～{lat_max:.4f}°N, {lon_min:.4f}～{lon_max:.4f}°E")
print(f"時間帯カバー: 24時間（1時間ごと）")
print("\nプレゼンテーション用画像一覧:")
print("  1. benchmark_result.png    - R-tree性能比較")
print("  2. cluster_low_stock.png   - DBSCAN不足エリア検出")
print("  3. station_ranking.png     - Space Savingランキング")
print("  4. flow_analysis.png       - 時系列フロー分析")
print("  5. bike_heatmap_tokyo_animation.gif - 時系列ヒートマップ動画")
print("=" * 60)
