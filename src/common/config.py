# ==============================================================================
# Central Configuration Manager Module (src/common/config.py)
# Cloud Native 12-Factor Compliant Config Loader with Thread-Safe Singleton & Secret Masking
# ==============================================================================

import os
import threading
from pathlib import Path
from typing import Any, Dict

# Define root directory of the project relative to this file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Load environment variables from .env file if available (12-Factor III)
try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=False)
except ImportError:
    # Fallback when python-dotenv is not installed yet
    pass

try:
    import yaml
except ImportError:
    yaml = None


class Settings:
    """
    Centralized Settings manager reading application.yaml defaults overlaid with environment variables.
    Implemented as a thread-safe singleton to prevent race conditions during parallel processing.
    """

    _instance = None
    _lock = threading.Lock()  # Thread lock to guarantee safe multi-threaded initialization

    def __new__(cls):
        # Implement thread-safe double-checked locking singleton pattern
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(Settings, cls).__new__(cls)
                    cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """
        Loads static YAML configuration and overrides values with environment variables.
        """
        # Define path to application.yaml
        yaml_config_path = PROJECT_ROOT / "config" / "application.yaml"
        self._raw_yaml: Dict[str, Any] = {}

        # Read static YAML configuration if it exists and yaml library is available
        if yaml is not None and yaml_config_path.exists():
            with open(yaml_config_path, "r", encoding="utf-8") as f:
                self._raw_yaml = yaml.safe_load(f) or {}

        # Parse project metadata settings
        project_cfg = self._raw_yaml.get("project", {})
        self.PROJECT_NAME: str = os.getenv("PROJECT_NAME", project_cfg.get("name", "traffic-prediction-lab5"))
        self.PROJECT_VERSION: str = os.getenv("PROJECT_VERSION", project_cfg.get("version", "1.0.0"))

        # Parse Hybrid Data Source Mode settings
        ingestion_cfg = self._raw_yaml.get("ingestion", {})
        self.DATA_SOURCE_MODE: str = os.getenv("DATA_SOURCE_MODE", os.getenv("INGESTION_MODE", "offline")).lower()
        self.TOMTOM_API_KEY: str = os.getenv("TOMTOM_API_KEY", "")
        self.INGESTION_MODE: str = self.DATA_SOURCE_MODE
        self.LAB_DATA_RAW_DIR: str = str(PROJECT_ROOT / "data" / "lab_raw")
        self.LOCATIONS_FILE: str = os.getenv(
            "LOCATIONS_FILE", str(PROJECT_ROOT / "data" / "locations" / "data_converted.csv")
        )
        self.REFERENCE_PROCESSED_FILE: str = os.getenv(
            "REFERENCE_PROCESSED_FILE", str(PROJECT_ROOT / "data" / "lab_reference" / "process_data_spark.csv")
        )
        self.CRAWL_INTERVAL_SECONDS: int = int(
            os.getenv("CRAWL_INTERVAL_SECONDS", os.getenv("ONLINE_POLL_INTERVAL_SECONDS", 1800))
        )
        self.MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", os.getenv("ONLINE_MAX_RETRIES", 3)))
        self.RETRY_DELAY_SECONDS: int = int(
            os.getenv("RETRY_DELAY_SECONDS", os.getenv("ONLINE_RETRY_DELAY_SECONDS", 5))
        )

        # Parse HDFS storage paths
        data_cfg = self._raw_yaml.get("data", {})
        self.HDFS_URI: str = os.getenv("HDFS_URI", "hdfs://namenode:9000")
        self.HDFS_RAW_PATH: str = os.getenv("HDFS_RAW_PATH", data_cfg.get("raw_hdfs_path", "/traffic_project/raw"))
        self.HDFS_PROCESSED_PATH: str = os.getenv(
            "HDFS_PROCESSED_PATH", data_cfg.get("processed_hdfs_path", "/traffic_project/processed")
        )
        self.HDFS_MODEL_PATH: str = os.getenv("HDFS_MODEL_PATH", "/traffic_project/models/gbt")
        self.HDFS_PREDICTION_PATH: str = os.getenv("HDFS_PREDICTION_PATH", "/traffic_project/predictions")

        # Parse Data files local locations
        self.LOCATIONS_FILE: str = str(
            PROJECT_ROOT / os.getenv("LOCATIONS_FILE", data_cfg.get("locations_file", "data/locations/data_converted.csv"))
        )
        self.SEED_FOLDER: str = str(
            PROJECT_ROOT / os.getenv("SEED_FOLDER", data_cfg.get("seed_folder", "data/seed"))
        )

        # Parse Apache Spark cluster configuration
        spark_cfg = self._raw_yaml.get("spark", {})
        self.SPARK_MASTER: str = os.getenv("SPARK_MASTER", spark_cfg.get("master", "spark://spark-master:7077"))
        self.SPARK_APP_NAME: str = os.getenv("SPARK_APP_NAME", spark_cfg.get("app_name", "traffic-prediction"))
        self.SPARK_DRIVER_MEMORY: str = os.getenv("SPARK_DRIVER_MEMORY", spark_cfg.get("driver_memory", "2g"))
        self.SPARK_EXECUTOR_MEMORY: str = os.getenv("SPARK_EXECUTOR_MEMORY", spark_cfg.get("executor_memory", "2g"))

        # Parse MLlib Model hyperparameters
        model_cfg = self._raw_yaml.get("model", {})
        hp_cfg = model_cfg.get("hyperparameters", {})
        self.MODEL_TARGET: str = model_cfg.get("target", "CurrentSpeed")
        self.MODEL_FEATURES: list = model_cfg.get(
            "features", ["Latitude", "Longitude", "TimeInMinutes", "DayOfWeek", "Weekend"]
        )
        self.MODEL_MAX_ITER: int = int(os.getenv("MODEL_MAX_ITER", hp_cfg.get("max_iter", 100)))
        self.MODEL_MAX_DEPTH: int = int(os.getenv("MODEL_MAX_DEPTH", hp_cfg.get("max_depth", 5)))
        self.MODEL_SEED: int = int(os.getenv("MODEL_SEED", hp_cfg.get("seed", 42)))

        # Parse Logging formatters & levels
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
        self.LOG_FORMAT: str = os.getenv("LOG_FORMAT", "CONSOLE").upper()

    def __repr__(self) -> str:
        """
        String representation of settings with sensitive API keys masked for security.
        """
        # Mask API key if set to prevent credential leaks in logs
        masked_api_key = "***MASKED***" if self.TOMTOM_API_KEY else "NOT_SET"

        return (
            f"Settings("
            f"PROJECT_NAME='{self.PROJECT_NAME}', "
            f"INGESTION_MODE='{self.INGESTION_MODE}', "
            f"TOMTOM_API_KEY='{masked_api_key}', "
            f"HDFS_URI='{self.HDFS_URI}', "
            f"SPARK_MASTER='{self.SPARK_MASTER}', "
            f"LOG_LEVEL='{self.LOG_LEVEL}')"
        )


# Instantiates thread-safe global settings object
settings = Settings()
