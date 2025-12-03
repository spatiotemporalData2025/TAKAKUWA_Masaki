"""
降水地点のクラスタリング結果を可視化（雨雲レーダー風）

実際の気象データから検出された雨雲クラスタを、
雨雲レーダーのように色分けして表示します。

実行方法:
    cd examples
    python visualize_rain_clusters.py
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from st_dbscan import STDBSCAN
from weather_data import fetch_tokyo_data
from export_utils import ClusteringResultExporter
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.animation import FuncAnimation, PillowWriter
import pandas as pd
import numpy as np

# 日本語フォント設定
try:
    from font_config import setup_japanese_font
    setup_japanese_font()
except:
    print("⚠️  日本語フォントの設定をスキップします")


def filter_data_for_visualization(weather_points, num_hours=6, min_value=0.5):
    """可視化用にデータをフィルタリング"""
    sorted_points = sorted(weather_points, key=lambda p: p.time)
    unique_times = sorted(list(set(p.time for p in sorted_points)))
    target_times = set(unique_times[:num_hours])
    
    filtered = [p for p in sorted_points 
                if p.time in target_times and p.value >= min_value]
    
    return filtered, list(target_times)


def create_rain_radar_plot(df, time_value, output_path, title_suffix=""):
    """
    特定時刻の雨雲レーダー風プロットを作成
    
    Parameters
    ----------
    df : pd.DataFrame
        クラスタリング結果のDataFrame
    time_value : float
        表示する時刻
    output_path : str
        保存先のパス
    title_suffix : str
        タイトルに追加する文字列
    """
    # 特定時刻のデータを抽出
    time_data = df[df['time'] == time_value].copy()
    
    if len(time_data) == 0:
        print(f"  ⚠️  時刻 {time_value} のデータがありません")
        return
    
    # 図の作成
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # 背景色を設定（レーダー風）
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#0f0f1e')
    
    # クラスタとノイズを分離
    noise = time_data[time_data['cluster'] == 0]
    clusters = time_data[time_data['cluster'] > 0]
    
    # ノイズをプロット（小さく薄く）
    if len(noise) > 0:
        ax.scatter(noise['lon'], noise['lat'], 
                  c='#666666', s=10, alpha=0.2, 
                  label='ノイズ', marker='.')
    
    # クラスタをプロット
    if len(clusters) > 0:
        # クラスタIDでカラーマップ
        cluster_ids = clusters['cluster'].unique()
        n_clusters = len(cluster_ids)
        
        # 雨雲レーダー風の色設定
        # 降水量に応じた色: 弱い雨(青) → 強い雨(赤)
        colors = []
        sizes = []
        
        for _, row in clusters.iterrows():
            value = row['value']
            cluster_id = row['cluster']
            
            # 降水量に応じた色（青→緑→黄→赤）
            if value < 1.0:
                color = '#4a90e2'  # 青（弱い雨）
                size = 50
            elif value < 2.0:
                color = '#50c878'  # 緑（中程度）
                size = 80
            elif value < 5.0:
                color = '#f5d100'  # 黄（やや強い雨）
                size = 120
            else:
                color = '#ff4444'  # 赤（強い雨）
                size = 150
            
            colors.append(color)
            sizes.append(size)
        
        # プロット
        scatter = ax.scatter(clusters['lon'], clusters['lat'],
                           c=colors, s=sizes, alpha=0.7,
                           edgecolors='white', linewidths=0.5)
        
        # クラスタごとに境界線を描画
        for cluster_id in cluster_ids:
            cluster_data = clusters[clusters['cluster'] == cluster_id]
            
            # クラスタの中心を計算
            center_lon = cluster_data['lon'].mean()
            center_lat = cluster_data['lat'].mean()
            
            # クラスタ番号を表示
            ax.text(center_lon, center_lat, f'#{int(cluster_id)}',
                   color='white', fontsize=12, fontweight='bold',
                   ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', 
                           facecolor='black', alpha=0.7, edgecolor='white'))
    
    # 凡例を作成（降水量の色分け）
    legend_elements = [
        mpatches.Patch(facecolor='#4a90e2', edgecolor='white', 
                      label='弱い雨 (< 1.0 mm/h)'),
        mpatches.Patch(facecolor='#50c878', edgecolor='white', 
                      label='中程度 (1.0-2.0 mm/h)'),
        mpatches.Patch(facecolor='#f5d100', edgecolor='white', 
                      label='やや強い雨 (2.0-5.0 mm/h)'),
        mpatches.Patch(facecolor='#ff4444', edgecolor='white', 
                      label='強い雨 (≥ 5.0 mm/h)'),
    ]
    
    if len(noise) > 0:
        legend_elements.append(
            mpatches.Patch(facecolor='#666666', edgecolor='white', 
                          label='ノイズ', alpha=0.3)
        )
    
    ax.legend(handles=legend_elements, loc='upper right',
             framealpha=0.9, facecolor='#1a1a2e', edgecolor='white',
             fontsize=10)
    
    # 軸ラベルとタイトル
    ax.set_xlabel('経度 (°E)', color='white', fontsize=12)
    ax.set_ylabel('緯度 (°N)', color='white', fontsize=12)
    
    # 時刻を表示
    dt = datetime.fromtimestamp(time_value)
    time_str = dt.strftime('%Y年%m月%d日 %H:%M')
    
    title = f'雨雲レーダー - {time_str}'
    if title_suffix:
        title += f' {title_suffix}'
    
    ax.set_title(title, color='white', fontsize=16, fontweight='bold', pad=20)
    
    # グリッド
    ax.grid(True, alpha=0.2, color='white', linestyle='--')
    ax.tick_params(colors='white')
    
    # 軸の色
    ax.spines['bottom'].set_color('white')
    ax.spines['top'].set_color('white')
    ax.spines['left'].set_color('white')
    ax.spines['right'].set_color('white')
    
    # 統計情報を表示
    n_clusters = len(clusters['cluster'].unique()) if len(clusters) > 0 else 0
    stats_text = f'クラスタ数: {n_clusters}\n降水ポイント数: {len(time_data)}'
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
           color='white', fontsize=10, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, facecolor='#0f0f1e', edgecolor='none')
    plt.close()
    
    print(f"  ✓ 保存: {output_path}")


def create_rain_animation(df, unique_times, output_path):
    """
    雨雲の時間変化アニメーションを作成
    
    Parameters
    ----------
    df : pd.DataFrame
        クラスタリング結果のDataFrame
    unique_times : List[float]
        時刻のリスト
    output_path : str
        保存先のパス
    """
    print("\n  アニメーション作成中...")
    
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # 背景色
    ax.set_facecolor('#1a1a2e')
    fig.patch.set_facecolor('#0f0f1e')
    
    # 軸の範囲を固定
    all_lats = df['lat']
    all_lons = df['lon']
    lat_margin = (all_lats.max() - all_lats.min()) * 0.1
    lon_margin = (all_lons.max() - all_lons.min()) * 0.1
    
    ax.set_xlim(all_lons.min() - lon_margin, all_lons.max() + lon_margin)
    ax.set_ylim(all_lats.min() - lat_margin, all_lats.max() + lat_margin)
    
    def update(frame):
        ax.clear()
        ax.set_facecolor('#1a1a2e')
        
        time_value = unique_times[frame]
        time_data = df[df['time'] == time_value]
        
        if len(time_data) == 0:
            return
        
        # ノイズとクラスタを分離
        noise = time_data[time_data['cluster'] == 0]
        clusters = time_data[time_data['cluster'] > 0]
        
        # ノイズをプロット
        if len(noise) > 0:
            ax.scatter(noise['lon'], noise['lat'], 
                      c='#666666', s=10, alpha=0.2, marker='.')
        
        # クラスタをプロット
        if len(clusters) > 0:
            colors = []
            sizes = []
            
            for _, row in clusters.iterrows():
                value = row['value']
                
                if value < 1.0:
                    color = '#4a90e2'
                    size = 50
                elif value < 2.0:
                    color = '#50c878'
                    size = 80
                elif value < 5.0:
                    color = '#f5d100'
                    size = 120
                else:
                    color = '#ff4444'
                    size = 150
                
                colors.append(color)
                sizes.append(size)
            
            ax.scatter(clusters['lon'], clusters['lat'],
                      c=colors, s=sizes, alpha=0.7,
                      edgecolors='white', linewidths=0.5)
            
            # クラスタIDを表示
            for cluster_id in clusters['cluster'].unique():
                cluster_data = clusters[clusters['cluster'] == cluster_id]
                center_lon = cluster_data['lon'].mean()
                center_lat = cluster_data['lat'].mean()
                
                ax.text(center_lon, center_lat, f'#{int(cluster_id)}',
                       color='white', fontsize=10, fontweight='bold',
                       ha='center', va='center',
                       bbox=dict(boxstyle='round,pad=0.3', 
                               facecolor='black', alpha=0.7))
        
        # タイトル
        dt = datetime.fromtimestamp(time_value)
        time_str = dt.strftime('%Y年%m月%d日 %H:%M')
        ax.set_title(f'雨雲レーダー - {time_str}', 
                    color='white', fontsize=16, fontweight='bold', pad=20)
        
        # 軸設定
        ax.set_xlabel('経度 (°E)', color='white', fontsize=12)
        ax.set_ylabel('緯度 (°N)', color='white', fontsize=12)
        ax.grid(True, alpha=0.2, color='white', linestyle='--')
        ax.tick_params(colors='white')
        
        for spine in ax.spines.values():
            spine.set_color('white')
        
        # 統計情報
        n_clusters = len(clusters['cluster'].unique()) if len(clusters) > 0 else 0
        stats_text = f'クラスタ数: {n_clusters}\nフレーム: {frame+1}/{len(unique_times)}'
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
               color='white', fontsize=10, verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='black', alpha=0.7))
    
    anim = FuncAnimation(fig, update, frames=len(unique_times), 
                        interval=500, repeat=True)
    
    writer = PillowWriter(fps=2)
    anim.save(output_path, writer=writer, dpi=100)
    plt.close()
    
    print(f"  ✓ アニメーション保存: {output_path}")


def main():
    print("=" * 70)
    print("🌧️ 降水地点のクラスタリング結果を可視化（雨雲レーダー風）")
    print("=" * 70)
    
    # ========================================
    # ステップ1: データ取得とクラスタリング
    # ========================================
    print("\n[1/4] データ取得とクラスタリング...")
    
    weather_points = fetch_tokyo_data(cache_dir='../data')
    print(f"  ✓ {len(weather_points)} 個の降水ポイントを取得")
    
    # フィルタリング
    filtered_points, unique_times = filter_data_for_visualization(
        weather_points, num_hours=6, min_value=0.5
    )
    print(f"  ✓ {len(filtered_points)} ポイントにフィルタリング（{len(unique_times)}時間分）")
    
    if len(filtered_points) < 20:
        print("  ⚠️  データポイントが少なすぎます")
        return
    
    # クラスタリング
    print("\n[2/4] ST-DBSCANクラスタリング実行中...")
    stdbscan = STDBSCAN(eps1=25.0, eps2=7200.0, min_pts=5)
    stdbscan.fit(filtered_points)
    
    stats = stdbscan.get_statistics()
    print(f"  ✓ クラスタリング完了")
    print(f"    検出されたクラスタ数: {stats['n_clusters']}")
    print(f"    ノイズ比率: {stats['noise_ratio']*100:.1f}%")
    
    # ========================================
    # ステップ3: データエクスポート
    # ========================================
    print("\n[3/4] 可視化用データをエクスポート...")
    output_dir = Path(__file__).parent.parent / 'output' / 'rain_radar_visualization'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exporter = ClusteringResultExporter(stdbscan)
    exporter.export_for_visualization(str(output_dir))
    
    # ========================================
    # ステップ4: 可視化
    # ========================================
    print("\n[4/4] 雨雲レーダー風の可視化を作成中...")
    
    df = exporter.to_dataframe()
    
    # 各時刻の画像を作成
    print("\n  各時刻の静止画を作成中...")
    for i, time_value in enumerate(unique_times[:3]):  # 最初の3時刻
        dt = datetime.fromtimestamp(time_value)
        filename = f"rain_radar_{dt.strftime('%Y%m%d_%H%M')}.png"
        output_path = output_dir / filename
        
        create_rain_radar_plot(df, time_value, str(output_path), 
                              title_suffix=f"({i+1}/{len(unique_times)})")
    
    # アニメーションを作成
    print("\n  アニメーションを作成中...")
    animation_path = output_dir / "rain_radar_animation.gif"
    create_rain_animation(df, unique_times, str(animation_path))
    
    # ========================================
    # 完了
    # ========================================
    print("\n" + "=" * 70)
    print("✨ 可視化完了！")
    print("=" * 70)
    print(f"\n📂 出力先: {output_dir}")
    print("\n📊 作成されたファイル:")
    print("  【可視化】")
    print("    - rain_radar_*.png: 各時刻の雨雲レーダー画像")
    print("    - rain_radar_animation.gif: 時間変化アニメーション")
    print("\n  【データ】")
    print("    - clustering_result.csv: 全ポイント情報（可視化担当者用）")
    print("    - clustering_result.json: JSON形式データ")
    print("    - cluster_colors.json: 推奨色情報")
    print("    - cluster_bounds.json: クラスタ範囲")
    print("    - clusters_by_time.json: 時刻別データ")
    
    print("\n💡 可視化担当者へ:")
    print(f"  {output_dir} 内のデータを使って")
    print("  独自の可視化を作成できます！")
    print("\n  参考: docs/HANDOFF_TO_VISUALIZATION.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
