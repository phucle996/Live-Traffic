# ==============================================================================
# Production Security & Ingress Integration Tests (tests/api/test_production_security.py)
# Verifies Nginx Ingress Gateway Routing and JWT Authentication/Authorization Gates
# ==============================================================================

import time
import requests
import pytest
import jwt

INGRESS_GATEWAY_URL = "http://localhost"
DEFAULT_SECRET = "prod_secret_key_change_me"


def create_test_jwt(sub: str, roles: list, scope: str, secret: str = DEFAULT_SECRET) -> str:
    """
    Sinh JWT token kiểm thử sử dụng PyJWT.
    """
    payload = {
        "sub": sub,
        "roles": roles,
        "scope": scope,
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def is_ingress_gateway_running() -> bool:
    """
    Helper function checking if Nginx Ingress Gateway is active on port 80.
    Sử dụng root endpoint / (Dashboard) không bị bảo mật làm liveness check.
    """
    try:
        r = requests.get(f"{INGRESS_GATEWAY_URL}/", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not is_ingress_gateway_running(), reason="Nginx Ingress Gateway is not active on port 80")
def test_ingress_routing_dashboard_root():
    """
    Verifies Nginx Ingress routes / to Web Dashboard (Port 8501) - Không yêu cầu Auth.
    """
    response = requests.get(f"{INGRESS_GATEWAY_URL}/", timeout=5)
    assert response.status_code == 200
    assert "Hệ Thống Giao Thông Đô Thị TP.HCM" in response.text


@pytest.mark.skipif(not is_ingress_gateway_running(), reason="Nginx Ingress Gateway is not active on port 80")
def test_ingress_routing_traffic_live_security_gates():
    """
    Verifies Go Live API /v1/traffic/live authentication & authorization gates.
    """
    url = f"{INGRESS_GATEWAY_URL}/v1/traffic/live"

    # 1. Không truyền token -> 401
    r_no_token = requests.get(url, timeout=5)
    assert r_no_token.status_code == 401

    # 2. Truyền token sai chữ ký -> 401
    token_bad_signature = create_test_jwt("user-123", ["viewer"], "traffic:read", secret="wrong_secret_key")
    r_bad_sig = requests.get(url, headers={"Authorization": f"Bearer {token_bad_signature}"}, timeout=5)
    assert r_bad_sig.status_code == 401

    # 3. Truyền token đúng nhưng thiếu scope -> 403
    token_missing_scope = create_test_jwt("user-123", ["viewer"], "prediction:execute")
    r_no_scope = requests.get(url, headers={"Authorization": f"Bearer {token_missing_scope}"}, timeout=5)
    assert r_no_scope.status_code == 403

    # 4. Truyền token hợp lệ -> 200
    token_valid = create_test_jwt("user-123", ["viewer"], "traffic:read")
    r_valid = requests.get(url, headers={"Authorization": f"Bearer {token_valid}"}, timeout=5)
    assert r_valid.status_code == 200
    assert "traffic_data" in r_valid.json()


@pytest.mark.skipif(not is_ingress_gateway_running(), reason="Nginx Ingress Gateway is not active on port 80")
def test_ingress_routing_rust_predictions_security_gates():
    """
    Verifies Rust Inference API /v1/predictions authentication & authorization gates.
    """
    url = f"{INGRESS_GATEWAY_URL}/v1/predictions"
    payload = {
        "latitude": 10.7781,
        "longitude": 106.6952,
        "free_flow_speed": 45.0,
        "confidence": 0.95,
        "street_name": "Nam Kỳ Khởi Nghĩa",
    }

    # 1. Không truyền token -> 401
    r_no_token = requests.post(url, json=payload, timeout=5)
    assert r_no_token.status_code == 401

    # 2. Truyền token sai chữ ký -> 401
    token_bad_signature = create_test_jwt("user-123", ["viewer"], "prediction:execute", secret="wrong_secret_key")
    r_bad_sig = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token_bad_signature}"}, timeout=5)
    assert r_bad_sig.status_code == 401

    # 3. Truyền token đúng nhưng thiếu scope -> 403
    token_missing_scope = create_test_jwt("user-123", ["viewer"], "traffic:read")
    r_no_scope = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token_missing_scope}"}, timeout=5)
    assert r_no_scope.status_code == 403

    # 4. Truyền token hợp lệ -> 200
    token_valid = create_test_jwt("user-123", ["viewer"], "prediction:execute")
    r_valid = requests.post(url, json=payload, headers={"Authorization": f"Bearer {token_valid}"}, timeout=5)
    assert r_valid.status_code == 200
    assert "predicted_speed_kmh" in r_valid.json()
