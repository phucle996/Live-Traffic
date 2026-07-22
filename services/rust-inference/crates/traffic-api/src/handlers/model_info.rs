// ==============================================================================
// Model Info & Hot Reload Handlers (crates/traffic-api/src/handlers/model_info.rs)
// Inspect Model Metadata & Trigger Zero-Downtime Atomic Hot Reload
// ==============================================================================

use crate::state::AppState;
use axum::extract::State;
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::Json;
use serde_json::json;

/// Get Model Info Endpoint: Trả về thông tin Metadata của mô hình hiện tại
pub async fn get_model_info_handler(State(state): State<AppState>) -> impl IntoResponse {
    let manifest_guard = state.manifest.load();
    let model_guard = state.model.load();

    let response = json!({
        "manifest": **manifest_guard,
        "num_trees": model_guard.num_trees,
        "feature_names": model_guard.feature_names,
        "status": "ACTIVE_PRODUCTION"
    });

    (StatusCode::OK, Json(response))
}

/// Hot Reload Endpoint: Thực hiện Atomic Swap nạp mô hình mới không gián đoạn dịch vụ
pub async fn reload_model_handler(State(state): State<AppState>) -> impl IntoResponse {
    match state.reload_model().await {
        Ok(_) => (
            StatusCode::OK,
            Json(json!({
                "status": "SUCCESS",
                "message": "Atomic Model Hot Reload complete!"
            })),
        ),
        Err(err) => (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(json!({
                "status": "FAILED",
                "error": err.to_string(),
                "message": "Giữ nguyên mô hình hiện tại do nạp mô hình mới thất bại!"
            })),
        ),
    }
}
