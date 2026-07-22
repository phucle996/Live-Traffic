# ==============================================================================
# GBT Tree Exporter (src/export/export_gbt_tree_model.py)
# Exports PySpark GBT Trees into Flat Array Versioned Tree JSON for Rust Engine
# ==============================================================================

import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List

from pyspark.ml import PipelineModel
from pyspark.ml.regression import GBTRegressionModel

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.common.spark_session import get_spark_session

# Instantiate logger for GBT tree export engine
logger = get_logger(__name__)


def parse_node(java_node, feature_names: List[str]) -> Dict[str, Any]:
    """
    Recursively parses PySpark Java DecisionTree node into a serializable Python dictionary.
    """
    is_leaf = java_node.getClass().getSimpleName() == "LeafNode"
    prediction = float(java_node.prediction())

    if is_leaf:
        return {
            "node_type": "leaf",
            "prediction": prediction,
        }
    else:
        # Internal decision node (Lấy chỉ số featureIndex từ PySpark Java Split)
        split = java_node.split()
        if hasattr(split, "featureIndex"):
            feature_idx = int(split.featureIndex())
        else:
            feature_idx = int(getattr(split, "feature")())

        feature_name = feature_names[feature_idx] if feature_idx < len(feature_names) else f"feature_{feature_idx}"

        # Lấy ngưỡng phân nhánh threshold cho ContinuousSplit
        threshold = float(split.threshold()) if hasattr(split, "threshold") else 0.0


        left_child = parse_node(java_node.leftChild(), feature_names)
        right_child = parse_node(java_node.rightChild(), feature_names)

        return {
            "node_type": "internal",
            "feature_index": feature_idx,
            "feature_name": feature_name,
            "threshold": threshold,
            "prediction": prediction,
            "left_child": left_child,
            "right_child": right_child,
        }


def export_gbt_custom_tree(model_dir: Path, output_dir: Path) -> Dict[str, Any]:
    """
    Exports PySpark GBT model trees into Candidate Custom Tree JSON & Manifest artifact.
    """
    logger.info(f"Exporting PySpark GBT Model trees to '{output_dir}'...")

    # 1. Nạp Spark PipelineModel
    spark = get_spark_session(app_name="export-gbt-tree-model")
    model_uri = f"file://{model_dir.resolve()}"
    pipeline_model = PipelineModel.load(model_uri)

    # 2. Xác định VectorAssembler feature names và GBT stage
    feature_names = []
    gbt_stage = None

    for stage in pipeline_model.stages:
        if hasattr(stage, "getInputCols"):
            feature_names = list(stage.getInputCols())
        if isinstance(stage, GBTRegressionModel):
            gbt_stage = stage

    if not gbt_stage:
        raise ValueError("Không tìm thấy GBTRegressionModel stage trong Spark PipelineModel!")

    # 3. Trích xuất cây và trọng số từ PySpark Java Model
    java_gbt = gbt_stage._java_obj
    java_trees = java_gbt.trees()
    tree_weights = [float(w) for w in gbt_stage.treeWeights]

    exported_trees = []
    for tree_idx, java_tree in enumerate(java_trees):
        root_node = java_tree.rootNode()
        parsed_root = parse_node(root_node, feature_names)
        exported_trees.append({
            "tree_index": tree_idx,
            "weight": tree_weights[tree_idx],
            "root_node": parsed_root,
        })

    # 4. Gom thành Tree Model Payload
    tree_model_payload = {
        "model_type": "gbt_regressor",
        "num_trees": len(exported_trees),
        "num_features": len(feature_names),
        "feature_names": feature_names,
        "tree_weights": tree_weights,
        "trees": exported_trees,
    }

    # Serialized JSON string
    json_str = json.dumps(tree_model_payload, indent=2, ensure_ascii=False)
    checksum = hashlib.sha256(json_str.encode("utf-8")).hexdigest()

    # 5. Lưu model.json
    output_dir.mkdir(parents=True, exist_ok=True)
    model_file = output_dir / "model.json"
    with open(model_file, "w", encoding="utf-8") as f:
        f.write(json_str)

    # 6. Tạo manifest.json
    manifest = {
        "model_version": "v1.0.0",
        "format": "rust_native_gbt",
        "checksum_sha256": checksum,
        "num_trees": len(exported_trees),
        "feature_names": feature_names,
        "created_at": "2026-07-21T20:46:00Z",
    }
    manifest_file = output_dir / "manifest.json"
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    logger.info(f"[SUCCESS] Exported Custom Tree Model artifact to: {model_file} (Checksum: {checksum[:12]}...)")
    return manifest


def main():
    model_dir = PROJECT_ROOT / "artifacts" / "models" / "gbt" / "latest"
    output_dir = PROJECT_ROOT / "artifacts" / "inference" / "candidate-tree"
    manifest = export_gbt_custom_tree(model_dir, output_dir)
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
