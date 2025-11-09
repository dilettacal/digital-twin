"""Application configuration."""
import os
from dotenv import load_dotenv
import boto3

# Load environment variables
load_dotenv()

# AI Provider configuration
AI_PROVIDER = os.getenv("AI_PROVIDER", "bedrock").lower()

# Bedrock configuration
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "eu.amazon.nova-lite-v1:0")
DEFAULT_AWS_REGION = os.getenv("DEFAULT_AWS_REGION", "eu-central-1")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Ollama configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

# Memory storage configuration
USE_S3 = os.getenv("USE_S3", "false").lower() == "true"
S3_BUCKET = os.getenv("S3_BUCKET", "")
HISTORY_DIR = os.getenv("HISTORY_DIR", "../history")

# Rate limiting configuration
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "10"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_COOLDOWN_SECONDS = float(os.getenv("RATE_LIMIT_COOLDOWN_SECONDS", "2.0"))

# CORS configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

# Initialize clients
bedrock_client = None
if AI_PROVIDER == "bedrock":
    bedrock_client = boto3.client(
        service_name="bedrock-runtime",
        region_name=DEFAULT_AWS_REGION
    )

openai_client = None
if AI_PROVIDER == "openai":
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is required when AI_PROVIDER=openai")
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
    except ImportError:
        raise ImportError("openai package is required. Install it with: uv add openai")

s3_client = None
if USE_S3:
    s3_client = boto3.client("s3")
