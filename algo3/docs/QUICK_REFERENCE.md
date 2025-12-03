# 気象データクラスタリング実装 - クイックリファレンス

## 🚀 すぐに実行する

```powershell
cd C:\dev\大学\TAKAKUWA_Masaki\algo3\examples
python weather_clustering_lite.py
```

## 📁 作成したファイル

### 1. コアモジュール
- **`weather_data.py`** - 気象データ取得モジュール（データ担当者作成を統合）
  - `fetch_tokyo_data()` - 東京周辺データの簡単取得
  - `fetch_weather_points()` - カスタマイズ可能な取得関数
  - `WeatherDataFetcher` - 低レベルAPI

### 2. 実装例（examples/）
- **`weather_clustering_lite.py`** ⭐ **推奨！**
  - 6時間分、252ポイント
  - 実行時間: 約1秒
  - 動作確認に最適

- **`weather_clustering_optimized.py`**
  - 24時間分、7,467ポイント
  - 処理時間: 中程度
  - バランスの良い選択

- **`weather_clustering.py`**
  - 全期間、12,313ポイント
  - 詳細な統計情報
  - エクスポート機能付き

- **`weather_clustering_quickstart.py`**
  - シンプルな実装例
  - 教育用に最適

### 3. ドキュメント（docs/）
- **`WEATHER_DATA_INTEGRATION.md`** - 実装完了報告
  - 統合内容
  - 実行結果
  - パラメータチューニング
  - 既知の問題

## 📊 実行結果（例）

```
🌧️ 気象データクラスタリング - 超軽量版
============================================================

[1/4] 東京周辺の気象データを取得中...
      ✓ 12313 個の降水ポイントを取得

[2/4] データをフィルタリング中...
    ✓ 252 ポイントにフィルタリング
    対象期間: 2025-11-24 23:00 ~ 2025-11-25 02:00

[3/4] ST-DBSCANクラスタリング実行中...
    ✓ クラスタリング完了 (0.87秒)

[4/4] 結果:
    検出されたクラスタ数: 2
    ノイズ比率: 0.0%
    
    クラスタ 1: 8 ポイント (東京湾南部付近)
    クラスタ 2: 244 ポイント (山梨県付近)
```

## 💡 使い方の基本

```python
# 1. データ取得
from weather_data import fetch_tokyo_data
weather_points = fetch_tokyo_data(cache_dir='./data')

# 2. クラスタリング
from st_dbscan import STDBSCAN
stdbscan = STDBSCAN(eps1=25.0, eps2=7200.0, min_pts=5)
stdbscan.fit(weather_points)

# 3. 結果取得
stats = stdbscan.get_statistics()
clusters = stdbscan.get_clusters()
```

## 🎯 パラメータ推奨値

### 軽量版（動作確認）
```python
eps1 = 25.0      # 空間距離: 25km（緩め）
eps2 = 7200.0    # 時間距離: 2時間
min_pts = 5      # 最小ポイント数
```

### 標準版（バランス）
```python
eps1 = 20.0      # 空間距離: 20km
eps2 = 7200.0    # 時間距離: 2時間
min_pts = 10     # 最小ポイント数
```

### 厳密版（小さな雨雲検出）
```python
eps1 = 15.0      # 空間距離: 15km
eps2 = 3600.0    # 時間距離: 1時間
min_pts = 5      # 最小ポイント数
```

## 🔧 データのフィルタリング

```python
from weather_data import fetch_weather_points

# カスタム設定
points = fetch_weather_points(
    lat_min=34.0, lat_max=36.5,      # 緯度範囲
    lon_min=137.5, lon_max=140.5,    # 経度範囲
    start_date='2025-11-20',         # 開始日
    end_date='2025-11-30',           # 終了日
    precipitation_threshold=0.5,     # 降水閾値 (mm/h)
    cache_dir='./data'
)
```

## 📈 パフォーマンス目安

| データ量 | 処理時間 | 推奨スクリプト |
|---------|---------|--------------|
| 250ポイント | 1秒 | weather_clustering_lite.py ⭐ |
| 2,000ポイント | 10秒 | weather_clustering_optimized.py |
| 7,000ポイント | 数分 | weather_clustering_optimized.py |
| 12,000ポイント | 長時間 | 要最適化 |

## 🐛 トラブルシューティング

### Q: 処理が遅い
**A:** `weather_clustering_lite.py` を使用してください

### Q: クラスタが検出されない
**A:** パラメータを調整:
- eps1を大きく（30.0など）
- eps2を大きく（10800.0 = 3時間）
- min_ptsを小さく（3など）

### Q: クラスタが多すぎる
**A:** パラメータを調整:
- eps1を小さく（15.0など）
- min_ptsを大きく（10以上）

## 🔗 関連ファイル

- `st_dbscan.py` - ST-DBSCANアルゴリズム本体
- `export_utils.py` - データエクスポート機能
- `requirements.txt` - 必要なパッケージ
- `README.md` - プロジェクト全体の説明

## 📞 次のステップ

### 可視化担当者へ
1. `weather_clustering_lite.py` を実行
2. クラスタデータを取得
3. 地図上にプロット

### 効果測定担当者へ
1. 異なるパラメータで実行
2. 実行時間を測定
3. クラスタの質を評価

### プレゼン担当者へ
1. 実データでの成功を報告
2. 検出された雨雲クラスタを説明
3. `docs/WEATHER_DATA_INTEGRATION.md` を参照

---

**更新日:** 2025年12月3日  
**ステータス:** ✅ 実装完了・動作確認済み
