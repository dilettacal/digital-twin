"""Ollama implementation of the AI service."""

from __future__ import annotations

import importlib
from typing import Dict, List

import requests

try:
    HTTPException = getattr(importlib.import_module("fastapi"), "HTTPException")
except ModuleNotFoundError:  # pragma: no cover - fallback for lint/test environments
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = "") -> None:
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

from app.core.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from app.core.context import prompt
from app.core.logging import get_logger

from .base import AIService


class OllamaAIService(AIService):
    """Generate responses using a local Ollama server."""

    def __init__(self) -> None:
        self._base_url = OLLAMA_BASE_URL.rstrip("/")
        self._model = OLLAMA_MODEL
        self._logger = get_logger(__name__).bind(provider="ollama", model=self._model)

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

        url = f"{self._base_url}/api/chat"
        payload = {
            "model": self._model,
            "messages": messages,
            "stream": False,
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
        except requests.RequestException as exc:
            self._logger.error("ai_request_failed", error=str(exc))
            raise HTTPException(status_code=502, detail=f"Ollama request failed: {exc}") from exc

        try:
            data = response.json()
            content = data["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            self._logger.error("ai_response_parse_failed", error=str(exc))
            raise HTTPException(status_code=500, detail="Unexpected Ollama response format.") from exc

        self._logger.info("ai_request_completed", response_length=len(content or ""))
        return content
