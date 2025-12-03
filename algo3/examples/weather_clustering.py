"""
気象データを使ったST-DBSCANクラスタリングの実装例

チームメンバーが実装したweather_data.pyのfetch_tokyo_data関数を使用して、
実際の気象データからST-DBSCANで雨雲クラスタを検出します。

使用方法:
    python weather_clustering.py
"""

import sys
import os
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from st_dbscan import STDBSCAN
from weather_data import fetch_tokyo_data
from export_utils import ClusteringResultExporter
import time


def main():
    """メイン処理"""
    print("=" * 70)
    print("気象データを使ったST-DBSCANクラスタリング")
    print("=" * 70)
    
    # ========================================
    # 1. 気象データの取得
    # ========================================
    print("\n[1] 気象データを取得中...")
    print("    東京周辺（緯度34.5-36.0、経度138.0-140.0）")
    print("    期間: 2025年11月24-29日")
    
    start_time = time.time()
    
    # チームメンバーが実装した関数を使用
    weather_points = fetch_tokyo_data(cache_dir='../data')
    
    fetch_time = time.time() - start_time
    
    print(f"    ✓ 取得完了: {len(weather_points)} 個の降水ポイント")
    print(f"    ✓ 取得時間: {fetch_time:.2f}秒")
    
    if len(weather_points) == 0:
        print("\n    ⚠️  降水データが見つかりませんでした。")
        print("    別の期間や閾値を試してください。")
        return
    
    # データの概要を表示
    print("\n    データの概要:")
    latitudes = [p.lat for p in weather_points]
    longitudes = [p.lon for p in weather_points]
    times = [p.time for p in weather_points]
    values = [p.value for p in weather_points]
    
    print(f"      緯度範囲: {min(latitudes):.2f} ~ {max(latitudes):.2f}")
    print(f"      経度範囲: {min(longitudes):.2f} ~ {max(longitudes):.2f}")
    print(f"      時間範囲: {min(times):.0f} ~ {max(times):.0f}")
    print(f"      降水量: {min(values):.2f} ~ {max(values):.2f} mm/h")
    print(f"      平均降水量: {sum(values)/len(values):.2f} mm/h")
    
    # ========================================
    # 2. ST-DBSCANクラスタリング
    # ========================================
    print("\n[2] ST-DBSCANクラスタリング実行中...")
    
    # パラメータ設定
    eps1 = 15.0      # 空間距離の閾値 (km) - 雨雲の典型的なサイズ
    eps2 = 3600.0    # 時間距離の閾値 (秒) - 1時間 = 3600秒
    min_pts = 5      # 最小ポイント数
    
    print(f"    パラメータ:")
    print(f"      eps1 (空間距離): {eps1} km")
    print(f"      eps2 (時間距離): {eps2/3600:.1f} 時間")
    print(f"      min_pts (最小ポイント数): {min_pts}")
    
    start_time = time.time()
    
    # ST-DBSCAN実行
    stdbscan = STDBSCAN(eps1=eps1, eps2=eps2, min_pts=min_pts)
    stdbscan.fit(weather_points)
    
    cluster_time = time.time() - start_time
    
    print(f"    ✓ クラスタリング完了")
    print(f"    ✓ 実行時間: {cluster_time:.2f}秒")
    
    # ========================================
    # 3. 結果の統計情報
    # ========================================
    print("\n[3] クラスタリング結果:")
    stats = stdbscan.get_statistics()
    
    print(f"    データポイント数: {stats['n_points']}")
    print(f"    検出されたクラスタ数: {stats['n_clusters']}")
    print(f"    ノイズポイント数: {stats['n_noise']}")
    print(f"    ノイズ比率: {stats['noise_ratio']*100:.1f}%")
    
    if stats['n_clusters'] > 0:
        print(f"\n    クラスタサイズ:")
        print(f"      最小: {stats['min_cluster_size']}")
        print(f"      平均: {stats['avg_cluster_size']:.1f}")
        print(f"      最大: {stats['max_cluster_size']}")
        
        # 各クラスタの詳細
        clusters = stdbscan.get_clusters()
        print(f"\n    各クラスタの詳細:")
        for cluster_id in sorted([cid for cid in clusters.keys() if cid > 0]):
            cluster_points = [weather_points[i] for i in clusters[cluster_id]]
            avg_value = sum(p.value for p in cluster_points) / len(cluster_points)
            print(f"      クラスタ {cluster_id}: {len(cluster_points)} ポイント "
                  f"(平均降水量: {avg_value:.2f} mm/h)")
    
    # ========================================
    # 4. 結果のエクスポート
    # ========================================
    print("\n[4] 結果をエクスポート中...")
    
    output_dir = Path(__file__).parent.parent / 'output' / 'weather_clustering'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    exporter = ClusteringResultExporter(stdbscan)
    exporter.export_for_visualization(output_dir=str(output_dir))
    
    print(f"    ✓ エクスポート完了: {output_dir}")
    print(f"    以下のファイルが作成されました:")
    print(f"      - clustering_result.csv")
    print(f"      - clustering_result.json")
    print(f"      - cluster_colors.json")
    print(f"      - cluster_bounds.json")
    print(f"      - clusters_by_time.json")
    
    # ========================================
    # 5. まとめ
    # ========================================
    print("\n" + "=" * 70)
    print("クラスタリング完了！")
    print("=" * 70)
    print(f"\n✨ 東京周辺の降水データから {stats['n_clusters']} 個の雨雲クラスタを検出しました。")
    print(f"\n📊 次のステップ:")
    print(f"   1. 可視化担当者に '{output_dir}' フォルダを共有")
    print(f"   2. パラメータを調整して再実行")
    print(f"   3. 効果測定担当者に統計情報を共有")
    print("\n" + "=" * 70)


def test_different_parameters():
    """異なるパラメータでのテスト"""
    print("\n" + "=" * 70)
    print("パラメータ感度テスト")
    print("=" * 70)
    
    # データ取得（1回のみ）
    print("\n気象データを取得中...")
    weather_points = fetch_tokyo_data(cache_dir='../data')
    print(f"✓ {len(weather_points)} 個のポイントを取得")
    
    if len(weather_points) == 0:
        print("⚠️  データが見つかりません")
        return
    
    # 異なるパラメータセット
    parameter_sets = [
        {"eps1": 10.0, "eps2": 3600.0, "min_pts": 5, "name": "厳密"},
        {"eps1": 15.0, "eps2": 3600.0, "min_pts": 5, "name": "標準"},
        {"eps1": 20.0, "eps2": 3600.0, "min_pts": 5, "name": "緩い"},
        {"eps1": 15.0, "eps2": 7200.0, "min_pts": 5, "name": "時間的に広い"},
        {"eps1": 15.0, "eps2": 3600.0, "min_pts": 10, "name": "大きなクラスタのみ"},
    ]
    
    print("\n異なるパラメータでクラスタリングを実行:")
    results = []
    
    for params in parameter_sets:
        print(f"\n  {params['name']}: eps1={params['eps1']}, "
              f"eps2={params['eps2']/3600:.1f}h, min_pts={params['min_pts']}")
        
        stdbscan = STDBSCAN(
            eps1=params['eps1'],
            eps2=params['eps2'],
            min_pts=params['min_pts']
        )
        
        start_time = time.time()
        stdbscan.fit(weather_points)
        elapsed = time.time() - start_time
        
        stats = stdbscan.get_statistics()
        results.append({
            'name': params['name'],
            'n_clusters': stats['n_clusters'],
            'n_noise': stats['n_noise'],
            'noise_ratio': stats['noise_ratio'],
            'time': elapsed
        })
        
        print(f"    クラスタ数: {stats['n_clusters']}, "
              f"ノイズ: {stats['n_noise']}, "
              f"実行時間: {elapsed:.2f}秒")
    
    # 結果のまとめ
    print("\n" + "=" * 70)
    print("パラメータ感度テスト結果")
    print("=" * 70)
    print(f"\n{'設定':<15} {'クラスタ数':<12} {'ノイズ数':<12} "
          f"{'ノイズ比率':<12} {'実行時間':<12}")
    print("-" * 70)
    
    for result in results:
        print(f"{result['name']:<15} {result['n_clusters']:<12} "
              f"{result['n_noise']:<12} "
              f"{result['noise_ratio']*100:<11.1f}% "
              f"{result['time']:<11.2f}秒")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    # メイン処理を実行
    main()
    
    # パラメータ感度テストも実行する場合はコメントを外す
    # test_different_parameters()
