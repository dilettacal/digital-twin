"""Pydantic models for request/response validation."""
from pydantic import BaseModel, field_validator
from typing import Optional
from app.core.rate_limiter import validate_message_content


class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    session_id: Optional[str] = None

    @field_validator('message')
    @classmethod
    def validate_message(cls, v: str) -> str:
        """Validate message content and length."""
        valid, error_msg = validate_message_content(v)
        if not valid:
            raise ValueError(error_msg)
        return v


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    session_id: str


class Message(BaseModel):
    """Conversation message model."""
    role: str
    content: str
    timestamp: str
