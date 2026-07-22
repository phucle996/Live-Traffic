# ==============================================================================
# Retraining Policy Decider (src/mlops/retraining_policy.py)
# Evaluates drift signals and data recency to decide if retraining is needed
# ==============================================================================

from pathlib import Path
from typing import Dict, Any
from datetime import datetime, timezone

import yaml

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for retraining policy
logger = get_logger(__name__)

DRIFT_THRESHOLDS_FILE = PROJECT_ROOT / "config" / "mlops" / "drift_thresholds.yaml"


class RetrainingPolicy:
    """
    Decides whether a new training run should be triggered based on:
    - Consecutive drift detections exceeding configured threshold
    - Data recency (number of new rows since last training)
    """

    def __init__(self):
        with open(DRIFT_THRESHOLDS_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        # Number of consecutive drift checks before forcing retraining
        self._consecutive_threshold: int = cfg["drift_thresholds"]["consecutive_drift_checks_to_retrain"]

    def should_retrain(
        self,
        consecutive_drift_count: int,
        new_rows_since_last_train: int,
        minimum_new_rows: int = 5000,
    ) -> bool:
        """
        Returns True if retraining should be triggered.

        Args:
            consecutive_drift_count: How many consecutive drift checks have fired.
            new_rows_since_last_train: New traffic rows ingested since last training.
            minimum_new_rows: Minimum new data volume to justify retraining.

        Returns:
            bool: True if retraining is recommended.
        """
        # Trigger retraining if drift has persisted for configured consecutive checks
        drift_trigger = consecutive_drift_count >= self._consecutive_threshold

        # Only retrain if new data volume is sufficiently large for meaningful update
        data_volume_trigger = new_rows_since_last_train >= minimum_new_rows

        should = drift_trigger and data_volume_trigger

        if should:
            logger.warning(
                f"RetrainingPolicy: RETRAINING REQUIRED. "
                f"Drift checks={consecutive_drift_count}, New rows={new_rows_since_last_train}"
            )
        else:
            logger.info(
                f"RetrainingPolicy: No retraining needed. "
                f"Drift checks={consecutive_drift_count}/{self._consecutive_threshold}, "
                f"New rows={new_rows_since_last_train}/{minimum_new_rows}"
            )

        return should
