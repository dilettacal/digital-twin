# Digital Twin AI

An AI-powered digital twin that mimics your communication style, knowledge, and personality. Built with FastAPI, Next.js, and AWS Bedrock.

## What is this?

This application creates a conversational AI that represents you. It learns from your personal data (LinkedIn profile, facts about you, communication style) and responds to questions as if it were you. Think of it as your digital representative that can answer questions about your background, experience, and expertise.

## How it works

The application consists of:
- **Backend**: FastAPI server that uses AWS Bedrock (Nova models) to generate responses based on your personal data
- **Frontend**: Next.js chat interface where users can interact with your digital twin
- **Data Layer**: Your personal information (LinkedIn PDF, facts, style guide) that personalizes the AI

When someone asks a question, the AI references your personal data to craft responses that sound like you and contain accurate information about you.

## Data Management

### Current Setup (Separate Private Repo)

This project is currently configured to keep personal data separate from the main codebase. Personal data is stored in a private repository and encrypted for deployment. This approach:
- ✅ Keeps the main project public-friendly
- ✅ Separates sensitive personal information
- ✅ Works with automated CI/CD deployments

### Alternative: Local Data Approach

A simpler local approach by committing data directly can also be used:

1. **Copy the templates** from `backend/data/personal_data_templates/` to `backend/data/personal_data/`
2. **Edit the files** with your actual information:
   - `facts.json` - Structured facts about you
   - `summary.txt` - Personal summary
   - `style.txt` - Your communication style
   - `linkedin.pdf` - Your LinkedIn profile as PDF
   - `me.txt` - Additional personal description (optional)

3. **Copy prompt templates** from `backend/data/prompts_template/` to `backend/data/prompts/`

**Quick setup command**:
```bash
./scripts/setup-local-data.sh
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- AWS credentials (for deployment)

### Local Development

1. **Install dependencies**:
```bash
# Backend
cd backend
uv sync

# Frontend
cd frontend
npm install
```

2. **Set up your personal data** (see Data Management section above)

3. **Configure environment variables** (optional):

For local development, you can use OpenAI instead of AWS Bedrock. Copy the example environment file and configure it:

```bash
cd backend
cp .env.example .env
# Edit .env and set AI_PROVIDER=openai and your OPENAI_API_KEY
```

See `backend/.env.example` for all available configuration options.

4. **Start the backend** (Terminal 1):
```bash
cd backend
uv run server.py
```
Backend runs on `http://localhost:8000`

5. **Start the frontend** (Terminal 2):
```bash
cd frontend
npm run dev
```
Frontend runs on `http://localhost:3000`

## Deployment

Deploy to AWS using Terraform:

```bash
./scripts/deploy.sh prod
```

This creates:
- Lambda function for the backend
- S3 + CloudFront for the frontend
- API Gateway for HTTP endpoints
- S3 buckets for data storage

For detailed deployment instructions, see [Technical Documentation](docs/README.md).

---

**More screenshots and documentation coming soon...**
