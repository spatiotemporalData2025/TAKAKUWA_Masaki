# ST-DBSCAN実装: algo3プロジェクト

> **最新の更新**: 🎨 **可視化機能完成！** 雨雲レーダー風の可視化 + 可視化担当者への引き継ぎ完了（2025/12/03）

<br>

---

<br>

## 📋 プロジェクト概要

地点別の気象データからST-DBSCANを使って時空間クラスタリングし、過去の雲の流れがクラスタとして現れるかを確認するプロジェクトです。

<br>

### 👥 役割分担

1. **データ取得する人** - 気象データの収集 ✅ **完了！**
2. **ST-DBSCANを実装して降水地点のクラスタリングをする人** ✅ **完了！** 
3. **クラスタリング結果から可視化する人** 🎨 **サンプル実装完了！引き継ぎ準備OK！**
4. **効果測定する人** - 実行時間測定、検証
5. **スライド作る人** - プレゼンテーション

<br>

### 🎉 実装完了機能

#### 1. 実データ対応
**データ取得担当者が実装した `weather_data.py` と統合完了！**

- ✅ Open-Meteo APIから東京周辺の実際の気象データを取得
- ✅ 5kmごと、1時間ごとの高解像度データ
- ✅ 降雨量・雲量などのメトリクスに対応
- ✅ `fetch_tokyo_data()` 関数でSTPointとして直接取得可能

#### 2. 雨雲レーダー風可視化 🆕
**クラスタリング結果を雨雲レーダーのように表示！**

- ✅ 降水量に応じた色分け（青→緑→黄→赤）
- ✅ クラスタごとの識別表示
- ✅ 時間変化アニメーション（GIF）
- ✅ 可視化担当者向けの完全なデータエクスポート

<br>

---

<br>

## 📁 プロジェクト構造

```
algo3/
├── README.md                          # このファイル
├── requirements.txt                   # 必要なパッケージ
│
├── st_dbscan.py                      # ST-DBSCANアルゴリズム実装
├── weather_data.py                   # 🆕 気象データ取得（データ担当者作成）
├── export_utils.py                   # データエクスポート機能
├── font_config.py                    # 日本語フォント設定
│
├── docs/                             # ドキュメント
│   ├── README_STDBSCAN.md
│   ├── README_FOR_VISUALIZATION_TEAM.md
│   ├── HANDOFF_TO_VISUALIZATION.md
│   └── FONT_FIX_SUMMARY.md
│
├── data/                             # 🆕 気象データキャッシュ
│   └── weather_2025-11-24_*.json     # Open-Meteo APIデータ
│
├── examples/                          # サンプルスクリプト
│   ├── test_clustering.py
│   ├── visualization_sample.py
│   ├── weather_clustering.py          # 🆕 実データクラスタリング
│   └── weather_clustering_quickstart.py  # 🆕 クイックスタート
│
└── output/                            # 出力ファイル
    ├── *.png                          # 可視化画像
    ├── *.gif                          # アニメーション
    ├── visualization_data/            # エクスポートデータ
    │   ├── clustering_result.csv
    │   ├── clustering_result.json
    │   ├── cluster_colors.json
    │   ├── cluster_bounds.json
    │   └── clusters_by_time.json
    └── weather_clustering/            # 🆕 実データ結果
        └── (上記と同じ構造)
```

<br>

---

<br>

## 🚀 クイックスタート

<br>

### 🎯 最速で雨雲レーダー風可視化（推奨！）

```powershell
# 1. パッケージのインストール
pip install -r requirements.txt

# 2. examples フォルダに移動
cd examples

# 3. 可視化実行！
python visualize_rain_clusters.py
```

**これだけで、実データから雨雲クラスタを検出・可視化できます！**

**実行結果:**
- 🖼️ 雨雲レーダー画像（PNG）
- 🎬 時間変化アニメーション（GIF）
- 📊 可視化用データ（CSV, JSON）

出力先: `output/rain_radar_visualization/`

<br>

### 📚 その他の実行オプション

#### クラスタリングのみ（軽量）
```powershell
# 超軽量版（6時間分、252ポイント、約1秒）
python weather_clustering_lite.py
```

#### 可視化担当者向けデータ準備
```powershell
# 可視化用データのみエクスポート
python visualize_rain_clusters.py
# → output/rain_radar_visualization/ にデータ作成
```

<br>

### 📚 その他のテストスクリプト

```powershell
# 🎨 雨雲レーダー風可視化（推奨！）
python visualize_rain_clusters.py
# → 画像 + アニメーション + データエクスポート

# 超軽量版（6時間分、252ポイント、約1秒）- 動作確認に最適！
python weather_clustering_lite.py

# 最適化版（24時間分、7,467ポイント）- 処理時間：中程度
python weather_clustering_optimized.py

# 完全版（全期間、12,313ポイント）- 詳細な統計とエクスポート付き
python weather_clustering.py

# クイックスタート版（全データ）- シンプルな実装例
python weather_clustering_quickstart.py

# サンプルデータでのテスト
python test_clustering.py

# 可視化のサンプル
python visualization_sample.py
```

**💡 推奨フロー:**
1. `visualize_rain_clusters.py` で可視化 🎨
2. `weather_clustering_lite.py` でパラメータ調整
3. 可視化担当者にデータを引き継ぎ

<br>

---

<br>

## 🌧️ 実データクラスタリングの使い方

<br>

### 基本的な使い方

```python
from st_dbscan import STDBSCAN
from weather_data import fetch_tokyo_data

# 1. 気象データを取得（Open-Meteo APIから）
weather_points = fetch_tokyo_data(cache_dir='./data')
print(f"取得: {len(weather_points)} 個の降水ポイント")

# 2. ST-DBSCANでクラスタリング
stdbscan = STDBSCAN(eps1=15.0, eps2=3600.0, min_pts=5)
stdbscan.fit(weather_points)

# 3. 結果を取得
stats = stdbscan.get_statistics()
print(f"検出されたクラスタ数: {stats['n_clusters']}")
```

<br>

### データ取得のカスタマイズ

```python
from weather_data import fetch_weather_points

# カスタム範囲・期間でデータ取得
points = fetch_weather_points(
    lat_min=34.0,           # 緯度範囲
    lat_max=36.5,
    lon_min=137.5,          # 経度範囲  
    lon_max=140.5,
    start_date='2025-11-20', # 期間
    end_date='2025-11-30',
    precipitation_threshold=0.5,  # 降水閾値 (mm/h)
    cache_dir='./data'
)
```

<br>

### データの特徴

- **空間解像度**: 約5km間隔のグリッド
- **時間解像度**: 1時間ごと
- **対象地域**: 東京周辺（デフォルト: 緯度34.5-36.0、経度138.0-140.0）
- **期間**: 2025年11月24-29日（デフォルト）
- **データソース**: Open-Meteo API（日本気象庁MSMモデル）

<br>

---

<br>

## 📊 出力ファイル

<br>

### `output/` フォルダ

実行結果が全て `output/` に保存されます：

<br>

#### 画像ファイル
- `clustering_result_2d.png` - 2D可視化
- `clustering_result_3d.png` - 3D可視化
- `visualization_timestep_0.png` - 時刻0の詳細
- `visualization_timestep_5.png` - 時刻5の詳細

<br>

#### アニメーション
- `rain_animation.gif` - 基本アニメーション
- `rain_radar_visualization.gif` - レーダー風アニメーション

<br>

#### データファイル（`output/visualization_data/`）
- `clustering_result.csv` - 全ポイント情報
- `clustering_result.json` - JSON形式データ
- `cluster_colors.json` - 推奨色情報
- `cluster_bounds.json` - クラスタ範囲
- `clusters_by_time.json` - 時刻別データ

<br>

---

<br>

## 📚 ドキュメント

<br>

### `docs/` フォルダ

詳細なドキュメントは `docs/` に整理されています：

<br>

#### アルゴリズム関連
- **`README_STDBSCAN.md`** - ST-DBSCANの詳細説明
  - アルゴリズムの概要
  - パラメータの説明
  - チューニングのヒント

<br>

#### 可視化担当者向け 🎨
- **`HANDOFF_TO_VISUALIZATION_v2.md`** - 最新引き継ぎガイド ⭐⭐ **NEW!**
  - 雨雲レーダー風可視化の作り方
  - データ形式の完全解説
  - サンプルコード多数
  - 3分で始められる！

- **`HANDOFF_TO_VISUALIZATION.md`** - クイック引継ぎガイド
  - 基本的な使い方
  - おすすめ！

- **`README_FOR_VISUALIZATION_TEAM.md`** - 詳細ガイド
  - データ形式の詳細
  - 実装例とヒント
  - トラブルシューティング

<br>

#### その他
- **`FONT_FIX_SUMMARY.md`** - 日本語フォント対応の記録

<br>

---

<br>

## 🎨 日本語表示の設定

図の日本語が文字化けする場合は、スクリプトの先頭に以下を追加：

```python
from font_config import setup_japanese_font
setup_japanese_font()
```

<br>

利用可能なフォントの確認：

```powershell
python font_config.py
```

<br>

---

<br>

## 🔄 担当者間の連携

<br>

### クラスタリング担当 → 可視化担当 🎨

#### ステップ1: データ準備（クラスタリング担当）
```powershell
cd examples
python visualize_rain_clusters.py
```

これで以下が自動生成されます：
- 📊 **CSV/JSONデータ** - `output/rain_radar_visualization/`
- 🖼️ **可視化サンプル** - 雨雲レーダー画像 & アニメーション
- 📋 **メタデータ** - クラスタ情報、色情報、境界情報

#### ステップ2: データの確認（可視化担当）
```python
import pandas as pd

# データ読み込み
df = pd.read_csv('output/rain_radar_visualization/clustering_result.csv')

# カラム: id, lat, lon, time, value, cluster, is_noise
print(df.head())
```

#### ステップ3: 独自の可視化作成（可視化担当）
```python
import matplotlib.pyplot as plt

# 時刻0のデータを取得
time_data = df[df['time'] == df['time'].unique()[0]]
clusters = time_data[time_data['cluster'] > 0]

# 雨雲レーダー風にプロット
plt.scatter(clusters['lon'], clusters['lat'],
           c=clusters['cluster'], s=clusters['value']*30,
           cmap='tab20', alpha=0.7)
plt.xlabel('経度')
plt.ylabel('緯度')
plt.title('雨雲クラスタ')
plt.colorbar(label='クラスタID')
plt.show()
```

#### 参考ドキュメント
- 📘 **`docs/HANDOFF_TO_VISUALIZATION_v2.md`** - 完全ガイド ⭐
- 📗 **`examples/visualize_rain_clusters.py`** - 実装サンプル

<br>

---

<br>

## 💡 使い方の例

<br>

### 雨雲レーダー風可視化 🆕

```python
from st_dbscan import STDBSCAN
from weather_data import fetch_tokyo_data
from export_utils import ClusteringResultExporter

# 1. データ取得
weather_points = fetch_tokyo_data(cache_dir='./data')

# 2. クラスタリング
stdbscan = STDBSCAN(eps1=25.0, eps2=7200.0, min_pts=5)
stdbscan.fit(weather_points)

# 3. 可視化用データをエクスポート
exporter = ClusteringResultExporter(stdbscan)
exporter.export_for_visualization(output_dir='./output/viz_data')

# 4. 可視化（matplotlibなど）
import pandas as pd
import matplotlib.pyplot as plt

df = exporter.to_dataframe()
time_data = df[df['time'] == df['time'].unique()[0]]
clusters = time_data[time_data['cluster'] > 0]

plt.scatter(clusters['lon'], clusters['lat'],
           c=clusters['cluster'], s=clusters['value']*30,
           cmap='tab20', alpha=0.7)
plt.show()
```

<br>

### クラスタリングの実行

```python
from st_dbscan import STDBSCAN, STPoint

# データの準備
points = [
    STPoint(id=0, lat=35.0, lon=139.0, time=0.0, value=5.0),
    # ...
]

# ST-DBSCANの実行
stdbscan = STDBSCAN(eps1=15.0, eps2=2.0, min_pts=5)
stdbscan.fit(points)

# 結果の取得
stats = stdbscan.get_statistics()
print(f"検出されたクラスタ数: {stats['n_clusters']}")
```

<br>

### データのエクスポート

```python
from export_utils import ClusteringResultExporter

# エクスポーター作成
exporter = ClusteringResultExporter(stdbscan)

# 全データをエクスポート
exporter.export_for_visualization(output_dir='output/visualization_data')
```

<br>

### 可視化

```python
import pandas as pd
import matplotlib.pyplot as plt
from font_config import setup_japanese_font

# 日本語設定
setup_japanese_font()

# データ読み込み
df = pd.read_csv('output/visualization_data/clustering_result.csv')

# 時刻0のクラスタを可視化
time_0 = df[df['time'] == 0]
clusters = time_0[time_0['cluster'] > 0]

plt.scatter(clusters['lon'], clusters['lat'],
           c=clusters['cluster'], cmap='tab20',
           s=clusters['value'] * 15, alpha=0.7)
plt.title('雨雲クラスタ')
plt.xlabel('経度')
plt.ylabel('緯度')
plt.show()
```

<br>

---

<br>

## 📈 パラメータチューニング

```python
stdbscan = STDBSCAN(
    eps1=15.0,    # 空間距離の閾値 (km)
                  # 小さい→厳密、大きい→緩い
    
    eps2=2.0,     # 時間距離の閾値 (タイムステップ)
                  # 小さい→同時刻のみ、大きい→時間的に広い
    
    min_pts=5     # 最小ポイント数
                  # 大きい→大きなクラスタのみ、小さい→小さなクラスタも
)
```

<br>

### 調整のヒント

- **eps1**: 雨雲の典型的なサイズ（10-30km）
- **eps2**: 雨雲の移動速度とデータ間隔を考慮
- **min_pts**: 検出したい最小クラスタサイズ

<br>

---

<br>

## 🐛 トラブルシューティング

<br>

### Q: examples/ でスクリプトが実行できない
**A**: カレントディレクトリを確認してください
```powershell
cd examples
python test_clustering.py
```

<br>

### Q: モジュールが見つからない
**A**: パスが正しく設定されているか確認
```python
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
```

<br>

### Q: 日本語が文字化けする
**A**: フォント設定を確認
```python
from font_config import setup_japanese_font
setup_japanese_font()
```

<br>

### Q: 出力ファイルが見つからない

**A**: `output/` フォルダを確認してください

<br>

---

<br>

## 🔬 効果測定担当者向け

<br>

### 測定すべき項目

1. **実行時間**
   ```python
   import time
   start = time.time()
   stdbscan.fit(points)
   elapsed = time.time() - start
   print(f"実行時間: {elapsed:.2f}秒")
   ```

<br>

2. **クラスタの質**
   - クラスタ数
   - ノイズ比率
   - クラスタサイズの分布

<br>

3. **パラメータ感度**
   - eps1, eps2, min_ptsを変えた時の影響

<br>

---

<br>

## 📞 質問・相談

プロジェクトメンバー間で情報共有しながら進めてください。

<br>

### 提供可能な追加データ
- ✅ 異なるパラメータでの再クラスタリング
- ✅ 特定の時間範囲のみのデータ
- ✅ クラスタの詳細な統計情報

<br>

---

<br>

## 📚 参考資料

<br>

### ST-DBSCANアルゴリズム
- Birant, D., & Kut, A. (2007). ST-DBSCAN: An algorithm for clustering spatial-temporal data. Data & Knowledge Engineering, 60(1), 208-221.

<br>

### 使用ライブラリ
- NumPy: 数値計算
- Pandas: データ処理
- Matplotlib: 可視化
- SciPy: 補助的な計算

<br>

---

<br>

**実装完了日**: 2025年11月29日  
**実装者**: クラスタリング担当  
**次のステップ**: 可視化担当者へデータを引き継ぎ

<br>

---

<br>

**Happy Clustering! 🌧️☁️**
