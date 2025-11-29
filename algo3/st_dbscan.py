"""
ST-DBSCAN (Spatio-Temporal DBSCAN) Implementation

時空間データのクラスタリングを行うST-DBSCANアルゴリズムの実装
降水地点データから雨雲のクラスタを検出する

参考文献:
Birant, D., & Kut, A. (2007). ST-DBSCAN: An algorithm for clustering 
spatial-temporal data. Data & Knowledge Engineering, 60(1), 208-221.
"""

import numpy as np
from typing import List, Tuple, Set
from dataclasses import dataclass
from collections import deque


@dataclass
class STPoint:
    """時空間データポイント"""
    id: int
    lat: float  # 緯度
    lon: float  # 経度
    time: float  # 時刻（Unix時刻やタイムステップ）
    value: float  # 降水量などの値
    cluster: int = -1  # クラスタID (-1: 未分類, 0: ノイズ, 1~: クラスタID)


class STDBSCAN:
    """
    ST-DBSCAN (Spatio-Temporal DBSCAN) クラスタリング
    
    Parameters
    ----------
    eps1 : float
        空間的な近傍半径 (km)
    eps2 : float
        時間的な近傍半径 (時間単位)
    min_pts : int
        コアポイントとなるための最小ポイント数
    """
    
    def __init__(self, eps1: float, eps2: float, min_pts: int):
        self.eps1 = eps1  # 空間距離の閾値 (km)
        self.eps2 = eps2  # 時間距離の閾値
        self.min_pts = min_pts  # 最小ポイント数
        self.points: List[STPoint] = []
        self.cluster_id = 0
        
    def haversine_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """
        2点間の距離をHaversine公式で計算 (km)
        
        Parameters
        ----------
        lat1, lon1 : float
            地点1の緯度・経度
        lat2, lon2 : float
            地点2の緯度・経度
            
        Returns
        -------
        float
            2点間の距離 (km)
        """
        R = 6371.0  # 地球の半径 (km)
        
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        dlon = np.radians(lon2 - lon1)
        dlat = np.radians(lat2 - lat1)
        
        a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        
        return R * c
    
    def temporal_distance(self, time1: float, time2: float) -> float:
        """
        時間距離を計算
        
        Parameters
        ----------
        time1, time2 : float
            2つの時刻
            
        Returns
        -------
        float
            時間距離の絶対値
        """
        return abs(time1 - time2)
    
    def get_neighbors(self, point_id: int) -> List[int]:
        """
        指定されたポイントのST近傍を取得
        
        空間距離がeps1以内、かつ時間距離がeps2以内のポイントを返す
        
        Parameters
        ----------
        point_id : int
            中心となるポイントのID
            
        Returns
        -------
        List[int]
            近傍ポイントのIDリスト
        """
        neighbors = []
        center_point = self.points[point_id]
        
        for i, point in enumerate(self.points):
            if i == point_id:
                continue
                
            # 空間距離の計算
            spatial_dist = self.haversine_distance(
                center_point.lat, center_point.lon,
                point.lat, point.lon
            )
            
            # 時間距離の計算
            temporal_dist = self.temporal_distance(
                center_point.time, point.time
            )
            
            # ST近傍の判定
            if spatial_dist <= self.eps1 and temporal_dist <= self.eps2:
                neighbors.append(i)
        
        return neighbors
    
    def expand_cluster(self, point_id: int, neighbors: List[int]) -> bool:
        """
        クラスタを拡張
        
        Parameters
        ----------
        point_id : int
            開始ポイントのID
        neighbors : List[int]
            近傍ポイントのIDリスト
            
        Returns
        -------
        bool
            クラスタの拡張に成功したかどうか
        """
        self.cluster_id += 1
        self.points[point_id].cluster = self.cluster_id
        
        # 幅優先探索でクラスタを拡張
        queue = deque(neighbors)
        
        while queue:
            current_id = queue.popleft()
            current_point = self.points[current_id]
            
            # ノイズポイントをクラスタに追加
            if current_point.cluster == 0:
                current_point.cluster = self.cluster_id
            
            # 未分類のポイントの場合
            if current_point.cluster == -1:
                current_point.cluster = self.cluster_id
                
                # 現在のポイントの近傍を取得
                current_neighbors = self.get_neighbors(current_id)
                
                # コアポイントの場合、その近傍もキューに追加
                if len(current_neighbors) >= self.min_pts:
                    for neighbor_id in current_neighbors:
                        if self.points[neighbor_id].cluster == -1:
                            queue.append(neighbor_id)
        
        return True
    
    def fit(self, data: List[STPoint]) -> 'STDBSCAN':
        """
        ST-DBSCANクラスタリングを実行
        
        Parameters
        ----------
        data : List[STPoint]
            時空間データポイントのリスト
            
        Returns
        -------
        STDBSCAN
            自身のインスタンス
        """
        self.points = data
        self.cluster_id = 0
        
        # 全てのポイントを未分類(-1)に初期化
        for point in self.points:
            point.cluster = -1
        
        # 各ポイントについてクラスタリング
        for i, point in enumerate(self.points):
            # 既に分類済みの場合はスキップ
            if point.cluster != -1:
                continue
            
            # 近傍ポイントを取得
            neighbors = self.get_neighbors(i)
            
            # コアポイントでない場合はノイズとしてマーク
            if len(neighbors) < self.min_pts:
                point.cluster = 0  # ノイズ
            else:
                # クラスタを拡張
                self.expand_cluster(i, neighbors)
        
        return self
    
    def get_clusters(self) -> dict:
        """
        クラスタリング結果を取得
        
        Returns
        -------
        dict
            {cluster_id: [point_indices]} の辞書
        """
        clusters = {}
        for i, point in enumerate(self.points):
            cluster_id = point.cluster
            if cluster_id not in clusters:
                clusters[cluster_id] = []
            clusters[cluster_id].append(i)
        
        return clusters
    
    def get_statistics(self) -> dict:
        """
        クラスタリング結果の統計情報を取得
        
        Returns
        -------
        dict
            統計情報の辞書
        """
        clusters = self.get_clusters()
        n_clusters = len([cid for cid in clusters.keys() if cid > 0])
        n_noise = len(clusters.get(0, []))
        n_points = len(self.points)
        
        cluster_sizes = [len(points) for cid, points in clusters.items() if cid > 0]
        
        stats = {
            'n_points': n_points,
            'n_clusters': n_clusters,
            'n_noise': n_noise,
            'noise_ratio': n_noise / n_points if n_points > 0 else 0,
            'cluster_sizes': cluster_sizes,
            'avg_cluster_size': np.mean(cluster_sizes) if cluster_sizes else 0,
            'max_cluster_size': max(cluster_sizes) if cluster_sizes else 0,
            'min_cluster_size': min(cluster_sizes) if cluster_sizes else 0
        }
        
        return stats


def create_precipitation_data(lats: np.ndarray, lons: np.ndarray, 
                              times: np.ndarray, values: np.ndarray,
                              threshold: float = 1.0) -> List[STPoint]:
    """
    気象データから降水地点データを作成
    
    Parameters
    ----------
    lats : np.ndarray
        緯度の配列
    lons : np.ndarray
        経度の配列
    times : np.ndarray
        時刻の配列
    values : np.ndarray
        降水量の配列
    threshold : float
        降水とみなす閾値 (mm/h)
        
    Returns
    -------
    List[STPoint]
        降水地点データのリスト
    """
    precipitation_points = []
    point_id = 0
    
    for i in range(len(lats)):
        if values[i] >= threshold:
            point = STPoint(
                id=point_id,
                lat=lats[i],
                lon=lons[i],
                time=times[i],
                value=values[i]
            )
            precipitation_points.append(point)
            point_id += 1
    
    return precipitation_points
