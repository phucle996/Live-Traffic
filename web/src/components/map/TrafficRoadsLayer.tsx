"use client";

// ==============================================================================
// Traffic Roads Layer Component (web/src/components/map/TrafficRoadsLayer.tsx)
// Renders Google Maps-style Colored Road Polylines (GeoJSON LineString)
// on MapLibre GL JS based on Real-Time Speed Data from Go Live API
// Clickable Road Segments → LocationDetails Panel Integration
// ==============================================================================

import React, { useEffect } from "react";
import maplibregl from "maplibre-gl";
import { LiveTrafficRecord } from "@/api/liveTrafficClient";

// Định nghĩa hướng tuyến đường xấp xỉ cho các điểm quan sát TP.HCM
// [lon_start, lat_start, lon_end, lat_end] — đoạn ~300m biểu thị hướng đường
const ROAD_GEOMETRY: Record<string, [number, number, number, number]> = {
  "Chợ Bến Thành":         [106.6970, 10.7727, 106.6990, 10.7727],
  "Đường Nguyễn Huệ":      [106.7030, 10.7730, 106.7042, 10.7750],
  "Ngã tư Hàng Xanh":      [106.7095, 10.8004, 106.7135, 10.8024],
  "Đường Điện Biên Phủ":   [106.6935, 10.7877, 106.6975, 10.7897],
  "Võ Văn Kiệt":           [106.6503, 10.7448, 106.6563, 10.7468],
  "Xa lộ Hà Nội":          [106.8680, 10.9483, 106.8760, 10.9503],
  "Ngã tư An Sương":       [106.6121, 10.8422, 106.6181, 10.8442],
  "Cầu Sài Gòn":           [106.7250, 10.7980, 106.7290, 10.8000],
  "Cách Mạng Tháng 8":     [106.6748, 10.7780, 106.6788, 10.7800],
  "Phạm Văn Đồng":         [106.7274, 10.8343, 106.7314, 10.8363],
  "Nguyễn Văn Linh":       [106.7231, 10.7516, 106.7271, 10.7536],
  "Phú Mỹ Hưng":           [106.7261, 10.7218, 106.7301, 10.7238],
};

// Tính màu sắc theo tốc độ thực tế / tốc độ tự do
function getSpeedColor(speed: number, freeFlowSpeed: number): string {
  const ratio = speed / (freeFlowSpeed || 45);
  if (ratio >= 0.75) return "#22c55e";   // 🟢 Thông thoáng
  if (ratio >= 0.45) return "#eab308";   // 🟡 Đông xe
  return "#ef4444";                       // 🔴 Ùn tắc
}

interface TrafficRoadsLayerProps {
  map: maplibregl.Map | null;
  records: LiveTrafficRecord[];
  onSelectRoad: (record: LiveTrafficRecord) => void;
}

export const TrafficRoadsLayer: React.FC<TrafficRoadsLayerProps> = ({
  map,
  records,
  onSelectRoad,
}) => {
  const SOURCE_ID = "traffic-roads-source";
  const LAYER_ID  = "traffic-roads-layer";
  const LAYER_CLICK_ID = "traffic-roads-click";

  useEffect(() => {
    if (!map || records.length === 0) return;

    // 1. Xây dựng GeoJSON FeatureCollection từ danh sách LiveTrafficRecord
    const features: GeoJSON.Feature<GeoJSON.LineString>[] = records.map((rec) => {
      const geo = ROAD_GEOMETRY[rec.location_name];

      // Nếu có geometry cố định ➔ dùng; nếu không ➔ tạo đoạn ngang 200m từ tọa độ
      const coords: [number, number][] = geo
        ? [
            [geo[0], geo[1]],
            [geo[2], geo[3]],
          ]
        : [
            [rec.longitude - 0.001, rec.latitude],
            [rec.longitude + 0.001, rec.latitude],
          ];

      return {
        type: "Feature",
        properties: {
          location_id:    rec.location_id,
          location_name:  rec.location_name,
          district:       rec.district,
          current_speed:  rec.current_speed,
          free_flow_speed: rec.free_flow_speed,
          confidence:     rec.confidence,
          observed_at:    rec.observed_at,
          data_age_seconds: rec.data_age_seconds,
          source:         rec.source,
          latitude:       rec.latitude,
          longitude:      rec.longitude,
          color:          getSpeedColor(rec.current_speed, rec.free_flow_speed),
        },
        geometry: {
          type: "LineString",
          coordinates: coords,
        },
      };
    });

    const geojson: GeoJSON.FeatureCollection<GeoJSON.LineString> = {
      type: "FeatureCollection",
      features,
    };

    // 2. Nếu source đã tồn tại ➔ cập nhật data, không tạo lại
    if (map.getSource(SOURCE_ID)) {
      (map.getSource(SOURCE_ID) as maplibregl.GeoJSONSource).setData(geojson);
      return;
    }

    // 3. Thêm GeoJSON Source
    map.addSource(SOURCE_ID, {
      type: "geojson",
      data: geojson,
    });

    // 4. Thêm Layer bóng (shadow line rộng hơn, trắng trong suốt) để tăng vùng click
    map.addLayer({
      id: LAYER_CLICK_ID,
      type: "line",
      source: SOURCE_ID,
      layout: {
        "line-cap": "round",
        "line-join": "round",
      },
      paint: {
        "line-color": "rgba(255,255,255,0)",
        "line-width": 24,  // Vùng click rộng 24px để dễ chọn
      },
    });

    // 5. Thêm Layer đường chính tô màu theo tốc độ
    map.addLayer({
      id: LAYER_ID,
      type: "line",
      source: SOURCE_ID,
      layout: {
        "line-cap": "round",
        "line-join": "round",
      },
      paint: {
        "line-color":   ["get", "color"],
        "line-width":   8,
        "line-opacity": 0.92,
        // Glow effect: outer shadow
        "line-blur":    0.5,
      },
    });

    // 6. Đăng ký sự kiện click trên vùng click (LAYER_CLICK_ID)
    map.on("click", LAYER_CLICK_ID, (e) => {
      const feature = e.features?.[0];
      if (!feature?.properties) return;

      // Dựng lại LiveTrafficRecord từ GeoJSON properties
      const props = feature.properties;
      const record: LiveTrafficRecord = {
        location_id:     props.location_id,
        location_name:   props.location_name,
        district:        props.district,
        current_speed:   props.current_speed,
        free_flow_speed: props.free_flow_speed,
        confidence:      props.confidence,
        observed_at:     props.observed_at,
        data_age_seconds: props.data_age_seconds,
        source:          props.source,
        latitude:        props.latitude,
        longitude:       props.longitude,
      };

      onSelectRoad(record);
    });

    // 7. Thay đổi con trỏ chuột khi hover đường
    map.on("mouseenter", LAYER_CLICK_ID, () => {
      map.getCanvas().style.cursor = "pointer";
    });
    map.on("mouseleave", LAYER_CLICK_ID, () => {
      map.getCanvas().style.cursor = "";
    });
  }, [map, records, onSelectRoad]);

  // Dọn dẹp khi component unmount
  useEffect(() => {
    return () => {
      if (!map) return;
      try {
        if (map.getLayer(LAYER_ID))       map.removeLayer(LAYER_ID);
        if (map.getLayer(LAYER_CLICK_ID)) map.removeLayer(LAYER_CLICK_ID);
        if (map.getSource(SOURCE_ID))     map.removeSource(SOURCE_ID);
      } catch (_) {}
    };
  }, [map]);

  return null; // Không render gì — MapLibre GL JS quản lý DOM của Canvas
};
