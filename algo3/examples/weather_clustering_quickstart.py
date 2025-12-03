"""
気象データクラスタリング - クイックスタート

このスクリプトは、チームメンバーが実装した気象データ取得機能と
ST-DBSCANを統合して、最短手順で実行できるようにしたものです。

実行方法:
    cd examples
    python weather_clustering_quickstart.py
"""

import sys
import os

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from st_dbscan import STDBSCAN
from weather_data import fetch_tokyo_data


def main():
    print("🌧️ 気象データクラスタリング - クイックスタート")
    print("=" * 60)
    
    # ステップ1: データ取得
    print("\n[1/3] 東京周辺の気象データを取得中...")
    weather_points = fetch_tokyo_data(cache_dir='../data')
    print(f"      ✓ {len(weather_points)} 個の降水ポイントを取得")
    
    if len(weather_points) == 0:
        print("      ⚠️  降水データが見つかりませんでした")
        return
    
    # ステップ2: クラスタリング
    print("\n[2/3] ST-DBSCANクラスタリング実行中...")
    stdbscan = STDBSCAN(eps1=15.0, eps2=3600.0, min_pts=5)
    stdbscan.fit(weather_points)
    print("      ✓ クラスタリング完了")
    
    # ステップ3: 結果表示
    print("\n[3/3] 結果:")
    stats = stdbscan.get_statistics()
    print(f"      検出されたクラスタ数: {stats['n_clusters']}")
    print(f"      ノイズポイント数: {stats['n_noise']}")
    print(f"      ノイズ比率: {stats['noise_ratio']*100:.1f}%")
    
    if stats['n_clusters'] > 0:
        print(f"\n      クラスタサイズ:")
        print(f"        平均: {stats['avg_cluster_size']:.1f} ポイント")
        print(f"        最大: {stats['max_cluster_size']} ポイント")
    
    print("\n" + "=" * 60)
    print("✨ 完了！")
    
    # データにアクセスする例
    print("\n💡 クラスタデータへのアクセス例:")
    clusters = stdbscan.get_clusters()
    
    # クラスタ1の情報を表示
    if 1 in clusters:
        cluster_1_indices = clusters[1]
        cluster_1_points = [weather_points[i] for i in cluster_1_indices]
        
        print(f"\nクラスタ1の詳細:")
        print(f"  ポイント数: {len(cluster_1_points)}")
        
        # 最初の3ポイントを表示
        print(f"  サンプルポイント（最初の3つ）:")
        for i, point in enumerate(cluster_1_points[:3], 1):
            print(f"    {i}. 緯度={point.lat:.2f}, 経度={point.lon:.2f}, "
                  f"降水量={point.value:.2f} mm/h")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
