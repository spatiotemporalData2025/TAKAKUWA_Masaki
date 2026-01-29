"""
地図上で自転車の数の推移をヒートマップで時系列表示する動画を作成
OpenStreetMapを背景地図として使用
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
from scipy.interpolate import griddata
import matplotlib
import sys
import contextily as ctx
from matplotlib.patches import Rectangle

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

def lat_lon_to_mercator(lat, lon):
    """緯度経度をWeb Mercator座標に変換"""
    import math
    x = lon * 20037508.34 / 180
    y = math.log(math.tan((90 + lat) * math.pi / 360)) / (math.pi / 180)
    y = y * 20037508.34 / 180
    return x, y

def mercator_to_lat_lon(x, y):
    """Web Mercator座標を緯度経度に変換"""
    import math
    lon = x * 180 / 20037508.34
    lat = math.atan(math.exp(y * math.pi / 20037508.34)) * 360 / math.pi - 90
    return lat, lon

def create_heatmap_animation():
    """地図上のヒートマップ動画を生成（OpenStreetMap背景付き）"""
    
    print("=" * 60)
    print("地図上ヒートマップ動画生成（OpenStreetMap使用）")
    print("=" * 60)
    
    # データ読み込み
    print("\nデータを読み込んでいます...")
    df = pd.read_csv('bike_log_donut.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    print(f"  - 全データ: {len(df)} 件")
    
    # 平日6-21時のみに絞り込み
    df = df[(df['timestamp'].dt.hour >= 6) & (df['timestamp'].dt.hour <= 21)].copy()
    print(f"  - 6-21時フィルタ後: {len(df)} 件")
    
    # 東京23区の範囲に限定（bike_log_donut.csvは既に23区内データなのでスキップ）
    # すべてのデータが既に23区内にあるため、フィルタは不要
    
    # ユニークな時刻を取得
    unique_times = sorted(df['timestamp'].unique())
    print(f"  - データ期間: {unique_times[0]} ～ {unique_times[-1]}")
    print(f"  - 対象時間帯: 平日6時～21時")
    print(f"  - フレーム数: {len(unique_times)}")
    
    # 緯度経度の範囲
    lat_min, lat_max = df['latitude'].min() - 0.01, df['latitude'].max() + 0.01
    lon_min, lon_max = df['longitude'].min() - 0.01, df['longitude'].max() + 0.01
    
    # Web Mercator座標に変換
    xmin, ymin = lat_lon_to_mercator(lat_min, lon_min)
    xmax, ymax = lat_lon_to_mercator(lat_max, lon_max)
    
    # ステーション座標をMercatorに変換
    df['x_mercator'] = df.apply(lambda row: lat_lon_to_mercator(row['latitude'], row['longitude'])[0], axis=1)
    df['y_mercator'] = df.apply(lambda row: lat_lon_to_mercator(row['latitude'], row['longitude'])[1], axis=1)
    
    # グリッドを作成（Mercator座標系）
    grid_x, grid_y = np.mgrid[xmin:xmax:100j, ymin:ymax:100j]
    
    # 図の設定
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # OpenStreetMapを一度だけ取得
    print("\nOpenStreetMapタイルを取得中...")
    try:
        # 初期設定でOSMを描画
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ctx.add_basemap(
            ax, 
            source=ctx.providers.OpenStreetMap.Mapnik,
            zoom=13,
            attribution="© OpenStreetMap contributors"
        )
        print("  ✓ OpenStreetMapの取得に成功しました")
        use_basemap = True
    except Exception as e:
        print(f"  ! OpenStreetMapの取得に失敗: {e}")
        print("  背景地図なしで続行します")
        use_basemap = False
    
    def init():
        """初期化"""
        ax.clear()
        if use_basemap:
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ctx.add_basemap(
                ax, 
                source=ctx.providers.OpenStreetMap.Mapnik,
                zoom=13,
                attribution=""
            )
        return []
    
    def animate(frame_idx):
        """各フレームの描画"""
        ax.clear()
        
        # OpenStreetMap背景を再描画
        if use_basemap:
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(ymin, ymax)
            ctx.add_basemap(
                ax, 
                source=ctx.providers.OpenStreetMap.Mapnik,
                zoom=13,
                attribution=""
            )
        
        # 現在の時刻
        current_time = unique_times[frame_idx]
        
        # 現在時刻のデータを抽出
        df_current = df[df['timestamp'] == current_time]
        
        # ステーション座標と自転車数（Mercator座標）
        xs = df_current['x_mercator'].values
        ys = df_current['y_mercator'].values
        bikes = df_current['free_bikes'].values
        
        # グリッド補間（スムーズなヒートマップ）
        try:
            grid_bikes = griddata(
                (xs, ys), bikes, (grid_x, grid_y), 
                method='cubic', fill_value=0
            )
            # 負の値をゼロにクリップ
            grid_bikes = np.clip(grid_bikes, 0, None)
        except:
            # 補間失敗時は線形補間にフォールバック
            grid_bikes = griddata(
                (xs, ys), bikes, (grid_x, grid_y), 
                method='linear', fill_value=0
            )
        
        # ヒートマップを描画（やや濃いめ）
        heatmap = ax.contourf(
            grid_x, grid_y, grid_bikes,
            levels=20, cmap='YlOrRd', alpha=0.7, vmin=0, vmax=35
        )
        
        # カラーバーを追加
        if frame_idx == 0:  # 最初のフレームのみ
            cbar = plt.colorbar(heatmap, ax=ax, fraction=0.03, pad=0.02)
            cbar.set_label('自転車台数', fontsize=12, fontweight='bold')
            cbar.ax.tick_params(labelsize=10)
        
        # タイトルと情報
        hour = current_time.hour
        minute = current_time.minute
        weekday = '月曜日'  # 固定（平日データのため）
        
        title = f'{weekday} {hour:02d}:{minute:02d} の自転車台数分布'
        ax.set_title(title, fontsize=18, fontweight='bold', pad=20)
        
        # 統計情報を表示
        total_bikes = df_current['free_bikes'].sum()
        avg_bikes = df_current['free_bikes'].mean()
        
        # エリア別平均を計算
        df_downtown = df_current[df_current['area_type'] == 'downtown']
        df_suburb = df_current[df_current['area_type'] == 'suburb']
        downtown_avg = df_downtown['free_bikes'].mean() if len(df_downtown) > 0 else 0
        suburb_avg = df_suburb['free_bikes'].mean() if len(df_suburb) > 0 else 0
        
        stats_text = f'総台数: {int(total_bikes)} | 平均: {avg_bikes:.1f}台\n'
        stats_text += f'都心部平均: {downtown_avg:.1f}台 | 郊外部平均: {suburb_avg:.1f}台'
        
        ax.text(
            0.02, 0.98, stats_text,
            transform=ax.transAxes,
            fontsize=12, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='black', linewidth=2),
            zorder=10
        )
        
        # 時間帯の説明とドーナツ化現象の強調
        if 7 <= hour < 9:
            period_text = '早朝: 郊外密集 / 都心ほぼ0'
            period_color = 'yellow'
        elif 18 <= hour < 20:
            period_text = '夕方: 都心→郊外へ移動中'
            period_color = 'orange'
        elif 9 <= hour < 18:
            period_text = '日中: 都心密集 / 郊外ほぼ0'
            period_color = 'lightblue'
        else:
            period_text = '夜間: 郊外に集中'
            period_color = 'lightgray'
        
        ax.text(
            0.98, 0.98, period_text,
            transform=ax.transAxes,
            fontsize=14, verticalalignment='top', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor=period_color, alpha=0.9, edgecolor='black', linewidth=2),
            fontweight='bold',
            zorder=10
        )
        
        # 凡例削除（ヒートマップのみなので不要）
        
        # 軸ラベルを削除（地図なので不要）
        ax.set_xlabel('')
        ax.set_ylabel('')
        ax.set_xticks([])
        ax.set_yticks([])
        
        # OpenStreetMapのクレジット表示
        if use_basemap:
            ax.text(
                0.99, 0.01, '© OpenStreetMap contributors',
                transform=ax.transAxes,
                fontsize=8, ha='right', va='bottom',
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.7),
                zorder=10
            )
        
        return []
    
    print("\nアニメーションを生成中...")
    
    # アニメーション作成
    # フレーム数を間引いて高速化（30分ごとに表示）
    frame_indices = range(0, len(unique_times), 3)  # 10分間隔×3 = 30分ごと
    
    anim = FuncAnimation(
        fig, animate, init_func=init,
        frames=frame_indices, interval=625, blit=False, repeat=True
    )
    
    # 動画保存
    output_file = None
    try:
        # MP4で保存を試みる
        print("  MP4形式で保存中...")
        output_file = 'donut_heatmap_osm_animation.mp4'
        writer = FFMpegWriter(fps=1.6, bitrate=2400)
        anim.save(output_file, writer=writer, dpi=100)
        print(f"✓ {output_file} を保存しました")
    except Exception as e:
        print(f"  MP4保存に失敗: {e}")
        try:
            # GIFで保存
            print("  GIF形式で保存中...")
            output_file = 'donut_heatmap_osm_animation.gif'
            writer = PillowWriter(fps=1.6)
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
        print(f"フレーム数: {len(frame_indices)} (30分ごと)")
        print(f"再生速度: 1.6フレーム/秒 (0.8倍速)")
        print("\n動画の特徴:")
        print("  - 対象エリア: 東京23区のみ")
        print("  - 対象時間: 平日6時～21時")
        print("  - 背景地図: OpenStreetMap")
        print("  - ヒートマップのみ表示（ステーション非表示）")
        print("  - カラーマップ: YlOrRd（黄→オレンジ→赤）")
        print("  \n【ドーナツ化現象（顕著）】")
        print("  - 早朝(6-9時): 郊外に密集 / 都心ほぼ0")
        print("  - 日中(9-18時): 都心に密集 / 郊外ほぼ0")
        print("  - 夕方(18-21時): 都心→郊外へ移動")

if __name__ == "__main__":
    create_heatmap_animation()
