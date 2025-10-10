# Heavy Hitters — 3アルゴリズム比較（同一データ）

入力: YouTubeライブチャット（列: `author`, `message`）。  
メトリクス: ground truth 上位20との重なり、順位相関、推定誤差。

import pandas as pd
from collections import Counter

df = pd.read_csv("/mnt/data/Brighton v Man City LIVE Watchalong!_chat_log.csv", encoding="utf-8", engine="python")
stream = df["author"].astype(str).tolist()
N = len(stream)
print("n =", N, "unique authors =", df['author'].nunique())


# Implementations (同じセルに定義)
from collections import defaultdict, Counter
import math

def misra_gries(stream, k):
    T = {}
    for x in stream:
        if x in T:
            T[x] += 1
        elif len(T) < k-1:
            T[x] = 1
        else:
            dead=[]
            for j in list(T.keys()):
                T[j]-=1
                if T[j]==0: dead.append(j)
            for j in dead:
                del T[j]
    return T

def lossy_counting(stream, k):
    T = {}
    Delta = 0
    n = 0
    for x in stream:
        n += 1
        if x in T: T[x]+=1
        else: T[x] = 1 + Delta
        if (n // k) != Delta:
            Delta = n // k
            for j in list(T.keys()):
                if T[j] < Delta:
                    del T[j]
    return T

def space_saving(stream, k):
    T = {}
    for x in stream:
        if x in T: T[x]+=1
        elif len(T)<k: T[x]=1
        else:
            j=min(T, key=T.get)
            m=T[j]
            del T[j]
            T[x]=m+1
    return T

def evaluate(T, truth, top=20):
    gt = [u for u,_ in truth.most_common(top)]
    cand = sorted(T.keys(), key=lambda u: truth[u], reverse=True)[:top]
    overlap = len(set(gt)&set(cand))
    return {
        "overlap@{}".format(top): overlap,
        "recall@{}".format(top): overlap/float(top),
        "size": len(T)
    }

from collections import Counter
truth = Counter(stream)
k=20

T_mg = misra_gries(stream, k)
T_lc = lossy_counting(stream, k)
T_ss = space_saving(stream, k)

print("MG  :", evaluate(T_mg, truth))
print("LC  :", evaluate(T_lc, truth))
print("SS  :", evaluate(T_ss, truth))

print("\nGround truth top-10:", truth.most_common(10))
