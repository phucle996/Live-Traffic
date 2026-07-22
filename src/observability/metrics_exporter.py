# ==============================================================================
# Python MLOps Prometheus Metrics Exporter (src/observability/metrics_exporter.py)
# Phơi bày các metrics huấn luyện, chất lượng dữ liệu và vòng đời mô hình
# ==============================================================================

import time
from typing import Dict, Any

from src.common.logging_utils import get_logger

# Instantiate logger cho metrics exporter
logger = get_logger(__name__)


class MLOpsMetricsExporter:
    """
    Ghi nhận và phơi bày các Prometheus metrics liên quan đến quy trình MLOps:
    - Thời gian huấn luyện mô hình (training_duration_seconds)
    - Chỉ số chất lượng mô hình (RMSE, MAE, R2)
    - Số lần kiểm tra chất lượng dữ liệu thất bại (data_quality_failures_total)
    - Thời gian chạy Spark job (spark_job_duration_seconds)
    """

    def __init__(self):
        # Khởi tạo cấu trúc lưu trữ metrics nội bộ (có thể tích hợp prometheus_client sau)
        self._metrics: Dict[str, Any] = {
            "training_duration_seconds": 0.0,
            "model_rmse": 0.0,
            "model_mae": 0.0,
            "model_r2": 0.0,
            "data_quality_failures_total": 0,
            "spark_job_duration_seconds": 0.0,
            "last_training_timestamp": None,
        }
        self._training_start: float = 0.0

    def training_start(self) -> None:
        """
        Bắt đầu đo thời gian quá trình huấn luyện mô hình GBTRegressor.
        """
        self._training_start = time.time()
        logger.info("[METRICS] Bắt đầu đo training_duration_seconds...")

    def training_complete(self, rmse: float, mae: float, r2: float) -> None:
        """
        Ghi nhận kết quả huấn luyện hoàn chỉnh: thời gian, RMSE, MAE, R2.
        """
        duration = time.time() - self._training_start
        self._metrics["training_duration_seconds"] = duration
        self._metrics["model_rmse"] = rmse
        self._metrics["model_mae"] = mae
        self._metrics["model_r2"] = r2
        self._metrics["last_training_timestamp"] = time.time()
        logger.info(f"[METRICS] training_duration={duration:.2f}s RMSE={rmse:.4f} MAE={mae:.4f} R2={r2:.4f}")

    def record_data_quality_failure(self) -> None:
        """
        Tăng bộ đếm số lần kiểm tra chất lượng dữ liệu thất bại.
        """
        self._metrics["data_quality_failures_total"] += 1
        logger.warning(f"[METRICS] data_quality_failures_total={self._metrics['data_quality_failures_total']}")

    def record_spark_job_duration(self, duration_seconds: float) -> None:
        """
        Ghi nhận thời gian chạy Spark batch job (ETL / Feature Engineering).
        """
        self._metrics["spark_job_duration_seconds"] = duration_seconds
        logger.info(f"[METRICS] spark_job_duration_seconds={duration_seconds:.2f}s")

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Trả về toàn bộ metrics snapshot hiện tại để phơi bày qua HTTP.
        """
        return dict(self._metrics)
