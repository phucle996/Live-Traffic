# ==============================================================================
# Model Metadata Generator & Versioning Manager (src/training/model_metadata.py)
# Generates Versioned Model Metadata JSON and Manages Artifact Directories
# ==============================================================================

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for model metadata manager
logger = get_logger(__name__)


def create_model_metadata(
    version: str,
    metrics: Dict[str, float],
    features: List[str],
    target: str,
    hyperparameters: Dict[str, Any],
    train_rows: int,
    test_rows: int,
) -> Dict[str, Any]:
    """
    Constructs a structured model metadata dictionary.

    Args:
        version (str): Model version string (e.g., "20260721_180000").
        metrics (Dict[str, float]): Model evaluation metrics (RMSE, MAE, R²).
        features (List[str]): Input feature column names in order.
        target (str): Target column name.
        hyperparameters (Dict[str, Any]): GBT model hyperparameters.
        train_rows (int): Number of training sample rows.
        test_rows (int): Number of test sample rows.

    Returns:
        Dict[str, Any]: Model metadata dictionary.
    """
    metadata = {
        "model_type": "GBTRegressor",
        "version": version,
        "created_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "target": target,
        "features": features,
        "metrics": metrics,
        "hyperparameters": hyperparameters,
        "dataset": {
            "training_rows": train_rows,
            "test_rows": test_rows,
        },
        "spark_version": "3.5.0",
    }

    return metadata


def save_model_metadata(metadata: Dict[str, Any], output_dir: Path) -> None:
    """
    Saves model metadata dictionary as JSON file inside model directory and artifacts/metrics.

    Args:
        metadata (Dict[str, Any]): Model metadata dictionary.
        output_dir (Path): Model output directory path.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_path = output_dir / "model_metadata.json"

    # Write metadata JSON file
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved model metadata JSON to '{metadata_path}'")

    # Also save to artifacts/metrics/metrics.json
    metrics_dir = PROJECT_ROOT / "artifacts" / "metrics"
    metrics_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = metrics_dir / "metrics.json"

    metrics_payload = {
        "model_version": metadata["version"],
        "created_at": metadata["created_at"],
        "metrics": metadata["metrics"],
        "hyperparameters": metadata["hyperparameters"],
    }

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics_payload, f, indent=2)

    logger.info(f"Saved standalone metrics JSON to '{metrics_path}'")
