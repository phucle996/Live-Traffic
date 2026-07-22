# ==============================================================================
# Airflow Spark ETL DAG (airflow/dags/traffic_etl_dag.py)
# Scheduled Hourly Spark ETL Job & Data Quality Report Execution
# ==============================================================================

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from src.orchestration.job_lock import JobLock
from src.orchestration.notifications import notify_job_failure
from src.orchestration.pipeline_state import PipelineStateTracker


default_args = {
    "owner": "traffic_data_team",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "on_failure_callback": notify_job_failure,
}


def run_spark_etl_task():
    """
    Task callable executing Spark ETL job under distributed JobLock.
    """
    with JobLock("spark_etl_job"):
        from src.processing.process_spark import main as spark_main
        spark_main()
        PipelineStateTracker.record_job_status("spark_etl_task", "SUCCESS")


def run_data_quality_task():
    """
    Task callable executing data quality report.
    """
    from src.processing.data_quality_report import main as quality_main
    quality_main()
    PipelineStateTracker.record_job_status("data_quality_task", "SUCCESS")


with DAG(
    dag_id="traffic_etl_dag",
    default_args=default_args,
    description="Runs Spark Parquet ETL every hour",
    schedule_interval="0 * * * *",  # Every hour
    catchup=False,
    max_active_runs=1,
) as dag:

    etl_task = PythonOperator(
        task_id="spark_etl_processing",
        python_callable=run_spark_etl_task,
    )

    quality_task = PythonOperator(
        task_id="data_quality_report",
        python_callable=run_data_quality_task,
    )

    etl_task >> quality_task
