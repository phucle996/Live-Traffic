// ==============================================================================
// Native Rust GBT Tree Inference Engine (crates/traffic-tree-engine/src/lib.rs)
// Ultra Low-Latency Flat-Array Decision Tree Traversal Engine (Zero Heap Allocations)
// ==============================================================================

use anyhow::{Context, Result};
use rayon::prelude::*;
use std::fs;
use std::path::Path;


/// Node phẳng nằm trong mảng tĩnh (Flat Node Array for CPU Cache Efficiency)
#[derive(Debug, Clone, Copy)]
pub struct FlatNode {
    pub feature_index: u32,
    pub threshold: f64,
    pub prediction: f64,
    pub left_child: u32,
    pub right_child: u32,
    pub is_leaf: bool,
}

/// Một cây GBT được chuyển đổi hoàn toàn thành mảng 1 chiều chứa các FlatNode
#[derive(Debug, Clone)]
pub struct CompiledTree {
    pub weight: f64,
    pub nodes: Vec<FlatNode>,
}

impl CompiledTree {
    /// Duyệt cây bằng vòng lặp while (Iterative Traversal - Zero Stack/Recursion Overflow)
    #[inline(always)]
    pub fn predict(&self, features: &[f64]) -> f64 {
        if self.nodes.is_empty() {
            return 0.0;
        }

        let mut curr_idx: usize = 0;

        // Vòng lặp duyệt node phẳng qua integer index cho đến khi gặp leaf node
        while curr_idx < self.nodes.len() {
            let node = unsafe { self.nodes.get_unchecked(curr_idx) };

            if node.is_leaf {
                return node.prediction;
            }

            let feat_idx = node.feature_index as usize;
            let feat_val = if feat_idx < features.len() {
                unsafe { *features.get_unchecked(feat_idx) }
            } else {
                0.0
            };

            // Kiểm tra ngưỡng split threshold
            if feat_val <= node.threshold {
                curr_idx = node.left_child as usize;
            } else {
                curr_idx = node.right_child as usize;
            }
        }

        0.0
    }
}

/// GBT Tree Ensemble Model chứa danh sách các cây đã được compile thành Mảng Phẳng
#[derive(Debug, Clone)]
pub struct NativeTreeModel {
    pub num_trees: usize,
    pub feature_names: Vec<String>,
    pub compiled_trees: Vec<CompiledTree>,
}

impl NativeTreeModel {
    /// Nạp model.json từ đĩa và compile tất cả các cây sang dạng Mảng Phẳng (Flat Array Arena)
    pub fn from_json_file<P: AsRef<Path>>(path: P) -> Result<Self> {
        let content = fs::read_to_string(path).context("Không thể đọc file JSON model")?;
        Self::from_json_str(&content)
    }

    /// Parse từ chuỗi JSON
    pub fn from_json_str(json_str: &str) -> Result<Self> {
        let raw_val: serde_json::Value = serde_json::from_str(json_str)?;

        let feature_names: Vec<String> = raw_val["feature_names"]
            .as_array()
            .unwrap_or(&vec![])
            .iter()
            .map(|v| v.as_str().unwrap_or("").to_string())
            .collect();

        let trees_raw = raw_val["trees"]
            .as_array()
            .context("Thiếu trường 'trees' trong model.json")?;

        let mut compiled_trees = Vec::with_capacity(trees_raw.len());

        for tree_json in trees_raw {
            let weight = tree_json["weight"].as_f64().unwrap_or(1.0);
            let root_raw = &tree_json["root_node"];

            let mut flat_nodes = Vec::new();
            Self::flatten_node(root_raw, &mut flat_nodes);

            compiled_trees.push(CompiledTree {
                weight,
                nodes: flat_nodes,
            });
        }

        Ok(NativeTreeModel {
            num_trees: compiled_trees.len(),
            feature_names,
            compiled_trees,
        })
    }

    /// Đệ quy chuyển đổi cấu trúc cây JSON lồng nhau thành mảng 1 chiều flat_nodes
    fn flatten_node(node_val: &serde_json::Value, flat_nodes: &mut Vec<FlatNode>) -> u32 {
        let curr_idx = flat_nodes.len() as u32;
        let is_leaf = node_val["node_type"].as_str().unwrap_or("") == "leaf";
        let prediction = node_val["prediction"].as_f64().unwrap_or(0.0);

        if is_leaf {
            flat_nodes.push(FlatNode {
                feature_index: 0,
                threshold: 0.0,
                prediction,
                left_child: 0,
                right_child: 0,
                is_leaf: true,
            });
        } else {
            let feature_index = node_val["feature_index"].as_u64().unwrap_or(0) as u32;
            let threshold = node_val["threshold"].as_f64().unwrap_or(0.0);

            // Placeholder node để giữ vị trí index
            flat_nodes.push(FlatNode {
                feature_index,
                threshold,
                prediction,
                left_child: 0,
                right_child: 0,
                is_leaf: false,
            });

            // Ghi nhận con trái và con phải
            let left_idx = Self::flatten_node(&node_val["left_child"], flat_nodes);
            let right_idx = Self::flatten_node(&node_val["right_child"], flat_nodes);

            // Cập nhật lại vị trí con trái và con phải
            flat_nodes[curr_idx as usize].left_child = left_idx;
            flat_nodes[curr_idx as usize].right_child = right_idx;
        }

        curr_idx
    }

    /// Thực hiện dự đoán cho 1 vector đặc trưng (Single Record Inference)
    #[inline(always)]
    pub fn predict_single(&self, features: &[f64]) -> f64 {
        let mut total_pred = 0.0;
        for tree in &self.compiled_trees {
            total_pred += tree.weight * tree.predict(features);
        }
        total_pred
    }

    /// Thực hiện dự đoán hàng loạt đa luồng (Batch Multi-Threaded Inference bằng Rayon)
    pub fn predict_batch(&self, batch_features: &[Vec<f64>]) -> Vec<f64> {
        batch_features
            .par_iter()
            .map(|feats| self.predict_single(feats))
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_native_tree_compilation_and_prediction() {
        let dummy_json = r#"{
            "num_trees": 1,
            "feature_names": ["f0", "f1"],
            "trees": [
                {
                    "tree_index": 0,
                    "weight": 1.0,
                    "root_node": {
                        "node_type": "internal",
                        "feature_index": 0,
                        "threshold": 5.0,
                        "prediction": 0.0,
                        "left_child": {
                            "node_type": "leaf",
                            "prediction": 10.0
                        },
                        "right_child": {
                            "node_type": "leaf",
                            "prediction": 50.0
                        }
                    }
                }
            ]
        }"#;

        let model = NativeTreeModel::from_json_str(dummy_json).unwrap();
        assert_eq!(model.num_trees, 1);

        // Test f0 <= 5.0 -> trả về 10.0
        let pred_left = model.predict_single(&[3.0, 10.0]);
        assert_eq!(pred_left, 10.0);

        // Test f0 > 5.0 -> trả về 50.0
        let pred_right = model.predict_single(&[8.0, 10.0]);
        assert_eq!(pred_right, 50.0);
    }
}
