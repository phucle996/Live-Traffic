# ==============================================================================
# Transparent Fallback Reporter Engine (src/ingestion/fallback_report.py)
# Formats Source Resolution Metadata & Exposes Status Badges for UI & Logging
# ==============================================================================

import json
from pathlib import Path
from typing import Dict, Any

from src.common.config import PROJECT_ROOT
from src.common.logging_utils import get_logger

# Instantiate logger for fallback reporter
logger = get_logger(__name__)


class FallbackReporter:
    """
    Manages structured fallback status reports and UI badge metadata.
    """

    REPORT_PATH = PROJECT_ROOT / "artifacts" / "reports" / "source_resolution.json"

    @classmethod
    def get_latest_resolution_report(cls) -> Dict[str, Any]:
        """
        Reads latest source resolution report from artifacts/reports/source_resolution.json.

        Returns:
            Dict[str, Any]: Source resolution report dictionary.
        """
        if cls.REPORT_PATH.exists():
            try:
                with open(cls.REPORT_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read source resolution report at '{cls.REPORT_PATH}': {e}")

        return {
            "requested_mode": "offline",
            "resolved_mode": "offline",
            "fallback": False,
            "fallback_reason": None,
            "checked_at": "N/A",
        }

    @classmethod
    def get_ui_badge_info(cls) -> Dict[str, str]:
        """
        Returns UI status badge info dictionary for Streamlit Dashboard display.

        Returns:
            Dict[str, str]: Badge text, color, and description.
        """
        report = cls.get_latest_resolution_report()
        resolved_mode = report.get("resolved_mode", "offline")
        is_fallback = report.get("fallback", False)
        reason = report.get("fallback_reason", "OFFLINE_MODE")

        if resolved_mode == "online":
            return {
                "label": "LIVE OBSERVATION",
                "color": "#38A169", # Green
                "description": "Nguồn: TomTom Traffic API thời gian thực",
                "is_live": True,
            }
        elif is_fallback:
            return {
                "label": f"OFFLINE SNAPSHOT (Fallback: {reason})",
                "color": "#DD6B20", # Orange
                "description": f"Cảnh báo: Fallback tự động sang dữ liệu Lab lịch sử do TomTom API không khả dụng ({reason}).",
                "is_live": False,
            }
        else:
            return {
                "label": "OFFLINE SNAPSHOT",
                "color": "#3182CE", # Blue
                "description": "Nguồn: Bộ dữ liệu thô lịch sử Lab 5",
                "is_live": False,
            }
