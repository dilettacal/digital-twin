"""Amazon S3-backed memory service."""

from __future__ import annotations

import json
from typing import Dict, List

try:
    from botocore.exceptions import ClientError
except ModuleNotFoundError as exc:
    raise ImportError("botocore is required to use the S3 memory service.") from exc

from app.core.config import S3_BUCKET, s3_client
from app.core.logging import get_logger

from .base import MemoryService
from .utils import get_memory_path


class S3MemoryService(MemoryService):
    """Store conversation memory in an S3 bucket."""

    def __init__(self) -> None:
        if s3_client is None:
            raise RuntimeError("S3 client is not configured. Ensure USE_S3 is set with valid credentials.")
        if not S3_BUCKET:
            raise RuntimeError("S3 bucket is not configured. Set the S3_BUCKET environment variable.")

        self._client = s3_client
        self._logger = get_logger(__name__).bind(backend="s3", bucket=S3_BUCKET)

    def load_conversation(self, session_id: str) -> List[Dict]:
        self._logger.debug("memory_load_attempt", session_id=session_id)
        try:
            response = self._client.get_object(Bucket=S3_BUCKET, Key=get_memory_path(session_id))
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "NoSuchKey":
                self._logger.debug("memory_load_empty", session_id=session_id)
                return []
            self._logger.error(
                "memory_load_failed",
                session_id=session_id,
                error_code=exc.response["Error"]["Code"],
                error_message=str(exc),
            )
            raise

        messages = json.loads(response["Body"].read().decode("utf-8"))
        self._logger.debug("memory_load_success", session_id=session_id, message_count=len(messages))
        return messages

    def save_conversation(self, session_id: str, messages: List[Dict]) -> None:
        self._logger.debug("memory_save_attempt", session_id=session_id, message_count=len(messages))
        self._client.put_object(
            Bucket=S3_BUCKET,
            Key=get_memory_path(session_id),
            Body=json.dumps(messages, indent=2),
            ContentType="application/json",
        )
        self._logger.info("memory_save_success", session_id=session_id, message_count=len(messages))
