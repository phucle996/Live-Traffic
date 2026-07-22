// ==============================================================================
// Traffic REST Serving API Main Entry (crates/traffic-api/src/main.rs)
// High-Availability Axum + Tokio Cloud-Native Prediction Server (Sub-ms Latency)
// ==============================================================================

// Đã gỡ bỏ mod auth (Hệ thống chạy Public High-Performance AI Inference)
mod feature_builder;
mod handlers;
mod metrics;
mod middleware;
mod state;

use anyhow::Result;
use axum::{
    middleware::from_fn,
    routing::{get, post},
    Router,
};
use std::net::SocketAddr;
use std::path::PathBuf;
use tracing::info;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

use handlers::{health, model_info, predictions};
use middleware::request_id::request_id_middleware;
use state::AppState;
use tower_http::cors::CorsLayer;

// Import metrics gather handler cho Prometheus scraping
use metrics::metrics_handler;

#[tokio::main]
async fn main() -> Result<()> {
    // 1. Khởi tạo Tracing Logger (Structured JSON Logging)
    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::new(
            std::env::var("RUST_LOG").unwrap_or_else(|_| "info,traffic_api=debug".into()),
        ))
        .with(tracing_subscriber::fmt::layer())
        .init();

    info!("Starting Cloud-Native Rust Traffic Inference API Service...");

    // Khởi tạo Prometheus Metrics Registry trước khi Router được khởi động
    metrics::init_metrics();
    info!("[METRICS] Prometheus metrics registry đã được khởi tạo thành công.");

    // 2. Tìm thư mục chứa model artifacts (Hỗ trợ env MODEL_DIR, local cargo run, và Docker container)
    let model_dir = std::env::var("MODEL_DIR")
        .map(PathBuf::from)
        .unwrap_or_else(|_| {
            let mut root = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
            while !root.join("artifacts").exists() && root.parent().is_some() {
                root = root.parent().unwrap().to_path_buf();
            }
            if root.join("artifacts").exists() {
                root.join("artifacts/inference/candidate-tree")
            } else {
                PathBuf::from("/app/artifacts/inference/candidate-tree")
            }
        });


    // 3. Khởi tạo AppState & thực hiện Model Warmup
    let state = AppState::new(&model_dir).await?;
    state.warmup().await;

    // 4. Cấu hình Axum Routing Table cho Public High-Performance AI Inference
    let app = Router::new()
        // Health Probes (Kubernetes Liveness & Readiness)
        .route("/health/live", get(health::liveness_handler))
        .route("/health/ready", get(health::readiness_handler))
        
        // Model Metadata Endpoint (Public Access cho Web Dashboard)
        .route("/v1/model", get(model_info::get_model_info_handler))
        .route("/v1/model/reload", post(model_info::reload_model_handler))
        
        // High-Speed Prediction Endpoints (Public Access không bắt buộc JWT Auth Token)
        .route("/v1/predictions", post(predictions::single_predict_handler))
        .route("/v1/predictions/batch", post(predictions::batch_predict_handler))
        
        // Prometheus Metrics Scraper Endpoint
        .route("/metrics", get(metrics_handler))
        
        // Attach Global Middlewares (CORS Permissive & Request-ID Generator)
        .layer(CorsLayer::permissive())
        .layer(from_fn(request_id_middleware))

        .with_state(state);

    // 5. Khởi chạy HTTP Server trên Port 8080 (hoặc PORT env)
    let port: u16 = std::env::var("PORT")
        .unwrap_or_else(|_| "8080".to_string())
        .parse()
        .unwrap_or(8080);

    let addr = SocketAddr::from(([0, 0, 0, 0], port));
    info!("[SUCCESS] Traffic REST Serving API running on http://{}", addr);

    // 6. Xử lý Graceful Shutdown khi nhận tín hiệu SIGINT / SIGTERM
    let listener = tokio::net::TcpListener::bind(addr).await?;
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown_signal())
        .await?;

    info!("Traffic API Server shut down gracefully.");
    Ok(())
}

/// Lắng nghe tín hiệu dừng Ctrl+C / SIGTERM để Shutdown server an toàn
async fn shutdown_signal() {
    let ctrl_c = async {
        tokio::signal::ctrl_c()
            .await
            .expect("Không thể khởi tạo handler lắng nghe Ctrl+C");
    };

    #[cfg(unix)]
    let terminate = async {
        tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("Không thể khởi tạo handler SIGTERM")
            .recv()
            .await;
    };

    #[cfg(not(unix))]
    let terminate = std::future::pending::<()>();

    tokio::select! {
        _ = ctrl_c => info!("Received Ctrl+C signal. Initiating graceful shutdown..."),
        _ = terminate => info!("Received SIGTERM signal. Initiating graceful shutdown..."),
    }
}
