# ==============================================================================
# Airflow Ingestion DAG (airflow/dags/traffic_ingestion_dag.py)
# Scheduled Traffic Flow Ingestion Every 30 Minutes
# ==============================================================================

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from src.orchestration.notifications import notify_job_failure
from src.orchestration.pipeline_state import PipelineStateTracker


default_args = {
    "owner": "traffic_data_team",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": notify_job_failure,
}


def run_ingestion_task():
    """
    Task callable executing central data ingestion batch.
    """
    from src.ingestion.ingest import execute_ingestion_batch
    resolved = execute_ingestion_batch()
    PipelineStateTracker.record_job_status("traffic_ingestion_task", "SUCCESS", {"resolved_source": resolved})


with DAG(
    dag_id="traffic_ingestion_dag",
    default_args=default_args,
    description="Ingests traffic data every 30 minutes",
    schedule_interval="*/30 * * * *",  # Every 30 minutes
    catchup=False,
    max_active_runs=1,
) as dag:

    ingest_task = PythonOperator(
        task_id="ingest_traffic_data",
        python_callable=run_ingestion_task,
    )
