# Digital Twin AI Production App

## 🏗️ Infrastructure Overview

This project deploys a serverless AI Digital Twin application on AWS with the following architecture:

### **Core Components:**
- **🌐 Frontend**: React/Next.js SPA hosted on S3 + CloudFront CDN
- **🤖 Backend**: FastAPI Lambda function powered by AWS Bedrock AI (Nova models)
- **🔗 API Gateway**: HTTP API for Lambda integration
- **💾 Storage**: S3 buckets for conversation memory and personal data
- **🔒 Security**: IAM roles, ACM SSL certificates, Route53 DNS

### **AWS Resources:**
- **S3 Buckets**: Frontend hosting, conversation memory, personal data storage
- **Lambda Function**: Python FastAPI backend with Bedrock integration
- **API Gateway**: HTTP API with CORS and routing
- **CloudFront**: Global CDN with custom domain support
- **Route53**: DNS management for custom domains
- **ACM**: SSL/TLS certificates (CloudFront requires us-east-1)
- **IAM**: Roles and policies for secure service access

### **Environments:**
- **dev**: Development environment with basic configuration
- **test**: Testing environment for validation
- **prod**: Production environment with custom domain support

### **Key Features:**
- ✅ Multi-environment support (dev/test/prod)
- ✅ Custom domain support with SSL certificates
- ✅ Secure personal data storage in S3
- ✅ GitHub Actions CI/CD pipeline
- ✅ Infrastructure as Code with Terraform
- ✅ Serverless architecture (pay-per-use)

---

## 🚀 Quick Start

### First Time Setup

```bash
# Clone the repository
git clone <repo-url>
cd digital-twin

# Run setup script (creates local data files from templates)
./scripts/setup.sh

# Install dependencies
cd backend && uv sync
cd ../frontend && npm install
```

### Starting the Application

**Start Backend (Terminal 1):**
```bash
cd backend
uv run server.py
```
- Backend runs on `http://localhost:8000`
- Auto-reload enabled for development
- **For OpenAI (local dev)**: Set `AI_PROVIDER=openai` and `OPENAI_API_KEY=your-key` in `backend/.env`

**Start Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```
- Frontend runs on `http://localhost:3000`
- Requires `NEXT_PUBLIC_API_URL` environment variable (defaults to `http://localhost:8000`)

**Note**: Make sure you have your personal data files in `backend/data/personal_data/` before starting (run `./scripts/setup-local-data.sh` if needed).

---

## 📝 Personal Data Management

**Important**: Personal data files are **not committed to git** to keep the repository public-friendly. Here's how to manage them:

### For Local Development

**Quick Setup:**
```bash
# Run the setup script
./scripts/setup-local-data.sh
```

The setup script will automatically:
- Copy template files from `backend/data/personal_data_templates/*_template.*` to create data files
- Create all required files for local development
- Skip files that already exist

**Note**: Personal data files should be placed in `backend/data/personal_data/` directory.

**Manual Setup (Alternative):**

1. **Template files are included** in the repo (in `backend/data/personal_data_templates/`):
   - `facts_template.json` - Template for structured facts
   - `linkedin_template.pdf` - Template for LinkedIn profile
   - `summary_template.txt` - Template for personal summary
   - `me_template.txt` - Template for personal description
   - `style_template.txt` - Communication style template

2. **Create your personal data files** by copying templates:
   ```bash
   cd backend
   mkdir -p data/personal_data
   mkdir -p data/prompts
   cp data/personal_data_templates/facts_template.json data/personal_data/facts.json
   cp data/personal_data_templates/summary_template.txt data/personal_data/summary.txt
   cp data/personal_data_templates/linkedin_template.pdf data/personal_data/linkedin.pdf
   cp data/personal_data_templates/style_template.txt data/personal_data/style.txt
   cp data/personal_data_templates/me_template.txt data/personal_data/me.txt  # Optional
   cp data/prompts_template/system_prompt.txt data/prompts/system_prompt.txt
   cp data/prompts_template/critical_rules.txt data/prompts/critical_rules.txt
   cp data/prompts_template/proficiency_levels.json data/prompts/proficiency_levels.json
   # Edit these files with your personal information
   ```

3. **Required files** for local development:
   - `facts.json` - Your structured facts
   - `summary.txt` - Your personal summary
   - `style.txt` - Your communication style
   - `linkedin.pdf` - Your LinkedIn profile (PDF)
   - `me.txt` - Optional personal description
   - `system_prompt.txt`, `critical_rules.txt`, `proficiency_levels.json` in `backend/data/prompts/`

4. **Note**: 
   - These files are gitignored and won't be committed to the repository
   - Each user creates their own local copies from templates

### Manual Download/Decrypt (Advanced)

If you need to manually download or decrypt:

```bash
# Download encrypted files from GitHub Release
./scripts/download-encrypted-data.sh

# Decrypt downloaded files
./scripts/decrypt-data.sh
```

### For Production Deployment

When deploying to AWS, upload your personal data to S3:

```bash
# Upload to dev environment
./scripts/upload-personal-data.sh dev

# Upload to production
./scripts/upload-personal-data.sh prod
```

The Lambda function will read from S3 during deployment. This is only for production - **no need to store data in S3 just for local development**.


---

## Deployment

### Quick Deploy
```bash
./scripts/deploy.sh prod
```

### GitHub Actions CI/CD

This project includes automated deployment via GitHub Actions:
- Automatic deployment to `dev` on push to `main`
- Manual deployment to any environment via workflow dispatch
- AWS authentication via OIDC (no secrets required)

For detailed setup instructions, see [Technical Documentation](docs/README.md).

---

## Additional Resources

- **[Technical Documentation](docs/README.md)**: Architecture, infrastructure details, and advanced setup
- **[Decryption Setup](docs/DECRYPTION_SETUP.md)**: How to download and decrypt encrypted data files
- **[Encryption Setup Instructions](docs/ENCRYPTION_SETUP_INSTRUCTIONS.md)**: Instructions for private repository (for repository owner)
