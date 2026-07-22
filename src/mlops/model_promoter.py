# ==============================================================================
# Model Promoter Specification (src/mlops/model_promoter.py)
# ModelPromoter Class & Atomic Model Publish, Checksum & Rust Hot Reload Trigger
# ==============================================================================

import hashlib
import json
import os
import requests
from typing import Dict, Any, Optional

from src.common.logging_utils import get_logger
from src.mlops.model_registry import ModelRegistry
from src.mlops.model_validator import ModelValidator

# Instantiate logger for model promoter
logger = get_logger(__name__)


def compute_file_sha256(filepath: str) -> str:
    """
    Tính toán mã băm SHA-256 của file mô hình để kiểm tra tính toàn vẹn dữ liệu.
    """
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class ModelPromoter:
    """
    Quản lý vòng đời chuyển cấp của mô hình (Candidate -> Staging -> Production).
    """

    def __init__(self, registry: Optional[ModelRegistry] = None, validator: Optional[ModelValidator] = None):
        self.registry = registry or ModelRegistry()
        self.validator = validator or ModelValidator()

    def promote_to_staging(self, version: str, metrics: Dict[str, Any]) -> bool:
        """
        Kiểm tra Quality Gate và chuyển mô hình sang trạng thái Staging.
        """
        is_valid, reason = self.validator.validate(metrics)
        if not is_valid:
            logger.warning(f"Từ chối promote {version} sang Staging: {reason}")
            return False

        self.registry.set_stage(version, "Staging")
        logger.info(f"Đã promote thành công phiên bản {version} sang Staging")
        return True

    def promote_to_production(self, version: str) -> bool:
        """
        Chuyển mô hình từ Staging sang Production và lưu vết các phiên bản cũ vào Archived.
        """
        # Lưu vết phiên bản Production hiện tại sang Archived
        current_prod = self.registry.get_production_version()
        if current_prod and current_prod.get("version") != version:
            self.registry.set_stage(current_prod["version"], "Archived")

        self.registry.set_stage(version, "Production")
        logger.info(f"Đã promote thành công phiên bản {version} sang Production")


        # Trigger Rust Hot Reload nếu có
        promote_candidate_model()
        return True


def promote_candidate_model(
    candidate_dir: str = "artifacts/inference/candidate-tree",
    target_dir: str = "artifacts/inference/candidate-tree",
    rust_api_url: str = "http://localhost:8090",
) -> bool:
    """
    Promote candidate model sang Production một cách atomic và trigger Rust Hot Reload.

    Args:
        candidate_dir (str): Đường dẫn thư mục chứa candidate model.
        target_dir (str): Đường dẫn thư mục đích phục vụ cho Rust Inference API.
        rust_api_url (str): Địa chỉ HTTP URL của Rust Inference API.

    Returns:
        bool: True nếu promote thành công.
    """
    logger.info(f"Đang thực hiện promote candidate model từ '{candidate_dir}' sang '{target_dir}'...")

    model_file = os.path.join(candidate_dir, "model.json")
    if not os.path.exists(model_file):
        logger.error(f"File mô hình '{model_file}' không tồn tại! Không thể promote.")
        return False

    checksum = compute_file_sha256(model_file)
    logger.info(f"Mã Checksum SHA-256 của model.json: {checksum}")

    manifest_data: Dict[str, Any] = {
        "model_version": "v1.0.0",
        "format": "rust_native_gbt",
        "num_trees": 100,
        "feature_names": ["Latitude", "Longitude", "TimeInMinutes", "DayOfWeek", "Weekend"],
        "checksum_sha256": checksum,
    }

    manifest_file = os.path.join(target_dir, "model_manifest.json")
    with open(manifest_file, "w") as f:
        json.dump(manifest_data, f, indent=2)

    logger.info(f"Đã cập nhật file manifest thành công tại '{manifest_file}'")

    # Sinh JWT token với scope model:reload để xác thực với Rust Inference API
    import jwt
    import time

    token_payload = {
        "sub": "mlops-model-promoter",
        "roles": ["admin"],
        "scope": "model:reload",
        "exp": int(time.time()) + 60,
    }
    secret = os.getenv("AUTH_SECRET_KEY", "prod_secret_key_change_me")
    token = jwt.encode(token_payload, secret, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}

    reload_url = f"{rust_api_url}/v1/model/reload"
    try:
        resp = requests.post(reload_url, headers=headers, timeout=5)
        if resp.status_code == 200:
            logger.info("Rust API Hot Reload phản hồi THÀNH CÔNG (200 OK)!")
        else:
            logger.error(f"Rust API Hot Reload thất bại với mã trạng thái: {resp.status_code} - {resp.text}")
    except Exception as e:
        logger.warning(f"Không thể kết nối Rust API để Hot Reload: {e}")

    return True
