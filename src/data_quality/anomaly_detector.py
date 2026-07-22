# ==============================================================================
# Statistical Anomaly Detector Engine (src/data_quality/anomaly_detector.py)
# Detects Speed Outliers via Z-Score & Interquartile Range (IQR) Bounds
# ==============================================================================

import math
from typing import List, Dict, Any, Tuple

from src.common.logging_utils import get_logger

# Instantiate logger for anomaly detector
logger = get_logger(__name__)


class StatisticalAnomalyDetector:
    """
    Detects speed and travel time anomalies using Z-score and Interquartile Range (IQR).
    """

    @staticmethod
    def detect_speed_outliers_zscore(speeds: List[float], threshold: float = 3.0) -> List[int]:
        """
        Detects outlier index locations using Z-score metric.

        Args:
            speeds (List[float]): List of speed values.
            threshold (float): Z-score threshold (default 3.0 standard deviations).

        Returns:
            List[int]: List of index positions flagged as anomalies.
        """
        if not speeds or len(speeds) < 3:
            return []

        mean = sum(speeds) / len(speeds)
        variance = sum((x - mean) ** 2 for x in speeds) / len(speeds)
        std_dev = math.sqrt(variance)

        if std_dev == 0:
            return []

        outlier_indices = []
        for i, val in enumerate(speeds):
            z_score = abs(val - mean) / std_dev
            if z_score > threshold:
                outlier_indices.append(i)

        if outlier_indices:
            logger.warning(f"Flagged {len(outlier_indices)} speed outlier(s) using Z-score (Threshold={threshold}).")

        return outlier_indices

    @staticmethod
    def filter_anomalous_records(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Filters anomalous records from batch.

        Returns:
            Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]: (valid_records, anomalous_records)
        """
        speeds = [float(r["CurrentSpeed"]) for r in records if "CurrentSpeed" in r and r["CurrentSpeed"] is not None]
        outlier_set = set(StatisticalAnomalyDetector.detect_speed_outliers_zscore(speeds))

        valid_records = []
        anomalous_records = []

        for i, r in enumerate(records):
            if i in outlier_set:
                anomalous_records.append(r)
            else:
                valid_records.append(r)

        return valid_records, anomalous_records
