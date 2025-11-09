"""AWS Bedrock implementation of the AI service."""

from __future__ import annotations

import importlib
from typing import Dict, List

try:
    ClientError = getattr(importlib.import_module("botocore.exceptions"), "ClientError")
except ModuleNotFoundError as exc:  # pragma: no cover - fail fast if dependency missing
    raise ImportError("botocore is required to use the Bedrock AI service.") from exc

try:
    HTTPException = getattr(importlib.import_module("fastapi"), "HTTPException")
except ModuleNotFoundError:  # pragma: no cover - fallback for lint/test environments
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str = "") -> None:
            super().__init__(detail)
            self.status_code = status_code
            self.detail = detail

from app.core.config import BEDROCK_MODEL_ID, bedrock_client
from app.core.context import prompt
from app.core.logging import get_logger

from .base import AIService


class BedrockAIService(AIService):
    """Generate responses using AWS Bedrock."""

    def __init__(self) -> None:
        if bedrock_client is None:
            raise RuntimeError("Bedrock client is not configured. Set AI_PROVIDER=bedrock with valid credentials.")

        self._client = bedrock_client
        self._logger = get_logger(__name__).bind(provider="bedrock", model_id=BEDROCK_MODEL_ID)

    def _build_messages(self, conversation: List[Dict], user_message: str) -> List[Dict]:
        messages: List[Dict] = [
            {
                "role": "user",
                "content": [{"text": f"System: {prompt()}"}],
            }
        ]

        for msg in self._truncate_history(conversation, self.history_limit):
            messages.append(
                {
                    "role": msg["role"],
                    "content": [{"text": msg["content"]}],
                }
            )

        messages.append(
            {
                "role": "user",
                "content": [{"text": user_message}],
            }
        )
        return messages

    def generate_response(self, conversation: List[Dict], user_message: str) -> str:
        self._logger.debug("ai_request_started", history_length=len(conversation))
        messages = self._build_messages(conversation, user_message)

        try:
            response = self._client.converse(
                modelId=BEDROCK_MODEL_ID,
                messages=messages,
                inferenceConfig={"maxTokens": 2000, "temperature": 0.7, "topP": 0.9},
            )
        except ClientError as exc:
            error_code = exc.response["Error"].get("Code", "Unknown")
            self._logger.error("ai_request_failed", error_code=error_code, detail=str(exc))
            if error_code == "ValidationException":
                raise HTTPException(status_code=400, detail="Invalid message format for Bedrock") from exc
            if error_code == "AccessDeniedException":
                raise HTTPException(status_code=403, detail="Access denied to Bedrock model") from exc
            raise HTTPException(status_code=500, detail=f"Bedrock error: {exc}") from exc

        try:
            content = response["output"]["message"]["content"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            self._logger.error("ai_response_parse_failed", error=str(exc))
            raise HTTPException(status_code=500, detail="Unexpected Bedrock response format.") from exc

        self._logger.info("ai_request_completed", response_length=len(content))
        return content
