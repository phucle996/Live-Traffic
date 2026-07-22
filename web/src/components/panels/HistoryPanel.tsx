"use client";

// ==============================================================================
// History Playback Panel Component (web/src/components/panels/HistoryPanel.tsx)
// Timeline Playback Slider (07:00 -> 23:00) & Historical Traffic Playback Controls
// ==============================================================================

import React, { useState, useEffect } from "react";

interface HistoryPanelProps {
  onTimeChange?: (timeHour: number, dateStr: string) => void;
}

export const HistoryPanel: React.FC<HistoryPanelProps> = ({ onTimeChange }) => {
  const [selectedDate, setSelectedDate] = useState<string>(() => {
    return new Date().toISOString().slice(0, 10);
  });
  const [selectedHour, setSelectedHour] = useState<number>(17); // Mặc định 17:00
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Playback timer loop tự động chuyển mốc thời gian mỗi 1.5 giây
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying) {
      interval = setInterval(() => {
        setSelectedHour((prev) => {
          if (prev >= 23) {
            setIsPlaying(false);
            return 7;
          }
          return prev + 1;
        });
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Trigger callback khi mốc thời gian thay đổi
  useEffect(() => {
    if (onTimeChange) {
      onTimeChange(selectedHour, selectedDate);
    }
  }, [selectedHour, selectedDate, onTimeChange]);

  const formatHourString = (hour: number) => {
    return `${hour.toString().padStart(2, "0")}:00`;
  };

  return (
    <div className="space-y-4">
      {/* Header Info */}
      <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-2xl">
        <h3 className="text-sm font-bold text-amber-400 flex items-center gap-1.5">
          <span>📜</span> Lịch Sử Giao Thông & Playback
        </h3>
        <p className="text-[11px] text-slate-400 mt-0.5">
          Xem lại diễn biến ùn tắc giao thông theo thời gian thực trong ngày.
        </p>
      </div>

      {/* Date Picker */}
      <div>
        <label className="text-[11px] font-semibold text-slate-300 block mb-1">
          Chọn Ngày Xem Lịch Sử:
        </label>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
          className="w-full py-2 px-3 bg-slate-800 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:ring-2 focus:ring-amber-500"
        />
      </div>

      {/* Timeline Slider Box */}
      <div className="p-4 bg-slate-800/80 rounded-2xl border border-slate-700 space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-xs text-slate-400">Mốc thời gian:</span>
          <span className="text-base font-extrabold text-amber-400 font-mono">
            {formatHourString(selectedHour)}
          </span>
        </div>

        {/* Range Slider (07:00 - 23:00) */}
        <input
          type="range"
          min={7}
          max={23}
          value={selectedHour}
          onChange={(e) => {
            setIsPlaying(false);
            setSelectedHour(parseInt(e.target.value, 10));
          }}
          className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-amber-500"
        />

        <div className="flex justify-between text-[10px] text-slate-400 font-mono">
          <span>07:00</span>
          <span>12:00</span>
          <span>17:00</span>
          <span>23:00</span>
        </div>

        {/* Playback Controls */}
        <div className="pt-2 flex space-x-2">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`flex-1 py-2 text-xs font-bold rounded-xl transition shadow flex items-center justify-center space-x-1 ${
              isPlaying
                ? "bg-amber-600 hover:bg-amber-700 text-white"
                : "bg-blue-600 hover:bg-blue-700 text-white"
            }`}
          >
            <span>{isPlaying ? "⏸ Tạm Dừng Playback" : "▶ Phát Playback (07:00 - 23:00)"}</span>
          </button>
          <button
            onClick={() => {
              setIsPlaying(false);
              setSelectedHour(7);
            }}
            className="px-3 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 text-xs font-medium rounded-xl transition"
          >
            🔄 Reset
          </button>
        </div>
      </div>
    </div>
  );
};
