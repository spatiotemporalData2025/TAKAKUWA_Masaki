"""
可視化担当者向けのサンプルスクリプト

エクスポートされたクラスタリング結果を読み込んで可視化する例
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import json
from font_config import setup_japanese_font

# 日本語フォントを設定
setup_japanese_font()


def load_data(data_dir='../output/visualization_data'):
    """
    エクスポートされたデータを読み込む
    
    Parameters
    ----------
    data_dir : str
        データディレクトリのパス
        
    Returns
    -------
    tuple
        (df, colors, bounds, time_data)
    """
    # CSVファイルから全データを読み込み
    df = pd.read_csv(f'{data_dir}/clustering_result.csv')
    
    # クラスタの色情報を読み込み
    with open(f'{data_dir}/cluster_colors.json', 'r') as f:
        colors = json.load(f)
    
    # クラスタの境界情報を読み込み
    with open(f'{data_dir}/cluster_bounds.json', 'r') as f:
        bounds = json.load(f)
    
    # 時刻ごとのデータを読み込み
    with open(f'{data_dir}/clusters_by_time.json', 'r') as f:
        time_data = json.load(f)
    
    return df, colors, bounds, time_data


def visualize_single_timestep(df, time_step, output_file=None):
    """
    特定の時刻のクラスタを可視化
    
    Parameters
    ----------
    df : pd.DataFrame
        クラスタリング結果のDataFrame
    time_step : float
        表示する時刻
    output_file : str, optional
        保存先ファイル名
    """
    # 指定時刻のデータを抽出
    time_data = df[df['time'] == time_step]
    
    if len(time_data) == 0:
        print(f"No data for time {time_step}")
        return
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # ノイズを描画（灰色）
    noise = time_data[time_data['cluster'] == 0]
    if len(noise) > 0:
        ax.scatter(noise['lon'], noise['lat'], 
                  c='gray', s=20, alpha=0.3, label='Noise', marker='x')
    
    # クラスタを描画
    clusters = time_data[time_data['cluster'] > 0]
    if len(clusters) > 0:
        # 降水量でサイズを変更、クラスタIDで色分け
        scatter = ax.scatter(clusters['lon'], clusters['lat'],
                           c=clusters['cluster'], cmap='tab20',
                           s=clusters['value'] * 15,  # 降水量に応じてサイズ変更
                           alpha=0.7, edgecolors='black', linewidth=0.5)
        
        plt.colorbar(scatter, ax=ax, label='Cluster ID')
        
        # 各クラスタの中心に番号を表示
        for cluster_id in clusters['cluster'].unique():
            cluster_points = clusters[clusters['cluster'] == cluster_id]
            center_lon = cluster_points['lon'].mean()
            center_lat = cluster_points['lat'].mean()
            ax.text(center_lon, center_lat, f'{int(cluster_id)}',
                   fontsize=12, fontweight='bold',
                   ha='center', va='center',
                   bbox=dict(boxstyle='round,pad=0.3', 
                           facecolor='white', alpha=0.7))
    
    ax.set_xlabel('Longitude (経度)', fontsize=12)
    ax.set_ylabel('Latitude (緯度)', fontsize=12)
    ax.set_title(f'雨雲クラスタ - Time: {time_step}', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig('../output/' + output_file, dpi=150, bbox_inches='tight')
        print(f"Saved: ../output/{output_file}")
    
    plt.show()


def create_rain_radar_animation(df, output_file='rain_radar.gif'):
    """
    雨雲レーダー風のアニメーションを作成
    
    Parameters
    ----------
    df : pd.DataFrame
        クラスタリング結果のDataFrame
    output_file : str
        出力ファイル名
    """
    unique_times = sorted(df['time'].unique())
    
    # 全体の範囲を計算
    lon_min, lon_max = df['lon'].min() - 0.2, df['lon'].max() + 0.2
    lat_min, lat_max = df['lat'].min() - 0.2, df['lat'].max() + 0.2
    
    fig, ax = plt.subplots(figsize=(12, 10))
    
    def update(frame):
        ax.clear()
        current_time = unique_times[frame]
        time_data = df[df['time'] == current_time]
        
        # ノイズ
        noise = time_data[time_data['cluster'] == 0]
        if len(noise) > 0:
            ax.scatter(noise['lon'], noise['lat'],
                      c='lightgray', s=10, alpha=0.3, marker='.')
        
        # クラスタ
        clusters = time_data[time_data['cluster'] > 0]
        if len(clusters) > 0:
            scatter = ax.scatter(clusters['lon'], clusters['lat'],
                               c=clusters['cluster'], cmap='jet',
                               s=clusters['value'] * 20,
                               alpha=0.7, edgecolors='black', linewidth=0.5)
            
            # 各クラスタの輪郭を強調
            for cluster_id in clusters['cluster'].unique():
                cluster_points = clusters[clusters['cluster'] == cluster_id]
                if len(cluster_points) > 2:
                    # 凸包で囲む（簡易的）
                    from scipy.spatial import ConvexHull
                    try:
                        points = cluster_points[['lon', 'lat']].values
                        hull = ConvexHull(points)
                        for simplex in hull.simplices:
                            ax.plot(points[simplex, 0], points[simplex, 1], 
                                   'k-', alpha=0.3, linewidth=1)
                    except:
                        pass
        
        ax.set_xlim(lon_min, lon_max)
        ax.set_ylim(lat_min, lat_max)
        ax.set_xlabel('Longitude (経度)', fontsize=12)
        ax.set_ylabel('Latitude (緯度)', fontsize=12)
        ax.set_title(f'雨雲レーダー | Time: {current_time:.1f} | Frame: {frame+1}/{len(unique_times)}',
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # タイムスタンプを表示
        ax.text(0.02, 0.98, f'Time: {current_time:.1f}',
               transform=ax.transAxes, fontsize=14,
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    anim = FuncAnimation(fig, update, frames=len(unique_times),
                        interval=500, repeat=True)
    
    try:
        anim.save('../output/' + output_file, writer='pillow', fps=2)
        print(f"Animation saved: ../output/{output_file}")
    except Exception as e:
        print(f"Could not save animation: {e}")
        plt.show()


def display_cluster_statistics(df):
    """
    クラスタの統計情報を表示
    
    Parameters
    ----------
    df : pd.DataFrame
        クラスタリング結果のDataFrame
    """
    print("=" * 60)
    print("クラスタ統計情報")
    print("=" * 60)
    
    # 全体統計
    print(f"\n総ポイント数: {len(df)}")
    print(f"ノイズ数: {len(df[df['cluster'] == 0])} ({len(df[df['cluster'] == 0])/len(df)*100:.1f}%)")
    print(f"クラスタ数: {df[df['cluster'] > 0]['cluster'].nunique()}")
    
    # 時刻ごとの統計
    print("\n時刻ごとのクラスタ数:")
    for time in sorted(df['time'].unique()):
        time_data = df[df['time'] == time]
        n_clusters = time_data[time_data['cluster'] > 0]['cluster'].nunique()
        n_points = len(time_data[time_data['cluster'] > 0])
        print(f"  Time {time}: {n_clusters} clusters, {n_points} points")
    
    # クラスタサイズの分布
    print("\nクラスタサイズの分布:")
    cluster_sizes = df[df['cluster'] > 0].groupby('cluster').size()
    print(f"  平均: {cluster_sizes.mean():.1f} points")
    print(f"  最小: {cluster_sizes.min()} points")
    print(f"  最大: {cluster_sizes.max()} points")
    print(f"  中央値: {cluster_sizes.median():.1f} points")
    
    # 降水量の統計
    print("\n降水量の統計:")
    print(f"  全体平均: {df['value'].mean():.2f}")
    print(f"  クラスタ内平均: {df[df['cluster'] > 0]['value'].mean():.2f}")
    print(f"  ノイズ平均: {df[df['cluster'] == 0]['value'].mean():.2f}")
    
    print("=" * 60)


def main():
    """メイン処理"""
    print("=" * 60)
    print("可視化サンプルスクリプト")
    print("=" * 60)
    
    # データの読み込み
    print("\n[1] Loading data...")
    try:
        df, colors, bounds, time_data = load_data('../output/visualization_data')
        print(f"Loaded {len(df)} points")
    except FileNotFoundError:
        print("Error: ../output/visualization_data directory not found!")
        print("Please run test_clustering.py first to generate the data.")
        return
    
    # 統計情報の表示
    print("\n[2] Displaying statistics...")
    display_cluster_statistics(df)
    
    # 特定時刻の可視化
    print("\n[3] Visualizing time step 0...")
    visualize_single_timestep(df, time_step=0, 
                             output_file='visualization_timestep_0.png')
    
    print("\n[4] Visualizing time step 5...")
    visualize_single_timestep(df, time_step=5, 
                             output_file='visualization_timestep_5.png')
    
    # アニメーション作成
    print("\n[5] Creating rain radar animation...")
    try:
        create_rain_radar_animation(df, output_file='rain_radar_visualization.gif')
    except Exception as e:
        print(f"Animation creation failed: {e}")
    
    print("\n" + "=" * 60)
    print("可視化完了！")
    print("=" * 60)
    print("\n作成されたファイル:")
    print("  - ../output/visualization_timestep_0.png")
    print("  - ../output/visualization_timestep_5.png")
    print("  - ../output/rain_radar_visualization.gif")


if __name__ == "__main__":
    main()
