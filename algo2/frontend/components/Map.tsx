"use client";
import React, { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";

type Poi = { id: number; name: string; category?: string; lat: number; lon: number };
type Basemap = "osm" | "gsi";

export default function Map({
  midpoint,
  pois,
  personA,
  personB,
  basemap = "osm",
  showRail = true,
  // removed terrain toggle
  bboxRect,
  enableDraw,
  onBBoxDrawn,
  loading,
  toolbar,
  onToggleDraw,
  onResetBBox,
  onRecenter,
  enableCluster = true,
  onPersonADrag,
  onPersonBDrag,
}: {
  midpoint?: [number, number];
  pois: Poi[];
  personA?: [number, number];
  personB?: [number, number];
  basemap?: Basemap;
  showRail?: boolean;
  // showTerrain removed
  bboxRect?: [number, number, number, number]; // [minLat, minLon, maxLat, maxLon]
  enableDraw?: boolean;
  onBBoxDrawn?: (bbox: [number, number, number, number]) => void;
  loading?: boolean;
  toolbar?: boolean;
  onToggleDraw?: () => void;
  onResetBBox?: () => void;
  onRecenter?: () => void;
  enableCluster?: boolean;
  onPersonADrag?: (lat: number, lon: number) => void;
  onPersonBDrag?: (lat: number, lon: number) => void;
}) {
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const mapContainer = useRef<HTMLDivElement | null>(null);
  const markersRef = useRef<Record<number, any>>({});
  const mapRef = useRef<any>(null);
  const drawActiveRef = useRef<boolean>(false);
  const drawStateRef = useRef<{ dLat?: number; dLon?: number } | null>(null);

  // Safe helpers to avoid errors when style isn't loaded or map is disposed
  const safeHasLayer = (mapObj: any, id: string) => {
    try { return !!(mapObj && mapObj.getLayer && mapObj.getLayer(id)); } catch { return false; }
  };
  const safeHasSource = (mapObj: any, id: string) => {
    try { return !!(mapObj && mapObj.getSource && mapObj.getSource(id)); } catch { return false; }
  };
  const safeRemoveLayer = (mapObj: any, id: string) => {
    try { if (safeHasLayer(mapObj, id)) mapObj.removeLayer(id); } catch { /* ignore */ }
  };
  const safeRemoveSource = (mapObj: any, id: string) => {
    try { if (safeHasSource(mapObj, id)) mapObj.removeSource(id); } catch { /* ignore */ }
  };

  // Create a simple blue pin icon and register to map
  const ensurePinImage = (map: any, id: string = "poi-pin") => {
    try { if (map.hasImage && map.hasImage(id)) return; } catch { /* ignore */ }
    const size = 41; // 人のデフォルトマーカーに合わせた概ねの高さ
    const c = document.createElement('canvas');
    c.width = size; c.height = size;
    const ctx = c.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0,0,size,size);
    ctx.save();
    ctx.translate(size/2, size/2 - 4);
    ctx.fillStyle = '#1e90ff';
    ctx.beginPath();
    ctx.arc(0, -6, 10, Math.PI, 0);
    ctx.quadraticCurveTo(10, 10, 0, 18);
    ctx.quadraticCurveTo(-10, 10, -10, -6);
    ctx.closePath();
    ctx.fill();
    ctx.beginPath();
    ctx.fillStyle = '#ffffff';
    ctx.arc(0, -6, 3.5, 0, Math.PI*2);
    ctx.fill();
    ctx.restore();
    try {
      const img = ctx.getImageData(0, 0, size, size);
      // pixelRatio:1 で CSS 上も約41px になるようにする
      map.addImage(id, img as any, { pixelRatio: 1 });
    } catch { /* ignore */ }
  };

  useEffect(() => {
    if (!midpoint) return;

    // ベースマップの選択（無料・キー不要）
  const osmStyle: any = {
      version: 8,
      sources: {
        osm: {
          type: "raster",
          tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution:
            '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        },
        ...(showRail
          ? {
              orm: {
                type: "raster",
                tiles: ["https://tiles.openrailwaymap.org/standard/{z}/{x}/{y}.png"],
                tileSize: 256,
                attribution:
                  '© <a href="https://www.openrailwaymap.org/">OpenRailwayMap</a> contributors',
              },
            }
          : {}),
      },
      layers: [
        { id: "osm", type: "raster", source: "osm", minzoom: 0, maxzoom: 20 },
        ...(showRail
          ? [{ id: "orm", type: "raster", source: "orm", minzoom: 0, maxzoom: 20, paint: { "raster-opacity": 0.8 } }] as any
          : []),
      ],
    };

  const gsiStyle: any = {
      version: 8,
      sources: {
        gsi_std: {
          type: "raster",
          tiles: ["https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png"],
          tileSize: 256,
          attribution:
            '地理院タイル © <a href="https://www.gsi.go.jp/">GSI</a> / © OpenStreetMap contributors',
        },
        ...(showRail
          ? {
              gsi_rail: {
                type: "raster",
                tiles: ["https://cyberjapandata.gsi.go.jp/xyz/railway/{z}/{x}/{y}.png"],
                tileSize: 256,
                attribution:
                  '地理院タイル（鉄道） © <a href="https://www.gsi.go.jp/">GSI</a>',
              },
            }
          : {}),
      },
      layers: [
        { id: "gsi_std", type: "raster", source: "gsi_std", minzoom: 0, maxzoom: 20 },
        ...(showRail
          ? [{ id: "gsi_rail", type: "raster", source: "gsi_rail", minzoom: 0, maxzoom: 20, paint: { "raster-opacity": 0.8 } }] as any
          : []),
      ],
    };

    const styleToUse = basemap === "gsi" ? gsiStyle : osmStyle;

  const map = new maplibregl.Map({
      container: mapContainer.current!,
      style: styleToUse,
      center: [midpoint[1], midpoint[0]],
      zoom: 13,
      attributionControl: true,
    });
  mapRef.current = map;

    // デバッグ: スタイルやタイルの取得エラーを表示
    let fallbackApplied = false;
    map.on("error", (e) => {
      // eslint-disable-next-line no-console
      console.error("MapLibre error:", (e as any)?.error || e);
      // もし何らかの理由で失敗したら OSM ベースへフォールバック
      const err = (e as any)?.error;
      if (!fallbackApplied && err && (err.status || err.name === "StyleLoadError")) {
        fallbackApplied = true;
        try {
          map.setStyle(osmStyle);
        } catch {
          // ignore
        }
      }
    });

  // Controls (Google Mapsのような基本操作)
  map.addControl(new maplibregl.NavigationControl(), "top-right");
  map.addControl(new maplibregl.ScaleControl({ maxWidth: 120, unit: "metric" }), "bottom-left");
  map.addControl(new maplibregl.GeolocateControl({ positionOptions: { enableHighAccuracy: true }, trackUserLocation: false }), "top-left");
  map.addControl(new maplibregl.AttributionControl({ compact: true }));

    // Person A/B (任意)
    if (personA) {
      const mkA = new maplibregl.Marker({ color: "green" as any, draggable: true })
        .setLngLat([personA[1], personA[0]])
        .setPopup(new maplibregl.Popup().setText("Person A"))
        .addTo(map);
      mkA.on('dragend', () => {
        const ll = mkA.getLngLat();
        onPersonADrag && onPersonADrag(ll.lat, ll.lng);
      });
    }
    if (personB) {
      const mkB = new maplibregl.Marker({ color: "purple" as any, draggable: true })
        .setLngLat([personB[1], personB[0]])
        .setPopup(new maplibregl.Popup().setText("Person B"))
        .addTo(map);
      mkB.on('dragend', () => {
        const ll = mkB.getLngLat();
        onPersonBDrag && onPersonBDrag(ll.lat, ll.lng);
      });
    }

    // 中間地点
    new maplibregl.Marker({ color: "red" as any })
      .setLngLat([midpoint[1], midpoint[0]])
      .setPopup(new maplibregl.Popup().setText("中間地点"))
      .addTo(map);

    // POIs: cluster layers or markers
    if (enableCluster) {
      const fc: any = {
        type: "FeatureCollection",
        features: pois.map((p) => ({
          type: "Feature",
          properties: { id: p.id, name: p.name, category: p.category ?? "" },
          geometry: { type: "Point", coordinates: [p.lon, p.lat] },
        })),
      };
      const apply = () => {
        const srcId = "pois-src";
        ensurePinImage(map, 'poi-pin');
        if (!map.getSource(srcId)) {
          map.addSource(srcId, { type: "geojson", data: fc, cluster: true, clusterRadius: 50 } as any);
          map.addLayer({
            id: "cluster-circles",
            type: "circle",
            source: srcId,
            filter: ["has", "point_count"],
            paint: {
              "circle-color": "#ffffff",
              "circle-opacity": 0.95,
              "circle-stroke-color": "#1e90ff",
              "circle-stroke-width": 2,
              "circle-radius": ["step", ["get", "point_count"], 18, 20, 24, 50, 32, 100, 40]
            }
          } as any);
          map.addLayer({
            id: "cluster-count",
            type: "symbol",
            source: srcId,
            filter: ["has", "point_count"],
            layout: {
              "text-field": ["to-string", ["get", "point_count"]],
              "text-size": 16,
              "text-allow-overlap": true,
              "text-anchor": "center"
            },
            paint: {
              "text-color": "#1e90ff",
              "text-halo-color": "#ffffff",
              "text-halo-width": 0.5
            }
          } as any);
          map.addLayer({
            id: "poi-unclustered",
            type: "symbol",
            source: srcId,
            filter: ["!has", "point_count"],
            layout: {
              "icon-image": "poi-pin",
              "icon-anchor": "bottom",
              "icon-allow-overlap": true,
              "icon-size": 1.0
            }
          } as any);
          map.addLayer({
            id: "poi-highlight",
            type: "circle",
            source: srcId,
            filter: ["all", ["!has", "point_count"], ["==", ["get", "id"], -1]],
            paint: {
              "circle-color": "#7c3aed",
              "circle-opacity": 0.2,
              "circle-radius": ["interpolate", ["linear"], ["zoom"], 8, 12, 16, 18, 20, 24]
            }
          } as any);

          map.on("click", "cluster-circles", (e: any) => {
            const features = map.queryRenderedFeatures(e.point, { layers: ["cluster-circles"] });
            const clusterId = features[0].properties.cluster_id;
            const src: any = map.getSource(srcId);
            src.getClusterExpansionZoom(clusterId, (err: any, zoom: number) => {
              if (err) return;
              map.easeTo({ center: (features[0].geometry as any).coordinates, zoom });
            });
          });

          map.on("click", "poi-unclustered", (e: any) => {
            const f = e.features && e.features[0];
            if (!f) return;
            const coords = (f.geometry as any).coordinates.slice();
            const name = f.properties.name;
            const category = f.properties.category;
            new maplibregl.Popup().setLngLat(coords).setText(`${name}${category ? ` (${category})` : ""}`).addTo(map);
            // set highlight
            const id = f.properties.id;
            if (map.getLayer("poi-highlight")) {
              map.setFilter("poi-highlight", ["all", ["!has", "point_count"], ["==", ["get", "id"], id]]);
            }
          });
        } else {
          (map.getSource(srcId) as any).setData(fc);
        }
      };
      if (map.isStyleLoaded && map.isStyleLoaded()) apply();
      else map.on("load", apply);
    } else {
      // 非クラスタ時は MapLibre のデフォルトマーカー（人と同じピン形状）で店舗を表示
      // 既存の POI マーカーをクリア
      Object.values(markersRef.current).forEach((m: any) => { try { m.remove(); } catch {} });
      markersRef.current = {};
      pois.forEach((p: Poi) => {
        const mk = new maplibregl.Marker({ color: "#1e90ff" as any })
          .setLngLat([p.lon, p.lat])
          .setPopup(new maplibregl.Popup().setText(`${p.name}${p.category ? ` (${p.category})` : ""}`))
          .addTo(map);
        markersRef.current[p.id] = mk;
      });
    }

    // BBox rectangle overlay
    if (bboxRect) {
      const [minLat, minLon, maxLat, maxLon] = bboxRect;
      const poly = {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: {},
            geometry: {
              type: "Polygon",
              coordinates: [[
                [minLon, minLat],
                [maxLon, minLat],
                [maxLon, maxLat],
                [minLon, maxLat],
                [minLon, minLat],
              ]],
            },
          },
        ],
      } as any;
      map.on("load", () => {
        if (!map.getSource("bbox-rect")) {
          map.addSource("bbox-rect", { type: "geojson", data: poly } as any);
          map.addLayer({
            id: "bbox-rect-fill",
            type: "fill",
            source: "bbox-rect",
            paint: { "fill-color": "#111214", "fill-opacity": 0.06 },
          } as any);
          map.addLayer({
            id: "bbox-rect-line",
            type: "line",
            source: "bbox-rect",
            paint: { "line-color": "#111214", "line-width": 2, "line-opacity": 0.7 },
          } as any);
        }
      });
    }

    // A-Bを結ぶライン
    if (personA && personB) {
      const lineGeojson: any = {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: {},
            geometry: {
              type: "LineString",
              coordinates: [
                [personA[1], personA[0]],
                [personB[1], personB[0]],
              ],
            },
          },
        ],
      };
      map.on("load", () => {
        if (!map.getSource("ab-line")) {
          map.addSource("ab-line", { type: "geojson", data: lineGeojson } as any);
          map.addLayer({
            id: "ab-line-layer",
            type: "line",
            source: "ab-line",
            paint: { "line-color": "#ff3b30", "line-width": 3, "line-opacity": 0.7 },
          } as any);
        }
      });
    }

    // すべての点が入るようにフィット
    const bounds = new maplibregl.LngLatBounds();
    const extend = (pt?: [number, number]) => {
      if (!pt) return;
      bounds.extend([pt[1], pt[0]]);
    };
    extend(personA);
    extend(personB);
    extend(midpoint);
    if (bboxRect) {
      const [minLat, minLon, maxLat, maxLon] = bboxRect;
      bounds.extend([minLon, minLat]);
      bounds.extend([maxLon, maxLat]);
    }
    pois.forEach((p) => bounds.extend([p.lon, p.lat]));
    if ((bounds as any)._ne && (bounds as any)._sw) {
      map.fitBounds(bounds, { padding: 80, duration: 600 });
    }

    return () => map.remove();
  }, [midpoint, pois, personA, personB, basemap, bboxRect, enableCluster]);

  // Drawing interaction: drag to set size around midpoint (center fixed)
  useEffect(() => {
    const map = mapRef.current;
    if (!map || !midpoint) return;

    const midLat = midpoint[0];
    const midLon = midpoint[1];

  const addOrUpdateDrawSource = (dLat: number, dLon: number) => {
      const poly = {
        type: "FeatureCollection",
        features: [
          {
            type: "Feature",
            properties: {},
            geometry: {
              type: "Polygon",
              coordinates: [[
                [midLon - dLon, midLat - dLat],
                [midLon + dLon, midLat - dLat],
                [midLon + dLon, midLat + dLat],
                [midLon - dLon, midLat + dLat],
                [midLon - dLon, midLat - dLat],
              ]],
            },
          },
        ],
      } as any;
      const srcId = "draw-rect";
      try {
        if (safeHasSource(map, srcId)) {
          (map.getSource(srcId) as any).setData(poly);
        } else if (map && map.addSource) {
          map.addSource(srcId, { type: "geojson", data: poly } as any);
          map.addLayer({ id: "draw-rect-fill", type: "fill", source: srcId, paint: { "fill-color": "#111214", "fill-opacity": 0.05 } } as any);
          map.addLayer({ id: "draw-rect-line", type: "line", source: srcId, paint: { "line-color": "#111214", "line-width": 2, "line-opacity": 0.6 } } as any);
        }
      } catch {
        // Style not ready yet; add on load once
        const once = () => {
          try {
            if (!safeHasSource(map, srcId)) {
              map.addSource(srcId, { type: "geojson", data: poly } as any);
              map.addLayer({ id: "draw-rect-fill", type: "fill", source: srcId, paint: { "fill-color": "#111214", "fill-opacity": 0.05 } } as any);
              map.addLayer({ id: "draw-rect-line", type: "line", source: srcId, paint: { "line-color": "#111214", "line-width": 2, "line-opacity": 0.6 } } as any);
            }
          } catch { /* ignore */ }
          map.off("load", once);
        };
        map.on("load", once);
      }
    };

    const clearDrawSource = () => {
      const srcId = "draw-rect";
      safeRemoveLayer(map, "draw-rect-fill");
      safeRemoveLayer(map, "draw-rect-line");
      safeRemoveSource(map, srcId);
    };

    const getEventLngLat = (e: any) => {
      if (e && e.lngLat) return e.lngLat;
      const p = e?.point || (e?.points && e.points[0]);
      try { return p ? map.unproject(p) : null; } catch { return null; }
    };

    const onMouseMove = (e: any) => {
      if (!drawActiveRef.current) return;
      const ll = getEventLngLat(e);
      if (!ll) return;
      const lon = ll.lng;
      const lat = ll.lat;
      const dLon = Math.abs(lon - midLon);
      const dLat = Math.abs(lat - midLat);
      drawStateRef.current = { dLat, dLon };
      addOrUpdateDrawSource(dLat, dLon);
    };

    const onMouseUp = () => {
      if (!drawActiveRef.current) return;
      drawActiveRef.current = false;
      map.getCanvas().style.cursor = "";
      map.dragPan.enable();
      const s = drawStateRef.current;
      if (s && s.dLat && s.dLon) {
        const bbox: [number, number, number, number] = [midLat - s.dLat, midLon - s.dLon, midLat + s.dLat, midLon + s.dLon];
        onBBoxDrawn && onBBoxDrawn(bbox);
      }
      // Clear preview; the final bbox will be rendered by bboxRect prop
      clearDrawSource();
      drawStateRef.current = null;
      map.off("mousemove", onMouseMove);
      map.off("mouseup", onMouseUp);
      map.off("touchmove", onMouseMove);
      map.off("touchend", onMouseUp);
    };

    const onMouseDown = (e: any) => {
      if (!enableDraw) return;
      const btn = e?.originalEvent?.button;
      if (typeof btn === 'number' && btn !== 0) return; // left button only for mouse; allow touch
      e.preventDefault();
      drawActiveRef.current = true;
      map.dragPan.disable();
      map.getCanvas().style.cursor = "crosshair";
      map.on("mousemove", onMouseMove);
      map.on("mouseup", onMouseUp);
      map.on("touchmove", onMouseMove);
      map.on("touchend", onMouseUp);
    };

    if (enableDraw) {
      map.on("mousedown", onMouseDown);
      map.on("touchstart", onMouseDown as any);
    }

    return () => {
      map.off("mousedown", onMouseDown);
      map.off("touchstart", onMouseDown as any);
      map.off("mousemove", onMouseMove);
      map.off("mouseup", onMouseUp);
      map.off("touchmove", onMouseMove);
      map.off("touchend", onMouseUp);
      clearDrawSource();
    };
  }, [enableDraw, midpoint]);

  // 外部から選択イベントを受け取り、地図上で強調＆移動
  useEffect(() => {
    const handler = (e: any) => {
      const id = e?.detail?.id as number | undefined;
      const map = mapRef.current;
      if (!id || !map) return;
      if (enableCluster) {
        // highlight via layer filter and flyTo
        if (map.getLayer("poi-highlight")) {
          map.setFilter("poi-highlight", ["all", ["!has", "point_count"], ["==", ["get", "id"], id]]);
        }
        // locate feature by id
        const features = (map.querySourceFeatures("pois-src") || []).filter((f: any) => !f.properties.point_count && f.properties.id === id);
        if (features[0]) {
          const coords = (features[0].geometry as any).coordinates;
          map.flyTo({ center: coords, zoom: Math.max(map.getZoom(), 15), duration: 600 });
        }
      } else {
        const mk = markersRef.current[id];
        if (!mk) return;
        const lngLat = mk.getLngLat();
        Object.entries(markersRef.current).forEach(([pid, m]) => { (m as any).getElement().style.filter = ""; });
        mk.getElement().style.filter = "hue-rotate(280deg) saturate(150%)";
        map.flyTo({ center: [lngLat.lng, lngLat.lat], zoom: Math.max(map.getZoom(), 15), duration: 600 });
        mk.togglePopup();
      }
    };
    window.addEventListener("poi-select", handler as any);
    return () => window.removeEventListener("poi-select", handler as any);
  }, [enableCluster]);

  return (
    <div ref={wrapperRef} style={{ position: "relative", width: "100%" }}>
      <div
        ref={mapContainer}
        // Tailwind未導入でも表示されるように明示的にサイズ指定
        style={{ width: "100%", height: "600px", borderRadius: 12, boxShadow: "0 2px 10px rgba(0,0,0,0.15)" }}
      />
    {toolbar ? (
        <div className="map-toolbar" style={{ position: 'absolute', top: 12, left: 12, display: 'flex', gap: 8, zIndex: 2 }}>
      {/* ドラッグON/OFFの切替ボタンは不要のため非表示 */}
          <button
            type="button"
            className="map-btn"
            onClick={() => onResetBBox && onResetBBox()}
            title="矩形をクリア"
            style={{ background: '#ffffff', color: '#111214', border: '1px solid #d9dde7', borderRadius: 8, padding: '8px 10px' }}
          >
            クリア
          </button>
          <button
            type="button"
            className="map-btn"
            onClick={() => {
              if (onRecenter) onRecenter();
              const map = mapRef.current;
              if (map && midpoint) {
                map.flyTo({ center: [midpoint[1], midpoint[0]], zoom: Math.max(map.getZoom(), 13), duration: 500 });
              }
            }}
            title="中間地点へ移動"
            style={{ background: '#ffffff', color: '#111214', border: '1px solid #d9dde7', borderRadius: 8, padding: '8px 10px' }}
          >
            中間地点
          </button>
        </div>
      ) : null}
      {loading ? (
        <div className="map-overlay" style={{ position: "absolute", inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', pointerEvents: 'none' }}>
          <div className="spinner" style={{ width: 28, height: 28, borderRadius: '50%', border: '3px solid #d9dde7', borderTopColor: '#111214', animation: 'spin 0.8s linear infinite' }} />
        </div>
      ) : null}
    </div>
  );
}
