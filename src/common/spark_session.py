# ==============================================================================
# Central SparkSession Factory Module (src/common/spark_session.py)
# Thread-Safe Singleton SparkSession Builder with HA Master & HDFS Configuration
# ==============================================================================

import threading
from typing import Optional
from pyspark.sql import SparkSession

from src.common.config import settings
from src.common.logging_utils import get_logger

# Instantiate logger for Spark session factory
logger = get_logger(__name__)


class SparkSessionManager:
    """
    Thread-safe Singleton manager for initializing and managing Apache SparkSession.
    Prevents race conditions when multiple modules request Spark handles simultaneously.
    """

    _spark_session: Optional[SparkSession] = None
    _lock = threading.Lock()  # Re-entrant thread lock for thread safety

    @classmethod
    def get_spark_session(cls, app_name: Optional[str] = None, master: Optional[str] = None) -> SparkSession:
        """
        Retrieves or initializes the active SparkSession instance.

        Args:
            app_name (Optional[str]): Application name override.
            master (Optional[str]): Spark Master URL override.

        Returns:
            SparkSession: Active configured SparkSession instance.
        """
        # Double-checked locking pattern to avoid lock overhead if session already exists
        if cls._spark_session is None or cls._spark_session._sc._is_closed:
            with cls._lock:
                if cls._spark_session is None or cls._spark_session._sc._is_closed:
                    # Resolve application name and master from parameters or central settings
                    effective_app_name = app_name or settings.SPARK_APP_NAME
                    effective_master = master or settings.SPARK_MASTER

                    # 1. Nếu đang chạy local (không có container spark-master), chuyển sang master "local[*]"
                    if effective_master.startswith("spark://") and not master:
                        import socket
                        try:
                            host = effective_master.split("//")[1].split(":")[0]
                            socket.gethostbyname(host)
                        except Exception:
                            logger.warning(f"Spark master '{effective_master}' không kết nối được. Tự động chuyển sang 'local[*]'.")
                            effective_master = "local[*]"

                    logger.info(
                        f"Initializing SparkSession - App: '{effective_app_name}', Master: '{effective_master}'"
                    )

                    # Build SparkSession with cluster configuration and HDFS defaults
                    builder = (
                        SparkSession.builder.appName(effective_app_name)
                        .master(effective_master)
                        .config("spark.driver.memory", settings.SPARK_DRIVER_MEMORY)
                        .config("spark.executor.memory", settings.SPARK_EXECUTOR_MEMORY)
                        .config("spark.sql.session.timeZone", "UTC")
                        .config("spark.sql.parquet.compression.codec", "snappy")
                    )
                    
                    # Cấu hình HDFS nếu URI hợp lệ
                    if "hdfs://" in settings.HDFS_URI:
                        builder = builder.config("fs.defaultFS", settings.HDFS_URI)

                    # Instantiate SparkSession instance
                    cls._spark_session = builder.getOrCreate()
                    logger.info(f"SparkSession initialized successfully. Version: {cls._spark_session.version}")


        return cls._spark_session

    @classmethod
    def stop_spark_session(cls) -> None:
        """
        Safely shuts down the active SparkSession.
        """
        with cls._lock:
            if cls._spark_session is not None and not cls._spark_session._sc._is_closed:
                logger.info("Stopping active SparkSession...")
                cls._spark_session.stop()
                cls._spark_session = None
                logger.info("SparkSession stopped successfully.")


def get_spark_session(app_name: Optional[str] = None, master: Optional[str] = None) -> SparkSession:
    """
    Convenience function to get active SparkSession.
    """
    return SparkSessionManager.get_spark_session(app_name=app_name, master=master)


def stop_spark_session() -> None:
    """
    Convenience function to stop active SparkSession.
    """
    SparkSessionManager.stop_spark_session()
