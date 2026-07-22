# ==============================================================================
# Unit Tests for Hybrid Data Source Router (tests/unit/test_source_router.py)
# ==============================================================================

import json
from pathlib import Path
from src.common.config import PROJECT_ROOT
from src.ingestion.source_router import SourceRouter


def test_source_router_offline_mode():
    """
    Tests that explicit 'offline' mode resolves to 'offline' without calling API.
    """
    router = SourceRouter(mode="offline")
    resolved = router.resolve_source()
    assert resolved == "offline"


def test_source_router_auto_fallback_when_missing_key():
    """
    Tests that 'auto' mode falls back transparently to 'offline' when API key is missing.
    """
    router = SourceRouter(mode="auto", api_key="")
    resolved = router.resolve_source()
    assert resolved == "offline"

    # Verify source resolution report artifact exists
    report_path = PROJECT_ROOT / "artifacts" / "reports" / "source_resolution.json"
    assert report_path.exists()

    with open(report_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    assert report["requested_mode"] == "auto"
    assert report["resolved_mode"] == "offline"
    assert report["fallback"] is True
    assert report["fallback_reason"] == "MISSING_API_KEY"


if __name__ == "__main__":
    test_source_router_offline_mode()
    test_source_router_auto_fallback_when_missing_key()
    print("All test_source_router unit tests PASSED!")
