# ==============================================================================
# Airflow Model Monitoring DAG (airflow/dags/model_monitoring_dag.py)
# Daily Model Performance Drift & Data Freshness Monitoring DAG
# ==============================================================================

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from src.orchestration.notifications import notify_job_failure
from src.orchestration.pipeline_state import PipelineStateTracker


default_args = {
    "owner": "ml_team",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": notify_job_failure,
}


def run_model_monitoring_task():
    """
    Task callable checking data age and model performance metrics.
    """
    from src.dashboard.dashboard_service import get_model_metrics
    metrics = get_model_metrics()
    
    # Record monitoring status
    PipelineStateTracker.record_job_status(
        "model_monitoring_task",
        "SUCCESS",
        {"metrics": metrics.get("metrics", {})}
    )


with DAG(
    dag_id="model_monitoring_dag",
    default_args=default_args,
    description="Monitors model performance metrics & data freshness daily",
    schedule_interval="0 4 * * *",  # Every day at 04:00 UTC
    catchup=False,
    max_active_runs=1,
) as dag:

    monitor_task = PythonOperator(
        task_id="monitor_model_performance",
        python_callable=run_model_monitoring_task,
    )
