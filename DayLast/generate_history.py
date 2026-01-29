import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv

print("=" * 60)
print("過去24時間のシェアサイクルデータをシミュレーション生成")
print("=" * 60)

# 期間設定：昨日0:00から現在まで
end_time = datetime.now()
start_time = datetime(end_time.year, end_time.month, end_time.day - 1, 0, 0, 0)

# 10分刻みでタイムスタンプを生成
timestamps = []
current = start_time
while current <= end_time:
    timestamps.append(current)
    current += timedelta(minutes=10)

print(f"\n期間: {start_time} ～ {end_time}")
print(f"データポイント数: {len(timestamps)}個 (10分間隔)")

# ステーション定義
stations = [
    # オフィスエリア（千代田区周辺）
    {"name": "Office_Station_1", "lat": 35.6812, "lon": 139.7671, "type": "office"},
    {"name": "Office_Station_2", "lat": 35.6820, "lon": 139.7660, "type": "office"},
    # 住宅エリア（江東区周辺）
    {"name": "Home_Station_1", "lat": 35.6500, "lon": 139.8000, "type": "home"},
    {"name": "Home_Station_2", "lat": 35.6510, "lon": 139.7990, "type": "home"},
]

# データ生成関数
def generate_bike_count(hour, station_type, base_count=20, max_count=30):
    """
    時間帯とステーションタイプに応じた自転車台数を生成
    """
    bikes = base_count
    
    if station_type == "office":
        # オフィスエリア: 朝は増加、夜は減少
        if 7 <= hour < 9:
            # 朝の通勤時間 - オフィスに自転車が集まる
            bikes += int(8 * (1 - abs(hour - 8) / 1))  # 8時がピーク
        elif 17 <= hour < 19:
            # 夜の退勤時間 - オフィスから自転車がなくなる
            bikes -= int(8 * (1 - abs(hour - 18) / 1))  # 18時がボトム
    
    elif station_type == "home":
        # 住宅エリア: 朝は減少、夜は増加
        if 7 <= hour < 9:
            # 朝の通勤時間 - 住宅から自転車がなくなる
            bikes -= int(8 * (1 - abs(hour - 8) / 1))  # 8時がボトム
        elif 17 <= hour < 19:
            # 夜の帰宅時間 - 住宅に自転車が戻る
            bikes += int(8 * (1 - abs(hour - 18) / 1))  # 18時がピーク
    
    # ランダムな変動を追加（小さめ）
    bikes += np.random.randint(-2, 3)
    
    # 範囲制限
    bikes = max(0, min(max_count, bikes))
    
    return bikes

# CSVファイル生成
output_file = "bike_log.csv"
print(f"\n{output_file} を生成中...")

with open(output_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['timestamp', 'station_name', 'free_bikes', 'latitude', 'longitude'])
    
    record_count = 0
    for ts in timestamps:
        hour = ts.hour
        for station in stations:
            bikes = generate_bike_count(hour, station['type'])
            writer.writerow([
                ts.strftime('%Y-%m-%d %H:%M:%S'),
                station['name'],
                bikes,
                station['lat'],
                station['lon']
            ])
            record_count += 1

print(f"✓ 生成完了: {record_count}レコード")

# 統計情報表示
print("\n" + "=" * 60)
print("データ統計")
print("=" * 60)

df = pd.read_csv(output_file)
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour

# エリア分類
def classify_area(name):
    if 'Office' in name:
        return 'オフィスエリア'
    elif 'Home' in name:
        return '住宅エリア'
    return 'その他'

df['area'] = df['station_name'].apply(classify_area)

# 時間帯別平均
print("\n【時間帯別平均台数】")
for area in ['オフィスエリア', '住宅エリア']:
    area_data = df[df['area'] == area]
    hourly_avg = area_data.groupby('hour')['free_bikes'].mean()
    
    print(f"\n{area}:")
    print(f"  朝7時: {hourly_avg.get(7, 0):.1f}台")
    print(f"  朝8時: {hourly_avg.get(8, 0):.1f}台")
    print(f"  朝9時: {hourly_avg.get(9, 0):.1f}台")
    print(f"  夕17時: {hourly_avg.get(17, 0):.1f}台")
    print(f"  夕18時: {hourly_avg.get(18, 0):.1f}台")
    print(f"  夕19時: {hourly_avg.get(19, 0):.1f}台")

# ピーク・ボトム検出
print("\n【ピーク・ボトム時刻】")
for area in ['オフィスエリア', '住宅エリア']:
    area_data = df[df['area'] == area]
    hourly_avg = area_data.groupby('hour')['free_bikes'].mean()
    
    peak_hour = hourly_avg.idxmax()
    bottom_hour = hourly_avg.idxmin()
    
    print(f"\n{area}:")
    print(f"  ピーク: {peak_hour}時 ({hourly_avg[peak_hour]:.1f}台)")
    print(f"  ボトム: {bottom_hour}時 ({hourly_avg[bottom_hour]:.1f}台)")

print("\n" + "=" * 60)
print("シミュレーションデータ生成完了！")
print("分析スクリプトを実行してグラフを生成できます:")
print("  python analyze_flow.py")
print("  python analyze_advanced.py")
print("  python create_heatmap_video.py")
print("=" * 60)
