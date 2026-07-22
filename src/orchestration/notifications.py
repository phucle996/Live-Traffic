# ==============================================================================
# Pipeline Notification & Failure Alert Engine (src/orchestration/notifications.py)
# Handles Failure Callbacks & Alerts for Airflow DAG Exceptions
# ==============================================================================

from typing import Dict, Any
from src.common.logging_utils import get_logger

# Instantiate logger for notification engine
logger = get_logger(__name__)


def notify_job_failure(context: Dict[str, Any]) -> None:
    """
    Airflow task failure callback function logging structured alert payload.

    Args:
        context (Dict[str, Any]): Airflow execution context dictionary.
    """
    dag_id = context.get("dag", "unknown_dag")
    task_id = context.get("task_instance", "unknown_task")
    execution_date = context.get("execution_date", "N/A")
    exception = context.get("exception", "Unspecified Exception")

    alert_payload = {
        "alert_type": "JOB_FAILURE",
        "dag_id": str(dag_id),
        "task_id": str(task_id),
        "execution_date": str(execution_date),
        "exception": str(exception),
    }

    logger.error(f"[ALERT - DAG FAILURE] Task '{task_id}' in DAG '{dag_id}' FAILED: {exception}")
    logger.error(f"Alert Payload: {alert_payload}")
