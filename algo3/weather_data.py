"""
Open-Meteo API を使用した気象データ取得モジュール

このモジュールは以下の機能を提供します:
- Open-Meteo APIからの気象データ取得
- シンプルなファイルキャッシュ機能（ファイルが存在すれば読み込む）
- ST-DBSCANで使用できる形式へのデータ変換

使用例:
    >>> from weather_data import WeatherDataFetcher
    >>> fetcher = WeatherDataFetcher(cache_dir='./data')
    >>> weather_data = fetcher.fetch(
    ...     lat_min=34.5, lat_max=36.0,
    ...     lon_min=138.0, lon_max=140.0,
    ...     start_date='2025-11-24', end_date='2025-11-29'
    ... )
    >>> weather_points = weather_data.to_stpoints()
"""

import json
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
import requests

from st_dbscan import STPoint


@dataclass
class WeatherPoint(STPoint):
    """
    天気データ用の時空間データポイント

    STPointを継承し、気象データに使用する
    """
    pass


class WeatherData:
    """
    Open-Meteo APIから取得した気象データを保持するクラス

    Parameters
    ----------
    api_response : List[Dict]
        Open-Meteo APIのレスポンスデータ（グリッドポイントのリスト）
    metadata : Dict, optional
        メタデータ（緯度経度範囲、取得時刻など）
    """

    def __init__(self, api_response, metadata: Optional[Dict] = None):
        # 常にリストとして扱う（辞書が渡された場合はリストにラップ）
        if isinstance(api_response, dict):
            self.grid_data = [api_response]
        else:
            self.grid_data = api_response
        self.metadata = metadata or {}

    def to_stpoints(self, precipitation_threshold: float = 0.1) -> List[WeatherPoint]:
        """
        WeatherPointのリストに変換

        Parameters
        ----------
        precipitation_threshold : float
            降水とみなす閾値 (mm/h、デフォルト: 0.1mm/h)

        Returns
        -------
        List[WeatherPoint]
            WeatherPointのリスト
        """
        weather_points = []
        point_id = 0

        # 各グリッドポイントを処理
        for grid_point in self.grid_data:
            lat = grid_point.get('latitude')
            lon = grid_point.get('longitude')
            hourly = grid_point.get('hourly', {})
            time_strings = hourly.get('time', [])
            precipitation_values = hourly.get('precipitation', [])

            if not time_strings or not precipitation_values:
                continue

            # 各時刻について処理
            for time_idx, (time_str, precip) in enumerate(zip(time_strings, precipitation_values)):
                # 降水がある場合のみWeatherPointを生成
                if precip is not None and precip >= precipitation_threshold:
                    # 時刻文字列をUnixタイムスタンプに変換
                    dt = datetime.fromisoformat(time_str)
                    unix_time = dt.timestamp()

                    point = WeatherPoint(
                        id=point_id,
                        lat=lat,
                        lon=lon,
                        time=unix_time,
                        value=float(precip)
                    )
                    weather_points.append(point)
                    point_id += 1

        return weather_points

    @classmethod
    def from_json(cls, filepath: str) -> 'WeatherData':
        """
        JSONファイルから気象データを読み込み

        Parameters
        ----------
        filepath : str
            JSONファイルのパス

        Returns
        -------
        WeatherData
            WeatherDataインスタンス
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # メタデータを分離
        metadata = data.get('_metadata', {})
        grid_data = data.get('grid_data', data)

        return cls(api_response=grid_data, metadata=metadata)

    def save_json(self, filepath: str) -> None:
        """
        気象データをJSONファイルに保存

        Parameters
        ----------
        filepath : str
            保存先のJSONファイルパス
        """
        # データとメタデータを結合
        save_data = {
            'grid_data': self.grid_data,
            '_metadata': self.metadata
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)


class WeatherDataFetcher:
    """
    Open-Meteo APIを使用した気象データ取得クラス

    Parameters
    ----------
    cache_dir : str, optional
        キャッシュファイルを保存するディレクトリ (デフォルト: 'data')
    api_base_url : str, optional
        Open-Meteo APIのベースURL
    """

    def __init__(self,
                 cache_dir: str = 'data',
                 api_base_url: str = 'https://api.open-meteo.com/v1/forecast'):
        self.cache_dir = Path(cache_dir)
        self.api_base_url = api_base_url

        # キャッシュディレクトリを作成
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_filename(self, lat_min: float, lat_max: float,
                           lon_min: float, lon_max: float,
                           start_date: str, end_date: str) -> str:
        """
        キャッシュファイル名を生成

        Parameters
        ----------
        lat_min, lat_max : float
            緯度の範囲
        lon_min, lon_max : float
            経度の範囲
        start_date, end_date : str
            日付の範囲

        Returns
        -------
        str
            キャッシュファイル名
        """
        filename = (f"weather_{start_date}_{end_date}_"
                   f"{lat_min:.2f}_{lat_max:.2f}_"
                   f"{lon_min:.2f}_{lon_max:.2f}.json")
        return filename

    def fetch(self,
             lat_min: float,
             lat_max: float,
             lon_min: float,
             lon_max: float,
             start_date: str,
             end_date: str,
             hourly_params: Optional[List[str]] = None,
             model: str = 'jma_msm',
             use_cache: bool = True) -> WeatherData:
        """
        Open-Meteo APIから気象データを取得

        Parameters
        ----------
        lat_min : float
            緯度の最小値
        lat_max : float
            緯度の最大値
        lon_min : float
            経度の最小値
        lon_max : float
            経度の最大値
        start_date : str
            開始日 (YYYY-MM-DD形式)
        end_date : str
            終了日 (YYYY-MM-DD形式)
        hourly_params : Optional[List[str]]
            取得する気象パラメータのリスト
            例: ['precipitation', 'cloud_cover', 'temperature_2m']
            デフォルト: ['precipitation']
        model : str
            使用する気象モデル (デフォルト: 'jma_msm' - 日本気象庁MSMモデル)
        use_cache : bool
            キャッシュを使用するかどうか (デフォルト: True)

        Returns
        -------
        WeatherData
            取得した気象データ

        Raises
        ------
        RuntimeError
            APIリクエストが失敗した場合
        """
        if hourly_params is None:
            hourly_params = ['precipitation']

        # キャッシュファイル名を生成
        cache_filename = self._get_cache_filename(
            lat_min, lat_max, lon_min, lon_max, start_date, end_date
        )
        cache_path = self.cache_dir / cache_filename

        # キャッシュが存在すれば読み込む
        if use_cache and cache_path.exists():
            print(f"✓ Loading from cache: {cache_filename}")
            return WeatherData.from_json(str(cache_path))

        # APIからデータを取得
        print("Fetching data from Open-Meteo API...")
        print(f"  Region: lat [{lat_min}, {lat_max}], lon [{lon_min}, {lon_max}]")
        print(f"  Period: {start_date} to {end_date}")
        print(f"  Parameters: {', '.join(hourly_params)}")

        # 中心座標を計算
        center_lat = (lat_min + lat_max) / 2
        center_lon = (lon_min + lon_max) / 2

        # APIリクエストパラメータを構築
        # bounding_boxの形式: lat_min,lon_min,lat_max,lon_max
        bounding_box_str = f"{lat_min},{lon_min},{lat_max},{lon_max}"

        params = {
            'latitude': center_lat,
            'longitude': center_lon,
            'hourly': ','.join(hourly_params),
            'models': model,
            'bounding_box': bounding_box_str,
            'start_date': start_date,
            'end_date': end_date,
        }

        try:
            response = requests.get(self.api_base_url, params=params, timeout=30)
            response.raise_for_status()
            api_data = response.json()

            # メタデータを作成
            metadata = {
                'fetch_time': datetime.now().isoformat(),
                'bounding_box': {
                    'lat_min': lat_min,
                    'lat_max': lat_max,
                    'lon_min': lon_min,
                    'lon_max': lon_max
                },
                'request_params': params
            }

            # WeatherDataインスタンスを作成
            weather_data = WeatherData(api_response=api_data, metadata=metadata)

            # キャッシュに保存
            if use_cache:
                weather_data.save_json(str(cache_path))
                print(f"✓ Saved to cache: {cache_filename}")

            grid_count = len(weather_data.grid_data)
            print(f"✓ Successfully fetched {grid_count} grid points")

            return weather_data

        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch weather data: {e}")


def fetch_weather_points(lat_min: float,
                         lat_max: float,
                         lon_min: float,
                         lon_max: float,
                         start_date: str,
                         end_date: str,
                         cache_dir: str = 'data',
                         hourly_params: Optional[List[str]] = None,
                         precipitation_threshold: float = 0.1,
                         use_cache: bool = True) -> List[WeatherPoint]:
    """
    気象データを取得してWeatherPointのリストを返す高レベル関数

    Parameters
    ----------
    lat_min : float
        緯度の最小値
    lat_max : float
        緯度の最大値
    lon_min : float
        経度の最小値
    lon_max : float
        経度の最大値
    start_date : str
        開始日 (YYYY-MM-DD形式)
    end_date : str
        終了日 (YYYY-MM-DD形式)
    cache_dir : str, optional
        キャッシュディレクトリ (デフォルト: 'data')
    hourly_params : Optional[List[str]], optional
        取得する気象パラメータのリスト (デフォルト: ['precipitation'])
    precipitation_threshold : float, optional
        降水とみなす閾値 (mm/h、デフォルト: 0.1mm/h)
    use_cache : bool, optional
        キャッシュを使用するかどうか (デフォルト: True)

    Returns
    -------
    List[WeatherPoint]
        WeatherPointのリスト

    Examples
    --------
    >>> points = fetch_weather_points(
    ...     lat_min=34.5, lat_max=36.0,
    ...     lon_min=138.0, lon_max=140.0,
    ...     start_date='2025-11-24',
    ...     end_date='2025-11-29'
    ... )
    """
    fetcher = WeatherDataFetcher(cache_dir=cache_dir)

    weather_data = fetcher.fetch(
        lat_min=lat_min,
        lat_max=lat_max,
        lon_min=lon_min,
        lon_max=lon_max,
        start_date=start_date,
        end_date=end_date,
        hourly_params=hourly_params,
        use_cache=use_cache
    )

    return weather_data.to_stpoints(
        precipitation_threshold=precipitation_threshold
    )


def fetch_tokyo_data(cache_dir: str = 'data') -> List[WeatherPoint]:
    """
    東京周辺の気象データを取得する簡易関数

    東京周辺（緯度34.5-36.0、経度138.0-140.0）の
    2025年11月24-29日の降水データを取得

    Parameters
    ----------
    cache_dir : str, optional
        キャッシュディレクトリ (デフォルト: 'data')

    Returns
    -------
    List[WeatherPoint]
        WeatherPointのリスト

    Examples
    --------
    >>> points = fetch_tokyo_data()
    >>> print(f"取得したポイント数: {len(points)}")
    """
    return fetch_weather_points(
        lat_min=34.5,
        lat_max=36.0,
        lon_min=138.0,
        lon_max=140.0,
        start_date='2025-11-24',
        end_date='2025-11-29',
        cache_dir=cache_dir,
        hourly_params=['precipitation', 'cloud_cover'],
        precipitation_threshold=0.1
    )


# 使用例
if __name__ == "__main__":
    print("=" * 60)
    print("Weather Data Fetcher - Usage Example")
    print("=" * 60)

    # 高レベル関数を使って気象データを取得
    print("\n[1] Fetching weather data using fetch_tokyo_data()...")
    weather_points = fetch_tokyo_data(cache_dir='./data')

    print(f"\n[2] Generated {len(weather_points)} weather points")

    if weather_points:
        print("\n[3] Sample weather points (first 5):")
        for i, point in enumerate(weather_points[:5]):
            print(f"    Point {i}: lat={point.lat:.2f}, lon={point.lon:.2f}, "
                  f"time={point.time:.0f}, value={point.value:.2f} mm/h")

    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)
