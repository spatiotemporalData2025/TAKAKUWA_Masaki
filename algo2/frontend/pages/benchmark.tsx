"use client";
import { useState } from "react";
import Link from "next/link";

type BenchmarkResponse = {
  midpoint: [number, number];
  total_pois: number;
  rtree_time_ms: number;
  linear_time_ms: number;
  speedup: number;
  rtree_results: { id: number; name: string; category?: string; lat: number; lon: number }[];
  linear_results: { id: number; name: string; category?: string; lat: number; lon: number }[];
};

export default function BenchmarkPage() {
  const [lat1, setLat1] = useState<string>("35.690921");
  const [lon1, setLon1] = useState<string>("139.700257");
  const [lat2, setLat2] = useState<string>("35.729503");
  const [lon2, setLon2] = useState<string>("139.7109");
  const [category, setCategory] = useState<string>("cafe");
  const [data, setData] = useState<BenchmarkResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runBenchmark = async () => {
    setLoading(true);
    setError(null);
    try {
      const aLat = parseFloat(lat1);
      const aLon = parseFloat(lon1);
      const bLat = parseFloat(lat2);
      const bLon = parseFloat(lon2);
      
      if ([aLat, bLat].some((v) => Number.isNaN(v) || v < -90 || v > 90) || 
          [aLon, bLon].some((v) => Number.isNaN(v) || v < -180 || v > 180)) {
        throw new Error("座標が不正です (-90..90, -180..180)");
      }

      const params = new URLSearchParams({
        lat1: String(aLat),
        lon1: String(aLon),
        lat2: String(bLat),
        lon2: String(bLon),
        category,
        limit: "10",
      });

      const res = await fetch(`http://127.0.0.1:8000/benchmark?${params.toString()}`);
      if (!res.ok) throw new Error(`API ${res.status}`);
      const json = (await res.json()) as BenchmarkResponse;
      setData(json);
    } catch (e: any) {
      setError(e.message ?? "エラーが発生しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <div>
            <div className="title">R-tree vs 線形探索 ベンチマーク</div>
            <div className="subtitle">処理速度の比較測定</div>
          </div>
          <Link href="/" style={{ color: '#007aff', textDecoration: 'none' }}>← メイン画面へ戻る</Link>
        </div>

        <div className="grid cols-3 items-start">
          <div className="card">
            <h2>Person A</h2>
            <div className="field">
              <input className="input" placeholder="lat" value={lat1} onChange={(e) => setLat1(e.target.value)} />
              <input className="input" placeholder="lon" value={lon1} onChange={(e) => setLon1(e.target.value)} />
            </div>
          </div>
          <div className="card">
            <h2>Person B</h2>
            <div className="field">
              <input className="input" placeholder="lat" value={lat2} onChange={(e) => setLat2(e.target.value)} />
              <input className="input" placeholder="lon" value={lon2} onChange={(e) => setLon2(e.target.value)} />
            </div>
          </div>
          <div className="card">
            <h2>検索設定</h2>
            <div className="row">
              <label>カテゴリ:</label>
              <select className="select" value={category} onChange={(e) => setCategory(e.target.value)}>
                <option value="cafe">cafe</option>
                <option value="restaurant">restaurant</option>
                <option value="bar">bar</option>
                <option value="pub">pub</option>
                <option value="fast_food">fast_food</option>
                <option value="ice_cream">ice_cream</option>
                <option value="library">library</option>
              </select>
              <button className="btn btn-primary" onClick={runBenchmark} disabled={loading}>
                {loading ? "測定中..." : "ベンチマーク実行"}
              </button>
            </div>
            {error && <p className="hint" style={{ color: '#ff6b6b' }}>{error}</p>}
          </div>
        </div>

        {data && (
          <>
            <hr className="divider" />
            <div className="card" style={{ marginTop: 16 }}>
              <h2>📊 ベンチマーク結果</h2>
              <div className="grid cols-2" style={{ marginTop: 16, gap: 16 }}>
                <div style={{ padding: 16, background: '#f8f9fa', borderRadius: 8 }}>
                  <h3 style={{ margin: 0, marginBottom: 12, fontSize: 16 }}>🌳 R-tree検索</h3>
                  <div style={{ fontSize: 32, fontWeight: 700, color: '#007aff' }}>
                    {data.rtree_time_ms.toFixed(3)} ms
                  </div>
                  <div style={{ fontSize: 14, color: '#666', marginTop: 4 }}>
                    空間インデックスを使用した高速検索
                  </div>
                </div>
                <div style={{ padding: 16, background: '#f8f9fa', borderRadius: 8 }}>
                  <h3 style={{ margin: 0, marginBottom: 12, fontSize: 16 }}>📏 線形探索</h3>
                  <div style={{ fontSize: 32, fontWeight: 700, color: '#ff9500' }}>
                    {data.linear_time_ms.toFixed(3)} ms
                  </div>
                  <div style={{ fontSize: 14, color: '#666', marginTop: 4 }}>
                    全POIを順次計算
                  </div>
                </div>
              </div>

              <div style={{ marginTop: 20, padding: 16, background: data.speedup > 1 ? '#e8f5e9' : '#fff3e0', borderRadius: 8 }}>
                <div style={{ fontSize: 14, color: '#666', marginBottom: 6 }}>高速化率</div>
                <div style={{ fontSize: 40, fontWeight: 700, color: data.speedup > 1 ? '#4caf50' : '#ff9800' }}>
                  {data.speedup.toFixed(2)}x
                </div>
                <div style={{ fontSize: 14, color: '#666', marginTop: 4 }}>
                  {data.speedup > 1 
                    ? `R-treeは線形探索より ${data.speedup.toFixed(2)}倍 高速です` 
                    : "線形探索とほぼ同等の速度"}
                </div>
              </div>

              <div className="hint" style={{ marginTop: 16 }}>
                <strong>対象POI数:</strong> {data.total_pois}件 | 
                <strong style={{ marginLeft: 10 }}>取得件数:</strong> 各{data.rtree_results.length}件
              </div>
            </div>

            <hr className="divider" />
            
            <div className="grid cols-2" style={{ marginTop: 16 }}>
              <div>
                <div className="section-title">🌳 R-tree検索結果</div>
                <ul className="list" style={{ display: 'grid', gap: 8 }}>
                  {data.rtree_results.map((p, idx) => (
                    <li key={p.id} className="list-item">
                      <div className="name">{idx + 1}. {p.name} {p.category ? `(${p.category})` : ""}</div>
                      <div className="meta">lat: {p.lat.toFixed(6)}, lon: {p.lon.toFixed(6)}</div>
                    </li>
                  ))}
                  {data.rtree_results.length === 0 && <li className="hint">該当スポットが見つかりませんでした</li>}
                </ul>
              </div>

              <div>
                <div className="section-title">📏 線形探索結果</div>
                <ul className="list" style={{ display: 'grid', gap: 8 }}>
                  {data.linear_results.map((p, idx) => (
                    <li key={p.id} className="list-item">
                      <div className="name">{idx + 1}. {p.name} {p.category ? `(${p.category})` : ""}</div>
                      <div className="meta">lat: {p.lat.toFixed(6)}, lon: {p.lon.toFixed(6)}</div>
                    </li>
                  ))}
                  {data.linear_results.length === 0 && <li className="hint">該当スポットが見つかりませんでした</li>}
                </ul>
              </div>
            </div>

            <div className="hint" style={{ marginTop: 16 }}>
              <strong>💡 ヒント:</strong> POI数が増えるほどR-treeの優位性が顕著になります。
              広範囲の検索や大量データで特に効果的です。
            </div>
          </>
        )}
      </div>
    </div>
  );
}
