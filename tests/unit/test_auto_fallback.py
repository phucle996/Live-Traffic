# ==============================================================================
# Unit Tests for Auto Mode & Fallback Mechanism (tests/unit/test_auto_fallback.py)
# Kiểm tra logic routing offline/online không dùng mock — chỉ test real behavior
# ==============================================================================

from src.ingestion.source_router import SourceRouter
from src.ingestion.fallback_report import FallbackReporter


def test_auto_mode_missing_api_key_fallback():
    """
    Verifies rằng AUTO mode fall back sang OFFLINE khi API key bị thiếu.
    Đây là behavior thực, không cần mock — logic nằm hoàn toàn trong SourceRouter.
    """
    router = SourceRouter(mode="auto", api_key="")
    resolved = router.resolve_source()
    assert resolved == "offline"

    badge = FallbackReporter.get_ui_badge_info()
    assert badge["is_live"] is False
    assert "Fallback: MISSING_API_KEY" in badge["label"]


def test_offline_mode_always_resolves_offline():
    """
    Verifies rằng explicit OFFLINE mode luôn resolve sang offline, không cần API.
    """
    router = SourceRouter(mode="offline")
    resolved = router.resolve_source()
    assert resolved == "offline"
