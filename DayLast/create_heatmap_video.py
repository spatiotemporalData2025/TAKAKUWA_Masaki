import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib
from matplotlib.colors import LinearSegmentedColormap
from scipy.interpolate import griddata
from datetime import datetime, timedelta
import contextily as ctx

matplotlib.rcParams['font.sans-serif'] = ['MS Gothic', 'Yu Gothic', 'Meiryo']
matplotlib.rcParams['axes.unicode_minus'] = False

print("=" * 60)
print("東京23区シェアサイクル時系列ヒートマップ動画生成")
print("=" * 60)

# データ読み込み
print("\nデータを読み込み中...")
df = pd.read_csv('bike_log_tokyo.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
df['date'] = df['timestamp'].dt.date

# 昨日の日付を取得
yesterday = (datetime.now() - timedelta(days=1)).date()

# 昨日のデータのみをフィルタリング
df = df[df['date'] == yesterday]
if len(df) == 0:
    print(f"エラー: {yesterday}のデータがありません")
    print("データを収集してから実行してください")
    exit(1)

print(f"{yesterday}のデータを使用")

# 時間範囲でフィルタリング（朝6時～夜21時：通勤パターンが見やすい時間帯）
df = df[(df['hour'] >= 6) & (df['hour'] <= 21)]
print(f"フィルタ後: 6:00～21:00のデータのみを使用")

# タイムスタンプでソート
df = df.sort_values('timestamp')

# ユニークなタイムスタンプを取得
unique_times = sorted(df['timestamp'].unique())
print(f"タイムスタンプ数: {len(unique_times)}個")

if len(unique_times) == 0:
    print("エラー: 指定された時間範囲にデータがありません")
    exit(1)

print(f"期間: {unique_times[0]} ～ {unique_times[-1]}")

# ステーション数確認
num_stations = df['station_name'].nunique()
print(f"ステーション数: {num_stations}箇所")

if len(unique_times) < 2:
    print(f"\n警告: タイムスタンプが{len(unique_times)}個しかないため、動画生成には不十分です")
    print("データを少なくとも数時間分蓄積してから実行してください")
    exit(1)

# 緯度経度の範囲を取得（余裕を持たせる）
lat_min, lat_max = df['lat'].min(), df['lat'].max()
lon_min, lon_max = df['lon'].min(), df['lon'].max()

# 範囲を広げる（地図表示のため - 東京23区全体が見えるように）
lat_margin = (lat_max - lat_min) * 0.15 if (lat_max - lat_min) > 0 else 0.02
lon_margin = (lon_max - lon_min) * 0.15 if (lon_max - lon_min) > 0 else 0.02
lat_min -= lat_margin
lat_max += lat_margin
lon_min -= lon_margin
lon_max += lon_margin

print(f"地図範囲: 緯度 {lat_min:.4f}～{lat_max:.4f}, 経度 {lon_min:.4f}～{lon_max:.4f}")

# Web Mercator座標系に変換
def lat_lon_to_mercator(lat, lon):
    from math import radians, log, tan, pi
    x = radians(lon) * 6378137
    y = 6378137 * log(tan(pi/4 + radians(lat)/2))
    return x, y

# 座標範囲をMercatorに変換
x_min, y_min = lat_lon_to_mercator(lat_min, lon_min)
x_max, y_max = lat_lon_to_mercator(lat_max, lon_max)

# グリッド作成（東京23区全体）
grid_resolution = 60
x_grid = np.linspace(x_min, x_max, grid_resolution)
y_grid = np.linspace(y_min, y_max, grid_resolution)
x_mesh, y_mesh = np.meshgrid(x_grid, y_grid)

# カスタムカラーマップ（台数が多いほど赤く）
colors = ['#1a9850', '#91cf60', '#d9ef8b', '#fee08b', '#fc8d59', '#d73027']
n_bins = 100
cmap = LinearSegmentedColormap.from_list('bike_cmap', colors, N=n_bins)

# アニメーション設定
fig, ax = plt.subplots(figsize=(14, 10))
plt.subplots_adjust(left=0.08, right=0.92, top=0.93, bottom=0.08)

# 最大値を取得
max_bikes = df['free_bikes'].max()

# 地図タイルを先に読み込み（1回のみ）
print("\n地図タイルを読み込み中...")
try:
    # 先に地図を描画
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_aspect('equal')
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, 
                   crs='EPSG:3857', alpha=0.5, zoom=10, attribution=None)
    map_loaded = True
    print("✓ 地図タイルの読み込み完了")
except Exception as e:
    map_loaded = False
    print(f"⚠ 地図タイル読み込みエラー: {e}")
    print("地図なしで続行します...")

# 初期化関数
def init():
    return []

# 更新関数
def update(frame):
    # ヒートマップとステーションのみをクリア（地図は残す）
    for artist in ax.collections + ax.images[1:] + ax.texts:
        artist.remove()
    
    # 現在のデータ取得
    current_time = unique_times[frame]
    current_data = df[df['timestamp'] == current_time]
    
    lons = current_data['lon'].values
    lats = current_data['lat'].values
    bikes = current_data['free_bikes'].values
    names = current_data['station_name'].values
    ward_types = current_data['ward_type'].values if 'ward_type' in current_data.columns else None
    
    # Mercator座標に変換
    x_points = []
    y_points = []
    for lat, lon in zip(lats, lons):
        x, y = lat_lon_to_mercator(lat, lon)
        x_points.append(x)
        y_points.append(y)
    
    x_points = np.array(x_points)
    y_points = np.array(y_points)
    
    # 補間ヒートマップ
    try:
        grid_bikes = griddata((x_points, y_points), bikes, (x_mesh, y_mesh), 
                             method='linear', fill_value=0)
        grid_bikes = np.clip(grid_bikes, 0, max_bikes)
    except:
        grid_bikes = griddata((x_points, y_points), bikes, (x_mesh, y_mesh), 
                             method='nearest', fill_value=0)
    
    # ヒートマップ描画（軽量化）
    im = ax.imshow(grid_bikes, extent=[x_min, x_max, y_min, y_max],
                   origin='lower', cmap=cmap, alpha=0.6, vmin=0, vmax=max_bikes,
                   interpolation='nearest')
    
    # ステーション点描画（サイズを小さく、100個対応）
    scatter = ax.scatter(x_points, y_points, c=bikes, cmap=cmap, s=80, 
                        edgecolors='black', linewidth=1, 
                        vmin=0, vmax=max_bikes, zorder=5, alpha=0.8)
    
    # 在庫が非常に少ない or 非常に多い箇所のみラベル表示（最大10個まで）
    extreme_indices = np.where((bikes <= 3) | (bikes >= 27))[0]
    if len(extreme_indices) > 0 and len(extreme_indices) <= 10:
        for idx in extreme_indices:
            x, y, name, bike = x_points[idx], y_points[idx], names[idx], bikes[idx]
            ward_name = name.split('_')[0]
            ax.text(x, y + (y_max - y_min) * 0.008, f'{ward_name}\n{bike:.0f}台', 
                   fontsize=7, ha='center', va='bottom',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.7, 
                            edgecolor='red' if bike <= 3 else 'blue'),
                   zorder=6)
    
    # タイトル
    time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    ax.set_title(f'東京23区シェアサイクル在庫ヒートマップ (6:00-21:00)\n{time_str} (フレーム {frame+1}/{len(unique_times)})',
                 fontsize=14, fontweight='bold', pad=20)
    
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.grid(False)
    
    # カラーバー
    if frame == 0:
        cbar = plt.colorbar(im, ax=ax, label='利用可能台数', pad=0.03, fraction=0.046)
        cbar.ax.tick_params(labelsize=10)
    
    # 統計情報（Office/Residentialエリア別）
    avg_bikes = bikes.mean()
    min_bikes = bikes.min()
    max_bikes_current = bikes.max()
    
    if ward_types is not None:
        office_mask = ward_types == 'Office'
        residential_mask = ward_types == 'Residential'
        
        office_avg = bikes[office_mask].mean() if office_mask.any() else 0
        residential_avg = bikes[residential_mask].mean() if residential_mask.any() else 0
        
        stats_text = f'全体平均: {avg_bikes:.1f}台\nOffice: {office_avg:.1f}台\nResidential: {residential_avg:.1f}台\n最小: {min_bikes:.0f}台 / 最大: {max_bikes_current:.0f}台'
    else:
        stats_text = f'平均: {avg_bikes:.1f}台\n最小: {min_bikes:.0f}台\n最大: {max_bikes_current:.0f}台'
    
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
            fontsize=9, verticalalignment='top', horizontalalignment='left',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor='gray', linewidth=1))
    
    # プログレス表示
    if (frame + 1) % max(1, len(unique_times) // 10) == 0:
        progress = (frame + 1) / len(unique_times) * 100
        print(f"進行状況: {progress:.1f}% ({frame+1}/{len(unique_times)})")
    
    return [im, scatter]

# アニメーション作成
print("\n動画を生成中...")
print(f"生成するフレーム数: {len(unique_times)}個")

anim = animation.FuncAnimation(fig, update, init_func=init,
                              frames=len(unique_times),
                              interval=200,
                              blit=False,
                              repeat=True)

# 動画保存（MP4形式）
output_file = 'bike_heatmap_tokyo_animation.mp4'
print(f"\n動画を保存中: {output_file}")
print("※ 東京23区全体・100ステーション対応のため、生成に時間がかかります...")

try:
    # ffmpegのパスを直接指定
    import os
    ffmpeg_path = r'C:\ProgramData\chocolatey\lib\ffmpeg\tools\ffmpeg\bin'
    if os.path.exists(ffmpeg_path):
        os.environ['PATH'] = ffmpeg_path + ';' + os.environ.get('PATH', '')
    
    # MP4として保存
    Writer = animation.writers['ffmpeg']
    writer = Writer(fps=6, metadata=dict(artist='Tokyo Bike Analysis'), bitrate=3000, codec='libx264')
    anim.save(output_file, writer=writer, dpi=100)
    print(f"\n✓ MP4動画の保存が完了しました: {output_file}")
    
    # ファイルサイズを表示
    file_size = os.path.getsize(output_file) / (1024 * 1024)
    print(f"ファイルサイズ: {file_size:.2f} MB")
    
except Exception as e:
    print(f"\n⚠ MP4形式での保存に失敗しました: {e}")
    print("ffmpegが正しくインストールされていることを確認してください。")

print("\n" + "=" * 60)
print("処理完了！")
print("=" * 60)
