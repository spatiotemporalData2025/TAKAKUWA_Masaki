"""
平日24時間のダミーデータ生成スクリプト
ドーナツ化現象を可視化できるデータを生成
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv

# ステーション定義
# 都心部（オフィス街）: 朝は自転車が減る（通勤で借りられる）、夕方は増える（返却される）
downtown_stations = [
    {"name": "丸の内オフィス前", "lat": 35.6812, "lon": 139.7671, "base_bikes": 15},
    {"name": "大手町駅", "lat": 35.6870, "lon": 139.7658, "base_bikes": 20},
    {"name": "日比谷公園", "lat": 35.6745, "lon": 139.7515, "base_bikes": 18},
    {"name": "霞が関官庁街", "lat": 35.6735, "lon": 139.7516, "base_bikes": 16},
    {"name": "新橋駅前", "lat": 35.6660, "lon": 139.7577, "base_bikes": 22},
    {"name": "銀座四丁目", "lat": 35.6710, "lon": 139.7642, "base_bikes": 17},
    {"name": "東京駅丸の内口", "lat": 35.6814, "lon": 139.7670, "base_bikes": 25},
    {"name": "虎ノ門ヒルズ", "lat": 35.6656, "lon": 139.7480, "base_bikes": 19},
    {"name": "神田駅", "lat": 35.6918, "lon": 139.7708, "base_bikes": 21},
    {"name": "秋葉原駅", "lat": 35.6984, "lon": 139.7731, "base_bikes": 23},
]

# 郊外部（住宅街）: 朝は自転車が増える（通勤で返却される）、夕方は減る（借りられる）
suburb_stations = [
    {"name": "豊洲駅前", "lat": 35.6550, "lon": 139.7954, "base_bikes": 12},
    {"name": "東雲住宅街", "lat": 35.6393, "lon": 139.8011, "base_bikes": 14},
    {"name": "有明ガーデン", "lat": 35.6348, "lon": 139.7900, "base_bikes": 10},
    {"name": "辰巳団地", "lat": 35.6448, "lon": 139.8178, "base_bikes": 13},
    {"name": "木場公園", "lat": 35.6711, "lon": 139.8113, "base_bikes": 11},
    {"name": "品川シーサイド", "lat": 35.6088, "lon": 139.7389, "base_bikes": 15},
    {"name": "大井町駅", "lat": 35.6056, "lon": 139.7335, "base_bikes": 14},
    {"name": "武蔵小山商店街", "lat": 35.6131, "lon": 139.7080, "base_bikes": 12},
    {"name": "中目黒駅", "lat": 35.6443, "lon": 139.6987, "base_bikes": 16},
    {"name": "学芸大学駅", "lat": 35.6301, "lon": 139.6961, "base_bikes": 13},
]

def calculate_bikes_downtown(hour, base_bikes):
    """
    都心部（オフィス街）の時間帯別自転車台数
    朝: 減少（通勤で借りられる）
    夕: 増加（返却される）
    """
    # 基本変動パターン
    if 5 <= hour < 7:  # 早朝: やや減少開始
        factor = 0.9
    elif 7 <= hour < 9:  # 朝ラッシュ: 大幅減少（通勤で借りられる）
        factor = 0.3 - 0.1 * (hour - 7)  # 7時: 0.3, 8時: 0.2
    elif 9 <= hour < 12:  # 午前中: 少ない状態維持
        factor = 0.25
    elif 12 <= hour < 14:  # 昼休み: やや回復
        factor = 0.4
    elif 14 <= hour < 18:  # 午後: 少ない状態
        factor = 0.3
    elif 18 <= hour < 20:  # 夕方ラッシュ: 大幅増加（返却される）
        factor = 1.2 + 0.3 * (hour - 18)  # 18時: 1.2, 19時: 1.5
    elif 20 <= hour < 22:  # 夜: 多い状態維持
        factor = 1.4
    elif 22 <= hour < 24:  # 深夜: 徐々に減少
        factor = 1.2
    else:  # 0-5時: 深夜
        factor = 1.0
    
    # ランダムノイズを追加（±20%）
    noise = np.random.uniform(0.8, 1.2)
    bikes = int(base_bikes * factor * noise)
    
    # 0台から最大容量（base_bikes * 2）の範囲に制限
    return max(0, min(bikes, base_bikes * 2))

def calculate_bikes_suburb(hour, base_bikes):
    """
    郊外部（住宅街）の時間帯別自転車台数
    朝: 増加（通勤で返却される）
    夕: 減少（借りられる）
    """
    # 基本変動パターン（都心部の逆）
    if 5 <= hour < 7:  # 早朝: やや増加開始
        factor = 1.1
    elif 7 <= hour < 9:  # 朝ラッシュ: 大幅増加（通勤で返却される）
        factor = 1.5 + 0.2 * (hour - 7)  # 7時: 1.5, 8時: 1.7
    elif 9 <= hour < 12:  # 午前中: 多い状態維持
        factor = 1.6
    elif 12 <= hour < 14:  # 昼休み: やや減少
        factor = 1.2
    elif 14 <= hour < 18:  # 午後: 多い状態
        factor = 1.4
    elif 18 <= hour < 20:  # 夕方ラッシュ: 大幅減少（借りられる）
        factor = 0.4 - 0.1 * (hour - 18)  # 18時: 0.4, 19時: 0.3
    elif 20 <= hour < 22:  # 夜: 少ない状態維持
        factor = 0.3
    elif 22 <= hour < 24:  # 深夜: 徐々に増加
        factor = 0.5
    else:  # 0-5時: 深夜
        factor = 0.8
    
    # ランダムノイズを追加（±20%）
    noise = np.random.uniform(0.8, 1.2)
    bikes = int(base_bikes * factor * noise)
    
    # 0台から最大容量（base_bikes * 2）の範囲に制限
    return max(0, min(bikes, base_bikes * 2))

def generate_donut_data():
    """平日24時間のドーナツ化現象データを生成"""
    
    # 開始時刻: 平日の0時から
    start_time = datetime(2026, 1, 27, 0, 0, 0)  # 月曜日
    
    # CSVファイル作成
    csv_file = "bike_log_donut.csv"
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'station_name', 'free_bikes', 'latitude', 'longitude', 'area_type'])
        
        # 24時間分のデータを10分間隔で生成
        for minutes in range(0, 24 * 60, 10):  # 10分間隔
            current_time = start_time + timedelta(minutes=minutes)
            hour = current_time.hour
            timestamp_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
            
            # 都心部ステーション
            for station in downtown_stations:
                bikes = calculate_bikes_downtown(hour, station['base_bikes'])
                writer.writerow([
                    timestamp_str,
                    station['name'],
                    bikes,
                    station['lat'],
                    station['lon'],
                    'downtown'
                ])
            
            # 郊外部ステーション
            for station in suburb_stations:
                bikes = calculate_bikes_suburb(hour, station['base_bikes'])
                writer.writerow([
                    timestamp_str,
                    station['name'],
                    bikes,
                    station['lat'],
                    station['lon'],
                    'suburb'
                ])
        
        print(f"✓ {csv_file} を生成しました")
        print(f"  - データ期間: 平日24時間（10分間隔）")
        print(f"  - データ数: {24 * 6 * (len(downtown_stations) + len(suburb_stations))} レコード")
        print(f"  - 都心部ステーション: {len(downtown_stations)}箇所")
        print(f"  - 郊外部ステーション: {len(suburb_stations)}箇所")

if __name__ == "__main__":
    print("=" * 60)
    print("平日24時間ドーナツ化現象データ生成")
    print("=" * 60)
    generate_donut_data()
    print("\n次のステップ:")
    print("  1. python visualize_donut_pattern.py  # 可視化")
    print("  2. python analyze_flow.py             # エリア別分析")
