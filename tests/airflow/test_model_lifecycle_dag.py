# ==============================================================================
# Model Lifecycle DAG Integration Tests (tests/airflow/test_model_lifecycle_dag.py)
# Verifies End-to-End Pipeline Tasks: Export, Golden Dataset, Parity Gate & Atomic Promote
# ==============================================================================

import os
import py_compile
import pytest

from src.common.config import PROJECT_ROOT
from src.mlops.model_promoter import promote_candidate_model, compute_file_sha256
from src.export.validate_exported_model import validate_model_parity

# Xác định đường dẫn đầy đủ tới model artifact dùng trong tests
_MODEL_JSON = str(PROJECT_ROOT / "artifacts" / "inference" / "candidate-tree" / "model.json")
_MODEL_EXISTS = os.path.exists(_MODEL_JSON)


def test_model_training_dag_syntax():
    """
    Verifies model_training_dag compiles without syntax errors.
    """
    dag_path = PROJECT_ROOT / "airflow" / "dags" / "model_training_dag.py"
    py_compile.compile(str(dag_path), doraise=True)


@pytest.mark.skipif(not _MODEL_EXISTS, reason="model.json artifact không tồn tại — chưa chạy training pipeline")
def test_model_promoter_sha256():
    """
    Verifies SHA-256 Checksum computation for model manifest.
    """
    checksum = compute_file_sha256(_MODEL_JSON)
    assert len(checksum) == 64  # Hex string 64 chars


def test_rust_parity_gate_validation():
    """
    Verifies Rust Parity Gate validation function (MAE <= 0.0001).
    """
    mae, is_valid = validate_model_parity()
    assert is_valid is True
    assert mae <= 0.0001


@pytest.mark.skipif(not _MODEL_EXISTS, reason="model.json artifact không tồn tại — chưa chạy training pipeline")
def test_atomic_model_promote():
    """
    Verifies atomic candidate model promotion function.
    """
    success = promote_candidate_model()
    assert success is True
