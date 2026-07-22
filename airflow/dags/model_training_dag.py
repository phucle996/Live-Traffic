# ==============================================================================
# Airflow Model Training DAG (airflow/dags/model_training_dag.py)
# End-to-End Model Lifecycle: Training, Export, Golden Dataset, Rust Parity Gate & Atomic Promote
# ==============================================================================

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from src.orchestration.job_lock import JobLock
from src.orchestration.notifications import notify_job_failure
from src.orchestration.pipeline_state import PipelineStateTracker


default_args = {
    "owner": "ml_team",
    "depends_on_past": False,
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
    "on_failure_callback": notify_job_failure,
}


def verify_quality_gate_task():
    """
    Task callable checking if data quality gate passed before training.
    """
    state = PipelineStateTracker.get_job_status("data_quality_task")
    if state and state.get("status") == "FAILED":
        raise RuntimeError("Quality Gate Failure: Previous data quality task did not pass successfully.")


def run_model_training_task():
    """
    Task callable executing GBTRegressor model training under distributed JobLock.
    """
    with JobLock("model_training_job"):
        from src.training.train_gbt import main as train_main
        train_main()
        PipelineStateTracker.record_job_status("model_training_task", "SUCCESS")


def export_model_task():
    """
    Task callable exporting PySpark GBT model to Native GBT JSON tree format and Feature Contract.
    """
    from src.export.export_feature_contract import main as export_contract_main
    from src.export.export_gbt_tree_model import main as export_tree_main

    export_contract_main()
    export_tree_main()
    PipelineStateTracker.record_job_status("model_export_task", "SUCCESS")


def generate_golden_dataset_task():
    """
    Task callable generating 1,000 Golden Dataset records for Rust parity validation.
    """
    from src.export.generate_golden_dataset import main as gen_golden_main
    gen_golden_main()
    PipelineStateTracker.record_job_status("golden_dataset_task", "SUCCESS")


def rust_parity_gate_task():
    """
    Rust Parity Gate: Validates prediction parity between Python GBT and Rust Native Engine (MAE <= 0.0001).
    Aborts DAG promotion if Parity Test fails!
    """
    from src.export.validate_exported_model import validate_model_parity
    mae, is_valid = validate_model_parity()

    if not is_valid or mae > 0.0001:
        raise RuntimeError(f"Rust Parity Gate Failure: MAE={mae:.6f} > 0.0001. Aborting promotion!")

    PipelineStateTracker.record_job_status("rust_parity_gate_task", "SUCCESS")


def atomic_promote_and_reload_task():
    """
    Task callable promoting candidate model atomically and triggering zero-downtime Rust Hot Reload.
    """
    from src.mlops.model_promoter import promote_candidate_model
    success = promote_candidate_model()
    if not success:
        raise RuntimeError("Atomic Model Promotion & Hot Reload failed!")
    PipelineStateTracker.record_job_status("atomic_promote_task", "SUCCESS")


with DAG(
    dag_id="model_training_dag",
    default_args=default_args,
    description="Trains Spark MLlib GBTRegressor model weekly with Rust Parity Gate & Hot Reload",
    schedule_interval="0 2 * * 0",  # Every Sunday at 02:00 UTC
    catchup=False,
    max_active_runs=1,
) as dag:

    quality_gate = PythonOperator(
        task_id="verify_quality_gate",
        python_callable=verify_quality_gate_task,
    )

    train = PythonOperator(
        task_id="train_gbt_model",
        python_callable=run_model_training_task,
    )

    export = PythonOperator(
        task_id="export_native_gbt_model",
        python_callable=export_model_task,
    )

    golden_dataset = PythonOperator(
        task_id="generate_golden_dataset",
        python_callable=generate_golden_dataset_task,
    )

    rust_parity_gate = PythonOperator(
        task_id="rust_parity_gate",
        python_callable=rust_parity_gate_task,
    )

    atomic_promote = PythonOperator(
        task_id="atomic_promote_and_reload",
        python_callable=atomic_promote_and_reload_task,
    )

    # Airflow Task Dependency Chain
    quality_gate >> train >> export >> golden_dataset >> rust_parity_gate >> atomic_promote
