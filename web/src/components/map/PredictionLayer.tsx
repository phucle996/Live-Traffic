"use client";

// ==============================================================================
// Prediction Layer Component (web/src/components/map/PredictionLayer.tsx)
// MapLibre GL JS Model Prediction Layer Rendering
// Distinct Diamond Symbol Markers (◆) for Model Predictions vs Circles (●) for Live
// ==============================================================================

import React, { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import { PredictionResponse } from "@/api/predictionClient";

export interface PredictionMarkerData extends PredictionResponse {
  latitude: number;
  longitude: number;
}

interface PredictionLayerProps {
  map: maplibregl.Map | null;
  predictions: PredictionMarkerData[];
}

export const PredictionLayer: React.FC<PredictionLayerProps> = ({ map, predictions }) => {
  const markersRef = useRef<maplibregl.Marker[]>([]);

  useEffect(() => {
    if (!map) return;

    // 1. Dọn dẹp các Marker Prediction cũ
    markersRef.current.forEach((m) => m.remove());
    markersRef.current = [];

    // 2. Render các Marker hình thoi (◆) cho Model Predictions
    predictions.forEach((pred) => {
      let color = "#22c55e"; // 🟢 Xanh
      if (pred.predicted_speed_kmh < 20) color = "#ef4444"; // 🔴 Đỏ
      else if (pred.predicted_speed_kmh < 35) color = "#eab308"; // 🟡 Vàng

      // Tạo HTML Element hình thoi (◆ Diamond Symbol)
      const el = document.createElement("div");
      el.className = "prediction-marker-diamond";
      el.style.width = "18px";
      el.style.height = "18px";
      el.style.backgroundColor = color;
      el.style.transform = "rotate(45deg)"; // Xoay 45 độ tạo hình thoi ◆
      el.style.border = "2px solid #ffffff";
      el.style.boxShadow = `0 0 12px ${color}`;
      el.style.cursor = "pointer";

      const popup = new maplibregl.Popup({ offset: 14, closeButton: false }).setHTML(`
        <div style="font-family:Inter,sans-serif;padding:4px">
          <div style="font-size:10px;font-weight:bold;color:#64748b">◆ AI MODEL PREDICTION</div>
          <b style="color:#0f172a;font-size:13px">${pred.street_name}</b><br/>
          Tốc độ dự đoán: <b style="color:${color};font-size:14px">${pred.predicted_speed_kmh.toFixed(1)} km/h</b><br/>
          <span style="font-size:10px;color:#64748b">Model: <code>${pred.model_version}</code></span>
        </div>
      `);

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([pred.longitude, pred.latitude])
        .setPopup(popup)
        .addTo(map);

      markersRef.current.push(marker);
    });

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
    };
  }, [map, predictions]);

  return null;
};
