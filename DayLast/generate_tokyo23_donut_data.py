#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
東京23区全域をカバーするドーナツ化現象データ生成
平日6-21時のみ、30分間隔
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# 東京23区の主要エリア（都心と郊外を広くカバー）
STATIONS_TOKYO23 = [
    # 都心部（千代田区、中央区、港区、新宿区、渋谷区）
    {"name": "丸の内オフィス前", "lat": 35.6812, "lon": 139.7671, "area": "downtown"},
    {"name": "大手町駅", "lat": 35.6870, "lon": 139.7658, "area": "downtown"},
    {"name": "日比谷公園", "lat": 35.6745, "lon": 139.7515, "area": "downtown"},
    {"name": "霞が関官庁街", "lat": 35.6735, "lon": 139.7516, "area": "downtown"},
    {"name": "新橋駅前", "lat": 35.6660, "lon": 139.7577, "area": "downtown"},
    {"name": "銀座四丁目", "lat": 35.6710, "lon": 139.7642, "area": "downtown"},
    {"name": "東京駅丸の内口", "lat": 35.6814, "lon": 139.7670, "area": "downtown"},
    {"name": "虎ノ門ヒルズ", "lat": 35.6656, "lon": 139.7480, "area": "downtown"},
    {"name": "神田駅", "lat": 35.6918, "lon": 139.7708, "area": "downtown"},
    {"name": "秋葉原駅", "lat": 35.6984, "lon": 139.7731, "area": "downtown"},
    {"name": "新宿駅西口", "lat": 35.6896, "lon": 139.7006, "area": "downtown"},
    {"name": "渋谷駅ハチ公口", "lat": 35.6595, "lon": 139.7004, "area": "downtown"},
    {"name": "六本木ヒルズ", "lat": 35.6604, "lon": 139.7292, "area": "downtown"},
    {"name": "赤坂見附駅", "lat": 35.6792, "lon": 139.7366, "area": "downtown"},
    {"name": "表参道駅", "lat": 35.6654, "lon": 139.7125, "area": "downtown"},
    
    # 郊外部（江東区、品川区、目黒区、世田谷区、杉並区、練馬区、板橋区、北区、足立区、葛飾区、江戸川区）
    {"name": "豊洲駅前", "lat": 35.6550, "lon": 139.7954, "area": "suburb"},
    {"name": "東雲住宅街", "lat": 35.6393, "lon": 139.8011, "area": "suburb"},
    {"name": "有明ガーデン", "lat": 35.6348, "lon": 139.7900, "area": "suburb"},
    {"name": "辰巳団地", "lat": 35.6448, "lon": 139.8178, "area": "suburb"},
    {"name": "木場公園", "lat": 35.6711, "lon": 139.8113, "area": "suburb"},
    {"name": "品川シーサイド", "lat": 35.6088, "lon": 139.7389, "area": "suburb"},
    {"name": "大井町駅", "lat": 35.6056, "lon": 139.7335, "area": "suburb"},
    {"name": "武蔵小山商店街", "lat": 35.6131, "lon": 139.7080, "area": "suburb"},
    {"name": "中目黒駅", "lat": 35.6443, "lon": 139.6987, "area": "suburb"},
    {"name": "学芸大学駅", "lat": 35.6301, "lon": 139.6961, "area": "suburb"},
    {"name": "三軒茶屋駅", "lat": 35.6434, "lon": 139.6694, "area": "suburb"},
    {"name": "下北沢駅", "lat": 35.6611, "lon": 139.6681, "area": "suburb"},
    {"name": "成城学園前駅", "lat": 35.6419, "lon": 139.6024, "area": "suburb"},
    {"name": "荻窪駅", "lat": 35.7053, "lon": 139.6203, "area": "suburb"},
    {"name": "高円寺駅", "lat": 35.7046, "lon": 139.6493, "area": "suburb"},
    {"name": "中野駅", "lat": 35.7056, "lon": 139.6656, "area": "suburb"},
    {"name": "練馬駅", "lat": 35.7375, "lon": 139.6524, "area": "suburb"},
    {"name": "光が丘公園", "lat": 35.7609, "lon": 139.6311, "area": "suburb"},
    {"name": "板橋区役所前", "lat": 35.7514, "lon": 139.7094, "area": "suburb"},
    {"name": "赤羽駅", "lat": 35.7775, "lon": 139.7222, "area": "suburb"},
    {"name": "王子駅", "lat": 35.7531, "lon": 139.7380, "area": "suburb"},
    {"name": "北千住駅", "lat": 35.7493, "lon": 139.8048, "area": "suburb"},
    {"name": "綾瀬駅", "lat": 35.7493, "lon": 139.8267, "area": "suburb"},
    {"name": "亀有駅", "lat": 35.7609, "lon": 139.8481, "area": "suburb"},
    {"name": "金町駅", "lat": 35.7647, "lon": 139.8706, "area": "suburb"},
    {"name": "葛西駅", "lat": 35.6656, "lon": 139.8599, "area": "suburb"},
    {"name": "西葛西駅", "lat": 35.6656, "lon": 139.8681, "area": "suburb"},
    {"name": "船堀駅", "lat": 35.6856, "lon": 139.8686, "area": "suburb"},
    {"name": "小岩駅", "lat": 35.7337, "lon": 139.8824, "area": "suburb"},
    {"name": "錦糸町駅", "lat": 35.6969, "lon": 139.8137, "area": "suburb"},
]

def generate_donut_pattern_data():
    """ドーナツ化現象を示すデータを生成"""
    print("=" * 70)
    print("東京23区ドーナツ化現象データ生成")
    print("=" * 70)
    
    # 平日1日分のデータ（6:00-21:50、10分間隔）
    start_time = datetime(2026, 1, 27, 6, 0, 0)
    time_points = []
    for i in range(96):  # 6:00-21:50 = 16時間 × 6 (10分間隔)
        time_points.append(start_time + timedelta(minutes=i*10))
    
    records = []
    
    for t in time_points:
        hour = t.hour + t.minute / 60.0
        
        # ドーナツ化パターン: 時間帯による都心/郊外の自転車数変動（顕著な差）
        for station in STATIONS_TOKYO23:
            if station["area"] == "downtown":
                # 都心部: 早朝・夜は極めて少なく、昼間は極めて多い
                if 6 <= hour < 9:
                    # 早朝: 都心部はほぼゼロ（住宅街から通勤で持ち出される）
                    base = 1
                    variation = np.random.randint(0, 2)
                elif 9 <= hour < 18:
                    # 日中: 都心部に大量集中（通勤者が持ってくる）
                    base = 28
                    variation = np.random.randint(-3, 5)
                elif 18 <= hour < 21:
                    # 夕方: 都心部から持ち出され始める
                    base = 12
                    variation = np.random.randint(-4, 4)
                else:
                    base = 2
                    variation = np.random.randint(0, 2)
            else:
                # 郊外部: 早朝・夜は極めて多く、昼間は極めて少ない
                if 6 <= hour < 9:
                    # 早朝: 郊外部に大量密集（住宅街に夜間停車）
                    base = 30
                    variation = np.random.randint(-3, 5)
                elif 9 <= hour < 18:
                    # 日中: 郊外部はほぼゼロ（通勤で持ち出される）
                    base = 2
                    variation = np.random.randint(0, 3)
                elif 18 <= hour < 21:
                    # 夕方: 郊外部に戻ってくる
                    base = 18
                    variation = np.random.randint(-5, 5)
                else:
                    base = 25
                    variation = np.random.randint(-4, 5)
            
            free_bikes = max(0, min(35, base + variation))
            
            records.append({
                "timestamp": t.strftime('%Y-%m-%d %H:%M:%S'),
                "station_name": station["name"],
                "free_bikes": free_bikes,
                "latitude": station["lat"],
                "longitude": station["lon"],
                "area_type": station["area"]
            })
    
    df = pd.DataFrame(records)
    
    # CSV保存
    output_file = "bike_log_donut.csv"
    df.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\n✓ {output_file} を生成しました")
    print(f"  - レコード数: {len(df):,}")
    print(f"  - ステーション数: {len(STATIONS_TOKYO23)}")
    print(f"  - 都心部: {len([s for s in STATIONS_TOKYO23 if s['area'] == 'downtown'])}")
    print(f"  - 郊外部: {len([s for s in STATIONS_TOKYO23 if s['area'] == 'suburb'])}")
    print(f"  - 時間範囲: 6:00-21:50 (10分間隔)")
    print(f"  - タイムスタンプ数: {len(time_points)}")
    print(f"  - 緯度範囲: {df['latitude'].min():.4f} ～ {df['latitude'].max():.4f}")
    print(f"  - 経度範囲: {df['longitude'].min():.4f} ～ {df['longitude'].max():.4f}")
    
    print("\n【ドーナツ化パターン（顕著）】")
    print("  早朝(6-9時): 都心→ほぼ0台 / 郊外→30台（密集）")
    print("  日中(9-18時): 都心→30台（密集） / 郊外→ほぼ0台")
    print("  夕方(18-21時): 都心→減少 / 郊外→増加")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    generate_donut_pattern_data()
