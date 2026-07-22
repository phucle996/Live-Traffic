# ==============================================================================
# Contract Compatibility Unit Tests (tests/unit/test_contract_compatibility.py)
# Verifies Shared Contracts SOT Integrity & Compatibility Across Components
# ==============================================================================

import json
from pathlib import Path

from src.common.config import PROJECT_ROOT
from src.prediction.feature_builder import FeatureBuilder


def test_feature_contract_file_exists():
    """
    Verifies that feature_contract.json exists in contracts/ directory.
    """
    contract_file = PROJECT_ROOT / "contracts" / "feature_contract.json"
    assert contract_file.exists(), "File contracts/feature_contract.json phải tồn tại!"


def test_feature_order_matches_builder():
    """
    Verifies that Feature Order in SOT feature_contract.json matches FeatureBuilder list.
    """
    contract_file = PROJECT_ROOT / "contracts" / "feature_contract.json"
    with open(contract_file, "r", encoding="utf-8") as f:
        contract = json.load(f)

    # 1. Lấy danh sách feature_order từ SOT contract
    contract_features = contract.get("feature_order", [])
    assert len(contract_features) > 0, "Feature order không được để trống!"

    # 2. Đảm bảo FeatureBuilder trong Python trả về chính xác thứ tự này
    builder_features = FeatureBuilder.FEATURE_COLS
    assert contract_features == builder_features, (
        f"Lệch thứ tự đặc trưng! SOT Contract: {contract_features} vs FeatureBuilder: {builder_features}"
    )


def test_feature_data_types_are_f64():
    """
    Verifies that all feature data types in SOT contract are defined as float64 (f64).
    """
    contract_file = PROJECT_ROOT / "contracts" / "feature_contract.json"
    with open(contract_file, "r", encoding="utf-8") as f:
        contract = json.load(f)

    features = contract.get("features", [])
    for feat in features:
        # Kiểm tra kiểu dữ liệu của từng đặc trưng phải là f64
        assert feat.get("data_type") == "f64", f"Đặc trưng {feat.get('name')} phải dùng kiểu f64!"


def test_all_contract_schemas_exist():
    """
    Verifies that all required contract files exist in contracts/ directory.
    """
    contracts_dir = PROJECT_ROOT / "contracts"
    required_files = [
        "traffic_event.proto",
        "prediction.openapi.yaml",
        "feature_contract.json",
        "model_manifest.schema.json",
        "source_resolution.schema.json",
        "examples/traffic_event.json",
        "examples/prediction_request.json",
        "examples/prediction_response.json",
    ]

    for fname in required_files:
        fpath = contracts_dir / fname
        assert fpath.exists(), f"Thiếu file hợp đồng dữ liệu: contracts/{fname}"
