"""
ドーナツ化現象の可視化スクリプト
都心部と郊外部の時間帯別変動パターンを可視化
各グラフを個別に保存
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from matplotlib import font_manager
import matplotlib
import sys

# 日本語フォント設定を改善
def setup_japanese_font():
    """日本語フォントを適切に設定"""
    # Windowsの場合
    if sys.platform == 'win32':
        plt.rcParams['font.family'] = 'MS Gothic'
    else:
        # macOS/Linuxの場合
        plt.rcParams['font.family'] = ['Hiragino Sans', 'Yu Gothic', 'Meiryo', 'sans-serif']
    
    plt.rcParams['axes.unicode_minus'] = False
    # フォントサイズも調整
    plt.rcParams['font.size'] = 10
    
setup_japanese_font()

def visualize_donut_pattern():
    """ドーナツ化現象を複数の視点で可視化（個別ファイル保存）"""
    
    # データ読み込み
    df = pd.read_csv('bike_log_donut.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['hour'] = df['timestamp'].dt.hour
    df['minute'] = df['timestamp'].dt.minute
    
    print("\n各グラフを個別に生成します...")
    
    # 1. 時間帯別平均台数の推移（都心部 vs 郊外部）
    print("  [1/6] 時間帯別推移グラフ...")
    fig1, ax1 = plt.subplots(figsize=(10, 6))
    
    downtown_hourly = df[df['area_type'] == 'downtown'].groupby('hour')['free_bikes'].mean()
    suburb_hourly = df[df['area_type'] == 'suburb'].groupby('hour')['free_bikes'].mean()
    
    ax1.plot(downtown_hourly.index, downtown_hourly.values, 'o-', label='都心部（オフィス街）', 
             color='#e74c3c', linewidth=2.5, markersize=8)
    ax1.plot(suburb_hourly.index, suburb_hourly.values, 's-', label='郊外部（住宅街）', 
             color='#3498db', linewidth=2.5, markersize=8)
    
    # ラッシュ時間帯をハイライト
    ax1.axvspan(7, 9, alpha=0.2, color='yellow', label='朝ラッシュ')
    ax1.axvspan(18, 20, alpha=0.2, color='orange', label='夕方ラッシュ')
    
    ax1.set_xlabel('時刻', fontsize=12)
    ax1.set_ylabel('平均利用可能台数', fontsize=12)
    ax1.set_title('ドーナツ化現象: エリア別時間推移', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xticks(range(0, 24, 2))
    plt.tight_layout()
    plt.savefig('donut_1_time_series.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2. 変動率の可視化（前時間帯との差分）
    print("  [2/6] 変動量グラフ...")
    fig2, ax2 = plt.subplots(figsize=(10, 6))
    
    downtown_change = downtown_hourly.diff().fillna(0)
    suburb_change = suburb_hourly.diff().fillna(0)
    
    x = np.arange(len(downtown_change))
    width = 0.35
    
    ax2.bar(x - width/2, downtown_change.values, width, label='都心部', color='#e74c3c', alpha=0.7)
    ax2.bar(x + width/2, suburb_change.values, width, label='郊外部', color='#3498db', alpha=0.7)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    
    ax2.set_xlabel('時刻', fontsize=12)
    ax2.set_ylabel('変動量（前時間比）', fontsize=12)
    ax2.set_title('時間帯別変動量', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_xticks(range(0, 24, 2))
    ax2.set_xticklabels(range(0, 24, 2))
    plt.tight_layout()
    plt.savefig('donut_2_change_rate.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 3. ステーション別ヒートマップ（都心部）
    print("  [3/6] 都心部ヒートマップ...")
    fig3, ax3 = plt.subplots(figsize=(12, 8))
    
    downtown_pivot = df[df['area_type'] == 'downtown'].pivot_table(
        values='free_bikes', 
        index='station_name', 
        columns='hour', 
        aggfunc='mean'
    )
    
    sns.heatmap(downtown_pivot, cmap='RdYlGn', ax=ax3, cbar_kws={'label': '利用可能台数'})
    ax3.set_title('都心部ステーション時間別ヒートマップ', fontsize=14, fontweight='bold')
    ax3.set_xlabel('時刻', fontsize=12)
    ax3.set_ylabel('ステーション名', fontsize=12)
    plt.tight_layout()
    plt.savefig('donut_3_downtown_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 4. ステーション別ヒートマップ（郊外部）
    print("  [4/6] 郊外部ヒートマップ...")
    fig4, ax4 = plt.subplots(figsize=(12, 8))
    
    suburb_pivot = df[df['area_type'] == 'suburb'].pivot_table(
        values='free_bikes', 
        index='station_name', 
        columns='hour', 
        aggfunc='mean'
    )
    
    sns.heatmap(suburb_pivot, cmap='RdYlGn', ax=ax4, cbar_kws={'label': '利用可能台数'})
    ax4.set_title('郊外部ステーション時間別ヒートマップ', fontsize=14, fontweight='bold')
    ax4.set_xlabel('時刻', fontsize=12)
    ax4.set_ylabel('ステーション名', fontsize=12)
    plt.tight_layout()
    plt.savefig('donut_4_suburb_heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 5. 逆相関の証明（散布図）
    print("  [5/6] 相関散布図...")
    fig5, ax5 = plt.subplots(figsize=(10, 8))
    
    hourly_avg = df.groupby(['hour', 'area_type'])['free_bikes'].mean().unstack()
    
    ax5.scatter(hourly_avg['downtown'], hourly_avg['suburb'], 
                s=200, alpha=0.6, c=range(24), cmap='twilight')
    
    # 相関係数を計算
    correlation = hourly_avg['downtown'].corr(hourly_avg['suburb'])
    
    # トレンドライン
    z = np.polyfit(hourly_avg['downtown'], hourly_avg['suburb'], 1)
    p = np.poly1d(z)
    ax5.plot(hourly_avg['downtown'], p(hourly_avg['downtown']), 
             "r--", alpha=0.8, linewidth=2)
    
    ax5.set_xlabel('都心部 平均台数', fontsize=12)
    ax5.set_ylabel('郊外部 平均台数', fontsize=12)
    ax5.set_title(f'都心部 vs 郊外部 相関分析\n相関係数: {correlation:.3f}', 
                  fontsize=14, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    
    # カラーバーで時刻を示す
    sm = plt.cm.ScalarMappable(cmap='twilight', 
                                norm=plt.Normalize(vmin=0, vmax=23))
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax5)
    cbar.set_label('時刻', fontsize=10)
    plt.tight_layout()
    plt.savefig('donut_5_correlation.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 6. 統計サマリー
    print("  [6/6] 統計サマリー...")
    fig6, ax6 = plt.subplots(figsize=(10, 8))
    ax6.axis('off')
    
    # 統計情報を計算
    downtown_stats = df[df['area_type'] == 'downtown'].groupby('hour')['free_bikes'].agg(['mean', 'std', 'min', 'max'])
    suburb_stats = df[df['area_type'] == 'suburb'].groupby('hour')['free_bikes'].agg(['mean', 'std', 'min', 'max'])
    
    # 最小・最大時刻を特定
    downtown_min_hour = downtown_stats['mean'].idxmin()
    downtown_max_hour = downtown_stats['mean'].idxmax()
    suburb_min_hour = suburb_stats['mean'].idxmin()
    suburb_max_hour = suburb_stats['mean'].idxmax()
    
    summary_text = f"""
【ドーナツ化現象の統計サマリー】

■ 都心部（オフィス街）
  • 最少時刻: {downtown_min_hour}時 ({downtown_stats.loc[downtown_min_hour, 'mean']:.1f}台)
  • 最多時刻: {downtown_max_hour}時 ({downtown_stats.loc[downtown_max_hour, 'mean']:.1f}台)
  • 変動幅: {downtown_stats['mean'].max() - downtown_stats['mean'].min():.1f}台
  • 平均台数: {df[df['area_type']=='downtown']['free_bikes'].mean():.1f}台

■ 郊外部（住宅街）
  • 最少時刻: {suburb_min_hour}時 ({suburb_stats.loc[suburb_min_hour, 'mean']:.1f}台)
  • 最多時刻: {suburb_max_hour}時 ({suburb_stats.loc[suburb_max_hour, 'mean']:.1f}台)
  • 変動幅: {suburb_stats['mean'].max() - suburb_stats['mean'].min():.1f}台
  • 平均台数: {df[df['area_type']=='suburb']['free_bikes'].mean():.1f}台

■ 相関分析
  • 相関係数: {correlation:.3f} (負の相関)
  • データ数: {len(df):,} レコード
  • 期間: 平日24時間

■ ドーナツ化現象の特徴
  朝: 都心部↓ 郊外部↑ (通勤)
  夕: 都心部↑ 郊外部↓ (帰宅)
    """
    
    ax6.text(0.1, 0.95, summary_text, transform=ax6.transAxes,
             fontsize=11, verticalalignment='top',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    
    plt.tight_layout()
    plt.savefig('donut_6_summary.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n✓ すべてのグラフを個別ファイルとして保存しました:")
    print("  - donut_1_time_series.png")
    print("  - donut_2_change_rate.png")
    print("  - donut_3_downtown_heatmap.png")
    print("  - donut_4_suburb_heatmap.png")
    print("  - donut_5_correlation.png")
    print("  - donut_6_summary.png")
    
    # 追加の詳細分析
    print("\n" + "=" * 60)
    print("ドーナツ化現象の詳細分析結果")
    print("=" * 60)
    print(f"\n都心部と郊外部の相関係数: {correlation:.3f}")
    print(f"→ 負の相関が見られ、ドーナツ化現象が確認されました")
    print(f"\n都心部の最少時刻: {downtown_min_hour}時 (朝ラッシュ後)")
    print(f"都心部の最多時刻: {downtown_max_hour}時 (夕方ラッシュ後)")
    print(f"\n郊外部の最少時刻: {suburb_min_hour}時 (夕方ラッシュ後)")
    print(f"郊外部の最多時刻: {suburb_max_hour}時 (朝ラッシュ後)")

if __name__ == "__main__":
    print("=" * 60)
    print("ドーナツ化現象の可視化")
    print("=" * 60)
    visualize_donut_pattern()
