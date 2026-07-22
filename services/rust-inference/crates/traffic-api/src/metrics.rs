// ==============================================================================
// Rust Prometheus Metrics Collector (src/metrics.rs)
// Khai báo các Prometheus Counters, Histograms, Gauges cho Rust Inference API
// ==============================================================================

use axum::http::StatusCode;
use axum::response::{IntoResponse, Response};
use prometheus::{
    register_counter, register_gauge, register_histogram, Counter, Encoder, Gauge, Histogram,
    TextEncoder,
};
use std::sync::OnceLock;

// Prometheus metric registry singletons (OnceLock đảm bảo chỉ khởi tạo một lần duy nhất)
static INFERENCE_REQUESTS: OnceLock<Counter> = OnceLock::new();
static INFERENCE_ERRORS: OnceLock<Counter> = OnceLock::new();
static INFERENCE_DURATION: OnceLock<Histogram> = OnceLock::new();
static MODEL_RELOAD_TOTAL: OnceLock<Counter> = OnceLock::new();
static ACTIVE_MODEL_VERSION: OnceLock<Gauge> = OnceLock::new();

// In-Memory Model Telemetry Metrics
static MODEL_FILE_SIZE_BYTES: OnceLock<Gauge> = OnceLock::new();
static PARSED_MODEL_RAM_BYTES: OnceLock<Gauge> = OnceLock::new();
static MODEL_LOAD_DURATION_SECONDS: OnceLock<Gauge> = OnceLock::new();
static WARM_PREDICTION_LATENCY_SECONDS: OnceLock<Gauge> = OnceLock::new();

/// Khởi tạo tất cả Prometheus metrics khi service khởi động.
pub fn init_metrics() {
    INFERENCE_REQUESTS.get_or_init(|| {
        register_counter!(
            "inference_requests_total",
            "Tổng số yêu cầu suy luận mô hình AI đã nhận"
        )
        .expect("Không thể đăng ký counter inference_requests_total")
    });

    INFERENCE_ERRORS.get_or_init(|| {
        register_counter!(
            "inference_errors_total",
            "Tổng số lỗi trong quá trình suy luận mô hình"
        )
        .expect("Không thể đăng ký counter inference_errors_total")
    });

    INFERENCE_DURATION.get_or_init(|| {
        register_histogram!(
            "inference_duration_seconds",
            "Phân phối thời gian suy luận mô hình (giây)",
            vec![0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1]
        )
        .expect("Không thể đăng ký histogram inference_duration_seconds")
    });

    MODEL_RELOAD_TOTAL.get_or_init(|| {
        register_counter!(
            "model_reload_total",
            "Tổng số lần model hot reload được thực thi thành công"
        )
        .expect("Không thể đăng ký counter model_reload_total")
    });

    ACTIVE_MODEL_VERSION.get_or_init(|| {
        register_gauge!(
            "active_model_version",
            "Nhãn phiên bản mô hình đang được kích hoạt trong RAM"
        )
        .expect("Không thể đăng ký gauge active_model_version")
    });

    MODEL_FILE_SIZE_BYTES.get_or_init(|| {
        register_gauge!(
            "model_file_size_bytes",
            "Kích thước file mô hình model.json trên đĩa (bytes)"
        )
        .expect("Không thể đăng ký gauge model_file_size_bytes")
    });

    PARSED_MODEL_RAM_BYTES.get_or_init(|| {
        register_gauge!(
            "parsed_model_ram_bytes",
            "Dung lượng RAM chiếm dụng của mô hình GBT sau khi parse thành flat array (bytes)"
        )
        .expect("Không thể đăng ký gauge parsed_model_ram_bytes")
    });

    MODEL_LOAD_DURATION_SECONDS.get_or_init(|| {
        register_gauge!(
            "model_load_duration_seconds",
            "Thời gian nạp và parse mô hình vào RAM (giây)"
        )
        .expect("Không thể đăng ký gauge model_load_duration_seconds")
    });

    WARM_PREDICTION_LATENCY_SECONDS.get_or_init(|| {
        register_gauge!(
            "warm_prediction_latency_seconds",
            "Độ trễ suy luận trung bình đo được trong quá trình warmup (giây)"
        )
        .expect("Không thể đăng ký gauge warm_prediction_latency_seconds")
    });
}

/// Ghi nhận yêu cầu suy luận thành công với độ trễ đo được.
pub fn record_inference_request(duration_ms: f64) {
    if let Some(ctr) = INFERENCE_REQUESTS.get() {
        ctr.inc();
    }
    if let Some(hist) = INFERENCE_DURATION.get() {
        hist.observe(duration_ms / 1000.0);
    }
}

/// Ghi nhận lỗi trong quá trình suy luận.
pub fn record_inference_error() {
    if let Some(ctr) = INFERENCE_ERRORS.get() {
        ctr.inc();
    }
}

/// Ghi nhận sự kiện hot reload mô hình thành công.
pub fn record_model_reload() {
    if let Some(ctr) = MODEL_RELOAD_TOTAL.get() {
        ctr.inc();
    }
}

/// Cập nhật kích thước tệp model.json trên đĩa
pub fn set_model_file_size_bytes(bytes: f64) {
    if let Some(g) = MODEL_FILE_SIZE_BYTES.get() {
        g.set(bytes);
    }
}

/// Cập nhật dung lượng bộ nhớ RAM của parsed model
pub fn set_parsed_model_ram_bytes(bytes: f64) {
    if let Some(g) = PARSED_MODEL_RAM_BYTES.get() {
        g.set(bytes);
    }
}

/// Cập nhật thời gian nạp và parse model
pub fn set_model_load_duration_seconds(sec: f64) {
    if let Some(g) = MODEL_LOAD_DURATION_SECONDS.get() {
        g.set(sec);
    }
}

/// Cập nhật độ trễ dự đoán trung bình trong warmup
pub fn set_warm_prediction_latency_seconds(sec: f64) {
    if let Some(g) = WARM_PREDICTION_LATENCY_SECONDS.get() {
        g.set(sec);
    }
}

/// Axum HTTP handler: GET /metrics — trả về Prometheus exposition text format.
/// Prometheus scraper gọi endpoint này theo `scrape_interval` đã cấu hình.
pub async fn metrics_handler() -> Response {
    let encoder = TextEncoder::new();
    let metric_families = prometheus::gather();
    let mut buffer = Vec::new();
    if encoder.encode(&metric_families, &mut buffer).is_err() {
        return (StatusCode::INTERNAL_SERVER_ERROR, "Failed to encode metrics").into_response();
    }
    // Trả về Content-Type đúng chuẩn Prometheus text/plain; version=0.0.4
    let body = String::from_utf8_lossy(&buffer).to_string();
    (
        StatusCode::OK,
        [("content-type", "text/plain; version=0.0.4; charset=utf-8")],
        body,
    )
        .into_response()
}

