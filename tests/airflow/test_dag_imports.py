# ==============================================================================
# Unit Tests for Airflow DAG Imports & Structural Integrity (tests/airflow/test_dag_imports.py)
# ==============================================================================

from pathlib import Path
from src.common.config import PROJECT_ROOT


def test_dag_files_exist():
    """
    Verifies that all 4 required Airflow DAG files exist in airflow/dags/.
    """
    dags_dir = PROJECT_ROOT / "airflow" / "dags"
    assert dags_dir.exists()

    expected_dags = [
        "traffic_ingestion_dag.py",
        "traffic_etl_dag.py",
        "model_training_dag.py",
        "model_monitoring_dag.py",
    ]

    for dag_file in expected_dags:
        path = dags_dir / dag_file
        assert path.exists(), f"Airflow DAG file missing: {path}"


def test_dag_syntax_compilation():
    """
    Verifies that all Airflow DAG python files compile without syntax errors.
    """
    import py_compile
    dags_dir = PROJECT_ROOT / "airflow" / "dags"

    for dag_file in dags_dir.glob("*.py"):
        py_compile.compile(str(dag_file), doraise=True)


if __name__ == "__main__":
    test_dag_files_exist()
    test_dag_syntax_compilation()
    print("All test_dag_imports unit tests PASSED!")
