// ==============================================================================
// Health Handlers (crates/traffic-api/src/handlers/health.rs)
// Liveness & Readiness Probes for Kubernetes / Cloud-Native Orchestration
// ==============================================================================

use crate::state::AppState;
use axum::extract::State;
use axum::http::StatusCode;
use axum::response::IntoResponse;
use axum::Json;
use serde_json::json;
use std::sync::atomic::Ordering;

/// Liveness Probe Endpoint: Trả về 200 OK nếu server process đang hoạt động
pub async fn liveness_handler() -> impl IntoResponse {
    (
        StatusCode::OK,
        Json(json!({
            "status": "UP",
            "service": "rust-traffic-inference-api"
        })),
    )
}

/// Readiness Probe Endpoint: Trả về 200 OK sau khi Model Warmup hoàn tất, trả 503 nếu Unready
pub async fn readiness_handler(State(state): State<AppState>) -> impl IntoResponse {
    let ready = state.is_ready.load(Ordering::SeqCst);
    if ready {
        (
            StatusCode::OK,
            Json(json!({
                "status": "READY",
                "model_loaded": true
            })),
        )
    } else {
        (
            StatusCode::SERVICE_UNAVAILABLE,
            Json(json!({
                "status": "UNREADY",
                "model_loaded": false,
                "reason": "Model warmup in progress"
            })),
        )
    }
}
