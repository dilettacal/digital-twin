"""Memory service package exposing backend-specific implementations."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import USE_S3
from app.core.logging import get_logger

from .base import MemoryService
from .local import LocalMemoryService
from .s3 import S3MemoryService

__all__ = [
    "MemoryService",
    "LocalMemoryService",
    "S3MemoryService",
    "get_memory_service",
]

_logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_memory_service() -> MemoryService:
    """Return the configured memory service instance."""
    if USE_S3:
        _logger.info("memory_service_selected", backend="s3")
        return S3MemoryService()
    _logger.info("memory_service_selected", backend="local")
    return LocalMemoryService()
