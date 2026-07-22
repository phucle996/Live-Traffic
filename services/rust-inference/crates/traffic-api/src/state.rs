// ==============================================================================
// Traffic API Shared State Management (crates/traffic-api/src/state.rs)
// Lockless In-memory Model Engine using ArcSwap & Atomic Swap (Zero Hot-path Overhead)
// ==============================================================================

use anyhow::{Context, Result};
use arc_swap::ArcSwap;
use sha2::{Digest, Sha256};
use std::fs;
use std::mem::size_of;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::time::Instant;

use traffic_tree_engine::{CompiledTree, FlatNode, NativeTreeModel};
use tracing::{info, warn};

use crate::metrics;

/// Shared Application State cho toàn bộ các HTTP Handlers (Lockless ArcSwap)
#[derive(Clone)]
pub struct AppState {
    pub model: Arc<ArcSwap<NativeTreeModel>>,
    pub manifest: Arc<ArcSwap<serde_json::Value>>,
    pub is_ready: Arc<AtomicBool>,
    pub model_dir: PathBuf,
}

impl AppState {
    /// Khởi tạo AppState mới, kiểm tra SHA-256 Checksum, nạp mô hình vào RAM và đo đạc telemetry
    pub async fn new<P: AsRef<Path>>(model_dir: P) -> Result<Self> {
        let dir_buf = model_dir.as_ref().to_path_buf();
        let tree_model_path = dir_buf.join("model.json");
        let manifest_path = dir_buf.join("manifest.json");

        let start_time = Instant::now();
        info!("Loading Native Tree Model from '{:?}'...", tree_model_path);

        // 1. Đọc file model.json từ đĩa
        let model_bytes = fs::read(&tree_model_path)
            .with_context(|| format!("Không thể đọc file model tại {:?}", tree_model_path))?;
        let file_size_bytes = model_bytes.len() as f64;

        // 2. Đọc file manifest.json từ đĩa (hoặc tạo manifest mặc định nếu không có)
        let manifest_str = fs::read_to_string(&manifest_path)
            .unwrap_or_else(|_| r#"{"model_version":"v1.0.0","format":"rust_native_gbt"}"#.to_string());
        let manifest_val: serde_json::Value = serde_json::from_str(&manifest_str)?;

        // 3. Kiểm tra tính toàn vẹn Checksum SHA-256
        verify_model_checksum(&model_bytes, &manifest_val)?;

        // 4. Parse model JSON thành flat in-memory array
        let model_str = String::from_utf8(model_bytes)?;
        let tree_model = NativeTreeModel::from_json_str(&model_str)
            .context("Không thể parse NativeTreeModel từ chuỗi JSON")?;

        let load_duration = start_time.elapsed().as_secs_f64();
        let ram_bytes = estimate_model_ram_bytes(&tree_model) as f64;

        // 5. Cập nhật các thông số Telemetry Metrics
        metrics::set_model_file_size_bytes(file_size_bytes);
        metrics::set_parsed_model_ram_bytes(ram_bytes);
        metrics::set_model_load_duration_seconds(load_duration);

        info!(
            "[METRICS] Loaded model: file_size={:.2}KB, ram_footprint={:.2}KB, duration={:.4}s",
            file_size_bytes / 1024.0,
            ram_bytes / 1024.0,
            load_duration
        );

        Ok(AppState {
            model: Arc::new(ArcSwap::from_pointee(tree_model)),
            manifest: Arc::new(ArcSwap::from_pointee(manifest_val)),
            is_ready: Arc::new(AtomicBool::new(false)),
            model_dir: dir_buf,
        })
    }

    /// Thực hiện Warmup mô hình trước khi đánh dấu Readiness = true (200 OK)
    pub async fn warmup(&self) {
        info!("Executing Model Warmup with synthetic feature vectors...");
        let start_warm = Instant::now();
        let current_model = self.model.load();

        // Sinh vector mẫu để chạy warmup 100 lần
        let dummy_vector = vec![10.778, 106.695, 45.0, 0.95, 8.0, 30.0, 510.0, 1.0, 0.0];
        let num_features = current_model.feature_names.len();
        let input = vec![dummy_vector[..num_features.min(9)].to_vec()];

        const WARMUP_COUNT: u32 = 100;
        for _ in 0..WARMUP_COUNT {
            let _ = current_model.predict_batch(&input);
        }

        let total_warm_sec = start_warm.elapsed().as_secs_f64();
        let avg_warm_sec = total_warm_sec / (WARMUP_COUNT as f64);
        metrics::set_warm_prediction_latency_seconds(avg_warm_sec);

        // Đánh dấu Readiness OK
        self.is_ready.store(true, Ordering::SeqCst);
        info!(
            "[SUCCESS] Model Warmup completed! Avg warm latency: {:.6}s. Readiness set to READY.",
            avg_warm_sec
        );
    }

    /// Hot Reload Model Nguyên Tử (Atomic Pointer Swap)
    /// Giữ nguyên model cũ trong RAM nếu nạp model mới thất bại
    pub async fn reload_model(&self) -> Result<()> {
        let tree_model_path = self.model_dir.join("model.json");
        let manifest_path = self.model_dir.join("manifest.json");

        let start_time = Instant::now();
        info!("Triggering Atomic Model Hot Reload from '{:?}'...", tree_model_path);

        // 1. Đọc và parse model mới trên RAM riêng
        let model_bytes = match fs::read(&tree_model_path) {
            Ok(b) => b,
            Err(e) => {
                warn!("Hot Reload FAILED! Không thể đọc file model mới: {}. Giữ nguyên model cũ!", e);
                return Err(e.into());
            }
        };

        let manifest_str = fs::read_to_string(&manifest_path).unwrap_or_default();
        let new_manifest: serde_json::Value = match serde_json::from_str(&manifest_str) {
            Ok(m) => m,
            Err(e) => {
                warn!("Hot Reload FAILED! File manifest mới không hợp lệ: {}. Giữ nguyên model cũ!", e);
                return Err(e.into());
            }
        };

        // 2. Verify SHA-256 Checksum của model mới
        if let Err(e) = verify_model_checksum(&model_bytes, &new_manifest) {
            warn!("Hot Reload FAILED! Checksum verification failed: {}. Giữ nguyên model cũ!", e);
            return Err(e);
        }

        // 3. Parse model mới
        let model_str = String::from_utf8(model_bytes)?;
        let new_model = match NativeTreeModel::from_json_str(&model_str) {
            Ok(m) => m,
            Err(e) => {
                warn!("Hot Reload FAILED! Không thể parse model mới: {}. Giữ nguyên model cũ!", e);
                return Err(e);
            }
        };

        let file_size_bytes = model_str.len() as f64;
        let ram_bytes = estimate_model_ram_bytes(&new_model) as f64;
        let load_duration = start_time.elapsed().as_secs_f64();

        // 4. Thực hiện Lockless Atomic Pointer Swap (0ms downtime)
        self.model.store(Arc::new(new_model));
        self.manifest.store(Arc::new(new_manifest));

        // 5. Cập nhật các Prometheus Metrics
        metrics::set_model_file_size_bytes(file_size_bytes);
        metrics::set_parsed_model_ram_bytes(ram_bytes);
        metrics::set_model_load_duration_seconds(load_duration);
        metrics::record_model_reload();

        info!(
            "[SUCCESS] Atomic Model Hot Reload succeeded! Model RAM footprint: {:.2}KB, Duration: {:.4}s",
            ram_bytes / 1024.0,
            load_duration
        );

        Ok(())
    }
}

/// Kiểm tra tính toàn vẹn Checksum SHA-256 giữa tệp model.json và manifest.json
fn verify_model_checksum(model_bytes: &[u8], manifest: &serde_json::Value) -> Result<()> {
    if let Some(expected_checksum) = manifest.get("checksum_sha256").and_then(|v| v.as_str()) {
        let mut hasher = Sha256::new();
        hasher.update(model_bytes);
        let result = hasher.finalize();
        let computed_checksum = format!("{:x}", result);

        if computed_checksum != expected_checksum {
            anyhow::bail!(
                "Checksum SHA-256 không khớp! Expected: {}, Computed: {}",
                expected_checksum,
                computed_checksum
            );
        }
        info!("[SECURITY] SHA-256 Checksum verification PASSED: {}", computed_checksum);
    }
    Ok(())
}

/// Ước tính dung lượng bộ nhớ RAM (bytes) của NativeTreeModel đã được parse
fn estimate_model_ram_bytes(model: &NativeTreeModel) -> usize {
    let mut total = size_of::<NativeTreeModel>();
    for tree in &model.compiled_trees {
        total += size_of::<CompiledTree>();
        total += tree.nodes.len() * size_of::<FlatNode>();
    }
    total
}
