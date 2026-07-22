# ==============================================================================
# Daily Request Budget Guard Engine (src/ingestion/request_budget.py)
# Enforces Daily API Request Quota Limits to Prevent Overuse & Quota Exhaustion
# ==============================================================================

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for request budget guard
logger = get_logger(__name__)


class RequestBudgetGuard:
    """
    Tracks daily API request counts and enforces ONLINE_REQUEST_BUDGET_PER_DAY limit.
    """

    def __init__(self, daily_budget: int = None, storage_file: Path = None):
        self.daily_budget = daily_budget or int(getattr(settings, "ONLINE_REQUEST_BUDGET_PER_DAY", 2000))
        self.storage_file = storage_file or (PROJECT_ROOT / "artifacts" / "reports" / "request_budget.json")
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.data: Dict[str, Any] = self._load_budget_data()

    def _load_budget_data(self) -> Dict[str, Any]:
        """
        Loads daily budget tracking data from JSON artifact.
        """
        if self.storage_file.exists():
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load request budget JSON at '{self.storage_file}': {e}")

        return {"date": self._current_date_str(), "requests_count": 0}

    def _current_date_str(self) -> str:
        """
        Returns current UTC date string YYYY-MM-DD.
        """
        return datetime.utcnow().strftime("%Y-%m-%d")

    def _reset_if_new_day(self) -> None:
        """
        Resets request counter if UTC date has advanced.
        """
        today = self._current_date_str()
        if self.data.get("date") != today:
            self.data["date"] = today
            self.data["requests_count"] = 0
            self._save_budget_data()

    def can_make_requests(self, count: int = 1) -> bool:
        """
        Checks if requested number of API calls exceeds remaining daily budget.

        Args:
            count (int): Planned number of API calls.

        Returns:
            bool: True if within budget, False if budget exceeded.
        """
        self._reset_if_new_day()
        current_count = self.data.get("requests_count", 0)
        return (current_count + count) <= self.daily_budget

    def record_requests(self, count: int = 1) -> None:
        """
        Increments daily request counter and saves state.

        Args:
            count (int): Number of executed API calls.
        """
        self._reset_if_new_day()
        self.data["requests_count"] = self.data.get("requests_count", 0) + count
        self._save_budget_data()
        logger.info(f"Updated API request count: {self.data['requests_count']}/{self.daily_budget} for {self.data['date']}")

    def _save_budget_data(self) -> None:
        """
        Saves budget tracking state JSON to disk.
        """
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2)
