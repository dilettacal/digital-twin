"""Pytest configuration and fixtures for backend tests."""
import os
import shutil
import tempfile
from pathlib import Path
import atexit

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Test data setup (executed at import time so modules see real files)
# ---------------------------------------------------------------------------

_TEST_DATA_ROOT = Path(tempfile.mkdtemp(prefix="digital_twin_test_data_"))
_TEST_PERSONAL_DATA_DIR = _TEST_DATA_ROOT / "personal_data"
_TEST_PROMPTS_DIR = _TEST_DATA_ROOT / "prompts"

_TEST_PERSONAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
_TEST_PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
(_TEST_PERSONAL_DATA_DIR / "__init__.py").touch()
(_TEST_PROMPTS_DIR / "__init__.py").touch()

_PROJECT_ROOT = Path(__file__).resolve().parent
_PERSONAL_TEMPLATES_DIR = _PROJECT_ROOT / "data" / "personal_data_templates"
_PROMPTS_TEMPLATES_DIR = _PROJECT_ROOT / "data" / "prompts_template"

if not _PERSONAL_TEMPLATES_DIR.exists():
    raise FileNotFoundError(f"Personal data templates directory not found at {_PERSONAL_TEMPLATES_DIR}")
if not _PROMPTS_TEMPLATES_DIR.exists():
    raise FileNotFoundError(f"Prompts templates directory not found at {_PROMPTS_TEMPLATES_DIR}")

for template_file in _PERSONAL_TEMPLATES_DIR.iterdir():
    if template_file.is_file():
        dest_name = template_file.name.replace("_template", "")
        dest_path = _TEST_PERSONAL_DATA_DIR / dest_name
        shutil.copy2(template_file, dest_path)

        if dest_name == "summary.txt" and dest_path.stat().st_size == 0:
            dest_path.write_text(
                "This is a test summary used for automated tests.\n",
                encoding="utf-8",
            )

for prompt_file in _PROMPTS_TEMPLATES_DIR.iterdir():
    if prompt_file.is_file():
        shutil.copy2(prompt_file, _TEST_PROMPTS_DIR / prompt_file.name)

# Export environment variables so application modules use test data
os.environ.setdefault("DIGITAL_TWIN_DATA_DIR", str(_TEST_DATA_ROOT))
os.environ.setdefault("DIGITAL_TWIN_PERSONAL_DATA_DIR", str(_TEST_PERSONAL_DATA_DIR))
os.environ.setdefault("DIGITAL_TWIN_PROMPTS_DIR", str(_TEST_PROMPTS_DIR))


@atexit.register
def _cleanup_test_data():
    shutil.rmtree(_TEST_DATA_ROOT, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables before any tests run."""
    # Set minimal required environment variables
    os.environ["AI_PROVIDER"] = "bedrock"
    os.environ["BEDROCK_MODEL_ID"] = "test-model"
    os.environ["USE_S3"] = "false"
    os.environ["HISTORY_DIR"] = "/tmp/test-memory"
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
