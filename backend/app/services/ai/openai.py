"""OpenAI implementation of the AI service."""

from __future__ import annotations

import importlib
from typing import Dict, List

try:
    HTTPException = getattr(importlib.import_module("fastapi"), "HTTPException")
except ModuleNotFoundError:  # pragma: no cover - fallback for lint/test environments
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = "") -> None:
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

from app.core.config import OPENAI_MODEL, openai_client
from app.core.context import prompt
from app.core.logging import get_logger

from .base import AIService


class OpenAIAIService(AIService):
    """Generate responses using OpenAI chat completions."""

    def __init__(self) -> None:
        if openai_client is None:
            raise RuntimeError("OpenAI client is not configured. Set AI_PROVIDER=openai with valid credentials.")

        self._client = openai_client
        self._logger = get_logger(__name__).bind(provider="openai", model=OPENAI_MODEL)

    def _build_messages(self, conversation: List[Dict], user_message: str) -> List[Dict]:
        messages: List[Dict] = [
            {
                "role": "system",
                "content": prompt(),
            }
        ]

        for msg in self._truncate_history(conversation, self.history_limit):
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})
        return messages

    def generate_response(self, conversation: List[Dict], user_message: str) -> str:
        self._logger.debug("ai_request_started", history_length=len(conversation))
        messages = self._build_messages(conversation, user_message)

        try:
            response = self._client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=2000,
                temperature=0.7,
            )
        except Exception as exc:
            self._logger.error("ai_request_failed", detail=str(exc))
            raise HTTPException(status_code=500, detail=f"OpenAI error: {exc}") from exc

        try:
            content = response.choices[0].message.content
        except (AttributeError, IndexError, TypeError) as exc:
            self._logger.error("ai_response_parse_failed", error=str(exc))
            raise HTTPException(status_code=500, detail="Unexpected OpenAI response format.") from exc

        self._logger.info("ai_request_completed", response_length=len(content or ""))
        return content
