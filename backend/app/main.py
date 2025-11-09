"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import chat
from app.core.config import (
    CORS_ORIGINS,
    AI_PROVIDER,
    OPENAI_MODEL,
    BEDROCK_MODEL_ID,
    USE_S3,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    RATE_LIMIT_COOLDOWN_SECONDS
)
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(title="Digital Twin API")

logger.info(
    "application_initialized",
    cors_origins=CORS_ORIGINS,
    use_s3=USE_S3,
    ai_provider=AI_PROVIDER,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, tags=["chat"])


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"AI Digital Twin API (Powered by {AI_PROVIDER.upper()})",
        "memory_enabled": True,
        "storage": "S3" if USE_S3 else "local",
        "ai_provider": AI_PROVIDER,
        "ai_model": OPENAI_MODEL if AI_PROVIDER == "openai" else BEDROCK_MODEL_ID,
        "rate_limits": {
            "max_requests": RATE_LIMIT_MAX_REQUESTS,
            "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
            "cooldown_seconds": RATE_LIMIT_COOLDOWN_SECONDS
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "use_s3": USE_S3,
        "ai_provider": AI_PROVIDER,
        "ai_model": OPENAI_MODEL if AI_PROVIDER == "openai" else BEDROCK_MODEL_ID
    }
