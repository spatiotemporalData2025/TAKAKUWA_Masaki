import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo']
matplotlib.rcParams['axes.unicode_minus'] = False

# データ読み込み
df = pd.read_csv('bike_log.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
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

# ステーションごとにグループ化
stations = df.groupby('station_name')

# 各ステーションの変動回数を計算
change_counts = {}
for station_name, group in stations:
    # 時系列順にソート
    group_sorted = group.sort_values('timestamp')
    # free_bikesの差分を計算（前回との比較）
    changes = (group_sorted['free_bikes'].diff() != 0).sum()
    # NaNでない変化をカウント
    change_counts[station_name] = changes

# 変動回数でソート
sorted_changes = sorted(change_counts.items(), key=lambda x: x[1], reverse=True)

# Top10を取得
top10 = sorted_changes[:10]
stations_top10 = [x[0] for x in top10]
counts_top10 = [x[1] for x in top10]

# 棒グラフ作成
plt.figure(figsize=(12, 6))
plt.barh(range(len(stations_top10)), counts_top10, color='steelblue')
plt.yticks(range(len(stations_top10)), stations_top10, fontsize=9)
plt.xlabel('変動回数', fontsize=12)
plt.ylabel('ステーション名', fontsize=12)
plt.title('在庫変動回数 Top10 ステーション', fontsize=14)
plt.gca().invert_yaxis()  # 上位を上に表示
plt.grid(axis='x', alpha=0.3)
plt.tight_layout()

# 保存
plt.savefig('station_ranking.png', dpi=150)

print('\n' + '='*60)
print('station_ranking.png を保存しました。')
print('='*60)
print('\n【Top10 変動回数ランキング】')
for i, (station, count) in enumerate(top10, 1):
    print(f'{i:2d}. {station}: {count:4d}回')

if len(sorted_changes) >= 10:
    print(f'\n【統計情報】')
    all_counts = [x[1] for x in sorted_changes]
    print(f'  総ステーション数: {len(sorted_changes)}')
    print(f'  平均変動回数: {np.mean(all_counts):.2f}回')
    print(f'  中央値: {np.median(all_counts):.2f}回')
    print(f'  最大変動回数: {max(all_counts)}回')
    print(f'  最小変動回数: {min(all_counts)}回')
    print(f'\n  変動が最も少ないステーション:')
    for i, (station, count) in enumerate(sorted_changes[-3:], 1):
        print(f'    {station}: {count}回')
print('='*60)
