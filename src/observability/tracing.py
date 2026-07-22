# ==============================================================================
# OpenTelemetry Tracing Manager (src/observability/tracing.py)
# Distributed Context Tracing & Request ID Propagation Manager
# ==============================================================================

import uuid
from contextvars import ContextVar
from typing import Optional

from src.common.logging_utils import get_logger

# Instantiate logger for tracing manager
logger = get_logger(__name__)

# Context variable tracking active request_id across async callstacks
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


class TracingManager:
    """
    Manages request_id context propagation across services.
    """

    @staticmethod
    def get_current_request_id() -> str:
        """
        Returns active request_id or generates new UUID if unassigned.
        """
        req_id = request_id_ctx.get()
        if not req_id:
            req_id = str(uuid.uuid4())
            request_id_ctx.set(req_id)
        return req_id

    @staticmethod
    def set_request_id(request_id: str) -> None:
        """
        Explicitly sets active request_id in context.
        """
        request_id_ctx.set(request_id)
        logger.debug(f"Context Request ID set to: {request_id}")
