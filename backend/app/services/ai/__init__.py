"""AI service package exposing provider-specific implementations."""

from __future__ import annotations

from functools import lru_cache

from app.core.config import AI_PROVIDER
from app.core.logging import get_logger

from .base import AIService
from .bedrock import BedrockAIService
from .ollama import OllamaAIService
from .openai import OpenAIAIService

__all__ = [
    "AIService",
    "BedrockAIService",
    "OllamaAIService",
    "OpenAIAIService",
    "get_ai_service",
]

_logger = get_logger(__name__)


@lru_cache(maxsize=1)
def get_ai_service() -> AIService:
    """Return the configured AI service implementation."""
    if AI_PROVIDER == "openai":
        _logger.info("ai_service_selected", provider="openai")
        return OpenAIAIService()
    if AI_PROVIDER == "ollama":
        _logger.info("ai_service_selected", provider="ollama")
        return OllamaAIService()
    _logger.info("ai_service_selected", provider="bedrock")
    return BedrockAIService()
