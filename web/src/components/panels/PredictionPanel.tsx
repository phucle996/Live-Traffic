"use client";

// ==============================================================================
// Prediction Form Panel Component (web/src/components/panels/PredictionPanel.tsx)
// Target Date/Time Picker, District Filter & Rust AI Engine Model Runner Controls
// Live vs Model Prediction Comparison & Model Version Metadata Display
// ==============================================================================

import React, { useState } from "react";
import { PredictionResponse } from "@/api/predictionClient";

interface PredictionPanelProps {
  onRunBatchPrediction: (datetimeStr: string, district: string) => void;
  isLoading: boolean;
  modelPredictionResult?: PredictionResponse | null;
  liveSpeed?: number | null;
}

export const PredictionPanel: React.FC<PredictionPanelProps> = ({
  onRunBatchPrediction,
  isLoading,
  modelPredictionResult,
  liveSpeed,
}) => {
  // Mặc định chọn thời gian hiện tại
  const [predictionTime, setPredictionTime] = useState<string>(() => {
    const now = new Date();
    now.setMinutes(now.getMinutes() + 30); // Dự đoán 30 phút tới
    return now.toISOString().slice(0, 16);
  });
  const [selectedDistrict, setSelectedDistrict] = useState<string>("ALL");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onRunBatchPrediction(predictionTime, selectedDistrict);
  };

  return (
    <div className="space-y-4">
      {/* Header Info */}
      <div className="p-3 bg-blue-600/10 border border-blue-500/30 rounded-2xl">
        <h3 className="text-sm font-bold text-blue-400 flex items-center gap-1.5">
          <span>🤖</span> AI Model Prediction Engine
        </h3>
        <p className="text-[11px] text-slate-400 mt-0.5">
          Dự đoán vận tốc & ùn tắc giao thông sử dụng Mô hình GBTRegressor trên Rust Inference Engine.
        </p>
      </div>

      {/* Prediction Configuration Form */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label className="text-[11px] font-semibold text-slate-300 block mb-1">
            Ngày & Giờ Dự Đoán:
          </label>
          <input
            type="datetime-local"
            value={predictionTime}
            onChange={(e) => setPredictionTime(e.target.value)}
            className="w-full py-2 px-3 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="text-[11px] font-semibold text-slate-300 block mb-1">
            Khu vực / Quận:
          </label>
          <select
            value={selectedDistrict}
            onChange={(e) => setSelectedDistrict(e.target.value)}
            className="w-full py-2 px-3 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="ALL">Tất cả khu vực TP.HCM</option>
            <option value="Quận 1">Quận 1</option>
            <option value="Quận 3">Quận 3</option>
            <option value="Quận 5">Quận 5</option>
            <option value="Bình Thạnh">Quận Bình Thạnh</option>
            <option value="Quận 7">Quận 7</option>
          </select>
        </div>

        <button
          type="submit"
          disabled={isLoading}
          className="w-full py-2.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl transition shadow-lg flex items-center justify-center space-x-2"
        >
          {isLoading ? (
            <span>⏳ Đang thực thi suy luận Rust Engine...</span>
          ) : (
            <>
              <span>🚀</span>
              <span>Chạy Dự Đoán Mô Hình AI</span>
            </>
          )}
        </button>
      </form>

      {/* Comparison Results Card */}
      {modelPredictionResult && (
        <div className="p-4 bg-slate-800/80 rounded-2xl border border-slate-700 space-y-3">
          <div className="flex items-center justify-between border-b border-slate-700 pb-2">
            <span className="text-xs font-bold text-slate-200">KẾT QUẢ SO SÁNH</span>
            <span className="text-[10px] px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded font-mono">
              ◆ Model Prediction
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div className="p-2.5 bg-slate-900/60 rounded-xl border border-slate-800">
              <span className="text-[10px] text-slate-400 block">● Live Thực tế</span>
              <span className="text-sm font-bold text-slate-200">
                {liveSpeed ? `${liveSpeed.toFixed(1)} km/h` : "--"}
              </span>
            </div>
            <div className="p-2.5 bg-slate-900/60 rounded-xl border border-slate-800">
              <span className="text-[10px] text-blue-400 block">◆ AI Dự đoán</span>
              <span className="text-sm font-extrabold text-blue-400">
                {modelPredictionResult.predicted_speed_kmh.toFixed(1)} km/h
              </span>
            </div>
          </div>

          {/* Model Version Metadata */}
          <div className="pt-2 text-[10px] text-slate-400 space-y-1 border-t border-slate-700/50">
            <div className="flex justify-between">
              <span>Model Version:</span>
              <code className="text-blue-300">{modelPredictionResult.model_version}</code>
            </div>
            <div className="flex justify-between">
              <span>Inference Engine:</span>
              <span className="text-slate-300">{modelPredictionResult.data_source}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
