# ==============================================================================
# Model Export Pipeline Unit Tests (tests/unit/test_export_pipeline.py)
# Verifies GBT Model Export, ONNX Export, Golden Dataset, & Parity Validation
# ==============================================================================

import json
from pathlib import Path

from src.common.config import PROJECT_ROOT
from src.export.inspect_spark_pipeline import inspect_pipeline_model
from src.export.export_feature_contract import verify_and_export_feature_contract
from src.export.validate_exported_model import validate_exported_gbt_model


def test_exported_candidate_artifacts_exist():
    """
    Verifies that exported candidate ONNX, Custom Tree, and Golden Dataset artifacts exist on disk.
    """
    tree_json = PROJECT_ROOT / "artifacts" / "inference" / "candidate-tree" / "model.json"
    tree_manifest = PROJECT_ROOT / "artifacts" / "inference" / "candidate-tree" / "manifest.json"
    onnx_model = PROJECT_ROOT / "artifacts" / "inference" / "candidate-onnx" / "model.onnx"
    onnx_manifest = PROJECT_ROOT / "artifacts" / "inference" / "candidate-onnx" / "manifest.json"
    golden_file = PROJECT_ROOT / "artifacts" / "inference" / "golden" / "golden_predictions.jsonl"

    assert tree_json.exists(), "File candidate-tree/model.json phải tồn tại!"
    assert tree_manifest.exists(), "File candidate-tree/manifest.json phải tồn tại!"
    assert onnx_model.exists(), "File candidate-onnx/model.onnx phải tồn tại!"
    assert onnx_manifest.exists(), "File candidate-onnx/manifest.json phải tồn tại!"
    assert golden_file.exists(), "File golden/golden_predictions.jsonl phải tồn tại!"


def test_golden_dataset_size_and_schema():
    """
    Verifies that Golden Dataset contains at least 1,000 records with exact required fields.
    """
    golden_file = PROJECT_ROOT / "artifacts" / "inference" / "golden" / "golden_predictions.jsonl"
    records = []
    with open(golden_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    assert len(records) >= 1000, f"Golden dataset phải chứa tối thiểu 1.000 bản ghi, thu được: {len(records)}"
    
    first = records[0]
    required_keys = ["sample_id", "input_business_fields", "ordered_feature_vector", "spark_prediction", "model_checksum"]
    for key in required_keys:
        assert key in first, f"Bản ghi Golden dataset thiếu trường: '{key}'"


def test_exported_tree_validation_parity():
    """
    Verifies that exported Custom Tree model achieves 100% parity (MAE <= 1e-4) against Golden Dataset.
    """
    tree_json = PROJECT_ROOT / "artifacts" / "inference" / "candidate-tree" / "model.json"
    golden_file = PROJECT_ROOT / "artifacts" / "inference" / "golden" / "golden_predictions.jsonl"

    report = validate_exported_gbt_model(tree_json, golden_file, max_mae_threshold=1e-4)
    assert report["status"] == "PASSED"
    assert report["max_absolute_error"] <= 1e-4
