# ==============================================================================
# Unit Tests for Daily Request Budget Guard (tests/unit/test_request_budget.py)
# ==============================================================================

from src.ingestion.request_budget import RequestBudgetGuard


def test_request_budget_tracking():
    """
    Verifies that RequestBudgetGuard tracks and enforces daily API call limit.
    """
    guard = RequestBudgetGuard(daily_budget=5)
    guard.data["requests_count"] = 0

    assert guard.can_make_requests(3) is True
    guard.record_requests(3)

    assert guard.can_make_requests(3) is False
    assert guard.can_make_requests(2) is True


if __name__ == "__main__":
    test_request_budget_tracking()
    print("All test_request_budget unit tests PASSED!")
