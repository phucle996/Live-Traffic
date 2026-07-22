# ==============================================================================
# Model Validator (src/mlops/model_validator.py)
# Evaluates candidate model metrics against promotion_rules.yaml gate criteria
# ==============================================================================

from pathlib import Path
from typing import Dict, Any, Tuple

import yaml

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for model validator
logger = get_logger(__name__)

# Path to promotion rules specification file
PROMOTION_RULES_FILE = PROJECT_ROOT / "config" / "mlops" / "promotion_rules.yaml"


class ModelValidator:
    """
    Evaluates whether a candidate model satisfies all configured promotion gate criteria.
    Returns (passed: bool, reasons: list[str]) for each validation outcome.
    """

    def __init__(self):
        # Load promotion rules from config/mlops/promotion_rules.yaml
        with open(PROMOTION_RULES_FILE, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        self._rules: Dict[str, Any] = cfg["promotion_rules"]

    def validate(self, metrics: Dict[str, float]) -> Tuple[bool, list]:
        """
        Validates candidate model metrics against each promotion gate rule.

        Args:
            metrics: Dict containing 'rmse', 'r2', 'test_rows' from training run.

        Returns:
            Tuple[bool, list]: (all_passed, list_of_failure_reasons)
        """
        failures = []

        rmse = metrics.get("rmse", float("inf"))
        r2 = metrics.get("r2", -float("inf"))
        test_rows = metrics.get("test_rows", 0)

        # Gate 1: RMSE must not exceed maximum
        if rmse > self._rules["maximum_rmse"]:
            failures.append(
                f"RMSE {rmse:.4f} exceeds maximum allowed {self._rules['maximum_rmse']}"
            )

        # Gate 2: R² must meet minimum requirement
        if r2 < self._rules["minimum_r2"]:
            failures.append(
                f"R² {r2:.4f} below minimum required {self._rules['minimum_r2']}"
            )

        # Gate 3: Test dataset must have enough rows for statistical significance
        if test_rows < self._rules["minimum_test_rows"]:
            failures.append(
                f"Test rows {test_rows} below minimum required {self._rules['minimum_test_rows']}"
            )

        passed = len(failures) == 0
        if passed:
            logger.info("ModelValidator: Candidate model PASSED all promotion gates.")
        else:
            logger.warning(f"ModelValidator: Candidate model FAILED promotion gates: {failures}")

        return passed, failures
