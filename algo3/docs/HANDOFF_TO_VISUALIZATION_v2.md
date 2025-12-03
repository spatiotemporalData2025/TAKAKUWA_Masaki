# 可視化担当者への引き継ぎガイド 🎨

> **作成日**: 2025年12月3日  
> **クラスタリング担当より**

---

## 🎯 目的

ST-DBSCANで検出された**雨雲クラスタ**を、雨雲レーダーのように色分けして表示する。

---

## 🚀 クイックスタート（3分で開始）

### 1. データの準備

```powershell
cd C:\dev\大学\TAKAKUWA_Masaki\algo3\examples
python visualize_rain_clusters.py
```

これで `output/rain_radar_visualization/` にデータと可視化サンプルが作成されます！

### 2. データの読み込み

```python
import pandas as pd

# CSVから読み込み（推奨）
df = pd.read_csv('output/rain_radar_visualization/clustering_result.csv')

print(df.head())
# id, lat, lon, time, value, cluster, is_noise
```

### 3. 基本的な可視化

```python
import matplotlib.pyplot as plt

# 特定時刻のデータを取得
time_0 = df[df['time'] == df['time'].unique()[0]]

# クラスタを色分けして表示
clusters = time_0[time_0['cluster'] > 0]  # ノイズを除外
noise = time_0[time_0['cluster'] == 0]

plt.figure(figsize=(12, 8))

# ノイズ（灰色）
plt.scatter(noise['lon'], noise['lat'], 
           c='gray', s=20, alpha=0.3, label='ノイズ')

# クラスタ（カラフルに）
plt.scatter(clusters['lon'], clusters['lat'],
           c=clusters['cluster'], cmap='tab20',
           s=clusters['value']*30, alpha=0.7)

plt.xlabel('経度 (°E)')
plt.ylabel('緯度 (°N)')
plt.title('雨雲クラスタ')
plt.legend()
plt.colorbar(label='クラスタID')
plt.grid(True, alpha=0.3)
plt.show()
```

---

## 📊 データ形式の詳細

### CSVファイル: `clustering_result.csv`

| カラム | 型 | 説明 | 例 |
|--------|----|----|-----|
| `id` | int | ポイントの一意ID | 0, 1, 2, ... |
| `lat` | float | 緯度 (度) | 35.68 |
| `lon` | float | 経度 (度) | 139.76 |
| `time` | float | Unixタイムスタンプ (秒) | 1732464000.0 |
| `value` | float | 降水量 (mm/h) | 1.5 |
| `cluster` | int | クラスタID (0=ノイズ, 1~=クラスタ) | 1 |
| `is_noise` | bool | ノイズかどうか | False |

### JSONファイル: `clustering_result.json`

```json
{
  "metadata": {
    "n_points": 252,
    "n_clusters": 2,
    "parameters": {
      "eps1": 25.0,
      "eps2": 7200.0,
      "min_pts": 5
    }
  },
  "points": [
    {
      "id": 0,
      "lat": 35.68,
      "lon": 139.76,
      "time": 1732464000.0,
      "value": 1.5,
      "cluster": 1
    }
  ],
  "clusters": [
    {
      "cluster_id": 1,
      "n_points": 244,
      "bounds": {
        "min_lat": 34.5,
        "max_lat": 36.0,
        ...
      }
    }
  ]
}
```

### 補助ファイル

#### `cluster_colors.json` - 推奨色情報
各クラスタの推奨RGB色（0.0-1.0の範囲）

```json
{
  "0": {"r": 0.5, "g": 0.5, "b": 0.5, "a": 0.3},
  "1": {"r": 0.12, "g": 0.47, "b": 0.71, "a": 1.0},
  "2": {"r": 1.0, "g": 0.5, "b": 0.05, "a": 1.0}
}
```

#### `cluster_bounds.json` - クラスタの範囲
各クラスタの空間的・時間的範囲

```json
{
  "1": {
    "min_lat": 34.53,
    "max_lat": 35.25,
    "min_lon": 138.20,
    "max_lon": 139.50,
    "center_lat": 35.08,
    "center_lon": 138.44,
    "n_points": 244
  }
}
```

#### `clusters_by_time.json` - 時刻別データ
時刻ごとに整理されたクラスタ情報

```json
{
  "1732464000.0": {
    "1": [
      {"lat": 35.68, "lon": 139.76, "value": 1.5, "cluster": 1}
    ],
    "2": [...]
  }
}
```

---

## 🎨 可視化のアイデア

### 1. 基本的な散布図（2D）

```python
import matplotlib.pyplot as plt
import pandas as pd

df = pd.read_csv('clustering_result.csv')
time_data = df[df['time'] == df['time'].unique()[0]]

plt.figure(figsize=(12, 8))
clusters = time_data[time_data['cluster'] > 0]

# クラスタごとに色分け
scatter = plt.scatter(
    clusters['lon'], clusters['lat'],
    c=clusters['cluster'], 
    s=clusters['value'] * 50,  # 降水量でサイズ調整
    cmap='tab20',
    alpha=0.6,
    edgecolors='black',
    linewidths=0.5
)

plt.colorbar(scatter, label='クラスタID')
plt.xlabel('経度 (°E)')
plt.ylabel('緯度 (°N)')
plt.title('雨雲クラスタ分布')
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig('rain_clusters_basic.png', dpi=150)
plt.show()
```

### 2. 雨雲レーダー風（カラフル）

```python
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

df = pd.read_csv('clustering_result.csv')
time_data = df[df['time'] == df['time'].unique()[0]]

fig, ax = plt.subplots(figsize=(14, 10))
ax.set_facecolor('#1a1a2e')  # 暗い背景
fig.patch.set_facecolor('#0f0f1e')

clusters = time_data[time_data['cluster'] > 0]

# 降水量に応じた色分け
colors = []
for value in clusters['value']:
    if value < 1.0:
        colors.append('#4a90e2')  # 青（弱い雨）
    elif value < 2.0:
        colors.append('#50c878')  # 緑（中程度）
    elif value < 5.0:
        colors.append('#f5d100')  # 黄（やや強い）
    else:
        colors.append('#ff4444')  # 赤（強い雨）

ax.scatter(clusters['lon'], clusters['lat'],
          c=colors, s=clusters['value']*40,
          alpha=0.7, edgecolors='white', linewidths=0.5)

# 凡例
legend_elements = [
    mpatches.Patch(color='#4a90e2', label='弱い雨 (< 1mm/h)'),
    mpatches.Patch(color='#50c878', label='中程度 (1-2mm/h)'),
    mpatches.Patch(color='#f5d100', label='やや強い (2-5mm/h)'),
    mpatches.Patch(color='#ff4444', label='強い雨 (≥5mm/h)')
]
ax.legend(handles=legend_elements, loc='upper right')

ax.set_xlabel('経度 (°E)', color='white')
ax.set_ylabel('緯度 (°N)', color='white')
ax.set_title('雨雲レーダー', color='white', fontsize=16, fontweight='bold')
ax.tick_params(colors='white')
ax.grid(True, alpha=0.2, color='white')

plt.tight_layout()
plt.savefig('rain_radar_style.png', dpi=150, facecolor='#0f0f1e')
plt.show()
```

### 3. 時間変化アニメーション

```python
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import pandas as pd

df = pd.read_csv('clustering_result.csv')
unique_times = sorted(df['time'].unique())

fig, ax = plt.subplots(figsize=(12, 8))

def update(frame):
    ax.clear()
    time_data = df[df['time'] == unique_times[frame]]
    clusters = time_data[time_data['cluster'] > 0]
    
    ax.scatter(clusters['lon'], clusters['lat'],
              c=clusters['cluster'], s=clusters['value']*30,
              cmap='tab20', alpha=0.6)
    
    ax.set_xlabel('経度 (°E)')
    ax.set_ylabel('緯度 (°N)')
    ax.set_title(f'雨雲の時間変化 - フレーム {frame+1}/{len(unique_times)}')
    ax.grid(True, alpha=0.3)

anim = FuncAnimation(fig, update, frames=len(unique_times), 
                    interval=500, repeat=True)

writer = PillowWriter(fps=2)
anim.save('rain_animation.gif', writer=writer, dpi=100)
plt.close()
```

### 4. クラスタごとの詳細表示

```python
import matplotlib.pyplot as plt

df = pd.read_csv('clustering_result.csv')
time_data = df[df['time'] == df['time'].unique()[0]]
clusters = time_data[time_data['cluster'] > 0]

# クラスタIDのユニークリスト
cluster_ids = clusters['cluster'].unique()

fig, axes = plt.subplots(1, len(cluster_ids), 
                        figsize=(6*len(cluster_ids), 5))

if len(cluster_ids) == 1:
    axes = [axes]

for ax, cluster_id in zip(axes, cluster_ids):
    cluster_data = clusters[clusters['cluster'] == cluster_id]
    
    ax.scatter(cluster_data['lon'], cluster_data['lat'],
              s=cluster_data['value']*50, c='blue', alpha=0.6)
    
    ax.set_title(f'クラスタ {int(cluster_id)}\n({len(cluster_data)} ポイント)')
    ax.set_xlabel('経度 (°E)')
    ax.set_ylabel('緯度 (°N)')
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('clusters_detailed.png', dpi=150)
plt.show()
```

---

## 🔧 便利な処理関数

### 時刻の変換

```python
from datetime import datetime

# Unixタイムスタンプ → 日時文字列
timestamp = 1732464000.0
dt = datetime.fromtimestamp(timestamp)
time_str = dt.strftime('%Y年%m月%d日 %H:%M')
print(time_str)  # 2025年11月24日 23:00
```

### クラスタの統計情報

```python
import pandas as pd

df = pd.read_csv('clustering_result.csv')
clusters = df[df['cluster'] > 0]

for cluster_id in clusters['cluster'].unique():
    cluster_data = clusters[clusters['cluster'] == cluster_id]
    
    print(f"\nクラスタ {int(cluster_id)}:")
    print(f"  ポイント数: {len(cluster_data)}")
    print(f"  中心位置: ({cluster_data['lat'].mean():.2f}, {cluster_data['lon'].mean():.2f})")
    print(f"  平均降水量: {cluster_data['value'].mean():.2f} mm/h")
    print(f"  最大降水量: {cluster_data['value'].max():.2f} mm/h")
```

### 時刻ごとのフィルタリング

```python
import pandas as pd

df = pd.read_csv('clustering_result.csv')

# 全ての時刻を取得
unique_times = sorted(df['time'].unique())

# 各時刻のデータを処理
for time_value in unique_times:
    time_data = df[df['time'] == time_value]
    n_clusters = len(time_data[time_data['cluster'] > 0]['cluster'].unique())
    
    print(f"時刻 {time_value}: {n_clusters} クラスタ, {len(time_data)} ポイント")
```

---

## 📦 必要なライブラリ

```bash
pip install pandas matplotlib pillow numpy
```

または

```bash
pip install -r requirements.txt
```

---

## 🎯 推奨される可視化フロー

1. **データの読み込み** → `clustering_result.csv`
2. **時刻の選択** → 特定時刻またはアニメーション
3. **データのフィルタリング** → ノイズ除去、クラスタ選択
4. **色の設定** → 降水量やクラスタIDで色分け
5. **サイズの設定** → 降水量でマーカーサイズ調整
6. **プロット** → matplotlibで描画
7. **保存** → PNG, GIF, MP4など

---

## 💡 可視化のヒント

### レーダー風の演出
- 背景を暗くする（`#1a1a2e`など）
- 降水量で色を変える（青→緑→黄→赤）
- マーカーサイズを降水量に比例させる
- 透明度で重なりを表現

### クラスタの強調
- クラスタごとに異なる色
- クラスタの中心に番号を表示
- 境界線やエリアを描画

### 時間変化の表現
- GIFアニメーション
- MP4動画
- スライダー付きインタラクティブプロット

---

## 🐛 トラブルシューティング

### Q: 日本語が文字化けする
```python
from font_config import setup_japanese_font
setup_japanese_font()
```

### Q: データが見つからない
```python
# パスを確認
import os
print(os.path.exists('clustering_result.csv'))

# 正しいパスを指定
df = pd.read_csv('output/rain_radar_visualization/clustering_result.csv')
```

### Q: クラスタが多すぎて色が足りない
```python
# カスタムカラーマップを使用
import matplotlib.cm as cm
colors = cm.get_cmap('hsv', n_clusters)
```

---

## 📞 質問・相談

- クラスタリング担当者に連絡
- `docs/HANDOFF_TO_VISUALIZATION.md` を参照
- サンプルコード: `examples/visualize_rain_clusters.py`

---

## ✅ チェックリスト

可視化開始前に確認：

- [ ] データファイルが存在する（`clustering_result.csv`）
- [ ] 必要なライブラリがインストール済み
- [ ] サンプルコードが実行できる
- [ ] データの構造を理解した
- [ ] 可視化の方針が決まった

---

**引き継ぎ完了！頑張ってください！🎨✨**

作成者: クラスタリング担当  
最終更新: 2025年12月3日
