# 可視化担当者向けドキュメント

## 👋 はじめに

このドキュメントは、ST-DBSCANクラスタリング結果を受け取って可視化を行う担当者向けのガイドです。

## 📁 提供されるデータ

クラスタリング実行後、`visualization_data/` フォルダに以下のファイルが生成されます：

### 1. `clustering_result.csv`
全ポイントの情報が含まれるCSVファイル

| カラム名 | 説明 | 値の範囲 |
|---------|------|---------|
| `id` | ポイントID | 0から始まる整数 |
| `lat` | 緯度 | 実数（例：35.0-38.0） |
| `lon` | 経度 | 実数（例：139.0-142.0） |
| `time` | 時刻 | 0から始まる整数（タイムステップ） |
| `value` | 降水量 | 実数（mm/h） |
| `cluster` | クラスタID | 0=ノイズ, 1~=クラスタ番号 |
| `is_noise` | ノイズかどうか | True/False |

### 2. `clustering_result.json`
全データとメタ情報を含むJSON形式

```json
{
  "metadata": {
    "n_points": 1500,
    "n_clusters": 30,
    "parameters": {
      "eps1": 0.15,
      "eps2": 2.0,
      "min_pts": 10
    }
  },
  "points": [...],
  "clusters": [...]
}
```

### 3. `cluster_colors.json`
各クラスタの推奨RGB色

```json
{
  "0": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 0.3},
  "1": {"r": 0.12, "g": 0.47, "b": 0.71, "a": 1.0},
  ...
}
```

### 4. `cluster_bounds.json`
各クラスタの空間的・時間的範囲

```json
{
  "1": {
    "min_lat": 34.5,
    "max_lat": 35.2,
    "min_lon": 138.8,
    "max_lon": 139.5,
    "min_time": 0,
    "max_time": 3,
    "center_lat": 34.85,
    "center_lon": 139.15,
    "n_points": 50
  },
  ...
}
```

### 5. `clusters_by_time.json`
時刻ごとに整理されたクラスタ情報

```json
{
  "0": {
    "1": [
      {"lat": 35.0, "lon": 139.0, "value": 5.0, "cluster": 1},
      ...
    ],
    ...
  },
  ...
}
```

## 🚀 クイックスタート

### ステップ0: 日本語フォント設定（重要！）

図の日本語が文字化けする場合は、スクリプトの先頭に以下を追加してください：

```python
from font_config import setup_japanese_font
setup_japanese_font()
```

これで日本語が正しく表示されます。

### ステップ1: データの読み込み

```python
import pandas as pd

# CSVから読み込み
df = pd.read_csv('visualization_data/clustering_result.csv')

# 基本情報を確認
print(df.head())
print(df.info())
```

### ステップ2: 特定時刻のデータを取得

```python
# 時刻0のデータを取得
time_0 = df[df['time'] == 0]

# ノイズを除外
clusters_only = time_0[time_0['cluster'] > 0]

print(f"Time 0: {len(clusters_only)} points in clusters")
```

### ステップ3: 基本的な可視化

```python
import matplotlib.pyplot as plt
from font_config import setup_japanese_font

# 日本語表示を有効化
setup_japanese_font()

# ノイズとクラスタを別々に描画
noise = time_0[time_0['cluster'] == 0]
clusters = time_0[time_0['cluster'] > 0]

plt.figure(figsize=(12, 10))

# ノイズは灰色
plt.scatter(noise['lon'], noise['lat'], 
           c='gray', s=20, alpha=0.3, label='Noise')

# クラスタは色分け、降水量でサイズ変更
scatter = plt.scatter(clusters['lon'], clusters['lat'],
                     c=clusters['cluster'], cmap='tab20',
                     s=clusters['value'] * 15, alpha=0.7)

plt.colorbar(scatter, label='Cluster ID')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Rain Clusters at Time 0')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

## 📊 サンプルスクリプトの使用

すぐに使えるサンプルスクリプトを用意しています：

```powershell
python visualization_sample.py
```

このスクリプトは以下を実行します：
1. データの読み込み
2. 統計情報の表示
3. 複数時刻の可視化
4. 雨雲レーダー風アニメーションの作成

## 🎨 可視化のアイデア

### 1. 静的な可視化
- **時刻別スナップショット**: 各時刻のクラスタを個別に表示
- **ヒートマップ**: 降水量の分布を色で表現
- **クラスタサイズの比較**: 各クラスタのポイント数を棒グラフで

### 2. 動的な可視化
- **アニメーション**: 時間経過に伴うクラスタの動き
- **トレイル表示**: 雨雲の軌跡を残す
- **フェードアウト**: 過去の時刻を徐々に薄くする

### 3. 3D可視化
- **時空間3Dプロット**: X=経度, Y=緯度, Z=時刻
- **高度を考慮**: 降水量を高さで表現

### 4. インタラクティブな可視化
- **Plotly**: ズーム、パン、ホバー情報
- **Bokeh**: スライダーで時刻を選択
- **Folium**: 実際の地図上に重ねる

## 💡 実装のヒント

### クラスタの輪郭を描く

```python
from scipy.spatial import ConvexHull

for cluster_id in clusters['cluster'].unique():
    cluster_points = clusters[clusters['cluster'] == cluster_id]
    points = cluster_points[['lon', 'lat']].values
    
    if len(points) > 2:
        try:
            hull = ConvexHull(points)
            for simplex in hull.simplices:
                plt.plot(points[simplex, 0], points[simplex, 1], 
                        'k-', alpha=0.5, linewidth=2)
        except:
            pass
```

### 推奨色の使用

```python
import json

with open('visualization_data/cluster_colors.json', 'r') as f:
    colors = json.load(f)

# クラスタIDごとに色を取得
for cluster_id in clusters['cluster'].unique():
    color_info = colors[str(cluster_id)]
    rgba = (color_info['r'], color_info['g'], 
            color_info['b'], color_info['a'])
    # この色を使って描画
```

### 時系列アニメーション

```python
from matplotlib.animation import FuncAnimation

fig, ax = plt.subplots()
unique_times = sorted(df['time'].unique())

def update(frame):
    ax.clear()
    current_time = unique_times[frame]
    time_data = df[df['time'] == current_time]
    
    clusters = time_data[time_data['cluster'] > 0]
    ax.scatter(clusters['lon'], clusters['lat'],
              c=clusters['cluster'], cmap='tab20',
              s=clusters['value'] * 15, alpha=0.7)
    
    ax.set_title(f'Time: {current_time}')

anim = FuncAnimation(fig, update, frames=len(unique_times),
                    interval=500, repeat=True)
anim.save('rain_animation.gif', writer='pillow')
```

## 🗺️ 実際の地図上に表示

### Foliumを使用

```python
import folium
from folium import plugins

# 地図の中心を計算
center_lat = df['lat'].mean()
center_lon = df['lon'].mean()

# 地図を作成
m = folium.Map(location=[center_lat, center_lon], zoom_start=10)

# 時刻0のクラスタを追加
time_0 = df[df['time'] == 0]
clusters = time_0[time_0['cluster'] > 0]

for _, row in clusters.iterrows():
    folium.CircleMarker(
        location=[row['lat'], row['lon']],
        radius=row['value'],
        color=f"#{row['cluster']:02x}0000",
        fill=True,
        fillOpacity=0.6
    ).add_to(m)

m.save('rain_map.html')
```

### Plotlyを使用（インタラクティブ）

```python
import plotly.express as px

fig = px.scatter_mapbox(
    df[df['time'] == 0],
    lat='lat',
    lon='lon',
    color='cluster',
    size='value',
    hover_data=['cluster', 'value'],
    mapbox_style='open-street-map',
    zoom=8
)
fig.show()
```

## 🔧 トラブルシューティング

### Q: データファイルが見つからない
**A**: まず `test_clustering.py` を実行してデータを生成してください。

### Q: アニメーションが保存できない
**A**: `pillow` をインストールしてください：
```powershell
pip install pillow
```

### Q: 地図表示ができない
**A**: `folium` または `plotly` をインストールしてください：
```powershell
pip install folium plotly
```

### Q: 日本語が文字化けする
**A**: スクリプトの先頭に以下を追加してください：
```python
from font_config import setup_japanese_font
setup_japanese_font()
```

利用可能なフォントを確認：
```powershell
python font_config.py
```

### Q: クラスタの色が見づらい
**A**: `cluster_colors.json` を編集して独自の色を設定できます。

## 📞 質問・相談

実装上の質問や、追加のデータが必要な場合は、クラスタリング担当者に連絡してください。

### 提供可能な追加データ：
- 特定のパラメータでの再クラスタリング
- 異なる時間範囲のデータ
- クラスタの統計情報の詳細

## 📚 参考リンク

- **Matplotlib**: https://matplotlib.org/
- **Pandas**: https://pandas.pydata.org/
- **Plotly**: https://plotly.com/python/
- **Folium**: https://python-visualization.github.io/folium/

---

**Happy Visualizing! 🎨🌧️**
