import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("=" * 70)
print("東京23区シェアサイクル大規模データ生成")
print("=" * 70)

# エリア定義
OFFICE_AREAS = {
    'Chiyoda': {'lat': 35.69, 'lon': 139.75, 'type': 'Office'},
    'Minato': {'lat': 35.65, 'lon': 139.75, 'type': 'Office'},
    'Shinjuku': {'lat': 35.69, 'lon': 139.70, 'type': 'Office'},
    'Chuo': {'lat': 35.67, 'lon': 139.77, 'type': 'Office'},
    'Shibuya': {'lat': 35.66, 'lon': 139.70, 'type': 'Office'},
}

RESIDENTIAL_AREAS = {
    'Setagaya': {'lat': 35.64, 'lon': 139.63, 'type': 'Residential'},
    'Nerima': {'lat': 35.73, 'lon': 139.65, 'type': 'Residential'},
    'Edogawa': {'lat': 35.70, 'lon': 139.87, 'type': 'Residential'},
    'Adachi': {'lat': 35.78, 'lon': 139.79, 'type': 'Residential'},
    'Ota': {'lat': 35.56, 'lon': 139.71, 'type': 'Residential'},
}

ALL_AREAS = {**OFFICE_AREAS, **RESIDENTIAL_AREAS}

# ステーション生成
print("\nステーションを生成中...")
stations = []
station_id = 1

for ward_name, ward_info in ALL_AREAS.items():
    center_lat = ward_info['lat']
    center_lon = ward_info['lon']
    ward_type = ward_info['type']
    
    # 各区に10個のステーションを生成（半径2~3km以内）
    for i in range(10):
        # ランダムな距離と角度で配置（緯度経度1度≈111km）
        distance = np.random.uniform(0.02, 0.03)  # 約2~3km
        angle = np.random.uniform(0, 2 * np.pi)
        
        lat = center_lat + distance * np.cos(angle)
        lon = center_lon + distance * np.sin(angle)
        
        stations.append({
            'station_id': station_id,
            'station_name': f'{ward_name}_Station_{i+1}',
            'lat': lat,
            'lon': lon,
            'ward': ward_name,
            'ward_type': ward_type,
            'max_capacity': 30,
            'initial_bikes': np.random.randint(12, 18)  # 初期値は15台前後
        })
        station_id += 1

print(f"生成されたステーション数: {len(stations)}個")
print(f"  - Officeエリア: {len([s for s in stations if s['ward_type'] == 'Office'])}個")
print(f"  - Residentialエリア: {len([s for s in stations if s['ward_type'] == 'Residential'])}個")

# 時系列データ生成
print("\n時系列データを生成中...")

# 昨日0:00から現在までの24時間（10分刻み）
yesterday = datetime.now() - timedelta(days=1)
start_time = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(hours=24)

timestamps = []
current_time = start_time
while current_time < end_time:
    timestamps.append(current_time)
    current_time += timedelta(minutes=10)

print(f"タイムスタンプ数: {len(timestamps)}個 (10分刻み)")
print(f"期間: {timestamps[0]} ～ {timestamps[-1]}")

# 各ステーション・各時刻のデータを生成
data = []

for station in stations:
    station_id = station['station_id']
    station_name = station['station_name']
    lat = station['lat']
    lon = station['lon']
    ward_type = station['ward_type']
    max_capacity = station['max_capacity']
    
    # 初期在庫
    current_bikes = station['initial_bikes']
    
    for timestamp in timestamps:
        hour = timestamp.hour
        minute = timestamp.minute
        time_value = hour + minute / 60.0
        
        # 時間帯による変動
        if ward_type == 'Office':
            # オフィスエリア: 朝に在庫増加、夜に在庫減少
            if 8.0 <= time_value < 10.0:
                # 出勤時間: 在庫が急増（人が自転車で来る）
                change = np.random.uniform(0.5, 2.0)
            elif 18.0 <= time_value < 20.0:
                # 退勤時間: 在庫が急減（人が自転車で帰る）
                change = np.random.uniform(-2.0, -0.5)
            else:
                # 通常時間: 小変動
                change = np.random.uniform(-0.3, 0.3)
        
        else:  # Residential
            # 住宅エリア: 朝に在庫減少、夜に在庫増加
            if 8.0 <= time_value < 10.0:
                # 出勤時間: 在庫が急減（人が自転車で出る）
                change = np.random.uniform(-2.0, -0.5)
            elif 18.0 <= time_value < 20.0:
                # 帰宅時間: 在庫が急増（人が自転車で戻る）
                change = np.random.uniform(0.5, 2.0)
            else:
                # 通常時間: 小変動
                change = np.random.uniform(-0.3, 0.3)
        
        # 在庫を更新（0～max_capacity の範囲内）
        current_bikes += change
        current_bikes = max(0, min(max_capacity, current_bikes))
        
        # データを記録
        data.append({
            'timestamp': timestamp,
            'station_id': station_id,
            'station_name': station_name,
            'lat': lat,
            'lon': lon,
            'free_bikes': int(round(current_bikes)),
            'ward_type': ward_type
        })

# DataFrameに変換
df = pd.DataFrame(data)

# CSVに保存
output_file = 'bike_log_tokyo.csv'
df.to_csv(output_file, index=False)

print(f"\n✓ データ生成完了！")
print(f"出力ファイル: {output_file}")
print(f"総レコード数: {len(df):,}行")
print(f"期間: {df['timestamp'].min()} ～ {df['timestamp'].max()}")

# データの統計情報
print("\n【統計情報】")
print(f"ステーション数: {df['station_id'].nunique()}箇所")
print(f"タイムスタンプ数: {df['timestamp'].nunique()}個")

morning_data = df[df['timestamp'].dt.hour == 9]
night_data = df[df['timestamp'].dt.hour == 19]

print(f"\n【朝9時の状況】")
print(f"  Office平均在庫: {morning_data[morning_data['ward_type']=='Office']['free_bikes'].mean():.1f}台")
print(f"  Residential平均在庫: {morning_data[morning_data['ward_type']=='Residential']['free_bikes'].mean():.1f}台")

print(f"\n【夜19時の状況】")
print(f"  Office平均在庫: {night_data[night_data['ward_type']=='Office']['free_bikes'].mean():.1f}台")
print(f"  Residential平均在庫: {night_data[night_data['ward_type']=='Residential']['free_bikes'].mean():.1f}台")

print("\n" + "=" * 70)
print("処理完了！")
print("=" * 70)
