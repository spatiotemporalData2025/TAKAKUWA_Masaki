import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from scipy.stats import pearsonr
from sklearn.cluster import DBSCAN
import seaborn as sns

matplotlib.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo']
matplotlib.rcParams['axes.unicode_minus'] = False

print("=" * 60)
print("高度なデータ分析レポート")
print("=" * 60)

# データ読み込み
df = pd.read_csv('bike_log.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=月曜, 6=日曜
df['date'] = df['timestamp'].dt.date

# 昨日の日付を取得
from datetime import datetime, timedelta
yesterday = (datetime.now() - timedelta(days=1)).date()

# 昨日のデータのみをフィルタリング
df = df[df['date'] == yesterday]
if len(df) == 0:
    print(f'\nエラー: {yesterday}のデータがありません')
    print('データを収集してから実行してください')
    exit(1)

print(f'\n{yesterday}のデータを使用')
print(f'データ件数: {len(df)}件\n')

# 時間範囲でフィルタリング（朝5時～夜24時）
df = df[(df['hour'] >= 5) & (df['hour'] <= 23)]

print(f"\n【データ概要】")
print(f"期間: {df['timestamp'].min()} ～ {df['timestamp'].max()}")
print(f"総レコード数: {len(df):,}件")
print(f"ユニークステーション数: {df['station_name'].nunique()}箇所")
print(f"データ取得回数: {df['timestamp'].nunique()}回")

# === 1. 時間帯別の利用パターン ===
print("\n" + "=" * 60)
print("【1】時間帯別の平均利用可能台数")
print("=" * 60)

hourly_avg = df.groupby('hour')['free_bikes'].mean()
print(hourly_avg.to_string())

fig, axes = plt.subplots(2, 2, figsize=(15, 12))

# 時間帯別の推移
axes[0, 0].plot(hourly_avg.index, hourly_avg.values, marker='o', linewidth=2, markersize=8)
axes[0, 0].set_xlabel('時刻', fontsize=11)
axes[0, 0].set_ylabel('平均利用可能台数', fontsize=11)
axes[0, 0].set_title('時間帯別の平均自転車台数（5:00～24:00）', fontsize=12, fontweight='bold')
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].set_xlim(5, 23)
axes[0, 0].set_xticks(range(5, 24, 2))

# === 2. 曜日別パターン（もしデータがあれば） ===
if len(df['date'].unique()) >= 2:
    day_names = ['月', '火', '水', '木', '金', '土', '日']
    daily_avg = df.groupby('day_of_week')['free_bikes'].mean()
    
    print("\n" + "=" * 60)
    print("【2】曜日別の平均利用可能台数")
    print("=" * 60)
    for day_idx, avg in daily_avg.items():
        if day_idx < len(day_names):
            print(f"{day_names[day_idx]}曜日: {avg:.2f}台")
    
    axes[0, 1].bar([day_names[i] for i in daily_avg.index if i < len(day_names)], 
                    daily_avg.values[:len(day_names)], color='steelblue')
    axes[0, 1].set_xlabel('曜日', fontsize=11)
    axes[0, 1].set_ylabel('平均利用可能台数', fontsize=11)
    axes[0, 1].set_title('曜日別の平均自転車台数', fontsize=12, fontweight='bold')
    axes[0, 1].grid(axis='y', alpha=0.3)
else:
    axes[0, 1].text(0.5, 0.5, 'データ期間が短いため\n曜日分析はスキップ', 
                     ha='center', va='center', fontsize=12)
    axes[0, 1].axis('off')

# === 3. ステーション別の利用状況分布 ===
print("\n" + "=" * 60)
print("【3】ステーション別統計（上位10ステーション）")
print("=" * 60)

station_stats = df.groupby('station_name')['free_bikes'].agg(['mean', 'std', 'min', 'max'])
station_stats = station_stats.sort_values('mean', ascending=False).head(10)
print(station_stats.to_string())

station_means = df.groupby('station_name')['free_bikes'].mean().sort_values(ascending=False)
top20 = station_means.head(20)

axes[1, 0].barh(range(len(top20)), top20.values, color='coral')
axes[1, 0].set_yticks(range(len(top20)))
axes[1, 0].set_yticklabels(top20.index, fontsize=8)
axes[1, 0].set_xlabel('平均利用可能台数', fontsize=11)
axes[1, 0].set_title('平均自転車台数 Top20 ステーション', fontsize=12, fontweight='bold')
axes[1, 0].invert_yaxis()
axes[1, 0].grid(axis='x', alpha=0.3)

# === 4. 空間的な分布（ヒートマップ風） ===
print("\n" + "=" * 60)
print("【4】空間的分布の可視化")
print("=" * 60)

# 最新のタイムスタンプのデータを使用
latest_time = df['timestamp'].max()
latest_data = df[df['timestamp'] == latest_time]

scatter = axes[1, 1].scatter(latest_data['longitude'], 
                              latest_data['latitude'],
                              c=latest_data['free_bikes'],
                              cmap='RdYlGn',
                              s=50,
                              alpha=0.6,
                              edgecolors='black',
                              linewidth=0.5)
axes[1, 1].set_xlabel('経度', fontsize=11)
axes[1, 1].set_ylabel('緯度', fontsize=11)
axes[1, 1].set_title(f'最新の自転車分布 ({latest_time})', fontsize=12, fontweight='bold')
plt.colorbar(scatter, ax=axes[1, 1], label='利用可能台数')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('advanced_analysis.png', dpi=150)
print("\n✓ advanced_analysis.png を保存しました。")

# === 5. 空間的クラスタリング（DBSCAN） ===
print("\n" + "=" * 60)
print("【5】空き自転車が少ないエリアのクラスタリング")
print("=" * 60)

# 自転車が3台以下のステーションを抽出
low_stock = latest_data[latest_data['free_bikes'] <= 3]
if len(low_stock) >= 5:
    coords = low_stock[['latitude', 'longitude']].values
    clustering = DBSCAN(eps=0.01, min_samples=3).fit(coords)
    
    num_clusters = len(set(clustering.labels_)) - (1 if -1 in clustering.labels_ else 0)
    print(f"検出されたクラスタ数: {num_clusters}個")
    print(f"クラスタに属するステーション数: {(clustering.labels_ != -1).sum()}箇所")
    
    # クラスタ可視化
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    scatter2 = ax2.scatter(low_stock['longitude'], 
                           low_stock['latitude'],
                           c=clustering.labels_,
                           cmap='tab10',
                           s=100,
                           alpha=0.7,
                           edgecolors='black',
                           linewidth=1)
    ax2.set_xlabel('経度', fontsize=12)
    ax2.set_ylabel('緯度', fontsize=12)
    ax2.set_title('自転車不足エリアのクラスタリング (DBSCAN)', fontsize=14, fontweight='bold')
    plt.colorbar(scatter2, ax=ax2, label='クラスタID')
    ax2.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('cluster_low_stock.png', dpi=150)
    print("✓ cluster_low_stock.png を保存しました。")
else:
    print("クラスタリングに十分なデータがありません（自転車3台以下が5箇所未満）")

# === 6. 相関分析（時間と在庫の関係） ===
print("\n" + "=" * 60)
print("【6】時間帯と在庫量の相関分析")
print("=" * 60)

# 各ステーションで時間帯と在庫の相関を計算
correlations = []
for station in df['station_name'].unique():
    station_data = df[df['station_name'] == station]
    if len(station_data) > 10 and station_data['hour'].nunique() > 1:  # 十分なデータと時間の変動がある場合のみ
        try:
            corr, p_value = pearsonr(station_data['hour'], station_data['free_bikes'])
            correlations.append({
                'station': station,
                'correlation': corr,
                'p_value': p_value
            })
        except:
            pass

if len(correlations) > 0:
    corr_df = pd.DataFrame(correlations)
    corr_df = corr_df.sort_values('correlation')
    
    print(f"\n時間と在庫の相関が強いステーション (Top5):")
    print(corr_df.head(min(5, len(corr_df)))[['station', 'correlation']].to_string(index=False))
    print(f"\n時間と在庫の相関が弱いステーション (Bottom5):")
    print(corr_df.tail(min(5, len(corr_df)))[['station', 'correlation']].to_string(index=False))
else:
    print("\n相関分析をスキップ: データ期間が短すぎます（複数の時間帯のデータが必要）")

# === 7. 変動の激しいステーション ===
print("\n" + "=" * 60)
print("【7】変動が激しいステーション（標準偏差が大きい）")
print("=" * 60)

volatility = df.groupby('station_name')['free_bikes'].std().sort_values(ascending=False).head(10)
print(volatility.to_string())

# === 8. 総合統計 ===
print("\n" + "=" * 60)
print("【8】全体統計サマリー")
print("=" * 60)
print(f"全体平均利用可能台数: {df['free_bikes'].mean():.2f}台")
print(f"全体標準偏差: {df['free_bikes'].std():.2f}台")
print(f"最小値: {df['free_bikes'].min()}台")
print(f"最大値: {df['free_bikes'].max()}台")
print(f"中央値: {df['free_bikes'].median():.2f}台")

# パーセンタイル
print(f"\nパーセンタイル:")
print(f"  25%: {df['free_bikes'].quantile(0.25):.2f}台")
print(f"  50%: {df['free_bikes'].quantile(0.50):.2f}台")
print(f"  75%: {df['free_bikes'].quantile(0.75):.2f}台")
print(f"  90%: {df['free_bikes'].quantile(0.90):.2f}台")

# ヒストグラム
fig3, ax3 = plt.subplots(figsize=(10, 6))
ax3.hist(df['free_bikes'], bins=50, color='skyblue', edgecolor='black', alpha=0.7)
ax3.set_xlabel('利用可能台数', fontsize=12)
ax3.set_ylabel('頻度', fontsize=12)
ax3.set_title('利用可能台数の分布', fontsize=14, fontweight='bold')
ax3.axvline(df['free_bikes'].mean(), color='red', linestyle='--', linewidth=2, label=f'平均: {df["free_bikes"].mean():.1f}台')
ax3.axvline(df['free_bikes'].median(), color='green', linestyle='--', linewidth=2, label=f'中央値: {df["free_bikes"].median():.1f}台')
ax3.legend()
ax3.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('distribution_histogram.png', dpi=150)
print("\n✓ distribution_histogram.png を保存しました。")

print("\n" + "=" * 60)
print("分析完了！以下の画像ファイルが生成されました：")
print("  - advanced_analysis.png")
print("  - cluster_low_stock.png (条件を満たす場合)")
print("  - distribution_histogram.png")
print("=" * 60)
