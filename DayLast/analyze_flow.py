import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo']
matplotlib.rcParams['axes.unicode_minus'] = False

# データ読み込み
df = pd.read_csv('bike_log.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
df['date'] = df['timestamp'].dt.date

# 昨日の日付を取得
from datetime import datetime, timedelta
yesterday = (datetime.now() - timedelta(days=1)).date()

# 昨日のデータのみをフィルタリング
df = df[df['date'] == yesterday]
if len(df) == 0:
    print(f'エラー: {yesterday}のデータがありません')
    print('データを収集してから実行してください')
    exit(1)

print(f'{yesterday}のデータを使用（データ件数: {len(df)}件）')

# 時間範囲でフィルタリング（朝5時～夜24時）
df = df[(df['hour'] >= 5) & (df['hour'] <= 23)]

# エリア判定
def classify_area(row):
    lat, lon = row['latitude'], row['longitude']
    # 千代田区エリア判定
    if 35.67 < lat < 35.69 and 139.75 < lon < 139.77:
        return '千代田区'
    # 江東区エリア判定
    elif 35.64 < lat < 35.66 and 139.78 < lon < 139.81:
        return '江東区'
    else:
        return 'その他'

df['area'] = df.apply(classify_area, axis=1)

# 千代田区と江東区のデータのみ抽出
df_filtered = df[df['area'].isin(['千代田区', '江東区'])]

# 時刻ごとにグループ化して平均台数を計算
time_area_avg = df_filtered.groupby(['timestamp', 'area'])['free_bikes'].mean().reset_index()

# 千代田区と江東区でデータを分離
chiyoda = time_area_avg[time_area_avg['area'] == '千代田区']
koto = time_area_avg[time_area_avg['area'] == '江東区']

# グラフ作成
plt.figure(figsize=(12, 6))
plt.plot(chiyoda['timestamp'], chiyoda['free_bikes'], marker='o', label='千代田区（オフィス街）', linewidth=2)
plt.plot(koto['timestamp'], koto['free_bikes'], marker='s', label='江東区（住宅街）', linewidth=2)
plt.xlabel('時刻', fontsize=12)
plt.ylabel('平均利用可能台数', fontsize=12)
plt.title('エリア別自転車台数推移の比較（5:00～24:00）', fontsize=14)
plt.legend(fontsize=11)
plt.grid(True, alpha=0.3)
plt.xticks(rotation=45)
plt.tight_layout()

# 保存
plt.savefig('flow_analysis.png', dpi=150)

print('\n' + '='*60)
print('flow_analysis.png を保存しました。')
print('='*60)
print(f'\n【千代田区（オフィス街）】')
print(f'  データポイント数: {len(chiyoda)}')
if len(chiyoda) > 0:
    print(f'  平均台数: {chiyoda["free_bikes"].mean():.2f}台')
    print(f'  最小台数: {chiyoda["free_bikes"].min():.2f}台')
    print(f'  最大台数: {chiyoda["free_bikes"].max():.2f}台')
    print(f'  標準偏差: {chiyoda["free_bikes"].std():.2f}台')

print(f'\n【江東区（住宅街）】')
print(f'  データポイント数: {len(koto)}')
if len(koto) > 0:
    print(f'  平均台数: {koto["free_bikes"].mean():.2f}台')
    print(f'  最小台数: {koto["free_bikes"].min():.2f}台')
    print(f'  最大台数: {koto["free_bikes"].max():.2f}台')
    print(f'  標準偏差: {koto["free_bikes"].std():.2f}台')

if len(chiyoda) > 0 and len(koto) > 0:
    diff = chiyoda['free_bikes'].mean() - koto['free_bikes'].mean()
    print(f'\n【比較】')
    print(f'  平均台数の差: {abs(diff):.2f}台（千代田区が{"多い" if diff > 0 else "少ない"}）')
print('='*60)
