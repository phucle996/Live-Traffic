# ==============================================================================
# Unit Tests for Security Modules (tests/unit/test_security_modules.py)
# Verifies SecretProvider functionality (fallback and string masking)
# ==============================================================================

import os
from src.security.secret_provider import SecretProvider


def test_secret_provider_fallback_and_masking():
    """
    Tests SecretProvider env fallback and string masking.
    """
    os.environ["TEST_SECRET_KEY"] = "my_super_secret_value_123"
    try:
        val = SecretProvider.get_secret("TEST_SECRET_KEY")
        assert val == "my_super_secret_value_123"

        masked = SecretProvider.mask_secret(val)
        assert "my_super_secret_value_123" not in masked
        assert masked.startswith("my***23")
    finally:
        del os.environ["TEST_SECRET_KEY"]
