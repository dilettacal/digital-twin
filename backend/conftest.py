"""Pytest configuration and fixtures for backend tests."""
import os
import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables before any tests run."""
    # Set minimal required environment variables
    os.environ["AI_PROVIDER"] = "bedrock"
    os.environ["BEDROCK_MODEL_ID"] = "test-model"
    os.environ["USE_S3"] = "false"
    os.environ["MEMORY_DIR"] = "/tmp/test-memory"
    os.environ["CORS_ORIGINS"] = "http://localhost:3000"
    
    # Rate limiting configuration for tests
    os.environ["RATE_LIMIT_MAX_REQUESTS"] = "5"
    os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "10"
    os.environ["RATE_LIMIT_COOLDOWN_SECONDS"] = "1.0"
    
    yield
    
    # Cleanup
    if os.path.exists("/tmp/test-memory"):
        import shutil
        shutil.rmtree("/tmp/test-memory", ignore_errors=True)


@pytest.fixture
def client():
    """Create a FastAPI test client."""
    # Import here to ensure environment variables are set
    from app.main import app
    return TestClient(app)


@pytest.fixture
def rate_limiter():
    """Create a fresh rate limiter instance for each test."""
    from app.core.rate_limiter import RateLimiter
    return RateLimiter()


@pytest.fixture
def mock_bedrock_response(monkeypatch):
    """Mock Bedrock API calls to avoid actual API calls in tests."""
    def mock_converse(*args, **kwargs):
        return {
            "output": {
                "message": {
                    "content": [{"text": "Test response from assistant"}]
                }
            }
        }
    
    # Only mock if using bedrock
    if os.environ.get("AI_PROVIDER") == "bedrock":
        from app.core.config import bedrock_client
        if bedrock_client:
            monkeypatch.setattr(bedrock_client, "converse", mock_converse)
    
    return mock_converse

