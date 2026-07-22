// ==============================================================================
// Request ID Middleware (crates/traffic-api/src/middleware/request_id.rs)
// Auto-generates or propagates X-Request-ID headers for Distributed Tracing (Axum 0.7)
// ==============================================================================

use axum::extract::Request;
use axum::http::{HeaderName, HeaderValue};
use axum::middleware::Next;
use axum::response::Response;

static REQUEST_ID_HEADER: HeaderName = HeaderName::from_static("x-request-id");

/// Middleware gắn X-Request-ID vào mọi HTTP Response (Axum 0.7 Compatible)
pub async fn request_id_middleware(req: Request, next: Next) -> Response {
    let req_id = req
        .headers()
        .get(&REQUEST_ID_HEADER)
        .cloned()
        .unwrap_or_else(|| {
            let uuid_str = format!("req-{}", chrono::Utc::now().timestamp_nanos_opt().unwrap_or(0));
            HeaderValue::from_str(&uuid_str).unwrap_or_else(|_| HeaderValue::from_static("req-unknown"))
        });

    let mut response = next.run(req).await;
    response.headers_mut().insert(REQUEST_ID_HEADER.clone(), req_id);
    response
}
