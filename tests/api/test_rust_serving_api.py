# ==============================================================================
# Rust Prediction API Integration Tests (tests/api/test_rust_serving_api.py)
# Verifies High-Performance Axum Serving Endpoints with JWT Authentication
# ==============================================================================

import time
import requests
import pytest
import jwt

RUST_API_BASE_URL = "http://localhost:8090"
DEFAULT_SECRET = "prod_secret_key_change_me"


def create_test_jwt(sub: str, roles: list, scope: str, secret: str = DEFAULT_SECRET) -> str:
    """
    Helper function sinh JWT token phục vụ tests.
    """
    payload = {
        "sub": sub,
        "roles": roles,
        "scope": scope,
        "exp": int(time.time()) + 3600,
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def is_rust_api_running() -> bool:
    """
    Helper function checking if Rust Inference API container is active on port 8090.
    """
    try:
        r = requests.get(f"{RUST_API_BASE_URL}/health/live", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


@pytest.mark.skipif(not is_rust_api_running(), reason="Rust API container is not active on port 8090")
def test_rust_health_live():
    """
    Verifies Liveness probe endpoint GET /health/live returns 200 OK.
    """
    response = requests.get(f"{RUST_API_BASE_URL}/health/live", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"


@pytest.mark.skipif(not is_rust_api_running(), reason="Rust API container is not active on port 8090")
def test_rust_health_ready():
    """
    Verifies Readiness probe endpoint GET /health/ready returns 200 OK after warmup.
    """
    response = requests.get(f"{RUST_API_BASE_URL}/health/ready", timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY"
    assert data["model_loaded"] is True


@pytest.mark.skipif(not is_rust_api_running(), reason="Rust API container is not active on port 8090")
def test_rust_get_model_info():
    """
    Verifies GET /v1/model returns active model metadata and SHA-256 checksum.
    Yêu cầu token có scope model:read.
    """
    token = create_test_jwt("user-123", ["viewer"], "model:read")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{RUST_API_BASE_URL}/v1/model", headers=headers, timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["num_trees"] == 100
    assert "checksum_sha256" in data["manifest"]


@pytest.mark.skipif(not is_rust_api_running(), reason="Rust API container is not active on port 8090")
def test_rust_single_prediction():
    """
    Verifies POST /v1/predictions single record prediction.
    Yêu cầu token có scope prediction:execute.
    """
    token = create_test_jwt("user-123", ["viewer"], "prediction:execute")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "latitude": 10.7781,
        "longitude": 106.6952,
        "free_flow_speed": 45.0,
        "confidence": 0.95,
        "street_name": "Nam Kỳ Khởi Nghĩa"
    }
    response = requests.post(f"{RUST_API_BASE_URL}/v1/predictions", headers=headers, json=payload, timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_speed_kmh" in data
    assert data["data_source"] == "rust_native_tree_engine"
    assert "model_version" in data


@pytest.mark.skipif(not is_rust_api_running(), reason="Rust API container is not active on port 8090")
def test_rust_batch_prediction():
    """
    Verifies POST /v1/predictions/batch batch prediction endpoint.
    Yêu cầu token có scope prediction:execute.
    """
    token = create_test_jwt("user-123", ["viewer"], "prediction:execute")
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "records": [
            {"latitude": 10.7781, "longitude": 106.6952},
            {"latitude": 10.7983, "longitude": 106.7115}
        ]
    }
    response = requests.post(f"{RUST_API_BASE_URL}/v1/predictions/batch", headers=headers, json=payload, timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 2
    assert len(data["predictions"]) == 2


@pytest.mark.skipif(not is_rust_api_running(), reason="Rust API container is not active on port 8090")
def test_rust_atomic_model_reload():
    """
    Verifies POST /v1/model/reload zero-downtime atomic model swap.
    Yêu cầu token có đặc quyền model:reload hoặc admin.
    """
    token = create_test_jwt("user-123", ["operator"], "model:reload")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(f"{RUST_API_BASE_URL}/v1/model/reload", headers=headers, timeout=5)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
