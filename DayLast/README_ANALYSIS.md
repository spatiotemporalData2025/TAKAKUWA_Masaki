# 自転車シェアリング分析ツール - README

## 概要
東京都心の自転車シェアリングデータをリアルタイムで収集・分析・可視化するシステムです。

## ファイル構成

### メインアプリケーション
- **app.py** - FastAPIベースのWebアプリケーション（データ収集＋リアルタイム表示）
- **templates/index.html** - インタラクティブな地図インターフェース

### データ分析スクリプト

#### 基本分析
1. **analyze_flow.py** - エリア別推移分析
   - 千代田区（オフィス街）と江東区（住宅街）の比較
   - 時刻ごとの平均利用可能台数の推移グラフ
   - 出力: `flow_analysis.png`

2. **analyze_ranking.py** - 変動ランキング
   - ステーション別の在庫変動回数をTop10でランキング
   - 利用が活発なステーションの特定
   - 出力: `station_ranking.png`

3. **benchmark_rtree.py** - R-tree性能検証
   - 10万件のデータで線形探索とR-treeを比較
   - 空間インデックスの有効性を実証
   - 出力: `benchmark_result.png`

#### 高度な分析（NEW!）
4. **analyze_advanced.py** - 多角的データ分析
   - 時間帯別の利用パターン分析
   - 曜日別の傾向分析
   - ステーション別統計（平均・標準偏差・最大最小）
   - 空間的分布の可視化
   - DBSCANによる自転車不足エリアのクラスタリング
   - 時間と在庫の相関分析
   - 変動が激しいステーションの特定
   - 全体統計とヒストグラム
   - 出力: 
     - `advanced_analysis.png` - 4つのグラフを含む総合分析
     - `cluster_low_stock.png` - 自転車不足エリアのクラスタ
     - `distribution_histogram.png` - 利用可能台数の分布

#### 動画生成（NEW!）
5. **create_heatmap_video.py** - 時系列ヒートマップ動画
   - 自転車台数の時間的変化を動画で可視化
   - 補間によるスムーズなヒートマップ
   - ステーション位置と統計情報を同時表示
   - 出力: `bike_heatmap_animation.mp4` または `bike_heatmap_animation.gif`

## 使い方

### 1. データ収集開始
```powershell
cd C:\dev\大学\TAKAKUWA_Masaki\DayLast
python -m uvicorn app:app --reload --port 8000
```
ブラウザで http://127.0.0.1:8000 にアクセス
→ 30秒ごとに自動的に `bike_log.csv` にデータが蓄積されます

### 2. 基本分析実行
```powershell
python analyze_flow.py       # エリア別推移分析
python analyze_ranking.py    # 変動ランキング
python benchmark_rtree.py    # R-tree性能検証
```

### 3. 高度な分析実行（NEW!）
```powershell
python analyze_advanced.py   # 多角的分析（8つの分析項目）
```

### 4. ヒートマップ動画生成（NEW!）
```powershell
python create_heatmap_video.py
```
※ ffmpegが必要です。なければGIF形式で保存されます

## 実装アルゴリズム

### 空間データ処理
- **R-tree** - 高速な範囲検索（O(log n)）
- **DBSCAN** - 密度ベースクラスタリング（自転車不足エリア検出）

### ストリーム処理
- **Space Saving** - 頻出アイテム検出（メモリ効率的）

### 統計・可視化
- **時系列分析** - 時間帯・曜日パターンの抽出
- **相関分析** - Pearson相関係数による関係性分析
- **ヒートマップ** - 空間補間による連続的可視化

## データ形式

### bike_log.csv
```
timestamp,station_name,free_bikes,latitude,longitude
2026-01-18 14:30:00,駅前ステーション,5,35.6812,139.7671
...
```

## 出力ファイル一覧

### 画像
- `flow_analysis.png` - エリア別推移比較
- `station_ranking.png` - 変動回数ランキング
- `benchmark_result.png` - R-tree性能比較
- `advanced_analysis.png` - 総合分析（4グラフ）
- `cluster_low_stock.png` - 自転車不足クラスタ
- `distribution_histogram.png` - 台数分布

### 動画
- `bike_heatmap_animation.mp4` - 時系列ヒートマップ動画（MP4形式）
- または `bike_heatmap_animation.gif` - 同上（GIF形式）

## 必要なライブラリ
```
fastapi
uvicorn
requests
scikit-learn
numpy
pandas
matplotlib
seaborn
scipy
rtree
pillow  # GIF生成用
ffmpeg  # MP4生成用（システムにインストール）
```

## 知見が得られるポイント

### 1. 時空間パターンの発見
- オフィス街と住宅街での利用パターンの違い
- 時間帯による需要の変動
- 曜日による利用傾向

### 2. 運用の最適化
- 変動が激しいステーション = 再配置が必要
- 自転車不足のクラスタ = 優先的に補充すべきエリア
- 相関分析 = 予測モデル構築の基礎

### 3. アルゴリズムの有効性
- R-treeによる検索速度の劇的な改善
- DBSCANによる異常エリアの自動検出
- Space Savingによる省メモリな頻出検出

### 4. 視覚的洞察
- ヒートマップ動画で時空間パターンを直感的に理解
- 統計グラフで数値的な裏付け
- 複合的な可視化で多角的な分析

## 今後の拡張案
- 機械学習による需要予測
- リアルタイム異常検知アラート
- 最適な自転車再配置ルートの提案
- 天気データとの相関分析
