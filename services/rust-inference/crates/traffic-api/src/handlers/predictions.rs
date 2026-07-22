// ==============================================================================
// Prediction Handlers (crates/traffic-api/src/handlers/predictions.rs)
// High-Performance Single & Batch Real-Time Inference Handlers
// ==============================================================================

use crate::feature_builder::RustFeatureBuilder;
use crate::state::AppState;
use axum::extract::State;
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::Json;
use serde::Deserialize;

use serde_json::json;

/// Payload Yêu cầu dự đoán đơn lẻ (Single Prediction Input Payload)
#[derive(Debug, Clone, Deserialize)]
pub struct SinglePredictionInput {
    pub latitude: f64,
    pub longitude: f64,
    pub free_flow_speed: Option<f64>,
    pub confidence: Option<f64>,
    pub timestamp: Option<String>,
    pub street_name: Option<String>,
}

/// Payload Yêu cầu dự đoán hàng loạt (Batch Prediction Input Payload)
#[derive(Debug, Clone, Deserialize)]
pub struct BatchPredictionInput {
    pub records: Vec<SinglePredictionInput>,
}

/// Single Prediction Endpoint: Dự đoán tốc độ xe cho 1 vị trí đơn lẻ
pub async fn single_predict_handler(
    State(state): State<AppState>,
    Json(payload): Json<SinglePredictionInput>,
) -> impl IntoResponse {
    let model_guard = state.model.load();
    let manifest_guard = state.manifest.load();

    let model_version = manifest_guard["model_version"]
        .as_str()
        .unwrap_or("v1.0.0")
        .to_string();

    let ff_speed = payload.free_flow_speed.unwrap_or(45.0);
    let conf = payload.confidence.unwrap_or(0.95);

    // Xây dựng feature vector chuẩn cho Native Tree Engine
    let feat_vec = RustFeatureBuilder::build_feature_vector(
        payload.latitude,
        payload.longitude,
        ff_speed,
        conf,
        payload.timestamp.as_deref(),
        &model_guard.feature_names,
    );

    // Thực thi suy luận bằng Native Rust Tree Engine
    let raw_pred = model_guard.predict_single(&feat_vec);
    let predicted_speed = raw_pred.clamp(0.0, ff_speed * 1.2);

    // Phân loại mức độ ùn tắc giao thông (Congestion Level)
    let ratio = predicted_speed / ff_speed;
    let congestion = if ratio < 0.35 {
        "HEAVY_CONGESTION"
    } else if ratio < 0.70 {
        "MODERATE_CONGESTION"
    } else {
        "SMOOTH_FLOW"
    };

    let response = json!({
        "street_name": payload.street_name.unwrap_or_else(|| "Tuyến đường HCMC".to_string()),
        "latitude": payload.latitude,
        "longitude": payload.longitude,
        "predicted_speed_kmh": (predicted_speed * 100.0).round() / 100.0,
        "free_flow_speed_kmh": ff_speed,
        "congestion_level": congestion,
        "model_version": model_version,
        "data_source": "rust_native_tree_engine",
        "timestamp": chrono::Local::now().to_rfc3339()
    });

    (StatusCode::OK, Json(response))
}

/// Batch Prediction Endpoint: Dự đoán hàng loạt cho danh sách bản ghi
pub async fn batch_predict_handler(
    State(state): State<AppState>,
    Json(payload): Json<BatchPredictionInput>,
) -> impl IntoResponse {
    // Giới hạn tối đa 5.000 bản ghi/request để phòng chống OOM DoS
    if payload.records.len() > 5000 {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({
                "error": "Batch size exceeds maximum limit of 5000 records"
            })),
        );
    }

    let model_guard = state.model.load();
    let manifest_guard = state.manifest.load();

    let model_version = manifest_guard["model_version"]
        .as_str()
        .unwrap_or("v1.0.0")
        .to_string();

    let mut batch_vectors = Vec::with_capacity(payload.records.len());
    for item in &payload.records {
        let ff_speed = item.free_flow_speed.unwrap_or(45.0);
        let conf = item.confidence.unwrap_or(0.95);

        let vec = RustFeatureBuilder::build_feature_vector(
            item.latitude,
            item.longitude,
            ff_speed,
            conf,
            item.timestamp.as_deref(),
            &model_guard.feature_names,
        );
        batch_vectors.push(vec);
    }

    // Dự đoán hàng loạt đa luồng qua Rayon
    let predictions = model_guard.predict_batch(&batch_vectors);

    let mut results = Vec::with_capacity(predictions.len());
    for (i, raw_pred) in predictions.into_iter().enumerate() {
        let item = &payload.records[i];
        let ff_speed = item.free_flow_speed.unwrap_or(45.0);
        let predicted_speed = raw_pred.clamp(0.0, ff_speed * 1.2);

        results.push(json!({
            "record_id": i + 1,
            "latitude": item.latitude,
            "longitude": item.longitude,
            "predicted_speed_kmh": (predicted_speed * 100.0).round() / 100.0,
            "model_version": model_version
        }));
    }

    (
        StatusCode::OK,
        Json(json!({
            "count": results.len(),
            "model_version": model_version,
            "predictions": results
        })),
    )
}
