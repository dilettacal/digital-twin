# Digital Twin Backend

## Project Structure

```
backend/
├── app/                    # Main application package
│   ├── __init__.py
│   ├── main.py            # FastAPI app setup
│   ├── models.py          # Pydantic models
│   ├── api/               # API routes
│   │   ├── __init__.py
│   │   └── chat.py        # Chat endpoints
│   ├── core/              # Core utilities
│   │   ├── __init__.py
│   │   ├── config.py      # Configuration
│   │   ├── context.py     # AI context/prompts
│   │   ├── prompt_loader.py # Prompt file loader
│   │   ├── rate_limiter.py # Rate limiting
│   │   └── resources.py   # Data resources
│   └── services/          # Business logic
│       ├── __init__.py
│       ├── ai_service.py  # AI provider integration
│       └── memory_service.py # Conversation storage
├── data/                  # Personal data & prompts
│   ├── prompts/          # AI prompt templates
│   │   ├── system_prompt.txt
│   │   ├── critical_rules.txt
│   │   └── proficiency_levels.json
│   └── facts.json, etc.  # Personal data files
├── tests/                 # Test suite
│   ├── test_api.py
│   └── test_rate_limiter.py
├── conftest.py           # Pytest fixtures
├── pytest.ini            # Pytest configuration
├── server.py             # Entry point
├── lambda_handler.py     # AWS Lambda handler
└── deploy.py             # Lambda deployment script
```

## Running Tests

Install dependencies:
```bash
uv sync
```

Run all tests:
```bash
uv run pytest
```

Run tests with verbose output:
```bash
uv run pytest -v
```

Run specific test file:
```bash
uv run pytest tests/test_rate_limiter.py
```

Run tests matching a pattern:
```bash
uv run pytest -k "rate_limit"
```

## Running the Server

Development:
```bash
uv run uvicorn server:app --reload
```

Or directly:
```bash
uv run python server.py
```

Production (via Lambda):
```bash
uv run python deploy.py
```

## Key Features

- ✅ Rate limiting (per-request and cooldown)
- ✅ Input validation and security filtering
- ✅ Multi-provider AI support (Bedrock/OpenAI)
- ✅ Conversation memory (local/S3)
- ✅ Comprehensive test suite (48 tests)
- ✅ Clean architecture with separation of concerns
