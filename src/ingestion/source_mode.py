# ==============================================================================
# Data Source Mode Enum Definition (src/ingestion/source_mode.py)
# Defines Allowed Data Source Modes: OFFLINE, ONLINE, AUTO
# ==============================================================================

from enum import Enum


class DataSourceMode(str, Enum):
    """
    Enum representing supported data source modes:
    - OFFLINE: Only use historical Lab CSV data from data/lab_raw/*.csv
    - ONLINE: Call live TomTom Traffic Flow Segment API
    - AUTO: Prefer TomTom API if key exists and healthy; fallback to Lab offline CSV otherwise
    """
    OFFLINE = "offline"
    ONLINE = "online"
    AUTO = "auto"
