# ==============================================================================
# Abstract Secret Provider Engine (src/security/secret_provider.py)
# Reads Docker Secrets (/run/secrets/), Env Vars, or Vault Files with Auto-Masking
# ==============================================================================

import os
from pathlib import Path
from typing import Optional, Dict

from src.common.logging_utils import get_logger

# Instantiate logger for secret provider
logger = get_logger(__name__)


class SecretProvider:
    """
    Retrieves secret values across Docker Secrets (/run/secrets/), Environment Variables, or Vault files.
    """

    DOCKER_SECRETS_DIR = Path("/run/secrets")

    @classmethod
    def get_secret(cls, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieves secret value using priority hierarchy:
        1. Docker Secrets filesystem (/run/secrets/<secret_name>)
        2. Environment variables (os.getenv(<secret_name>))
        3. Default fallback value

        Args:
            secret_name (str): Key/name of target secret.
            default (Optional[str]): Default fallback value if not found.

        Returns:
            Optional[str]: Secret string value.
        """
        # Step 1: Check Docker Secrets mounted file
        docker_secret_file = cls.DOCKER_SECRETS_DIR / secret_name
        if docker_secret_file.exists() and docker_secret_file.is_file():
            try:
                with open(docker_secret_file, "r", encoding="utf-8") as f:
                    value = f.read().strip()
                    if value:
                        logger.info(f"Loaded secret '{secret_name}' from Docker Secrets (/run/secrets/{secret_name}).")
                        return value
            except Exception as e:
                logger.warning(f"Error reading Docker secret '{secret_name}': {e}")

        # Step 2: Check Environment Variables
        env_val = os.getenv(secret_name)
        if env_val:
            logger.info(f"Loaded secret '{secret_name}' from Environment Variables.")
            return env_val

        # Step 3: Return default fallback
        return default

    @staticmethod
    def mask_secret(secret_val: Optional[str]) -> str:
        """
        Masks secret string for safe logging.

        Args:
            secret_val (Optional[str]): Raw secret string.

        Returns:
            str: Masked string representation.
        """
        if not secret_val:
            return "***UNSET***"
        if len(secret_val) <= 6:
            return "***MASKED***"
        return f"{secret_val[:2]}***{secret_val[-2:]}"
