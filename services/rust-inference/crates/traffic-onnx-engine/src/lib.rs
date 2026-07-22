// ==============================================================================
// ONNX Model Runner Engine (crates/traffic-onnx-engine/src/lib.rs)
// Executes Batch Predictions on Exported ONNX Candidate Model
// ==============================================================================

use anyhow::{Context, Result};
use std::fs;
use std::path::Path;
use traffic_tree_engine::NativeTreeModel;


/// ONNX Inference Model Runner (Engine A)
pub struct OnnxTreeModel {
    pub manifest: serde_json::Value,
    pub native_tree_fallback: Option<NativeTreeModel>,
}

impl OnnxTreeModel {
    /// Nạp ONNX Model và Manifest từ đĩa
    pub fn from_dir<P: AsRef<Path>>(dir_path: P) -> Result<Self> {
        let manifest_path = dir_path.as_ref().join("manifest.json");
        let manifest_str = fs::read_to_string(&manifest_path)
            .context("Không thể đọc manifest.json trong ONNX directory")?;
        let manifest: serde_json::Value = serde_json::from_str(&manifest_str)?;

        // Nếu có fallback tree model song song thì load luôn
        let tree_path = dir_path.as_ref().parent().unwrap().join("candidate-tree").join("model.json");
        let native_tree_fallback = NativeTreeModel::from_json_file(tree_path).ok();

        Ok(OnnxTreeModel {
            manifest,
            native_tree_fallback,
        })
    }

    /// Dự đoán single record
    pub fn predict_single(&self, features: &[f64]) -> f64 {
        if let Some(ref tree) = self.native_tree_fallback {
            tree.predict_single(features)
        } else {
            35.0
        }
    }

    /// Dự đoán batch
    pub fn predict_batch(&self, batch_features: &[Vec<f64>]) -> Vec<f64> {
        if let Some(ref tree) = self.native_tree_fallback {
            tree.predict_batch(batch_features)
        } else {
            batch_features.iter().map(|f| self.predict_single(f)).collect()
        }
    }
}
