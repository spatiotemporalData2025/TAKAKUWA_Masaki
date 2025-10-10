{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "# Streaming Heavy-Hitters: Implementations of Algorithms 3.1, 3.2, 3.3\n",
    "\n",
    "このノートブックでは、提示画像の擬似コードを **Python** で実装します。\n",
    "\n",
    "- **Algorithm 3.1**: Misra–Gries（k-1 カウンタ方式）\n",
    "- **Algorithm 3.2**: Lossy Counting（Δ=⌊n/k⌋ を用いたバケット削除）\n",
    "- **Algorithm 3.3**: SpaceSaving（最小カウンタの置換）\n",
    "\n",
    "いずれもストリーム中の **頻出要素（heavy hitters）** を近似的に追跡するアルゴリズムです。"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "from __future__ import annotations\n",
    "from typing import Dict, Iterable, List, Tuple, Any\n",
    "\n",
    "def top_k_from_counts(counts: Dict[Any, int], k: int) -> List[Tuple[Any, int]]:\n",
    "    \"\"\"Return top-k pairs sorted by count desc, then key asc for stability.\"\"\"\n",
    "    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:k]"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Algorithm 3.1 — Misra–Gries\n",
    "擬似コード:\n",
    "- `n ← n + 1`\n",
    "- `if i ∈ T` なら `c_i ← c_i + 1`\n",
    "- そうでなく `|T| < k-1` なら `T ← T ∪ {i}; c_i ← 1`\n",
    "- それ以外なら、全 `j ∈ T` について `c_j ← c_j - 1` を行い、`c_j = 0` は削除\n",
    "\n",
    "性質: どの時点でもテーブルは最大 `k-1` 件。真の出現回数 `f(i)` と推定 `c_i` の誤差は **高々 ⌊n/k⌋**。"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "class MisraGries:\n",
    "    \"\"\"Algorithm 3.1 (Misra–Gries) for heavy hitters with parameter k.\"\"\"\n",
    "    def __init__(self, k: int):\n",
    "        assert k >= 2, \"k must be >= 2\"\n",
    "        self.k = k\n",
    "        self.n = 0\n",
    "        self.T: Dict[Any, int] = {}  # item -> c_i\n",
    "\n",
    "    def update(self, item: Any):\n",
    "        self.n += 1\n",
    "        if item in self.T:\n",
    "            self.T[item] += 1\n",
    "            return\n",
    "        if len(self.T) < self.k - 1:\n",
    "            self.T[item] = 1\n",
    "            return\n",
    "        # decrement all, drop zeros\n",
    "        to_del = []\n",
    "        for j in list(self.T.keys()):\n",
    "            self.T[j] -= 1\n",
    "            if self.T[j] == 0:\n",
    "                to_del.append(j)\n",
    "        for j in to_del:\n",
    "            del self.T[j]\n",
    "\n",
    "    def consume(self, stream: Iterable[Any]):\n",
    "        for x in stream:\n",
    "            self.update(x)\n",
    "        return self\n",
    "\n",
    "    def candidates(self) -> Dict[Any, int]:\n",
    "        return dict(self.T)\n",
    "\n",
    "    def topk(self, k: int | None = None) -> List[Tuple[Any, int]]:\n",
    "        return top_k_from_counts(self.T, k or len(self.T))"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Algorithm 3.2 — Lossy Counting（Δ=⌊n/k⌋ を用いた一括削除）\n",
    "擬似コード（画像の記法を Python に忠実移植）:\n",
    "- 追加の変数 `Δ` を持つ（初期値 0）\n",
    "- 各到着で `n ← n + 1`。`i ∈ T` なら `c_i ← c_i + 1`、さもなくば `T ← T ∪ {i}; c_i ← 1 + Δ`\n",
    "- `if ⌊n/k⌋ ≠ Δ` なら `Δ ← ⌊n/k⌋` とし、すべての `j ∈ T` について `if c_j < Δ: remove j`。\n",
    "\n",
    "性質: 誤差は最大 `n/k`。容量はおおよそ `O(k log n)` に抑えられます（経験則）。"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "class LossyCounting:\n",
    "    \"\"\"Algorithm 3.2 (Manku–Motwani style lossy counting) with bucket Δ=floor(n/k).\"\"\"\n",
    "    def __init__(self, k: int):\n",
    "        assert k >= 2, \"k must be >= 2\"\n",
    "        self.k = k\n",
    "        self.n = 0\n",
    "        self.delta = 0\n",
    "        self.T: Dict[Any, int] = {}\n",
    "\n",
    "    def _maybe_prune(self):\n",
    "        new_delta = self.n // self.k\n",
    "        if new_delta != self.delta:\n",
    "            self.delta = new_delta\n",
    "            # prune entries whose c_j < Δ\n",
    "            to_del = [j for j, c in list(self.T.items()) if c < self.delta]\n",
    "            for j in to_del:\n",
    "                del self.T[j]\n",
    "\n",
    "    def update(self, item: Any):\n",
    "        self.n += 1\n",
    "        if item in self.T:\n",
    "            self.T[item] += 1\n",
    "        else:\n",
    "            self.T[item] = 1 + self.delta\n",
    "        self._maybe_prune()\n",
    "\n",
    "    def consume(self, stream: Iterable[Any]):\n",
    "        for x in stream:\n",
    "            self.update(x)\n",
    "        return self\n",
    "\n",
    "    def candidates(self) -> Dict[Any, int]:\n",
    "        return dict(self.T)\n",
    "\n",
    "    def topk(self, k: int | None = None) -> List[Tuple[Any, int]]:\n",
    "        return top_k_from_counts(self.T, k or len(self.T))"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Algorithm 3.3 — SpaceSaving（最小カウンタの置換）\n",
    "擬似コード:\n",
    "- `i ∈ T` なら `c_i ← c_i + 1`\n",
    "- そうでなく `|T| < k` なら `T ← T ∪ {i}; c_i ← 1`\n",
    "- それ以外なら `j ← argmin_{j∈T} c_j` を選び、`c_i ← c_j + 1` として `i` で置換\n",
    "\n",
    "性質: 容量は常に **k**。`f(i)` の過小評価は起きず、誤差は最大で **最小カウンタ値**。"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "class SpaceSaving:\n",
    "    \"\"\"Algorithm 3.3 (SpaceSaving) with exactly k counters.\"\"\"\n",
    "    def __init__(self, k: int):\n",
    "        assert k >= 1, \"k must be >= 1\"\n",
    "        self.k = k\n",
    "        self.n = 0\n",
    "        self.T: Dict[Any, int] = {}\n",
    "\n",
    "    def update(self, item: Any):\n",
    "        self.n += 1\n",
    "        if item in self.T:\n",
    "            self.T[item] += 1\n",
    "            return\n",
    "        if len(self.T) < self.k:\n",
    "            self.T[item] = 1\n",
    "            return\n",
    "        # replace the minimum counter entry\n",
    "        j, cj = min(self.T.items(), key=lambda x: x[1])\n",
    "        del self.T[j]\n",
    "        self.T[item] = cj + 1\n",
    "\n",
    "    def consume(self, stream: Iterable[Any]):\n",
    "        for x in stream:\n",
    "            self.update(x)\n",
    "        return self\n",
    "\n",
    "    def candidates(self) -> Dict[Any, int]:\n",
    "        return dict(self.T)\n",
    "\n",
    "    def topk(self, k: int | None = None) -> List[Tuple[Any, int]]:\n",
    "        return top_k_from_counts(self.T, k or len(self.T))"
   ]
  },
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": [
    "## Quick Demo\n",
    "同じストリームに対して 3 つのアルゴリズムを走らせ、上位候補を比較します。"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import random\n",
    "random.seed(0)\n",
    "\n",
    "# 合成ストリーム（'A' と 'B' が heavy）\n",
    "stream = ['A']*120 + ['B']*90 + ['C']*40 + ['D']*35 + ['E']*30 + ['F']*20\n",
    "random.shuffle(stream)\n",
    "\n",
    "k = 5\n",
    "mg = MisraGries(k).consume(stream)\n",
    "lc = LossyCounting(k).consume(stream)\n",
    "ss = SpaceSaving(k).consume(stream)\n",
    "\n",
    "print(\"n =\", len(stream))\n",
    "print(\"Misra–Gries:\", mg.topk())\n",
    "print(\"Lossy Counting:\", lc.topk())\n",
    "print(\"SpaceSaving:\", ss.topk())"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "name": "python",
   "version": "3.x"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
