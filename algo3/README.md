# ST-DBSCAN実装: algo3プロジェクト

> **最新の更新**: フォルダ構造を整理しました（2025/11/29）

<br>

---

<br>

## 📋 プロジェクト概要

地点別の気象データからST-DBSCANを使って時空間クラスタリングし、過去の雲の流れがクラスタとして現れるかを確認するプロジェクトです。

<br>

### 👥 役割分担

1. **データ取得する人** - 気象データの収集
2. **ST-DBSCANを実装して降水地点のクラスタリングをする人** ← 現在の担当
3. **クラスタリング結果から可視化する人** - 雨雲レーダー表示
4. **効果測定する人** - 実行時間測定、検証
5. **スライド作る人** - プレゼンテーション

<br>

---

<br>

## 📁 プロジェクト構造

```
algo3/
├── README.md                 # このファイル
├── requirements.txt          # 必要なパッケージ
│
├── st_dbscan.py             # ST-DBSCANアルゴリズム実装
├── export_utils.py          # データエクスポート機能
├── font_config.py           # 日本語フォント設定
│
├── docs/                    # ドキュメント
│   ├── README_STDBSCAN.md
│   ├── README_FOR_VISUALIZATION_TEAM.md
│   ├── HANDOFF_TO_VISUALIZATION.md
│   └── FONT_FIX_SUMMARY.md
│
├── examples/                # サンプルスクリプト
│   ├── test_clustering.py
│   └── visualization_sample.py
│
└── output/                  # 出力ファイル
    ├── *.png                # 可視化画像
    ├── *.gif                # アニメーション
    └── visualization_data/  # エクスポートデータ
        ├── clustering_result.csv
        ├── clustering_result.json
        ├── cluster_colors.json
        ├── cluster_bounds.json
        └── clusters_by_time.json
```

<br>

---

<br>

## 🚀 クイックスタート

<br>

### 1. 環境構築

```powershell
# パッケージのインストール
pip install -r requirements.txt
```

<br>

### 2. テスト実行

```powershell
# examples フォルダに移動
cd examples

# クラスタリングのテスト
python test_clustering.py

# 可視化のサンプル
python visualization_sample.py
```

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

#### 可視化担当者向け
- **`HANDOFF_TO_VISUALIZATION.md`** - クイック引継ぎガイド ⭐
  - 3分で始められる
  - コードサンプル多数
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

### クラスタリング担当 → 可視化担当

1. `examples/test_clustering.py` を実行
2. `output/visualization_data/` フォルダが生成される
3. 可視化担当者に以下を共有：
   - `output/visualization_data/` フォルダ
   - `docs/HANDOFF_TO_VISUALIZATION.md` ⭐

<br>

---

<br>

## 💡 使い方の例

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
