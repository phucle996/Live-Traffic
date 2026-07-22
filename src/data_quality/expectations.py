# ==============================================================================
# Data Quality Expectations (src/data_quality/expectations.py)
# Phase HERE-6 — Quy Tắc Kiểm Tra Chất Lượng Dữ Liệu Traffic Flow
# ==============================================================================

from typing import Dict, Any, List

QUALITY_RULES = [
    {
        "name": "valid_speed_range",
        "description": "Vận tốc thực tế phải trong khoảng từ 0 đến 150 km/h",
        "condition": "current_speed_kph >= 0.0 AND current_speed_kph <= 150.0"
    },
    {
        "name": "valid_free_flow_speed",
        "description": "Vận tốc tự do phải lớn hơn 0",
        "condition": "free_flow_speed_kph > 0.0 AND free_flow_speed_kph <= 150.0"
    },
    {
        "name": "valid_confidence",
        "description": "Độ tin cậy dữ liệu phải từ 0.0 đến 1.0",
        "condition": "confidence >= 0.0 AND confidence <= 1.0"
    },
    {
        "name": "valid_coordinates",
        "description": "Tọa độ địa lý phải nằm trong phạm vi TP.HCM",
        "condition": "latitude >= 10.0 AND latitude <= 11.5 AND longitude >= 106.0 AND longitude <= 107.5"
    },
    {
        "name": "valid_provider",
        "description": "Provider không được rỗng",
        "condition": "provider IS NOT NULL AND length(provider) > 0"
    }
]

def apply_quality_filters(df):
    """
    Áp dụng các quy tắc lọc dữ liệu hợp lệ trên PySpark DataFrame.
    """
    valid_df = df
    for rule in QUALITY_RULES:
        valid_df = valid_df.filter(rule["condition"])
    return valid_df
