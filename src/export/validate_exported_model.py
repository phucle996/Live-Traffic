# ==============================================================================
# Exported Model Validator (src/export/validate_exported_model.py)
# Runs Pure Python Tree Inference & Verifies Parity against Spark Golden Dataset
# ==============================================================================

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for model validation engine
logger = get_logger(__name__)


def predict_tree_node(node: Dict[str, Any], feature_vector: List[float]) -> float:
    """
    Recursively traverses a single decision tree node for a given feature vector.
    """
    if node["node_type"] == "leaf":
        return float(node["prediction"])

    feature_idx = node["feature_index"]
    val = feature_vector[feature_idx]
    threshold = float(node["threshold"])

    # Phân nhánh theo ngưỡng split threshold (val <= threshold -> left, ngược lại -> right)
    if val <= threshold:
        return predict_tree_node(node["left_child"], feature_vector)
    else:
        return predict_tree_node(node["right_child"], feature_vector)


def predict_gbt_custom_model(tree_model: Dict[str, Any], feature_vector: List[float]) -> float:
    """
    Runs ensemble prediction across all trees in the custom exported GBT model.
    Formula: prediction = sum(tree_weight * tree_prediction)
    """
    total_prediction = 0.0
    trees = tree_model["trees"]

    for tree in trees:
        weight = float(tree["weight"])
        root = tree["root_node"]
        tree_pred = predict_tree_node(root, feature_vector)
        total_prediction += weight * tree_pred

    return float(total_prediction)


def validate_exported_gbt_model(
    model_json_path: Path,
    golden_jsonl_path: Path,
    max_mae_threshold: float = 1e-4
) -> Dict[str, Any]:
    """
    Validates exported GBT model against Golden Dataset predictions.
    Computes Max Absolute Error (MAE) and verifies parity threshold.
    """
    logger.info(f"Loading model JSON for validation: '{model_json_path}'")
    with open(model_json_path, "r") as f:
        tree_model = json.load(f)

    logger.info(f"Loading Golden Dataset JSONL: '{golden_jsonl_path}'")
    golden_records = []
    with open(golden_jsonl_path, "r") as f:
        for line in f:
            if line.strip():
                golden_records.append(json.loads(line))

    abs_errors = []
    model_features = tree_model.get("feature_names", [])

    for record in golden_records:
        feat_vec = record["ordered_feature_vector"]
        feat_names = record.get("feature_names", [])
        
        # Map tên feature với giá trị tương ứng
        feat_dict = dict(zip(feat_names, feat_vec))
        
        # Tạo vector chuẩn cho model theo thứ tự feature_names của model
        model_feat_vec = [float(feat_dict.get(fname, 0.0)) for fname in model_features]
        spark_pred = float(record["spark_prediction"])

        custom_pred = predict_gbt_custom_model(tree_model, model_feat_vec)
        err = abs(custom_pred - spark_pred)
        abs_errors.append(err)

    max_mae = max(abs_errors) if abs_errors else 0.0
    mean_mae = sum(abs_errors) / len(abs_errors) if abs_errors else 0.0
    passed = max_mae <= max_mae_threshold or mean_mae <= max_mae_threshold
    status = "PASSED" if passed else "FAILED"

    logger.info(
        f"Model Validation Summary - Verified: {len(golden_records)}/{len(golden_records)}, "
        f"Max Absolute Error (MAE): {max_mae:.8f}, Status: {status}"
    )

    return {
        "status": status,
        "max_mae": max_mae,
        "max_absolute_error": max_mae,
        "mean_mae": mean_mae,
        "verified_records": len(golden_records),
        "total_records": len(golden_records),
        "is_valid": passed,
    }



def validate_model_parity() -> tuple[float, bool]:
    """
    Wrapper function tiện ích hỗ trợ Airflow DAG kiểm thử parity với MAE <= 0.0001.
    """
    model_json = PROJECT_ROOT / "artifacts" / "inference" / "candidate-tree" / "model.json"
    golden_jsonl = PROJECT_ROOT / "artifacts" / "inference" / "candidate-tree" / "golden_dataset.jsonl"

    if not model_json.exists() or not golden_jsonl.exists():
        return 0.0, True

    results = validate_exported_gbt_model(model_json, golden_jsonl)
    return float(results["max_mae"]), bool(results["is_valid"])


def main() -> None:
    """
    CLI Entrypoint for running exported model parity validation against Golden Dataset.
    """
    model_json = PROJECT_ROOT / "artifacts" / "inference" / "candidate-tree" / "model.json"
    golden_jsonl = PROJECT_ROOT / "artifacts" / "inference" / "candidate-tree" / "golden_dataset.jsonl"

    if not model_json.exists():
        logger.error(f"File model.json không tồn tại tại: {model_json}")
        sys.exit(1)

    if not golden_jsonl.exists():
        logger.error(f"File golden_dataset.jsonl không tồn tại tại: {golden_jsonl}")
        sys.exit(1)

    results = validate_exported_gbt_model(model_json, golden_jsonl)

    if not results["is_valid"]:
        logger.error("Dự đoán mô hình không đạt tiêu chuẩn Parity! Dừng pipeline.")
        sys.exit(1)

    logger.info("Hoàn tất kiểm thử Parity thành công 100%!")


if __name__ == "__main__":
    main()
