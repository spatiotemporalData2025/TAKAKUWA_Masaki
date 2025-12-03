"""
気象データクラスタリング - 超軽量版

非常に少ないデータで動作確認するためのスクリプト
- 最初の6時間のみ
- より少ないポイント数

実行方法:
    cd examples
    python weather_clustering_lite.py
"""

import sys
import os
from datetime import datetime

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from st_dbscan import STDBSCAN
from weather_data import fetch_tokyo_data
import time


def filter_by_time_and_value(weather_points, num_hours=6, min_value=1.0):
    """
    時間範囲と降水量でフィルタリング
    
    Parameters
    ----------
    weather_points : List[WeatherPoint]
        全ての気象ポイント
    num_hours : int
        取得する時間数
    min_value : float
        最小降水量 (mm/h)
    
    Returns
    -------
    List[WeatherPoint]
        フィルタリングされたポイント
    """
    # 時刻でソート
    sorted_points = sorted(weather_points, key=lambda p: p.time)
    
    # ユニークな時刻を取得
    unique_times = sorted(list(set(p.time for p in sorted_points)))
    
    # 最初のnum_hours時間のみ
    target_times = set(unique_times[:num_hours])
    
    # 時間と降水量でフィルタリング
    filtered = [p for p in sorted_points 
                if p.time in target_times and p.value >= min_value]
    
    print(f"    時間範囲: 最初の {num_hours} 時間")
    print(f"    降水量閾値: {min_value} mm/h 以上")
    print(f"    対象時刻数: {len(target_times)}")
    
    return filtered


def main():
    print("🌧️ 気象データクラスタリング - 超軽量版")
    print("=" * 60)
    print("💡 動作確認のため、少量のデータで実行します")
    
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
    
    filtered_points = filter_by_time_and_value(
        weather_points,
        num_hours=6,       # 最初の6時間のみ
        min_value=1.0      # 1mm/h以上の降水のみ
    )
    
    print(f"    ✓ {len(filtered_points)} ポイントにフィルタリング")
    
    if len(filtered_points) == 0:
        print("      ⚠️  フィルタリング後のデータがありません")
        print("      💡 min_valueを小さくしてみてください")
        return
    
    if len(filtered_points) < 50:
        print(f"      ⚠️  データポイントが少なすぎます ({len(filtered_points)})")
        print("      💡 num_hoursを増やすか、min_valueを小さくしてください")
        return
    
    # データの時間範囲を表示
    times = [p.time for p in filtered_points]
    start_time = datetime.fromtimestamp(min(times))
    end_time = datetime.fromtimestamp(max(times))
    print(f"    対象期間: {start_time.strftime('%Y-%m-%d %H:%M')} ~ "
          f"{end_time.strftime('%Y-%m-%d %H:%M')}")
    
    # 降水量の統計
    values = [p.value for p in filtered_points]
    print(f"    降水量: {min(values):.2f} ~ {max(values):.2f} mm/h "
          f"(平均: {sum(values)/len(values):.2f})")
    
    # ========================================
    # ステップ3: クラスタリング
    # ========================================
    print("\n[3/4] ST-DBSCANクラスタリング実行中...")
    
    # パラメータ設定
    eps1 = 25.0       # 空間距離: 緩めに設定
    eps2 = 7200.0     # 時間距離: 2時間
    min_pts = 5       # 最小ポイント数: 小さめ
    
    print(f"    パラメータ:")
    print(f"      eps1 (空間距離): {eps1} km")
    print(f"      eps2 (時間距離): {eps2/3600:.1f} 時間")
    print(f"      min_pts: {min_pts}")
    print(f"    処理中... (データポイント数: {len(filtered_points)})")
    
    start = time.time()
    
    stdbscan = STDBSCAN(eps1=eps1, eps2=eps2, min_pts=min_pts)
    
    # 進捗表示用
    print(f"    ", end="", flush=True)
    stdbscan.fit(filtered_points)
    
    elapsed = time.time() - start
    
    print(f"\n    ✓ クラスタリング完了 ({elapsed:.2f}秒)")
    
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
        for cluster_id in sorted([cid for cid in clusters.keys() if cid > 0]):
            cluster_points = [filtered_points[i] for i in clusters[cluster_id]]
            avg_value = sum(p.value for p in cluster_points) / len(cluster_points)
            avg_lat = sum(p.lat for p in cluster_points) / len(cluster_points)
            avg_lon = sum(p.lon for p in cluster_points) / len(cluster_points)
            
            # 時間範囲
            times_in_cluster = [p.time for p in cluster_points]
            start_t = datetime.fromtimestamp(min(times_in_cluster))
            end_t = datetime.fromtimestamp(max(times_in_cluster))
            
            print(f"      クラスタ {cluster_id}:")
            print(f"        ポイント数: {len(cluster_points)}")
            print(f"        中心位置: {avg_lat:.2f}°N, {avg_lon:.2f}°E")
            print(f"        平均降水量: {avg_value:.2f} mm/h")
            print(f"        時間範囲: {start_t.strftime('%H:%M')} ~ {end_t.strftime('%H:%M')}")
    else:
        print("\n    ⚠️  クラスタが検出されませんでした")
        print("    💡 パラメータを調整してみてください:")
        print("       - eps1を大きく（例: 30.0）")
        print("       - eps2を大きく（例: 10800.0 = 3時間）")
        print("       - min_ptsを小さく（例: 3）")
    
    print("\n" + "=" * 60)
    print("✨ 完了！")
    print("\n📊 次のステップ:")
    print("  1. パラメータを調整して最適なクラスタリングを見つける")
    print("  2. より多くのデータで試す（num_hours, min_valueを調整）")
    print("  3. 可視化担当者にデータを渡す")
    print("=" * 60)


if __name__ == "__main__":
    main()
