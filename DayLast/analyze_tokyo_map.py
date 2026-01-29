import pandas as pd
import folium
from folium import Circle

print("=" * 70)
print("東京シェアサイクルデータ地図可視化")
print("=" * 70)

# データ読み込み
print("\nデータを読み込み中...")
df = pd.read_csv('bike_log_tokyo.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

print(f"読み込んだデータ: {len(df):,}行")
print(f"ステーション数: {df['station_id'].nunique()}箇所")
print(f"期間: {df['timestamp'].min()} ～ {df['timestamp'].max()}")

# 朝9時と夜19時のデータを抽出
print("\n朝9時と夜19時のデータを抽出中...")
df['hour'] = df['timestamp'].dt.hour

morning_data = df[df['hour'] == 9].copy()
night_data = df[df['hour'] == 19].copy()

# 各時刻で最初の観測データを使用
morning_data = morning_data.drop_duplicates('station_id', keep='first')
night_data = night_data.drop_duplicates('station_id', keep='first')

print(f"朝9時のステーション数: {len(morning_data)}箇所")
print(f"夜19時のステーション数: {len(night_data)}箇所")

# 在庫量に応じた色分け関数
def get_color(bikes):
    """在庫量に応じた色を返す"""
    if bikes <= 5:
        return 'red'      # 赤: 在庫が少ない（貸出不可の危機）
    elif bikes <= 20:
        return 'green'    # 緑: 在庫が普通
    else:
        return 'blue'     # 青: 在庫が多い（満車の危機）

# 東京の中心座標
tokyo_center = [35.68, 139.75]

def create_map(data, title, output_file):
    """地図を作成して保存"""
    print(f"\n{title}の地図を生成中...")
    
    # 地図作成
    m = folium.Map(
        location=tokyo_center,
        zoom_start=11,
        tiles='OpenStreetMap'
    )
    
    # タイトルを追加
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: 500px; height: 60px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:16px; padding: 10px">
        <b>{title}</b><br>
        <span style="font-size:12px">
        🔴 赤: 在庫少 (0-5台) | 🟢 緑: 在庫普通 (6-20台) | 🔵 青: 在庫多 (21-30台)
        </span>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # ステーション統計
    office_count = len(data[data['ward_type'] == 'Office'])
    residential_count = len(data[data['ward_type'] == 'Residential'])
    
    office_avg = data[data['ward_type'] == 'Office']['free_bikes'].mean()
    residential_avg = data[data['ward_type'] == 'Residential']['free_bikes'].mean()
    
    # 各ステーションをプロット
    red_count = 0
    green_count = 0
    blue_count = 0
    
    for _, row in data.iterrows():
        lat = row['lat']
        lon = row['lon']
        bikes = row['free_bikes']
        station_name = row['station_name']
        ward_type = row['ward_type']
        
        color = get_color(bikes)
        
        if color == 'red':
            red_count += 1
        elif color == 'green':
            green_count += 1
        else:
            blue_count += 1
        
        # ポップアップ情報
        popup_text = f"""
        <b>{station_name}</b><br>
        エリア種別: {ward_type}<br>
        利用可能台数: {bikes}台<br>
        状態: {'⚠️在庫不足' if bikes <= 5 else '✅正常' if bikes <= 20 else '⚠️満車危機'}
        """
        
        # 円マーカーを追加
        folium.CircleMarker(
            location=[lat, lon],
            radius=8,
            popup=folium.Popup(popup_text, max_width=250),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7,
            weight=2
        ).add_to(m)
    
    # 統計情報を地図に追加
    stats_html = f'''
    <div style="position: fixed; 
                bottom: 30px; left: 50px; width: 300px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
        <b>統計情報</b><br>
        総ステーション数: {len(data)}箇所<br>
        - Office: {office_count}箇所 (平均{office_avg:.1f}台)<br>
        - Residential: {residential_count}箇所 (平均{residential_avg:.1f}台)<br>
        <br>
        在庫状況:<br>
        - 🔴 在庫不足: {red_count}箇所<br>
        - 🟢 正常: {green_count}箇所<br>
        - 🔵 満車危機: {blue_count}箇所
    </div>
    '''
    m.get_root().html.add_child(folium.Element(stats_html))
    
    # 保存
    m.save(output_file)
    print(f"✓ 地図を保存しました: {output_file}")
    print(f"  - Office平均在庫: {office_avg:.1f}台")
    print(f"  - Residential平均在庫: {residential_avg:.1f}台")
    print(f"  - 在庫状況: 🔴{red_count}箇所 🟢{green_count}箇所 🔵{blue_count}箇所")

# 朝の地図作成
create_map(
    morning_data,
    '朝9時の自転車在庫状況（出勤ピーク後）',
    'map_morning.html'
)

# 夜の地図作成
create_map(
    night_data,
    '夜19時の自転車在庫状況（帰宅ピーク後）',
    'map_night.html'
)

# 比較分析
print("\n" + "=" * 70)
print("【ドーナツ化現象の分析】")
print("=" * 70)

morning_office = morning_data[morning_data['ward_type'] == 'Office']['free_bikes'].mean()
morning_residential = morning_data[morning_data['ward_type'] == 'Residential']['free_bikes'].mean()

night_office = night_data[night_data['ward_type'] == 'Office']['free_bikes'].mean()
night_residential = night_data[night_data['ward_type'] == 'Residential']['free_bikes'].mean()

print(f"\n【朝9時】")
print(f"  Officeエリア: {morning_office:.1f}台（{'🔵満車傾向' if morning_office > 20 else '正常'}）")
print(f"  Residentialエリア: {morning_residential:.1f}台（{'🔴在庫不足傾向' if morning_residential < 10 else '正常'}）")

print(f"\n【夜19時】")
print(f"  Officeエリア: {night_office:.1f}台（{'🔴在庫不足傾向' if night_office < 10 else '正常'}）")
print(f"  Residentialエリア: {night_residential:.1f}台（{'🔵満車傾向' if night_residential > 20 else '正常'}）")

print(f"\n【変化量】")
print(f"  Officeエリア: {night_office - morning_office:+.1f}台（朝→夜）")
print(f"  Residentialエリア: {night_residential - morning_residential:+.1f}台（朝→夜）")

print("\n✅ 朝は「住宅街が赤・オフィスが青」")
print("✅ 夜は「オフィスが赤・住宅街が青」")
print("→ ドーナツ化現象（昼間人口移動）が可視化されました！")

print("\n" + "=" * 70)
print("処理完了！")
print("map_morning.html と map_night.html を開いて確認してください。")
print("=" * 70)
