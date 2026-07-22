# ==============================================================================
# Multi-Stage Dockerfile for High-Performance Rust Inference API
# Optimized Layer Caching for Fast Build Times (Zero-Python, Zero-Java, Zero-Spark)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build binary using official Rust 1.95 toolchain with Layer Caching
# ------------------------------------------------------------------------------
FROM rust:1.95-slim as builder

WORKDIR /usr/src/rust-inference

# 1. Copy Cargo workspace configs
COPY Cargo.toml Cargo.lock ./

# 2. Tạo cấu trúc thư mục dummy cho các crates để Cache Dependencies
RUN mkdir -p crates/traffic-contract/src \
    && mkdir -p crates/traffic-tree-engine/src \
    && mkdir -p crates/traffic-onnx-engine/src \
    && mkdir -p crates/traffic-inference/src \
    && mkdir -p crates/traffic-api/src \
    && echo "fn main() {}" > crates/traffic-api/src/main.rs \
    && echo "fn main() {}" > crates/traffic-inference/src/main.rs \
    && touch crates/traffic-contract/src/lib.rs \
    && touch crates/traffic-tree-engine/src/lib.rs \
    && touch crates/traffic-onnx-engine/src/lib.rs

COPY crates/traffic-contract/Cargo.toml crates/traffic-contract/
COPY crates/traffic-tree-engine/Cargo.toml crates/traffic-tree-engine/
COPY crates/traffic-onnx-engine/Cargo.toml crates/traffic-onnx-engine/
COPY crates/traffic-inference/Cargo.toml crates/traffic-inference/
COPY crates/traffic-api/Cargo.toml crates/traffic-api/

# 3. Biên dịch trước các dependencies để lưu Cache Layer của Docker
RUN cargo build --release -p traffic-api || true

# 4. Copy mã nguồn thật sự vào workspace và touch các file nguồn để invalidate cache
COPY crates ./crates
RUN touch crates/traffic-contract/src/lib.rs \
    && touch crates/traffic-tree-engine/src/lib.rs \
    && touch crates/traffic-onnx-engine/src/lib.rs \
    && touch crates/traffic-api/src/main.rs

# 5. Build chính thức binary traffic-api (Chỉ mất vài giây nhờ Cache Layer)
RUN cargo build --release -p traffic-api

# ------------------------------------------------------------------------------
# Stage 2: Ultra-lightweight debian-slim runtime container (~30MB image size)
# ------------------------------------------------------------------------------
FROM debian:bookworm-slim as runtime

WORKDIR /app

# Install ca-certificates and curl cho healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy compiled Rust binary từ builder stage
COPY --from=builder /usr/src/rust-inference/target/release/traffic-api /app/traffic-api

# Tạo Non-root Daemon User (UID 10001) cho mục đích an ninh bảo mật container
RUN groupadd -g 10001 appgroup && useradd -u 10001 -g appgroup -s /bin/sh appuser \
    && chown -R appuser:appgroup /app

USER appuser:appgroup


# Environment variables
ENV PORT=8080
ENV RUST_LOG=info

EXPOSE 8080


# Healthcheck probe cho Docker Orchestration
HEALTHCHECK --interval=5s --timeout=3s --retries=3 \
  CMD curl -f http://localhost:8080/health/ready || exit 1

ENTRYPOINT ["/app/traffic-api"]
