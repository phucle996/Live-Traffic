# ==============================================================================
# TomTom Traffic Flow API Client Module (src/ingestion/tomtom_client.py)
# Resilient HTTP Client with Bounded Exponential Backoff & Non-Retryable Error Handlers
# ==============================================================================

import time
from typing import Dict, Any, Optional
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.common.config import settings
from src.common.logging_utils import get_logger

# Instantiate logger for TomTom client
logger = get_logger(__name__)


class TomTomTrafficClient:
    """
    HTTP Client for TomTom Traffic Flow Segment API.
    Supports timeouts, connection pooling, status logging, and automatic retry backoff.
    """

    BASE_URL = "https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json"

    def __init__(self, api_key: Optional[str] = None, timeout_seconds: int = 10):
        # Retrieve API key from parameter or central settings
        self.api_key = api_key or settings.TOMTOM_API_KEY
        self.timeout_seconds = timeout_seconds

        # Configure urllib3 Retry strategy for transient 5xx server errors
        retry_strategy = Retry(
            total=settings.MAX_RETRIES,
            backoff_factor=2,  # Exponential backoff factor (2s, 4s, 8s...)
            status_forcelist=[500, 502, 503, 504],
            raise_on_status=False,
        )

        # Create HTTP session with mounted retry adapter
        self.session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get_flow_segment(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """
        Queries TomTom Flow Segment API for a specific latitude and longitude point.

        Args:
            latitude (float): Target geographical latitude.
            longitude (float): Target geographical longitude.

        Returns:
            Optional[Dict[str, Any]]: Parsed JSON payload or None if query fails.
        """
        # Validate that API key is present before sending request
        if not self.api_key:
            logger.error("TOMTOM_API_KEY is not set. Cannot execute API request.")
            return None

        # Build query parameters dictionary
        params = {
            "key": self.api_key,
            "point": f"{latitude},{longitude}",
            "unit": "KMPH",
        }

        try:
            logger.debug(f"Querying TomTom Traffic API for point ({latitude}, {longitude})...")

            # Execute HTTP GET request with explicit timeout
            response = self.session.get(self.BASE_URL, params=params, timeout=self.timeout_seconds)

            # Fail-fast on authentication errors without wasting retries
            if response.status_code in (401, 403):
                logger.error(f"TomTom API Authentication Failed (HTTP {response.status_code}). Check API Key.")
                return None

            # Raise HTTP error if status code indicates failure
            response.raise_for_status()

            # Parse JSON payload
            data = response.json()
            flow_data = data.get("flowSegmentData", {})

            # Extract current speed, free-flow speed, and confidence score
            current_speed = flow_data.get("currentSpeed")
            free_flow_speed = flow_data.get("freeFlowSpeed")
            confidence = flow_data.get("confidence", 1.0)

            logger.info(
                f"Fetched point ({latitude:.4f}, {longitude:.4f}) -> "
                f"CurrentSpeed: {current_speed} km/h, FreeFlow: {free_flow_speed} km/h, Confidence: {confidence}"
            )

            return {
                "latitude": latitude,
                "longitude": longitude,
                "current_speed": current_speed,
                "free_flow_speed": free_flow_speed,
                "confidence": confidence,
                "raw_response": flow_data,
            }

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error querying TomTom API for point ({latitude}, {longitude}): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error processing TomTom response: {str(e)}", exc_info=True)
            return None
