"""
気象データクラスタリング - 最適化版

大量のデータポイントに対応するため、以下の最適化を実施:
1. 時間単位でのフィルタリング
2. より緩いパラメータ設定
3. 処理状況の表示

実行方法:
    cd examples
    python weather_clustering_optimized.py
"""

import sys
import os
from datetime import datetime

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from st_dbscan import STDBSCAN
from weather_data import fetch_tokyo_data
import time


def filter_by_time_range(weather_points, start_idx=0, num_hours=24):
    """
    特定の時間範囲のデータのみを抽出
    
    Parameters
    ----------
    weather_points : List[WeatherPoint]
        全ての気象ポイント
    start_idx : int
        開始時刻のインデックス（0から）
    num_hours : int
        取得する時間数
    
    Returns
    -------
    List[WeatherPoint]
        フィルタリングされたポイント
    """
    # 時刻でソート
    sorted_points = sorted(weather_points, key=lambda p: p.time)
    
    # ユニークな時刻を取得
    unique_times = sorted(list(set(p.time for p in sorted_points)))
    
    if start_idx >= len(unique_times):
        return []
    
    # 対象時間範囲を決定
    end_idx = min(start_idx + num_hours, len(unique_times))
    target_times = set(unique_times[start_idx:end_idx])
    
    # フィルタリング
    filtered = [p for p in sorted_points if p.time in target_times]
    
    print(f"    時間範囲: {start_idx}時間目 ~ {end_idx}時間目")
    print(f"    対象時刻数: {len(target_times)}")
    
    return filtered


def main():
    print("🌧️ 気象データクラスタリング - 最適化版")
    print("=" * 60)
    
    # ========================================
    # ステップ1: データ取得
    # ========================================
    print("\n[1/4] 東京周辺の気象データを取得中...")
    weather_points = fetch_tokyo_data(cache_dir='../data')
    print(f"      ✓ {len(weather_points)} 個の降水ポイントを取得")
    
    if len(weather_points) == 0:
        print("      ⚠️  降水データが見つかりませんでした")
        return
    
    # ========================================
    # ステップ2: データのフィルタリング
    # ========================================
    print("\n[2/4] データをフィルタリング中...")
    print("    💡 処理時間短縮のため、最初の24時間のデータのみを使用します")
    
    filtered_points = filter_by_time_range(
        weather_points, 
        start_idx=0,      # 最初の時刻から
        num_hours=24      # 24時間分
    )
    
    print(f"    ✓ {len(filtered_points)} ポイントにフィルタリング")
    
    if len(filtered_points) == 0:
        print("      ⚠️  フィルタリング後のデータがありません")
        return
    
    # データの時間範囲を表示
    times = [p.time for p in filtered_points]
    start_time = datetime.fromtimestamp(min(times))
    end_time = datetime.fromtimestamp(max(times))
    print(f"    対象期間: {start_time.strftime('%Y-%m-%d %H:%M')} ~ "
          f"{end_time.strftime('%Y-%m-%d %H:%M')}")
    
    # ========================================
    # ステップ3: クラスタリング
    # ========================================
    print("\n[3/4] ST-DBSCANクラスタリング実行中...")
    
    # パラメータ設定（大量データ向けに調整）
    eps1 = 20.0       # 空間距離: やや緩めに設定
    eps2 = 7200.0     # 時間距離: 2時間（大きめに設定）
    min_pts = 10      # 最小ポイント数: やや大きめ
    
    print(f"    パラメータ:")
    print(f"      eps1 (空間距離): {eps1} km")
    print(f"      eps2 (時間距離): {eps2/3600:.1f} 時間")
    print(f"      min_pts: {min_pts}")
    
    start = time.time()
    
    stdbscan = STDBSCAN(eps1=eps1, eps2=eps2, min_pts=min_pts)
    stdbscan.fit(filtered_points)
    
    elapsed = time.time() - start
    
    print(f"    ✓ クラスタリング完了 ({elapsed:.2f}秒)")
    
    # ========================================
    # ステップ4: 結果表示
    # ========================================
    print("\n[4/4] 結果:")
    stats = stdbscan.get_statistics()
    
    print(f"    データポイント数: {stats['n_points']}")
    print(f"    検出されたクラスタ数: {stats['n_clusters']}")
    print(f"    ノイズポイント数: {stats['n_noise']}")
    print(f"    ノイズ比率: {stats['noise_ratio']*100:.1f}%")
    
    if stats['n_clusters'] > 0:
        print(f"\n    クラスタサイズ:")
        print(f"      平均: {stats['avg_cluster_size']:.1f} ポイント")
        print(f"      最大: {stats['max_cluster_size']} ポイント")
        print(f"      最小: {stats['min_cluster_size']} ポイント")
        
        # 各クラスタの詳細
        clusters = stdbscan.get_clusters()
        print(f"\n    各クラスタの詳細:")
        for cluster_id in sorted([cid for cid in clusters.keys() if cid > 0])[:5]:
            cluster_points = [filtered_points[i] for i in clusters[cluster_id]]
            avg_value = sum(p.value for p in cluster_points) / len(cluster_points)
            avg_lat = sum(p.lat for p in cluster_points) / len(cluster_points)
            avg_lon = sum(p.lon for p in cluster_points) / len(cluster_points)
            print(f"      クラスタ {cluster_id}: {len(cluster_points)} ポイント "
                  f"(中心: {avg_lat:.2f}°N, {avg_lon:.2f}°E, "
                  f"平均降水量: {avg_value:.2f} mm/h)")
        
        if stats['n_clusters'] > 5:
            print(f"      ... 他 {stats['n_clusters'] - 5} クラスタ")
    
    print("\n" + "=" * 60)
    print("✨ 完了！")
    print("\n💡 ヒント:")
    print("  - より多くのデータを処理する場合は start_idx, num_hours を調整")
    print("  - パラメータ (eps1, eps2, min_pts) を調整してクラスタ検出を最適化")
    print("  - 全データを処理する場合は weather_clustering.py を使用")
    print("=" * 60)


if __name__ == "__main__":
    main()
