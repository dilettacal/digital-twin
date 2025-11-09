"""Memory/conversation storage service."""
import json
import os
import re
from pathlib import Path
from typing import Dict, List
from botocore.exceptions import ClientError
from app.core.config import MEMORY_DIR, S3_BUCKET, USE_S3, s3_client

_SESSION_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


def get_memory_path(session_id: str) -> str:
    """Get the storage path for a session."""
    safe_session_id = _sanitize_session_id(session_id)
    return f"{safe_session_id}.json"


def load_conversation(session_id: str) -> List[Dict]:
    """Load conversation history from storage."""
    if USE_S3:
        try:
            response = s3_client.get_object(Bucket=S3_BUCKET, Key=get_memory_path(session_id))
            return json.loads(response["Body"].read().decode("utf-8"))
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return []
            raise
    else:
        # Local file storage
        file_path = _safe_join(MEMORY_DIR, get_memory_path(session_id))
        if file_path.exists():
            with file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        return []


def save_conversation(session_id: str, messages: List[Dict]):
    """Save conversation history to storage."""
    if USE_S3:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=get_memory_path(session_id),
            Body=json.dumps(messages, indent=2),
            ContentType="application/json",
        )
    else:
        # Local file storage
        os.makedirs(MEMORY_DIR, exist_ok=True)
        file_path = _safe_join(MEMORY_DIR, get_memory_path(session_id))
        with file_path.open("w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2)


def _sanitize_session_id(session_id: str) -> str:
    """Validate and sanitize session IDs before using them in storage."""
    if not session_id:
        raise ValueError("Session ID must be provided.")
    if not _SESSION_ID_PATTERN.fullmatch(session_id):
        raise ValueError("Session ID contains invalid characters.")
    return session_id


def _safe_join(base_dir: str, filename: str) -> Path:
    """Safely join paths ensuring the final path stays within base_dir."""
    base_path = Path(base_dir).resolve()
    candidate_path = (base_path / filename).resolve()
    try:
        candidate_path.relative_to(base_path)
    except ValueError:
        raise ValueError("Invalid path derived from session ID.")
    return candidate_path
