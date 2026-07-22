# ==============================================================================
# Experiment Tracker (src/mlops/experiment_tracker.py)
# Records training runs: hyperparameters, metrics, artifact paths, dataset info
# ==============================================================================

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for experiment tracker
logger = get_logger(__name__)

# Directory storing per-run experiment JSON files
EXPERIMENTS_DIR = PROJECT_ROOT / "artifacts" / "mlops" / "experiments"


class ExperimentTracker:
    """
    Records training experiment metadata — hyperparams, metrics, artifact paths.
    Each training run gets a unique run_id and persists to its own JSON file.
    """

    def __init__(self, experiment_name: str):
        # Generate unique run_id for this training experiment
        self.run_id: str = str(uuid.uuid4())[:8]
        self.experiment_name = experiment_name
        self.started_at: str = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Aggregate buckets for this experiment run
        self._params: Dict[str, Any] = {}
        self._metrics: Dict[str, float] = {}
        self._artifacts: Dict[str, str] = {}
        self._dataset_info: Dict[str, Any] = {}

        EXPERIMENTS_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"ExperimentTracker: Started run '{self.run_id}' for '{experiment_name}'")

    def log_params(self, params: Dict[str, Any]) -> None:
        """Logs model hyperparameters (e.g., maxDepth, maxIter, stepSize)."""
        self._params.update(params)

    def log_metrics(self, metrics: Dict[str, float]) -> None:
        """Logs evaluation metrics (e.g., RMSE, R², MAE)."""
        self._metrics.update(metrics)

    def log_artifact(self, name: str, path: str) -> None:
        """Logs path to model artifact or dataset file."""
        self._artifacts[name] = path

    def log_dataset(self, info: Dict[str, Any]) -> None:
        """Logs dataset lineage info: source, row count, partition date."""
        self._dataset_info.update(info)

    def finish(self) -> str:
        """
        Persists experiment run record to artifacts/mlops/experiments/{run_id}.json.
        Returns run_id for downstream registry registration.
        """
        record = {
            "run_id": self.run_id,
            "experiment_name": self.experiment_name,
            "started_at": self.started_at,
            "finished_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "params": self._params,
            "metrics": self._metrics,
            "artifacts": self._artifacts,
            "dataset": self._dataset_info,
        }

        run_file = EXPERIMENTS_DIR / f"{self.run_id}.json"
        with open(run_file, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, ensure_ascii=False)

        logger.info(f"ExperimentTracker: Run '{self.run_id}' persisted to {run_file}")
        return self.run_id
