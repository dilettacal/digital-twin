# Technical Documentation

This document contains technical details, architecture information, and advanced setup instructions for the Digital Twin AI project.

## Table of Contents

- [Architecture](#architecture)
- [Infrastructure Details](#infrastructure-details)
- [Data Management](#data-management)
- [Terraform Setup](#terraform-setup)
- [CI/CD Configuration](#cicd-configuration)
- [Development Details](#development-details)

---

## Architecture

### System Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   CloudFront    │ (CDN)
│   (Frontend)    │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│   S3 Bucket     │ (Static Files)
│   (Frontend)    │
└─────────────────┘

┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  API Gateway    │ (HTTP API)
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Lambda         │ (FastAPI Backend)
│  Function       │
└──────┬──────────┘
       │
       ├─────────────────┐
       ▼                 ▼
┌─────────────┐   ┌─────────────┐
│   Bedrock   │   │  S3 Buckets │
│   (AI)      │   │  (Data)     │
└─────────────┘   └─────────────┘
```

### Component Details

#### Frontend
- **Framework**: Next.js 14+ (React)
- **Build**: Static export (`output: 'export'`)
- **Hosting**: S3 + CloudFront
- **Configuration**: Environment variables via `NEXT_PUBLIC_API_URL`

#### Backend
- **Framework**: FastAPI (Python 3.12+)
- **Runtime**: AWS Lambda (via Mangum adapter)
- **AI Service**: AWS Bedrock (Nova models)
- **Package Manager**: `uv` (Python)

#### Infrastructure
- **IaC**: Terraform
- **State Management**: S3 backend + DynamoDB locks
- **Environments**: Workspaces (dev/test/prod)

---

## Infrastructure Details

### AWS Resources

#### S3 Buckets
1. **Frontend Bucket**: `digital-twin-frontend-{env}`
   - Static website hosting
   - CloudFront origin
   - Public read access

2. **Memory Bucket**: `digital-twin-memory-{env}`
   - Conversation history storage
   - Private, encrypted
   - Lambda read/write access

3. **Personal Data Bucket**: `digital-twin-data-{env}`
   - User personal data (summary, facts, LinkedIn, etc.)
   - Private, encrypted
   - Lambda read access
   - Uploaded via `upload-personal-data.sh`

4. **Terraform State Bucket**: `digital-twin-terraform-state-{account_id}`
   - Versioned
   - Encrypted
   - Private

#### Lambda Function
- **Runtime**: Python 3.12
- **Handler**: `lambda_handler.handler`
- **Timeout**: 30 seconds (configurable)
- **Memory**: 512 MB (configurable)
- **Environment Variables**:
  - `BEDROCK_MODEL_ID`: Bedrock model identifier
  - `MEMORY_BUCKET`: S3 bucket for conversation memory
  - `PERSONAL_DATA_BUCKET`: S3 bucket for personal data
  - `USE_S3`: Boolean flag for S3 memory storage

#### API Gateway
- **Type**: HTTP API (v2)
- **CORS**: Enabled for frontend origin
- **Throttling**: Configured
- **Integration**: Lambda proxy integration

#### CloudFront
- **Origin**: S3 frontend bucket
- **Behaviors**: Default cache policy
- **Custom Domain**: Optional (prod only)
- **SSL/TLS**: ACM certificate

#### Route53 & ACM
- **DNS**: Custom domain management (prod only)
- **Certificates**: ACM in `us-east-1` (CloudFront requirement)

#### IAM Roles
- **Lambda Execution Role**: Bedrock, S3 access
- **GitHub Actions Role**: Deployment permissions (OIDC)

---


## Data Management

### Personal Data Storage

All personal data files should be placed in the `backend/data/` directory.

#### Local Development
- **Location**: `backend/data/`
- **Files**: `facts.json`, `summary.txt`, `style.txt`, `linkedin.pdf`, `me.txt`
- **Templates**: `backend/data/*_template.*` (in same directory)
- **Git Status**: Data files ignored, templates committed

#### Production
- **Storage**: S3 bucket (`digital-twin-data-{env}`)
- **Upload**: `./scripts/upload-personal-data.sh {env}`
- **Access**: Lambda reads from S3 during execution
- **Deployment**: Downloaded during Lambda package creation

### Conversation Memory

#### Local Development
- **Location**: `memory/` directory (project root)
- **Format**: JSON files (`{session_id}.json`)
- **Storage**: File system

#### Production
- **Storage**: S3 bucket (`digital-twin-memory-{env}`)
- **Format**: JSON files (`{session_id}.json`)
- **Access**: Lambda read/write

---

## Terraform Setup

### Backend Configuration

Terraform state is stored remotely in S3 with DynamoDB locking.

#### Bootstrap Process

If starting from scratch or after deleting AWS resources:

1. **Create bootstrap configuration** (`terraform/bootstrap.tf`):
```hcl
resource "aws_s3_bucket" "terraform_state" {
  bucket = "digital-twin-terraform-state-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name        = "Terraform State Store"
    Environment = "global"
    ManagedBy   = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "terraform_locks" {
  name         = "digital-twin-terraform-locks"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  tags = {
    Name        = "Terraform State Locks"
    Environment = "global"
    ManagedBy   = "terraform"
  }
}
```

2. **Bootstrap**:
```bash
cd terraform
terraform init
terraform apply
```

3. **Configure remote backend** in `terraform/versions.tf`:
```hcl
terraform {
  backend "s3" {
    bucket         = "digital-twin-terraform-state-{ACCOUNT_ID}"
    key            = "terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "digital-twin-terraform-locks"
    encrypt        = true
  }
}
```

4. **Migrate state**:
```bash
terraform init  # Will prompt to migrate
rm bootstrap.tf
```

### Workspaces

Terraform uses workspaces for environment separation:
- `dev`: Development environment
- `test`: Testing environment  
- `prod`: Production environment

**Usage**:
```bash
terraform workspace select dev
terraform plan
terraform apply
```

### Variables

Key variables in `terraform/variables.tf`:
- `project_name`: Resource name prefix (default: `digital-twin`)
- `environment`: Environment name (dev/test/prod)
- `bedrock_model_id`: Bedrock model identifier
- `use_custom_domain`: Enable custom domain (prod only)
- `root_domain`: Custom domain name

---

## CI/CD Configuration

### GitHub Actions

The project uses GitHub Actions for automated deployment with OIDC authentication.

#### OIDC Setup

1. **Create OIDC configuration** (`terraform/github-oidc.tf`):
```hcl
variable "github_repository" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
}

resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
  
  client_id_list = ["sts.amazonaws.com"]
  
  thumbprint_list = [
    "1b511abead59c6ce207077c0bf0e0043b1382612"
  ]
}

resource "aws_iam_role" "github_actions" {
  name = "github-actions-digital-twin-deploy"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_repository}:*"
        }
      }
    }]
  })
}

# Attach policies (Lambda, S3, API Gateway, CloudFront, etc.)
# ... (see main README for full configuration)
```

2. **Deploy OIDC resources**:
```bash
cd terraform
terraform apply \
  -target=aws_iam_openid_connect_provider.github \
  -target=aws_iam_role.github_actions \
  # ... other targets
  -var="github_repository=USERNAME/repo-name"
```

3. **Configure GitHub secret**:
   - Add `AWS_ROLE_ARN` secret in GitHub repository settings
   - Value: Output from `terraform output github_actions_role_arn`

4. **Workflow**:
   - Automatic: Deploys to `dev` on push to `main`
   - Manual: Use workflow dispatch for `dev/test/prod`

#### Workflow Details

- **Triggers**: Push to `main`, manual dispatch
- **Authentication**: OIDC (no AWS credentials needed)
- **Steps**:
  1. Checkout code
  2. Setup Python/Node.js
  3. Build Lambda package
  4. Build frontend
  5. Terraform init/plan/apply
  6. Deploy frontend to S3

---

## Development Details

### Backend Development

#### Local Server
```bash
cd backend
uv sync
uv run server.py
```
- Runs on `http://localhost:8000`
- Auto-reload enabled
- Reads data from `./data/` directory

#### Lambda Package
```bash
cd backend
python deploy.py
```
- Creates `lambda-deployment.zip`
- Includes dependencies
- Downloads from S3 if `PERSONAL_DATA_BUCKET` is set

#### File Structure
- `server.py`: FastAPI application (local dev)
- `lambda_handler.py`: Lambda entry point
- `context.py`: AI context and prompt management
- `resources.py`: Data file loading
- `deploy.py`: Lambda packaging script

### Frontend Development

#### Local Server
```bash
cd frontend
npm install
npm run dev
```
- Runs on `http://localhost:3000`
- Requires `NEXT_PUBLIC_API_URL` environment variable

#### Build
```bash
npm run build
```
- Creates static export in `out/` directory
- Ready for S3 deployment

### Environment Variables

#### Backend (Lambda)
- `AI_PROVIDER`: AI provider to use - `"bedrock"` (default) or `"openai"` for local dev
- `BEDROCK_MODEL_ID`: AWS Bedrock model (default: `eu.amazon.nova-lite-v1:0`)
- `OPENAI_API_KEY`: OpenAI API key (required when `AI_PROVIDER=openai`)
- `OPENAI_MODEL`: OpenAI model to use (default: `gpt-4o-mini`)
- `MEMORY_BUCKET`: S3 bucket for conversation memory
- `PERSONAL_DATA_BUCKET`: S3 bucket for personal data
- `USE_S3`: Use S3 for memory storage (default: `false`)

#### Frontend
- `NEXT_PUBLIC_API_URL`: API Gateway endpoint URL

### Data Files

#### Required Files
- `facts.json`: Structured personal facts (JSON)
- `summary.txt`: Personal summary (text)
- `style.txt`: Communication style (text)
- `linkedin.pdf`: LinkedIn profile (PDF)

#### Optional Files
- `me.txt`: Additional personal description (text)

#### Template Files
Located in `backend/data/` (with `_template` suffix):
- `facts_template.json`
- `summary_template.txt`
- `linkedin_template.pdf`
- `style_template.txt`
- `me_template.txt`

### Scripts

- `scripts/deploy.sh`: Full deployment pipeline
- `scripts/destroy.sh`: Infrastructure teardown
- `scripts/upload-personal-data.sh`: Upload data to S3
- `scripts/setup-local-data.sh`: Setup local data files

---

## Troubleshooting

### Common Issues

#### Lambda Deployment Package Too Large
- Lambda limit: 50MB zipped, 250MB unzipped
- Solution: Use Lambda layers for dependencies (not currently implemented)


#### Terraform State Lock
- Check if another process is running
- Check DynamoDB table for locks
- Force unlock if needed: `terraform force-unlock LOCK_ID`

#### CloudFront Not Updating
- CloudFront has cache - wait for TTL or invalidate cache
- Invalidate: AWS Console → CloudFront → Invalidations

#### Bedrock Model Not Available
- Check model availability in your region
- Verify IAM permissions
- Check model ID format (may need `eu.` or `us.` prefix)

---

## Security Considerations

1. **IAM Roles**: Least privilege access
2. **S3 Buckets**: Private with encryption
3. **API Gateway**: CORS configured, throttling enabled
4. **Secrets**: Use AWS Secrets Manager for sensitive data (not implemented)
5. **Custom Domain**: SSL/TLS via ACM certificates

---

## Performance Optimization

1. **Lambda**: Adjust memory/timeout based on usage
2. **CloudFront**: Configure cache policies
3. **Bedrock**: Choose appropriate model tier (micro/lite/pro)
4. **S3**: Use appropriate storage class
5. **API Gateway**: Configure throttling and caching

---

## Cost Optimization

1. **Bedrock**: Use `nova-micro` for development, `nova-lite` for production
2. **Lambda**: Right-size memory allocation
3. **CloudFront**: Use appropriate cache TTL
4. **S3**: Use lifecycle policies for old data
5. **API Gateway**: Monitor and optimize request patterns

---

For more information, see the main [README.md](../README.md) or [ONBOARDING.md](../ONBOARDING.md).

