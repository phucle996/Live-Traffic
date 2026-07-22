# ==============================================================================
# Production Web Dashboard Integration Tests (tests/api/test_dashboard_api.py)
# Verifies Web Server Health Probes & Static Asset Serving (index.html, style.css, app.js)
# ==============================================================================

import requests
import pytest

WEB_DASHBOARD_URL = "http://localhost:8501"


def is_web_dashboard_running() -> bool:
    """
    Helper function checking if Web Dashboard server is active on port 8501.
    """
    try:
        r = requests.get(f"{WEB_DASHBOARD_URL}/health/live", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not is_web_dashboard_running(), reason="Web Dashboard is not active on port 8501")
def test_web_dashboard_health_live():
    """
    Verifies Liveness probe GET /health/live returns 200 OK.
    """
    response = requests.get(f"{WEB_DASHBOARD_URL}/health/live", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"


@pytest.mark.skipif(not is_web_dashboard_running(), reason="Web Dashboard is not active on port 8501")
def test_web_dashboard_static_index_html():
    """
    Verifies index.html Single Page App is served properly.
    """
    response = requests.get(f"{WEB_DASHBOARD_URL}/", timeout=5)
    assert response.status_code == 200
    assert "Leaflet" in response.text
    assert "Hệ Thống Giao Thông Đô Thị TP.HCM" in response.text


@pytest.mark.skipif(not is_web_dashboard_running(), reason="Web Dashboard is not active on port 8501")
def test_web_dashboard_static_css_js():
    """
    Verifies style.css and app.js static assets are served properly.
    """
    resp_css = requests.get(f"{WEB_DASHBOARD_URL}/css/style.css", timeout=5)
    assert resp_css.status_code == 200
    assert "--bg-dark" in resp_css.text

    resp_js = requests.get(f"{WEB_DASHBOARD_URL}/js/app.js", timeout=5)
    assert resp_js.status_code == 200
    assert "fetchLiveTraffic" in resp_js.text
