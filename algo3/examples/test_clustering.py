"""
ST-DBSCANのテストスクリプト

架空の降水データを生成してクラスタリングを実行する
結果を可視化担当者向けにエクスポートする
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from st_dbscan import STDBSCAN, STPoint, create_precipitation_data
from export_utils import ClusteringResultExporter, get_visualization_guide
from font_config import setup_japanese_font

# 日本語フォントを設定
setup_japanese_font()


def generate_synthetic_rain_clouds(n_clouds: int = 3, 
                                   points_per_cloud: int = 50,
                                   time_steps: int = 10,
                                   noise_ratio: float = 0.1) -> list:
    """
    架空の雨雲データを生成
    
    複数の雨雲が時間とともに移動するシミュレーションデータを作成
    
    Parameters
    ----------
    n_clouds : int
        雨雲の数
    points_per_cloud : int
        各雨雲のポイント数
    time_steps : int
        タイムステップ数
    noise_ratio : float
        ノイズの比率
        
    Returns
    -------
    list
        STPointのリスト
    """
    np.random.seed(42)
    points = []
    point_id = 0
    
    # 各雨雲の初期位置と移動方向を設定
    cloud_centers = []
    for i in range(n_clouds):
        center_lat = 35.0 + np.random.uniform(-2, 2)  # 東京周辺
        center_lon = 139.0 + np.random.uniform(-2, 2)
        velocity_lat = np.random.uniform(-0.05, 0.05)  # 緯度方向の移動速度
        velocity_lon = np.random.uniform(-0.05, 0.05)  # 経度方向の移動速度
        cloud_centers.append({
            'lat': center_lat,
            'lon': center_lon,
            'v_lat': velocity_lat,
            'v_lon': velocity_lon
        })
    
    # 各タイムステップで雨雲を生成
    for t in range(time_steps):
        for cloud_idx, cloud in enumerate(cloud_centers):
            # 雨雲の中心位置を更新（移動）
            current_lat = cloud['lat'] + cloud['v_lat'] * t
            current_lon = cloud['lon'] + cloud['v_lon'] * t
            
            # 雨雲内のポイントを生成（正規分布）
            for _ in range(points_per_cloud):
                # 雨雲の広がり（標準偏差）
                spread = 0.1
                lat = np.random.normal(current_lat, spread)
                lon = np.random.normal(current_lon, spread)
                
                # 降水量（雨雲の中心ほど強い）
                dist_from_center = np.sqrt((lat - current_lat)**2 + (lon - current_lon)**2)
                value = max(0, 10 - dist_from_center * 50) + np.random.uniform(0, 2)
                
                point = STPoint(
                    id=point_id,
                    lat=lat,
                    lon=lon,
                    time=float(t),
                    value=value
                )
                points.append(point)
                point_id += 1
    
    # ノイズポイントを追加
    n_noise = int(len(points) * noise_ratio)
    for _ in range(n_noise):
        lat = 35.0 + np.random.uniform(-3, 3)
        lon = 139.0 + np.random.uniform(-3, 3)
        time = float(np.random.randint(0, time_steps))
        value = np.random.uniform(1, 5)
        
        point = STPoint(
            id=point_id,
            lat=lat,
            lon=lon,
            time=time,
            value=value
        )
        points.append(point)
        point_id += 1
    
    return points


def visualize_clusters_2d(points: list, title: str = "ST-DBSCAN Clustering Result"):
    """
    クラスタリング結果を2D空間上に可視化
    
    Parameters
    ----------
    points : list
        STPointのリスト
    title : str
        グラフのタイトル
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # 時刻ごとに色分け（左図）
    times = np.array([p.time for p in points])
    lats = np.array([p.lat for p in points])
    lons = np.array([p.lon for p in points])
    
    scatter1 = axes[0].scatter(lons, lats, c=times, cmap='viridis', 
                              alpha=0.6, s=50)
    axes[0].set_xlabel('Longitude')
    axes[0].set_ylabel('Latitude')
    axes[0].set_title('Points colored by Time')
    axes[0].grid(True, alpha=0.3)
    plt.colorbar(scatter1, ax=axes[0], label='Time step')
    
    # クラスタIDごとに色分け（右図）
    clusters = np.array([p.cluster for p in points])
    scatter2 = axes[1].scatter(lons, lats, c=clusters, cmap='tab20', 
                              alpha=0.6, s=50)
    axes[1].set_xlabel('Longitude')
    axes[1].set_ylabel('Latitude')
    axes[1].set_title('Points colored by Cluster ID')
    axes[1].grid(True, alpha=0.3)
    plt.colorbar(scatter2, ax=axes[1], label='Cluster ID')
    
    fig.suptitle(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig('../output/clustering_result_2d.png', dpi=150, bbox_inches='tight')
    print("2D visualization saved as '../output/clustering_result_2d.png'")
    plt.show()


def visualize_clusters_3d(points: list, title: str = "ST-DBSCAN 3D Visualization"):
    """
    クラスタリング結果を3D時空間上に可視化
    
    Parameters
    ----------
    points : list
        STPointのリスト
    title : str
        グラフのタイトル
    """
    from mpl_toolkits.mplot3d import Axes3D
    
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection='3d')
    
    lons = np.array([p.lon for p in points])
    lats = np.array([p.lat for p in points])
    times = np.array([p.time for p in points])
    clusters = np.array([p.cluster for p in points])
    
    # クラスタIDごとに色分け
    scatter = ax.scatter(lons, lats, times, c=clusters, cmap='tab20', 
                        alpha=0.6, s=30)
    
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.set_zlabel('Time step')
    ax.set_title(title)
    
    plt.colorbar(scatter, ax=ax, label='Cluster ID', pad=0.1)
    plt.tight_layout()
    plt.savefig('../output/clustering_result_3d.png', dpi=150, bbox_inches='tight')
    print("3D visualization saved as '../output/clustering_result_3d.png'")
    plt.show()


def visualize_animation(points: list, output_file: str = 'rain_animation.gif'):
    """
    時間経過に伴う雨雲の動きをアニメーション化
    
    Parameters
    ----------
    points : list
        STPointのリスト
    output_file : str
        出力ファイル名
    """
    # 時刻でソート
    unique_times = sorted(set([p.time for p in points]))
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    def update(frame):
        ax.clear()
        current_time = unique_times[frame]
        
        # 現在の時刻のポイントを抽出
        current_points = [p for p in points if p.time == current_time]
        
        if current_points:
            lons = [p.lon for p in current_points]
            lats = [p.lat for p in current_points]
            clusters = [p.cluster for p in current_points]
            values = [p.value for p in current_points]
            
            # クラスタIDで色分け、降水量でサイズを変更
            scatter = ax.scatter(lons, lats, c=clusters, cmap='tab20',
                               s=[v*10 for v in values], alpha=0.6)
            
            ax.set_xlabel('Longitude')
            ax.set_ylabel('Latitude')
            ax.set_title(f'Rain Clusters - Time: {current_time:.1f}')
            ax.grid(True, alpha=0.3)
            
            # 軸の範囲を固定
            all_lons = [p.lon for p in points]
            all_lats = [p.lat for p in points]
            ax.set_xlim(min(all_lons) - 0.2, max(all_lons) + 0.2)
            ax.set_ylim(min(all_lats) - 0.2, max(all_lats) + 0.2)
    
    anim = FuncAnimation(fig, update, frames=len(unique_times),
                        interval=500, repeat=True)
    
    try:
        anim.save('../output/' + output_file, writer='pillow', fps=2)
        print(f"Animation saved as '../output/{output_file}'")
    except Exception as e:
        print(f"Could not save animation: {e}")
        print("Displaying animation instead...")
        plt.show()


def main():
    """メイン処理"""
    print("=" * 60)
    print("ST-DBSCAN Clustering Test")
    print("=" * 60)
    
    # 1. 架空の雨雲データを生成
    print("\n[1] Generating synthetic rain cloud data...")
    points = generate_synthetic_rain_clouds(
        n_clouds=3,
        points_per_cloud=50,
        time_steps=10,
        noise_ratio=0.1
    )
    print(f"Generated {len(points)} points")
    
    # 2. ST-DBSCANクラスタリングを実行
    print("\n[2] Running ST-DBSCAN clustering...")
    stdbscan = STDBSCAN(
        eps1=15.0,      # 空間距離の閾値 (km) - 約15km
        eps2=2.0,       # 時間距離の閾値 (タイムステップ)
        min_pts=5       # 最小ポイント数
    )
    
    stdbscan.fit(points)
    print("Clustering completed!")
    
    # 3. 統計情報を表示
    print("\n[3] Clustering Statistics:")
    stats = stdbscan.get_statistics()
    print(f"  Total points: {stats['n_points']}")
    print(f"  Number of clusters: {stats['n_clusters']}")
    print(f"  Noise points: {stats['n_noise']} ({stats['noise_ratio']*100:.1f}%)")
    print(f"  Average cluster size: {stats['avg_cluster_size']:.1f}")
    print(f"  Cluster size range: [{stats['min_cluster_size']}, {stats['max_cluster_size']}]")
    
    clusters = stdbscan.get_clusters()
    print(f"\n  Cluster details:")
    for cid in sorted(clusters.keys()):
        if cid > 0:  # ノイズ以外
            print(f"    Cluster {cid}: {len(clusters[cid])} points")
    
    # 4. 可視化
    print("\n[4] Creating visualizations...")
    visualize_clusters_2d(points)
    visualize_clusters_3d(points)
    
    # アニメーション（オプション）
    try:
        print("\n[5] Creating animation...")
        visualize_animation(points)
    except Exception as e:
        print(f"Animation creation failed: {e}")
    
    # 5. データのエクスポート（可視化担当者向け）
    print("\n[6] Exporting data for visualization team...")
    exporter = ClusteringResultExporter(stdbscan)
    exporter.export_for_visualization(output_dir='../output/visualization_data')
    
    # DataFrameのサンプルを表示
    print("\n[7] Data Preview (first 10 rows):")
    df = exporter.to_dataframe()
    print(df.head(10).to_string())
    
    # 時刻ごとのクラスタ数を表示
    print("\n[8] Clusters per time step:")
    clusters_by_time = exporter.get_clusters_by_time()
    for time in sorted(clusters_by_time.keys()):
        n_clusters = len([cid for cid in clusters_by_time[time].keys() if cid > 0])
        print(f"  Time {time}: {n_clusters} clusters")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    print("\n次のステップ:")
    print("  1. output/visualization_data/ フォルダ内のファイルを確認")
    print("  2. 可視化担当者にファイルを共有")
    print("  3. export_utils.py の get_visualization_guide() を参照")
    print("\n可視化担当者向けガイドを表示するには:")
    print("  python -c \"from export_utils import get_visualization_guide; print(get_visualization_guide())\"")
    print("=" * 60)


if __name__ == "__main__":
    main()
