# ==============================================================================
# TomTom API Health Check Utility (src/ingestion/api_healthcheck.py)
# Validates API Credentials & Endpoints Before Executing Crawl Batches
# ==============================================================================

from typing import Tuple
from src.common.config import settings
from src.common.logging_utils import get_logger

# Instantiate logger for API health check
logger = get_logger(__name__)


class ApiHealthCheck:
    """
    Performs ping check to verify TomTom API connectivity and key validity.
    """

    @staticmethod
    def check_health(api_key: str = None) -> Tuple[bool, str]:
        """
        Pings TomTom API endpoint with sample coordinates to verify credentials.

        Args:
            api_key (str): Optional TomTom API key.

        Returns:
            Tuple[bool, str]: (is_healthy, status_message)
        """
        key = api_key or settings.TOMTOM_API_KEY
        if not key or key in ("dummy_api_key_for_testing", "NOT_SET", ""):
            logger.warning("TomTom API key is missing or not configured.")
            return False, "MISSING_API_KEY"

        import requests
        try:
            url = f"https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json?key={key}&point=10.7769,106.7009&unit=KMPH"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                logger.info("TomTom API Health Check: SUCCESS (HTTP 200 OK)")
                return True, "API_HEALTHY"
            elif resp.status_code in (401, 403):
                logger.error(f"TomTom API Health Check: FAILED (HTTP {resp.status_code} Unauthorized)")
                return False, "INVALID_API_KEY"
            else:
                logger.warning(f"TomTom API Health Check: Unexpected HTTP status {resp.status_code}")
                return False, f"API_HTTP_{resp.status_code}"
        except Exception as e:
            logger.warning(f"TomTom API Health Check: Network Error ({type(e).__name__})")
            return False, f"NETWORK_ERROR_{type(e).__name__}"
