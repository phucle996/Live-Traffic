# ==============================================================================
# Hybrid Data Source Router (src/ingestion/source_router.py)
# Resolves Data Source Mode (offline vs online) & Manages Transparent Fallback Logging
# ==============================================================================

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

from src.common.config import settings, PROJECT_ROOT
from src.common.logging_utils import get_logger
from src.ingestion.source_mode import DataSourceMode

# Instantiate logger for source router
logger = get_logger(__name__)


class SourceRouter:
    """
    Resolves data source execution mode ('offline' vs 'online') and manages transparent fallback reports.
    """

    def __init__(self, mode: str = None, api_key: str = None):
        self.mode_str = (mode or settings.DATA_SOURCE_MODE).lower()
        self.api_key = api_key or settings.TOMTOM_API_KEY

    def check_api_health(self) -> Tuple[bool, str]:
        """
        Checks if TomTom API key is present and perform lightweight ping health check.

        Returns:
            Tuple[bool, str]: (is_healthy, failure_reason)
        """
        # Check 1: API key presence
        if not self.api_key or self.api_key in ("dummy_api_key_for_testing", "NOT_SET", ""):
            return False, "MISSING_API_KEY"

        # Check 2: Connectivity ping to TomTom endpoint (Simulated / Ping)
        import requests
        try:
            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={self.api_key}&point=10.7769,106.7009&unit=KMPH"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                return True, "API_HEALTHY"
            elif resp.status_code in (401, 403):
                return False, "INVALID_API_KEY"
            else:
                return False, f"API_ERROR_HTTP_{resp.status_code}"
        except Exception as e:
            return False, f"NETWORK_ERROR_{type(e).__name__}"

    def resolve_source(self) -> str:
        """
        Resolves active data source ('offline' or 'online') and logs resolution report.

        Returns:
            str: Resolved mode string ("offline" or "online").
        """
        logger.info(f"Resolving Data Source Mode - Configured Mode: '{self.mode_str}'")

        resolution_report = {
            "requested_mode": self.mode_str,
            "resolved_mode": "offline",
            "fallback": False,
            "fallback_reason": None,
            "checked_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

        # Case 1: Explicit OFFLINE Mode
        if self.mode_str == DataSourceMode.OFFLINE:
            resolution_report["resolved_mode"] = "offline"
            logger.info("Data Source Mode resolved to 'OFFLINE' (Lab Raw CSV data).")

        # Case 2: Explicit ONLINE Mode
        elif self.mode_str == DataSourceMode.ONLINE:
            is_healthy, reason = self.check_api_health()
            if not is_healthy:
                logger.error(f"DATA_SOURCE_MODE=online but API check failed: '{reason}'. Pipeline fail-fast.")
                resolution_report["resolved_mode"] = "online"
                resolution_report["fallback_reason"] = reason
                self._save_resolution_report(resolution_report)
                raise RuntimeError(f"DATA_SOURCE_MODE=online failed health check: {reason}")
            
            resolution_report["resolved_mode"] = "online"
            logger.info("Data Source Mode resolved to 'ONLINE' (TomTom Live API).")

        # Case 3: AUTO Mode
        else:
            is_healthy, reason = self.check_api_health()
            if is_healthy:
                resolution_report["resolved_mode"] = "online"
                logger.info("Auto Mode: TomTom API healthy. Resolved to 'ONLINE'.")
            else:
                resolution_report["resolved_mode"] = "offline"
                resolution_report["fallback"] = True
                resolution_report["fallback_reason"] = reason
                logger.warning(
                    f"Auto Mode Fallback Warning: TomTom API unavailable ({reason}). "
                    f"Falling back to 'OFFLINE' Lab data. NO SILENT FALLBACK."
                )

        self._save_resolution_report(resolution_report)
        return resolution_report["resolved_mode"]

    def _save_resolution_report(self, report: Dict[str, Any]) -> None:
        """
        Saves source resolution report JSON to artifacts/reports/source_resolution.json.
        """
        out_dir = PROJECT_ROOT / "artifacts" / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "source_resolution.json"

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Saved source resolution report to '{out_path}'")


def resolve_active_data_source() -> str:
    """
    Convenience function to resolve data source mode.
    """
    router = SourceRouter()
    return router.resolve_source()
