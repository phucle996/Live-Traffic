# ==============================================================================
# Drift Detector (src/mlops/drift_detector.py)
# Detects feature data drift and prediction distribution shifts
# Uses Kolmogorov-Smirnov (KS) statistic and mean/std comparison
# ==============================================================================

import math
from typing import Dict, Any, Tuple, List
from pathlib import Path

import yaml

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for drift detector
logger = get_logger(__name__)

# Path to drift threshold configuration
DRIFT_THRESHOLDS_FILE = PROJECT_ROOT / "config" / "mlops" / "drift_thresholds.yaml"


def _ks_statistic(baseline: List[float], live: List[float]) -> float:
    """
    Computes simplified Kolmogorov-Smirnov test statistic.
    Measures maximum absolute difference between two empirical CDFs.
    Returns KS statistic in range [0, 1]. Higher = more drift.
    """
    if not baseline or not live:
        return 0.0

    # Build empirical CDFs by sorting and normalizing
    all_vals = sorted(set(baseline + live))
    n_base = len(baseline)
    n_live = len(live)

    # Convert lists to frequency maps
    base_set = sorted(baseline)
    live_set = sorted(live)

    ks_max = 0.0
    base_i = 0
    live_i = 0

    for val in all_vals:
        # Advance indices until we pass this value
        while base_i < n_base and base_set[base_i] <= val:
            base_i += 1
        while live_i < n_live and live_set[live_i] <= val:
            live_i += 1

        # Compute empirical CDF difference at this value
        diff = abs(base_i / n_base - live_i / n_live)
        if diff > ks_max:
            ks_max = diff

    return ks_max


class DriftDetector:
    """
    Evaluates statistical drift between training baseline distributions
    and live observation distributions.
    """

    def __init__(self):
        with open(DRIFT_THRESHOLDS_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        self._thresholds = cfg["drift_thresholds"]

    def detect_feature_drift(
        self,
        baseline_speeds: List[float],
        live_speeds: List[float],
    ) -> Tuple[bool, float]:
        """
        Computes KS statistic between baseline and live speed distributions.

        Returns:
            Tuple[bool, float]: (drift_detected, ks_stat)
        """
        ks_stat = _ks_statistic(baseline_speeds, live_speeds)
        threshold = self._thresholds["feature_drift_ks_stat"]
        drift_detected = ks_stat > threshold

        if drift_detected:
            logger.warning(
                f"DriftDetector: Feature drift detected. KS={ks_stat:.4f} > threshold={threshold}"
            )
        else:
            logger.info(f"DriftDetector: No feature drift. KS={ks_stat:.4f}")

        return drift_detected, ks_stat

    def detect_prediction_drift(
        self,
        baseline_predictions: List[float],
        live_predictions: List[float],
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Compares mean and std deviation of production predictions vs baseline.

        Returns:
            Tuple[bool, dict]: (drift_detected, drift_stats)
        """
        if not baseline_predictions or not live_predictions:
            return False, {}

        # Compute baseline distribution statistics
        base_mean = sum(baseline_predictions) / len(baseline_predictions)
        base_var = sum((x - base_mean) ** 2 for x in baseline_predictions) / len(baseline_predictions)
        base_std = math.sqrt(base_var)

        # Compute live distribution statistics
        live_mean = sum(live_predictions) / len(live_predictions)
        live_var = sum((x - live_mean) ** 2 for x in live_predictions) / len(live_predictions)
        live_std = math.sqrt(live_var)

        mean_delta = abs(live_mean - base_mean)
        std_ratio = (live_std / base_std) if base_std > 0 else 1.0

        drift_detected = (
            mean_delta > self._thresholds["prediction_drift_mean_delta"] or
            std_ratio > self._thresholds["prediction_drift_std_ratio"]
        )

        stats = {
            "baseline_mean": round(base_mean, 4),
            "live_mean": round(live_mean, 4),
            "mean_delta": round(mean_delta, 4),
            "std_ratio": round(std_ratio, 4),
        }

        if drift_detected:
            logger.warning(f"DriftDetector: Prediction drift detected. Stats={stats}")
        else:
            logger.info(f"DriftDetector: No prediction drift. Stats={stats}")

        return drift_detected, stats
