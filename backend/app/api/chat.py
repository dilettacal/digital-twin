"""Chat API endpoints."""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request
from app.models import ChatRequest, ChatResponse
from app.services.memory_service import load_conversation, save_conversation
from app.services.ai_service import get_ai_response
from app.core.rate_limiter import rate_limiter, get_client_identifier
from app.core.config import (
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    RATE_LIMIT_COOLDOWN_SECONDS
)

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, http_request: Request):
    """
    Chat endpoint with rate limiting.
    
    Accepts a message and optional session_id, returns AI response.
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Get client identifier for rate limiting
        client_id = get_client_identifier(
            request_headers=dict(http_request.headers),
            session_id=session_id
        )
        
        # Check rate limits
        allowed, error_msg = rate_limiter.check_rate_limit(
            identifier=client_id,
            max_requests=RATE_LIMIT_MAX_REQUESTS,
            window_seconds=RATE_LIMIT_WINDOW_SECONDS,
            cooldown_seconds=RATE_LIMIT_COOLDOWN_SECONDS
        )
        
        if not allowed:
            raise HTTPException(status_code=429, detail=error_msg)

        # Load conversation history
        conversation = load_conversation(session_id)

        # Get AI response
        assistant_response = get_ai_response(conversation, request.message)

        # Update conversation history
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

        # Save conversation
        save_conversation(session_id, conversation)

        return ChatResponse(response=assistant_response, session_id=session_id)

    except HTTPException:
        raise
    except ValueError as e:
        # Validation errors from pydantic
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversation/{session_id}")
async def get_conversation(session_id: str):
    """Retrieve conversation history for a session."""
    try:
        conversation = load_conversation(session_id)
        return {"session_id": session_id, "messages": conversation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

