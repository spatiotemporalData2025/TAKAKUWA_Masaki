"""
クラスタリング結果のエクスポートと可視化用ユーティリティ

次の担当者（可視化担当）がクラスタリング結果を使いやすいように、
データのエクスポートとインターフェースを提供します。
"""

import json
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from st_dbscan import STDBSCAN, STPoint


class ClusteringResultExporter:
    """
    クラスタリング結果をエクスポートするクラス
    
    可視化担当者が使いやすい形式でデータを出力
    """
    
    def __init__(self, stdbscan: STDBSCAN):
        """
        Parameters
        ----------
        stdbscan : STDBSCAN
            クラスタリング済みのSTDBSCANインスタンス
        """
        self.stdbscan = stdbscan
        self.points = stdbscan.points
    
    def to_dataframe(self) -> pd.DataFrame:
        """
        クラスタリング結果をpandas DataFrameに変換
        
        Returns
        -------
        pd.DataFrame
            以下のカラムを持つDataFrame:
            - id: ポイントID
            - lat: 緯度
            - lon: 経度
            - time: 時刻
            - value: 降水量などの値
            - cluster: クラスタID (0=ノイズ, 1~=クラスタ)
            - is_noise: ノイズかどうか
        """
        data = {
            'id': [p.id for p in self.points],
            'lat': [p.lat for p in self.points],
            'lon': [p.lon for p in self.points],
            'time': [p.time for p in self.points],
            'value': [p.value for p in self.points],
            'cluster': [p.cluster for p in self.points],
            'is_noise': [p.cluster == 0 for p in self.points]
        }
        return pd.DataFrame(data)
    
    def to_json(self, filepath: str = None) -> str:
        """
        クラスタリング結果をJSON形式でエクスポート
        
        Parameters
        ----------
        filepath : str, optional
            保存先のファイルパス。Noneの場合はJSON文字列を返す
            
        Returns
        -------
        str
            JSON文字列
        """
        result = {
            'metadata': {
                'n_points': len(self.points),
                'n_clusters': self.stdbscan.get_statistics()['n_clusters'],
                'parameters': {
                    'eps1': self.stdbscan.eps1,
                    'eps2': self.stdbscan.eps2,
                    'min_pts': self.stdbscan.min_pts
                }
            },
            'points': [
                {
                    'id': p.id,
                    'lat': p.lat,
                    'lon': p.lon,
                    'time': p.time,
                    'value': p.value,
                    'cluster': p.cluster
                }
                for p in self.points
            ],
            'clusters': self._get_cluster_summaries()
        }
        
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(json_str)
            print(f"JSON exported to: {filepath}")
        
        return json_str
    
    def to_csv(self, filepath: str = 'clustering_result.csv'):
        """
        クラスタリング結果をCSV形式でエクスポート
        
        Parameters
        ----------
        filepath : str
            保存先のファイルパス
        """
        df = self.to_dataframe()
        df.to_csv(filepath, index=False, encoding='utf-8')
        print(f"CSV exported to: {filepath}")
    
    def get_clusters_by_time(self) -> Dict[float, Dict[int, List[STPoint]]]:
        """
        時刻ごとにクラスタをグループ化
        
        Returns
        -------
        Dict[float, Dict[int, List[STPoint]]]
            {時刻: {クラスタID: [ポイントのリスト]}}
        """
        clusters_by_time = {}
        
        for point in self.points:
            time = point.time
            cluster_id = point.cluster
            
            if time not in clusters_by_time:
                clusters_by_time[time] = {}
            
            if cluster_id not in clusters_by_time[time]:
                clusters_by_time[time][cluster_id] = []
            
            clusters_by_time[time][cluster_id].append(point)
        
        return clusters_by_time
    
    def get_cluster_colors(self, cmap_name: str = 'tab20') -> Dict[int, Tuple[float, float, float, float]]:
        """
        各クラスタに色を割り当て
        
        Parameters
        ----------
        cmap_name : str
            matplotlibのカラーマップ名
            
        Returns
        -------
        Dict[int, Tuple[float, float, float, float]]
            {クラスタID: (R, G, B, A)} の辞書
        """
        import matplotlib.cm as cm
        import matplotlib.colors as mcolors
        
        clusters = self.stdbscan.get_clusters()
        cluster_ids = sorted([cid for cid in clusters.keys() if cid > 0])
        
        if not cluster_ids:
            return {}
        
        cmap = cm.get_cmap(cmap_name)
        colors = {}
        
        # ノイズは灰色
        colors[0] = (0.5, 0.5, 0.5, 0.3)
        
        # 各クラスタに色を割り当て
        n_clusters = len(cluster_ids)
        for i, cid in enumerate(cluster_ids):
            color = cmap(i / max(n_clusters - 1, 1))
            colors[cid] = color
        
        return colors
    
    def get_cluster_bounds(self) -> Dict[int, Dict[str, float]]:
        """
        各クラスタの空間的・時間的範囲を取得
        
        Returns
        -------
        Dict[int, Dict[str, float]]
            {クラスタID: {
                'min_lat', 'max_lat', 'min_lon', 'max_lon',
                'min_time', 'max_time', 'center_lat', 'center_lon'
            }}
        """
        clusters = self.stdbscan.get_clusters()
        bounds = {}
        
        for cluster_id, point_indices in clusters.items():
            if cluster_id == 0:  # ノイズは除外
                continue
            
            cluster_points = [self.points[i] for i in point_indices]
            
            lats = [p.lat for p in cluster_points]
            lons = [p.lon for p in cluster_points]
            times = [p.time for p in cluster_points]
            
            bounds[cluster_id] = {
                'min_lat': min(lats),
                'max_lat': max(lats),
                'min_lon': min(lons),
                'max_lon': max(lons),
                'min_time': min(times),
                'max_time': max(times),
                'center_lat': np.mean(lats),
                'center_lon': np.mean(lons),
                'n_points': len(cluster_points)
            }
        
        return bounds
    
    def _get_cluster_summaries(self) -> List[Dict]:
        """クラスタの要約情報を取得"""
        clusters = self.stdbscan.get_clusters()
        bounds = self.get_cluster_bounds()
        summaries = []
        
        for cluster_id in sorted(clusters.keys()):
            if cluster_id == 0:  # ノイズ
                continue
            
            summary = {
                'cluster_id': cluster_id,
                'n_points': len(clusters[cluster_id]),
                'bounds': bounds.get(cluster_id, {})
            }
            summaries.append(summary)
        
        return summaries
    
    def export_for_visualization(self, output_dir: str = '.'):
        """
        可視化に必要な全てのデータをエクスポート
        
        Parameters
        ----------
        output_dir : str
            出力ディレクトリ
        """
        import os
        
        os.makedirs(output_dir, exist_ok=True)
        
        # CSV形式
        csv_path = os.path.join(output_dir, 'clustering_result.csv')
        self.to_csv(csv_path)
        
        # JSON形式
        json_path = os.path.join(output_dir, 'clustering_result.json')
        self.to_json(json_path)
        
        # クラスタの色情報
        colors = self.get_cluster_colors()
        colors_dict = {
            str(cid): {
                'r': float(c[0]),
                'g': float(c[1]),
                'b': float(c[2]),
                'a': float(c[3])
            }
            for cid, c in colors.items()
        }
        colors_path = os.path.join(output_dir, 'cluster_colors.json')
        with open(colors_path, 'w', encoding='utf-8') as f:
            json.dump(colors_dict, f, indent=2)
        print(f"Cluster colors exported to: {colors_path}")
        
        # クラスタの境界情報
        bounds = self.get_cluster_bounds()
        bounds_path = os.path.join(output_dir, 'cluster_bounds.json')
        with open(bounds_path, 'w', encoding='utf-8') as f:
            json.dump(bounds, f, indent=2)
        print(f"Cluster bounds exported to: {bounds_path}")
        
        # 時刻ごとのデータ
        clusters_by_time = self.get_clusters_by_time()
        time_data = {}
        for time, clusters in clusters_by_time.items():
            time_data[str(time)] = {
                str(cluster_id): [
                    {
                        'lat': p.lat,
                        'lon': p.lon,
                        'value': p.value,
                        'cluster': p.cluster
                    }
                    for p in points
                ]
                for cluster_id, points in clusters.items()
            }
        
        time_path = os.path.join(output_dir, 'clusters_by_time.json')
        with open(time_path, 'w', encoding='utf-8') as f:
            json.dump(time_data, f, indent=2)
        print(f"Time-based clusters exported to: {time_path}")
        
        print(f"\nAll visualization data exported to: {output_dir}")
        print("Files created:")
        print("  - clustering_result.csv: 全ポイントの情報")
        print("  - clustering_result.json: JSON形式の全データ")
        print("  - cluster_colors.json: 各クラスタの推奨色")
        print("  - cluster_bounds.json: 各クラスタの空間的範囲")
        print("  - clusters_by_time.json: 時刻ごとのクラスタ情報")


def load_clustering_result(filepath: str) -> pd.DataFrame:
    """
    エクスポートされたクラスタリング結果を読み込む
    
    可視化担当者がこの関数を使ってデータを読み込めます
    
    Parameters
    ----------
    filepath : str
        CSVまたはJSONファイルのパス
        
    Returns
    -------
    pd.DataFrame
        クラスタリング結果のDataFrame
    """
    if filepath.endswith('.csv'):
        return pd.read_csv(filepath)
    elif filepath.endswith('.json'):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data['points'])
    else:
        raise ValueError("Unsupported file format. Use .csv or .json")


def get_visualization_guide() -> str:
    """
    可視化担当者向けのガイドを返す
    
    Returns
    -------
    str
        使い方ガイド
    """
    guide = """
    ================================
    可視化担当者向けガイド
    ================================
    
    ## データの読み込み方
    
    ### CSVファイルから読み込む場合:
    ```python
    import pandas as pd
    df = pd.read_csv('clustering_result.csv')
    
    # カラム:
    # - id: ポイントID
    # - lat: 緯度
    # - lon: 経度
    # - time: 時刻
    # - value: 降水量
    # - cluster: クラスタID (0=ノイズ, 1~=クラスタ)
    # - is_noise: ノイズかどうか (True/False)
    ```
    
    ### JSONファイルから読み込む場合:
    ```python
    import json
    with open('clustering_result.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # data['metadata']: クラスタリングのメタ情報
    # data['points']: 全ポイントのリスト
    # data['clusters']: クラスタの要約情報
    ```
    
    ## 推奨される可視化の流れ
    
    1. 時刻ごとにデータをフィルタ
    2. クラスタIDで色分け
    3. 降水量でサイズや透明度を調整
    4. アニメーションで時間変化を表現
    
    ## サンプルコード: 特定時刻のデータを取得
    
    ```python
    import pandas as pd
    
    df = pd.read_csv('clustering_result.csv')
    
    # 時刻0のデータのみ取得
    time_0_data = df[df['time'] == 0]
    
    # ノイズを除外
    time_0_clusters = time_0_data[time_0_data['cluster'] > 0]
    
    # クラスタIDでグループ化
    for cluster_id, group in time_0_clusters.groupby('cluster'):
        print(f"Cluster {cluster_id}: {len(group)} points")
        print(f"  Center: ({group['lat'].mean():.2f}, {group['lon'].mean():.2f})")
    ```
    
    ## サンプルコード: matplotlib で可視化
    
    ```python
    import matplotlib.pyplot as plt
    import pandas as pd
    
    df = pd.read_csv('clustering_result.csv')
    time_data = df[df['time'] == 0]
    
    plt.figure(figsize=(10, 8))
    
    # ノイズ
    noise = time_data[time_data['cluster'] == 0]
    plt.scatter(noise['lon'], noise['lat'], c='gray', 
                s=20, alpha=0.3, label='Noise')
    
    # クラスタ
    clusters = time_data[time_data['cluster'] > 0]
    scatter = plt.scatter(clusters['lon'], clusters['lat'], 
                         c=clusters['cluster'], cmap='tab20',
                         s=clusters['value']*10, alpha=0.6)
    
    plt.colorbar(scatter, label='Cluster ID')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title('Rain Clusters at Time 0')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.show()
    ```
    
    ## 便利な情報ファイル
    
    - cluster_colors.json: 各クラスタの推奨RGB色
    - cluster_bounds.json: 各クラスタの空間範囲（境界ボックス）
    - clusters_by_time.json: 時刻ごとに整理されたクラスタ情報
    
    ## 質問があれば
    
    クラスタリング担当者に連絡してください！
    """
    return guide


if __name__ == "__main__":
    # 使用例
    print(get_visualization_guide())
