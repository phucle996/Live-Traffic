// ==============================================================================
// Rust Feature Builder (crates/traffic-api/src/feature_builder.rs)
// Maps Incoming Business Requests to Ordered f64 Feature Vectors
// ==============================================================================

use chrono::{Datelike, Timelike};
use std::collections::HashMap;

/// Rust Feature Builder giúp trích xuất và biến đổi đặc trưng thời gian và không gian
pub struct RustFeatureBuilder;

impl RustFeatureBuilder {
    /// Danh sách các cột đặc trưng chuẩn theo Single Source of Truth (SOT)
    pub fn feature_cols() -> Vec<&'static str> {
        vec![
            "Latitude",
            "Longitude",
            "FreeFlowSpeed",
            "Confidence",
            "Hour",
            "Minute",
            "TimeInMinutes",
            "DayOfWeek",
            "Weekend",
        ]
    }

    /// Trích xuất vector f64 theo thứ tự tên cột `target_features` của model
    pub fn build_feature_vector(
        lat: f64,
        lon: f64,
        free_flow_speed: f64,
        confidence: f64,
        dt_str: Option<&str>,
        target_features: &[String],
    ) -> Vec<f64> {
        // Parsing thời gian từ datetime string hoặc lấy thời gian hiện tại
        let now = chrono::Local::now();
        let (hour, minute, day_of_week) = if let Some(ts) = dt_str {
            if let Ok(parsed) = chrono::NaiveDateTime::parse_from_str(ts, "%Y-%m-%d %H:%M:%S") {
                (
                    parsed.hour() as f64,
                    parsed.minute() as f64,
                    parsed.weekday().num_days_from_monday() as f64,
                )
            } else {
                (
                    now.hour() as f64,
                    now.minute() as f64,
                    now.weekday().num_days_from_monday() as f64,
                )
            }
        } else {
            (
                now.hour() as f64,
                now.minute() as f64,
                now.weekday().num_days_from_monday() as f64,
            )
        };

        let time_in_minutes = hour * 60.0 + minute;
        let is_weekend = if day_of_week >= 5.0 { 1.0 } else { 0.0 };

        // HashMap lưu cặp khóa-giá trị đặc trưng
        let mut feat_map = HashMap::new();
        feat_map.insert("Latitude", lat);
        feat_map.insert("Longitude", lon);
        feat_map.insert("FreeFlowSpeed", free_flow_speed);
        feat_map.insert("Confidence", confidence);
        feat_map.insert("Hour", hour);
        feat_map.insert("Minute", minute);
        feat_map.insert("TimeInMinutes", time_in_minutes);
        feat_map.insert("DayOfWeek", day_of_week);
        feat_map.insert("Weekend", is_weekend);

        // Duyệt theo thứ tự `target_features` của model
        target_features
            .iter()
            .map(|fname| *feat_map.get(fname.as_str()).unwrap_or(&0.0))
            .collect()
    }
}
