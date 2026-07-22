# ==============================================================================
# Pipeline State Tracker Engine (src/orchestration/pipeline_state.py)
# Records Task Execution Status, Timestamps, & Success Gates across Airflow DAGs
# ==============================================================================

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for pipeline state tracker
logger = get_logger(__name__)


class PipelineStateTracker:
    """
    Persists and tracks task execution statuses across Airflow DAGs.
    """

    STATE_FILE = PROJECT_ROOT / "artifacts" / "reports" / "pipeline_state.json"

    @classmethod
    def record_job_status(cls, job_name: str, status: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        Records job execution status (e.g. SUCCESS, FAILED, RUNNING) in JSON state file.

        Args:
            job_name (str): Unique job identifier (e.g. 'spark_etl_job').
            status (str): Execution status string.
            details (Optional[Dict[str, Any]]): Execution detail metadata.
        """
        cls.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        state_data = cls.get_all_states()

        state_data[job_name] = {
            "status": status.upper(),
            "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "details": details or {},
        }

        with open(cls.STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2)

        logger.info(f"Recorded pipeline state for job '{job_name}': {status.upper()}")

    @classmethod
    def get_job_status(cls, job_name: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves status details for given job_name.
        """
        states = cls.get_all_states()
        return states.get(job_name)

    @classmethod
    def get_all_states(cls) -> Dict[str, Any]:
        """
        Reads all recorded job states from JSON file.
        """
        if cls.STATE_FILE.exists():
            try:
                with open(cls.STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read pipeline state JSON: {e}")

        return {}
