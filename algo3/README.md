# algo3 - DBSCANレポート課題


## DBSCAN (Density-Based Spatial Clustering of Applications with Noise)

### アルゴリズムの概要

DBSCANは密度ベースのクラスタリングアルゴリズムで、空間データベース内のノイズを含む大規模データからクラスタを発見するために設計されている。

### 主要パラメータ

1. **ε (epsilon)**: 近傍を定義する距離の半径
2. **MinPts**: コアポイントとみなすために必要な最小点数

### アルゴリズムの動作

1. **コアポイント**: ε-近傍内にMinPts以上の点を持つ点
2. **境界ポイント**: コアポイントのε-近傍内にあるが、自身はコアポイントでない点
3. **ノイズポイント**: コアポイントでも境界ポイントでもない点

### 特徴

**長所:**
- 任意の形状のクラスタを発見できる
- クラスタ数を事前に指定する必要がない
- ノイズを検出できる
- パラメータが2つだけで比較的シンプルである

**短所:**
- 密度が大きく異なるクラスタの検出が困難である
- 高次元データには効果が低い
- パラメータの選択が結果に大きく影響する

---

## 後続研究の発展

### 1. OPTICS (Ordering Points To Identify the Clustering Structure, 1999)

**参考文献:**
Ankerst, Mihael, et al. "OPTICS: ordering points to identify the clustering structure." *ACM Sigmod record*. Vol. 28. No. 2. ACM, 1999.

**改善点:**
- DBSCANの密度パラメータ依存性を解決
- 階層的なクラスタリング構造を発見
- 到達可能性距離(reachability distance)の概念を導入
- εパラメータを自動的に決定可能

**進化のポイント:**
- DBSCANは単一のεパラメータに依存していたが、OPTICSは複数の密度レベルを同時に考慮
- クラスタリング結果を到達可能性プロット(reachability plot)として可視化

### 2. HDBSCAN (Hierarchical DBSCAN, 2013)

**参考文献:**
Campello, Ricardo JGB, Davoud Moulavi, and Joerg Sander. "Density-based clustering based on hierarchical density estimates." *Pacific-Asia conference on knowledge discovery and data mining*. Springer, Berlin, Heidelberg, 2013.

**改善点:**
- 完全に階層的なクラスタリング
- 異なる密度のクラスタを自動検出
- MinPtsパラメータのみで動作（εが不要）
- クラスタの安定性を評価する指標を提供

**進化のポイント:**
- DBSCANの「単一密度しきい値」の制約を完全に解消
- 最小スパニングツリー(MST)ベースのアプローチ
- クラスタの階層構造をデンドログラムで表現

### 3. DBSCAN* (2014)

**参考文献:**
Campello, Ricardo JGB, et al. "Hierarchical density estimates for data clustering, visualization, and outlier detection." *ACM Transactions on Knowledge Discovery from Data (TKDD)* 10.1 (2015): 1-51.

**改善点:**
- 境界ポイントの扱いを改善
- より一貫性のあるクラスタ割り当て
- アウトライア検出の強化

### 4. ST-DBSCAN (Spatial-Temporal DBSCAN, 2007)

**参考文献:**
Birant, Derya, and Alp Kut. "ST-DBSCAN: An algorithm for clustering spatial–temporal data." *Data & Knowledge Engineering* 60.1 (2007): 208-221.

**改善点:**
- 時空間データへの拡張
- 空間距離と時間距離を組み合わせた類似度
- 移動体データやトラジェクトリデータのクラスタリングに適用

**進化のポイント:**
- DBSCANの2つのパラメータ（ε, MinPts）に加え、時間的な閾値を導入
- 空間的に近く、時間的にも近い点をクラスタ化

### 5. DBCLASD (Distribution-Based Clustering of LArge Spatial Databases, 2001)

**参考文献:**
Xu, Xiaowei, Jochen Jäger, and Hans-Peter Kriegel. "A fast parallel clustering algorithm for large spatial databases." *Data mining and knowledge discovery* 3.3 (1999): 263-290.

**改善点:**
- 並列処理に対応
- 大規模データセットへのスケーラビリティ向上
- 分散ベースのアプローチ

---

## 図解

### DBSCANの基本概念

```
     ●  ●  ●           ← クラスタA
    ●  ●  ●  ●
     ●  ●  ●

              ×         ← ノイズ

                 ●  ●   ← クラスタB
                ●  ●  ●
                 ●  ●

凡例:
● = データポイント
○ = コアポイント（中心部）
◎ = 境界ポイント
× = ノイズポイント
```

### パラメータεとMinPtsの影響

```
ε小・MinPts小 → 多数の小さなクラスタ + 多くのノイズ
ε大・MinPts大 → 少数の大きなクラスタ + 少ないノイズ
最適なバランス → 意味のあるクラスタ構造を発見
```

### DBSCANとOPTICSの比較

```
DBSCAN:
- 単一のε値
- フラットなクラスタリング
- パラメータに敏感

OPTICS:
- 複数の密度レベル
- 階層的構造
- 到達可能性プロットで可視化
```

---

## 実装の参考

### Python (scikit-learn)

```python
from sklearn.cluster import DBSCAN
import numpy as np

# サンプルデータ
X = np.array([[1, 2], [2, 2], [2, 3], [8, 7], [8, 8], [25, 80]])

# DBSCANの適用
clustering = DBSCAN(eps=3, min_samples=2).fit(X)

# ラベルの取得
labels = clustering.labels_
print(labels)
# 出力例: [ 0  0  0  1  1 -1]
# -1 はノイズを表す
```

---

## まとめ

DBSCANは1996年に提案された革新的なクラスタリングアルゴリズムであり、以下の点で画期的であった：

1. **密度ベースのアプローチ**: K-meansのような重心ベースではなく、点の密度に基づく
2. **任意形状のクラスタ**: 球状以外の複雑な形状も検出可能
3. **ノイズ検出**: 外れ値を自動的に識別
4. **クラスタ数不要**: 事前にクラスタ数を指定する必要がない

その後、OPTICS、HDBSCAN、ST-DBSCANなどの改良版が開発され、以下の課題を解決した：

- 異なる密度のクラスタの検出
- パラメータ選択の自動化
- 時空間データへの拡張
- 大規模データへのスケーラビリティ

DBSCANとその派生アルゴリズムは、現在でも多くの分野で広く使用されている：
- 地理空間データ分析
- 画像処理
- 異常検出
- ソーシャルネットワーク分析
- バイオインフォマティクス

---

## 参考文献

1. Ester, M., Kriegel, H. P., Sander, J., & Xu, X. (1996). A density-based algorithm for discovering clusters in large spatial databases with noise. *Kdd*, 96(34), 226-231.

2. Ankerst, M., Breunig, M. M., Kriegel, H. P., & Sander, J. (1999). OPTICS: ordering points to identify the clustering structure. *ACM Sigmod record*, 28(2), 49-60.

3. Campello, R. J., Moulavi, D., & Sander, J. (2013). Density-based clustering based on hierarchical density estimates. *Pacific-Asia conference on knowledge discovery and data mining* (pp. 160-172).

4. Birant, D., & Kut, A. (2007). ST-DBSCAN: An algorithm for clustering spatial–temporal data. *Data & Knowledge Engineering*, 60(1), 208-221.

5. Schubert, E., Sander, J., Ester, M., Kriegel, H. P., & Xu, X. (2017). DBSCAN revisited, revisited: why and how you should (still) use DBSCAN. *ACM Transactions on Database Systems (TODS)*, 42(3), 1-21.

6. McInnes, L., Healy, J., & Astels, S. (2017). hdbscan: Hierarchical density based clustering. *J. Open Source Softw.*, 2(11), 205.
