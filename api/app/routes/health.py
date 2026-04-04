"""Health check route.

A lightweight endpoint used by load balancers and monitoring tools to verify
that the API process is alive and accepting connections.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Service health check endpoint.

    Returns:
        A dict containing ``status`` and an ISO-8601 ``timestamp``.
    """
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}
