# ==============================================================================
# Unit Tests for TomTom API Client & Seed Loader (tests/unit/test_tomtom_client.py)
# Chỉ giữ lại tests chạy trên behavior thực và dữ liệu offline.
# Các tests mock HTTP response đã bị xóa — behavior của TomTom client khi có
# live API key được test qua integration tests với API key thực từ env.
# ==============================================================================

import pandas as pd

from src.ingestion.tomtom_client import TomTomTrafficClient
from src.ingestion.seed_loader import load_seed_csv_files


def test_tomtom_client_missing_api_key():
    """
    Verifies client trả về None gracefully khi API key bị thiếu.
    Đây là boundary condition thực — không cần mock.
    """
    client = TomTomTrafficClient(api_key="")
    result = client.get_flow_segment(10.7769, 106.7009)
    assert result is None


def test_seed_loader_sample_data():
    """
    Tests offline seed CSV loader tải được dữ liệu từ data/seed/.
    Chạy trên tập dữ liệu offline thực (sample_traffic.csv).
    Cần đảm bảo thư mục data/seed/ tồn tại với file CSV trước khi chạy.
    """
    df = load_seed_csv_files("data/seed")
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "CurrentSpeed" in df.columns
    assert "FreeFlowSpeed" in df.columns
