#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DBSCAN在庫不足エリア検出（OpenStreetMap地図背景版）
プレゼンテーション用の地図ベース可視化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
import sys
import contextily as ctx
import warnings
warnings.filterwarnings('ignore')

# 日本語フォント設定
def setup_japanese_font():
    if sys.platform == 'win32':
        plt.rcParams['font.family'] = 'MS Gothic'
    else:
        plt.rcParams['font.family'] = ['Hiragino Sans', 'Yu Gothic']
    plt.rcParams['axes.unicode_minus'] = False

setup_japanese_font()

def lat_lon_to_mercator(lat, lon):
    """緯度経度をWeb Mercator座標に変換"""
    import math
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * 20037508.34 / 180
    return x, y

def haversine_km(lat1, lon1, lat2, lon2):
    """2点間距離(km)を計算"""
    import math
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c

print("=" * 70)
print("DBSCAN 在庫不足エリア検出（地図背景版）")
print("=" * 70)

# データ読み込み
print("\nデータ読み込み中...")
df = pd.read_csv('bike_log.csv')
print(f"✓ {len(df):,} 件のレコード")

# 都心/郊外の簡易判定（東京駅からの距離）
TOKYO_STATION = (35.681236, 139.767125)
CORE_RADIUS_KM = 10.0
df['distance_km'] = df.apply(
    lambda r: haversine_km(r['latitude'], r['longitude'], TOKYO_STATION[0], TOKYO_STATION[1]),
    axis=1
)
core_mask = df['distance_km'] <= CORE_RADIUS_KM

# 在庫が少ないステーションを抽出（3台以下）
low_stock = df[df['free_bikes'] <= 3].copy()
low_stock_core = low_stock[core_mask].copy()

# 郊外で在庫が豊富なステーション（上位25%）
suburb = df[~core_mask].copy()
if len(suburb) > 0:
    abundant_threshold = max(8, suburb['free_bikes'].quantile(0.75))
    suburb_abundant = suburb[suburb['free_bikes'] >= abundant_threshold].copy()
else:
    abundant_threshold = 8
    suburb_abundant = suburb

print(f"✓ 在庫3台以下のレコード: {len(low_stock):,} 件 ({len(low_stock)/len(df)*100:.1f}%)")
print(f"✓ 都心(東京駅から{CORE_RADIUS_KM:.0f}km以内): {core_mask.sum():,} 件")
print(f"✓ 郊外(東京駅から{CORE_RADIUS_KM:.0f}km超): {len(df) - core_mask.sum():,} 件")

if len(low_stock_core) > 10:
    # DBSCAN クラスタリング
    print("\nDBSCAN クラスタリング実行中...")
    coords = low_stock_core[['latitude', 'longitude']].values
    clustering = DBSCAN(eps=0.01, min_samples=3).fit(coords)
    labels = clustering.labels_
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    
    print(f"✓ 検出クラスタ数: {n_clusters}")
    print(f"  eps: 0.01度（約1km）")
    print(f"  min_samples: 3ステーション")
    
    # Web Mercator座標に変換
    print("\n地図座標に変換中...")
    df['x_merc'], df['y_merc'] = zip(*df.apply(
        lambda row: lat_lon_to_mercator(row['latitude'], row['longitude']), axis=1
    ))
    low_stock_core['x_merc'], low_stock_core['y_merc'] = zip(*low_stock_core.apply(
        lambda row: lat_lon_to_mercator(row['latitude'], row['longitude']), axis=1
    ))
    suburb_abundant['x_merc'], suburb_abundant['y_merc'] = zip(*suburb_abundant.apply(
        lambda row: lat_lon_to_mercator(row['latitude'], row['longitude']), axis=1
    ))
    
    # 地図の範囲を設定
    lat_min, lat_max = df['latitude'].min() - 0.02, df['latitude'].max() + 0.02
    lon_min, lon_max = df['longitude'].min() - 0.02, df['longitude'].max() + 0.02
    xmin, ymin = lat_lon_to_mercator(lat_min, lon_min)
    xmax, ymax = lat_lon_to_mercator(lat_max, lon_max)
    
    # 図の作成
    print("\n地図背景付き可視化を生成中...")
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # OpenStreetMap背景を追加
    try:
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ctx.add_basemap(
            ax,
            source=ctx.providers.OpenStreetMap.Mapnik,
            zoom=12,
            attribution="© OpenStreetMap contributors"
        )
        print("  ✓ OpenStreetMap背景を追加")
    except Exception as e:
        print(f"  ! OpenStreetMap取得失敗: {e}")
        print("  背景なしで続行...")
    
    # 全ステーション（台数に応じてカラーマップで色分け）
    scatter = ax.scatter(df['x_merc'], df['y_merc'], 
                        c=df['free_bikes'], 
                        cmap='RdYlGn',  # 赤（少ない）→黄→緑（多い）
                        s=60, alpha=0.35, 
                        edgecolors='none',
                        vmin=0, vmax=df['free_bikes'].quantile(0.95),
                        label='全ステーション（台数別）', zorder=2)
    
    # カラーバーを追加
    cbar = plt.colorbar(scatter, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label('利用可能台数', fontsize=13, fontweight='bold')
    cbar.ax.tick_params(labelsize=11)
    
    # 都心: 在庫3台以下（濃いオレンジで強調）
    ax.scatter(low_stock_core['x_merc'], low_stock_core['y_merc'], 
              c='darkorange', s=140, alpha=0.95, 
              edgecolors='orangered', linewidths=2.0,
              label=f'都心(東京駅{CORE_RADIUS_KM:.0f}km以内): 在庫3台以下', zorder=4)

    # 郊外: 在庫が豊富（上位25%）
    if len(suburb_abundant) > 0:
        ax.scatter(suburb_abundant['x_merc'], suburb_abundant['y_merc'],
                  c='green', s=120, alpha=0.85, marker='s',
                  edgecolors='darkgreen', linewidths=1.5,
                  label=f'郊外(東京駅{CORE_RADIUS_KM:.0f}km超): 在庫豊富(≥{abundant_threshold:.0f}台)',
                  zorder=4)
    
    # クラスタ化されたエリア（赤×）
    cluster_mask = labels >= 0
    if cluster_mask.any():
        cluster_data = low_stock_core[cluster_mask]
        ax.scatter(cluster_data['x_merc'], cluster_data['y_merc'],
                  c='red', s=250, alpha=0.9, marker='X', 
                  edgecolors='darkred', linewidths=3,
                  label=f'検出: 利用困難エリア ({n_clusters}クラスタ)', 
                  zorder=5)
        
        # クラスタごとに円で囲む
        for cluster_id in set(labels[labels >= 0]):
            cluster_points = low_stock_core[labels == cluster_id]
            if len(cluster_points) >= 3:
                center_x = cluster_points['x_merc'].mean()
                center_y = cluster_points['y_merc'].mean()
                
                # クラスタの範囲を計算
                radius = np.sqrt(
                    (cluster_points['x_merc'] - center_x).pow(2).max() +
                    (cluster_points['y_merc'] - center_y).pow(2).max()
                ) * 1.2
                
                circle = plt.Circle((center_x, center_y), radius, 
                                   color='red', fill=False, 
                                   linewidth=3, linestyle='--', 
                                   alpha=0.6, zorder=6)
                ax.add_patch(circle)
    
    # タイトルと説明
    ax.set_title('DBSCAN による在庫不足エリア検出\n（都心: 1km以内に3台以下×3ステーション以上）', 
                fontsize=17, fontweight='bold', pad=20)
    
    # 凡例
    ax.legend(loc='upper right', fontsize=13, framealpha=0.95, 
             edgecolor='black', fancybox=True, shadow=True)
    
    # 軸ラベルを削除（地図なので不要）
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_xticks([])
    ax.set_yticks([])
    
    # 統計情報ボックス
    stats_text = (
        f'【検出結果】\n'
        f'・総ステーション: {len(df):,}\n'
        f'・都心在庫不足: {len(low_stock_core):,}件\n'
        f'・郊外在庫豊富: {len(suburb_abundant):,}件\n'
        f'・クラスタ数: {n_clusters}\n'
        f'・検出率: {len(low_stock_core[cluster_mask])/len(low_stock_core)*100:.1f}%'
    )
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           fontsize=12, verticalalignment='top',
           bbox=dict(boxstyle='round,pad=0.8', facecolor='white', 
                     alpha=0.95, edgecolor='black', linewidth=2),
           zorder=10)
    
    # OpenStreetMapクレジット
    ax.text(0.99, 0.01, '© OpenStreetMap contributors',
           transform=ax.transAxes,
           fontsize=9, ha='right', va='bottom',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8),
           zorder=10)
    
    plt.tight_layout()
    plt.savefig('cluster_low_stock.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print("  ✓ cluster_low_stock.png を保存")
    
else:
    print("\n⚠ データ不足のためDBSCANスキップ")

print("\n" + "=" * 70)
print("完了！")
print("=" * 70)
print("\n生成ファイル: cluster_low_stock.png")
print("  - OpenStreetMap背景付き")
print("  - DBSCANクラスタ検出: 赤い×印")
print("  - クラスタ範囲: 赤い点線の円")
print("  - 在庫不足ステーション: オレンジ")
print("=" * 70)
