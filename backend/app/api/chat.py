"""Chat API endpoints."""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from app.models import ChatRequest, ChatResponse
from app.services.memory_service import load_conversation, save_conversation
from app.services.ai_service import get_ai_response
from app.core.rate_limiter import rate_limiter, get_client_identifier
from app.core.auth import get_current_user
from app.core.config import (
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    RATE_LIMIT_COOLDOWN_SECONDS
)
from structlog.contextvars import bind_contextvars, clear_contextvars
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    """
    Chat endpoint with rate limiting and optional authentication.
    
    Accepts a message and optional session_id, returns AI response.
    Authentication is optional but provides better rate limiting.
    """
    bind_contextvars(endpoint="chat")
    try:
        user = await get_current_user(http_request)

        session_id = request.session_id or str(uuid.uuid4())
        bind_contextvars(session_id=session_id)

        if user and user.get("user_id"):
            client_id = f"user:{user['user_id']}"
        else:
            client_id = get_client_identifier(
                request_headers=dict(http_request.headers),
                session_id=session_id
            )

        bind_contextvars(client_id=client_id)

        allowed, error_msg = rate_limiter.check_rate_limit(
            identifier=client_id,
            max_requests=RATE_LIMIT_MAX_REQUESTS,
            window_seconds=RATE_LIMIT_WINDOW_SECONDS,
            cooldown_seconds=RATE_LIMIT_COOLDOWN_SECONDS
        )

        if not allowed:
            logger.warning("chat_rate_limited", reason=error_msg)
            raise HTTPException(status_code=429, detail=error_msg)

        conversation = load_conversation(session_id)

        assistant_response = get_ai_response(conversation, request.message)

        conversation.append(
            {"role": "user", "content": request.message, "timestamp": datetime.now().isoformat()}
        )
        conversation.append(
            {
                "role": "assistant",
                "content": assistant_response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        save_conversation(session_id, conversation)

        logger.info(
            "chat_completed",
            authenticated=bool(user),
            provided_session_id=bool(request.session_id),
            message_count=len(conversation),
        )

        return ChatResponse(response=assistant_response, session_id=session_id)

    except HTTPException as exc:
        logger.warning("chat_http_error", status_code=exc.status_code, detail=exc.detail)
        raise
    except ValueError as exc:
        logger.warning("chat_validation_error", error=str(exc))
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.exception("chat_unexpected_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        clear_contextvars()


@router.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Retrieve conversation history for a session."""
    bind_contextvars(endpoint="get_conversation", session_id=session_id)
    try:
        conversation = load_conversation(session_id)
        return {"session_id": session_id, "messages": conversation}
    except Exception as exc:
        logger.exception("conversation_fetch_error", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        clear_contextvars()

