"""
地図上で自転車の数の推移をヒートマップで時系列表示する動画を作成
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
from scipy.interpolate import griddata
import matplotlib
import sys

# 日本語フォント設定
def setup_japanese_font():
    """日本語フォントを適切に設定"""
    if sys.platform == 'win32':
        plt.rcParams['font.family'] = 'MS Gothic'
    else:
        plt.rcParams['font.family'] = ['Hiragino Sans', 'Yu Gothic', 'Meiryo', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
    plt.rcParams['font.size'] = 10

setup_japanese_font()

def create_heatmap_animation():
    """地図上のヒートマップ動画を生成"""
    
    print("=" * 60)
    print("地図上ヒートマップ動画生成")
    print("=" * 60)
    
    # データ読み込み
    print("\nデータを読み込んでいます...")
    df = pd.read_csv('bike_log_donut.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # ユニークな時刻を取得
    unique_times = sorted(df['timestamp'].unique())
    print(f"  - データ期間: {unique_times[0]} ～ {unique_times[-1]}")
    print(f"  - フレーム数: {len(unique_times)}")
    
    # 地図の範囲を設定
    lat_min, lat_max = df['latitude'].min() - 0.01, df['latitude'].max() + 0.01
    lon_min, lon_max = df['longitude'].min() - 0.01, df['longitude'].max() + 0.01
    
    # グリッドを作成（ヒートマップ補間用）
    grid_lat, grid_lon = np.mgrid[lat_min:lat_max:100j, lon_min:lon_max:100j]
    
    # 図の設定
    fig, ax = plt.subplots(figsize=(14, 10))
    
    def init():
        """初期化"""
        ax.clear()
        return []
    
    def animate(frame_idx):
        """各フレームの描画"""
        ax.clear()
        
        # 現在の時刻
        current_time = unique_times[frame_idx]
        
        # 現在時刻のデータを抽出
        df_current = df[df['timestamp'] == current_time]
        
        # ステーション座標と自転車数
        lats = df_current['latitude'].values
        lons = df_current['longitude'].values
        bikes = df_current['free_bikes'].values
        
        # グリッド補間（スムーズなヒートマップ）
        try:
            grid_bikes = griddata(
                (lats, lons), bikes, (grid_lat, grid_lon), 
                method='cubic', fill_value=0
            )
            # 負の値をゼロにクリップ
            grid_bikes = np.clip(grid_bikes, 0, None)
        except:
            # 補間失敗時は線形補間にフォールバック
            grid_bikes = griddata(
                (lats, lons), bikes, (grid_lat, grid_lon), 
                method='linear', fill_value=0
            )
        
        # ヒートマップを描画
        heatmap = ax.contourf(
            grid_lon, grid_lat, grid_bikes,
            levels=20, cmap='YlOrRd', alpha=0.6, vmin=0, vmax=35
        )
        
        # ステーション位置をプロット
        # 都心部と郊外部で色分け
        df_downtown = df_current[df_current['area_type'] == 'downtown']
        df_suburb = df_current[df_current['area_type'] == 'suburb']
        
        # 都心部ステーション（赤）
        scatter1 = ax.scatter(
            df_downtown['longitude'], df_downtown['latitude'],
            c=df_downtown['free_bikes'], s=200, cmap='Reds',
            edgecolors='black', linewidths=2, vmin=0, vmax=35,
            marker='s', label='都心部', alpha=0.9
        )
        
        # 郊外部ステーション（青）
        scatter2 = ax.scatter(
            df_suburb['longitude'], df_suburb['latitude'],
            c=df_suburb['free_bikes'], s=200, cmap='Blues',
            edgecolors='black', linewidths=2, vmin=0, vmax=35,
            marker='o', label='郊外部', alpha=0.9
        )
        
        # ステーション名と自転車数を表示（主要ステーションのみ）
        for idx, row in df_current.iterrows():
            # 全ステーションに台数を表示
            ax.text(
                row['longitude'], row['latitude'],
                f"{int(row['free_bikes'])}", 
                fontsize=8, ha='center', va='center',
                color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7)
            )
        
        # タイトルと情報
        hour = current_time.hour
        minute = current_time.minute
        weekday = '月曜日'  # 固定（平日データのため）
        
        title = f'{weekday} {hour:02d}:{minute:02d} の自転車台数分布'
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        
        # 統計情報を表示
        total_bikes = df_current['free_bikes'].sum()
        avg_bikes = df_current['free_bikes'].mean()
        downtown_avg = df_downtown['free_bikes'].mean()
        suburb_avg = df_suburb['free_bikes'].mean()
        
        stats_text = f'総台数: {int(total_bikes)} | 平均: {avg_bikes:.1f}台\n'
        stats_text += f'都心部平均: {downtown_avg:.1f}台 | 郊外部平均: {suburb_avg:.1f}台'
        
        ax.text(
            0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )
        
        # 時間帯の説明
        if 7 <= hour < 9:
            period_text = '朝ラッシュ: 通勤時間帯'
            period_color = 'yellow'
        elif 18 <= hour < 20:
            period_text = '夕方ラッシュ: 帰宅時間帯'
            period_color = 'orange'
        elif 9 <= hour < 18:
            period_text = '日中: 業務時間帯'
            period_color = 'lightblue'
        else:
            period_text = '深夜・早朝: 低活動時間帯'
            period_color = 'lightgray'
        
        ax.text(
            0.98, 0.98, period_text,
            transform=ax.transAxes,
            fontsize=12, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor=period_color, alpha=0.7),
            fontweight='bold'
        )
        
        # 凡例
        ax.legend(loc='upper right', fontsize=10, framealpha=0.9)
        
        # 軸ラベル
        ax.set_xlabel('経度', fontsize=12)
        ax.set_ylabel('緯度', fontsize=12)
        
        # グリッド
        ax.grid(True, alpha=0.3, linestyle='--')
        
        # 縦横比を維持
        ax.set_aspect('equal')
        
        # カラーバー（最初のフレームのみ）
        if frame_idx == 0:
            cbar = plt.colorbar(scatter1, ax=ax, pad=0.02)
            cbar.set_label('利用可能台数', fontsize=11)
        
        return []
    
    print("\nアニメーションを生成中...")
    
    # アニメーション作成
    # フレーム数を間引いて高速化（1時間ごとに表示）
    frame_indices = range(0, len(unique_times), 6)  # 10分間隔×6 = 1時間ごと
    
    anim = FuncAnimation(
        fig, animate, init_func=init,
        frames=frame_indices, interval=500, blit=False, repeat=True
    )
    
    # 動画保存
    output_file = None
    try:
        # MP4で保存を試みる
        print("  MP4形式で保存中...")
        output_file = 'donut_heatmap_animation.mp4'
        writer = FFMpegWriter(fps=2, bitrate=1800)
        anim.save(output_file, writer=writer, dpi=100)
        print(f"✓ {output_file} を保存しました")
    except Exception as e:
        print(f"  MP4保存に失敗: {e}")
        try:
            # GIFで保存
            print("  GIF形式で保存中...")
            output_file = 'donut_heatmap_animation.gif'
            writer = PillowWriter(fps=2)
            anim.save(output_file, writer=writer, dpi=80)
            print(f"✓ {output_file} を保存しました")
        except Exception as e2:
            print(f"  GIF保存にも失敗: {e2}")
            print("  注意: ffmpegまたはPillowのインストールが必要です")
    
    plt.close()
    
    # 詳細情報
    print("\n" + "=" * 60)
    print("動画生成完了")
    print("=" * 60)
    if output_file:
        print(f"\n出力ファイル: {output_file}")
        print(f"フレーム数: {len(frame_indices)} (1時間ごと)")
        print(f"再生速度: 2フレーム/秒")
        print("\n動画の特徴:")
        print("  - 都心部ステーション: 赤い四角")
        print("  - 郊外部ステーション: 青い円")
        print("  - ヒートマップ: 自転車台数の空間分布")
        print("  - 朝ラッシュ: 都心部が減少、郊外部が増加")
        print("  - 夕方ラッシュ: 都心部が増加、郊外部が減少")

if __name__ == "__main__":
    create_heatmap_animation()
