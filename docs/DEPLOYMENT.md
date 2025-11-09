# Cloud Deployment Guide

This guide covers deploying the Digital Twin AI application to AWS.

---

## ⚠️ Cost Disclaimer

**IMPORTANT**: Deploying this application to AWS will incur cloud infrastructure costs. These costs are the responsibility of the user and will be charged to your AWS account. Costs may vary based on:

- Number of requests and API calls
- Data transfer and storage
- CloudFront distribution usage
- Lambda execution time
- Geographic distribution of users

Please review the [Cost Optimization](#cost-optimization) section for more details and monitor your AWS billing dashboard regularly.

---

## Table of Contents

- [Prerequisites](#prerequisites)
  - [AWS IAM User Setup](#prerequisites-aws-iam-user-setup)
  - [AWS Terraform Backend Setup](#prerequisites-aws-terraform-backend-setup)
- [Deployment Methods](#deployment-methods)
  - [Standard Deployment (with encrypted private repo)](#standard-deployment-with-encrypted-private-repo)
  - [Local Data Deployment](#local-data-deployment)
- [What Gets Created](#what-gets-created)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites: AWS IAM User Setup

⚠️ **IMPORTANT: Do NOT use the AWS root user for these operations!**

Before proceeding with deployment, ensure you have:

1. **Created an IAM user** (not root) with appropriate permissions
2. **Configured AWS CLI** with this IAM user's credentials

### Required IAM Permissions

Your IAM user needs the following permissions to deploy this application:

- **S3**: Full access (for frontend hosting, data storage, and Terraform state)
- **Lambda**: Full access (for backend function deployment)
- **API Gateway**: Full access (for HTTP API)
- **CloudFront**: Full access (for CDN distribution)
- **IAM**: Create and manage roles/policies (for Lambda execution role)
- **Route53**: Manage DNS records (optional, for custom domains)
- **ACM**: Manage SSL certificates (optional, for custom domains)
- **DynamoDB**: Create and manage tables (for Terraform state locking)

**Recommended approach**: Attach the following AWS managed policies to your IAM user:
- `PowerUserAccess` (recommended for development)
- Or create a custom policy with the specific permissions listed above

### Configure AWS CLI

```bash
aws configure
# Enter your IAM user's Access Key ID
# Enter your IAM user's Secret Access Key
# Default region: eu-central-1 (or your preferred region)
# Default output format: json
```

Verify your configuration:
```bash
aws sts get-caller-identity
# Should show your IAM user ARN (NOT root)
```

### Check Your IAM Permissions

To verify what permissions your IAM user has:

```bash
# Get your username
USERNAME=$(aws sts get-caller-identity --query Arn --output text | cut -d'/' -f2)

# List attached managed policies
aws iam list-attached-user-policies --user-name "$USERNAME"

# List groups and their policies
aws iam list-groups-for-user --user-name "$USERNAME"
```

---

## Prerequisites: AWS Terraform Backend Setup

**This is a one-time setup per AWS account** to enable remote state management for Terraform.

### 1. Create S3 bucket for Terraform state

This bucket stores the `.tfstate` files for all environments (dev/test/prod):

```bash
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

aws s3 mb s3://digital-twin-terraform-state-${AWS_ACCOUNT_ID} --region eu-central-1

aws s3api put-bucket-versioning \
  --bucket digital-twin-terraform-state-${AWS_ACCOUNT_ID} \
  --versioning-configuration Status=Enabled \
  --region eu-central-1
```

**Note**: The bucket name must be globally unique (using your AWS account ID ensures this). Versioning is enabled to recover previous state versions if needed.

### 2. Create DynamoDB table for state locking

This prevents concurrent `terraform apply` operations on the same state:

```bash
aws dynamodb create-table \
  --table-name digital-twin-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-central-1
```

**Note**: This table stores a single lock record at a time to coordinate Terraform operations.

### 3. Backend configuration

The backend is already configured in `terraform/backend.tf` and the deployment script automatically connects to it. Once the S3 bucket and DynamoDB table exist, you can run:

```bash
./scripts/deploy.sh dev
```

Terraform will automatically use the shared remote backend with:
- **Bucket**: `digital-twin-terraform-state-<account-id>`
- **Lock table**: `digital-twin-terraform-locks`
- **Encryption**: Enabled

This setup works for both local development and CI/CD pipelines.

---

## Deployment Methods

### Standard Deployment (with encrypted private repo)

This method uses encrypted data stored in a separate private repository.

Deploy to AWS using Terraform:

```bash
./scripts/deploy.sh dev
```

**Available environments:**
- `dev` - Development environment
- `test` - Testing environment
- `prod` - Production environment

**What happens during deployment:**

1. **Download encrypted data** from the private repository
2. **Decrypt the data files** using the encryption key
3. **Upload data to S3** for the Lambda function to access
4. **Build Lambda package** with all dependencies
5. **Deploy infrastructure** using Terraform (Lambda, API Gateway, S3, CloudFront)
6. **Build and upload frontend** to S3 and CloudFront

### Local Data Deployment

If you're using local data (not the private repo approach), use the `--use-local` flag:

```bash
./scripts/deploy.sh --use-local dev
```

This will skip the download and decryption steps and use the data files you have in `backend/data/personal_data/`.

**Use this approach if:**
- You don't have a private data repository
- You've committed your data directly to the repo
- You're forking the project and using your own data

### Deployment Script Options

View all deployment options:

```bash
./scripts/deploy.sh --help
```

**Usage:**
```bash
./scripts/deploy.sh [--use-local] [ENVIRONMENT] [PROJECT_NAME]
```

**Examples:**
```bash
# Deploy dev with encrypted data from private repo
./scripts/deploy.sh dev

# Deploy prod with local data
./scripts/deploy.sh --use-local prod

# Deploy to custom project name
./scripts/deploy.sh prod my-digital-twin
```

---

## What Gets Created

The deployment creates the following AWS resources:

### Core Infrastructure

- **Lambda Function**: Python FastAPI backend with AWS Bedrock integration
- **API Gateway**: HTTP API endpoint for backend communication
- **S3 Buckets**:
  - Frontend hosting bucket
  - Personal data storage bucket
  - Conversation memory bucket
- **CloudFront Distribution**: Global CDN for fast frontend delivery
- **IAM Roles**: Lambda execution role with necessary permissions

### Optional Resources (for production)

- **Route53 Records**: DNS records for custom domain
- **ACM Certificate**: SSL/TLS certificate for HTTPS

### Terraform State Management

- **S3 Backend**: Remote state storage
- **DynamoDB Lock Table**: State locking for concurrent operations

---

## Environments

The application supports three environments:

### Dev
- For development and testing
- Uses default AWS Bedrock configuration
- No custom domain

**Deploy:**
```bash
./scripts/deploy.sh dev
```

### Test
- For pre-production testing
- Mirrors production configuration
- No custom domain

**Deploy:**
```bash
./scripts/deploy.sh test
```

### Prod
- Production environment
- Custom domain support (optional)
- Configured via `terraform/prod.tfvars`

**Deploy:**
```bash
./scripts/deploy.sh prod
```

---

## Post-Deployment

After successful deployment, you'll see output like:

```
✅ Deployment complete!
============================================
🌐 CloudFront: https://d1234567890.cloudfront.net
🔗 Custom domain: https://your-domain.com (if configured)

ℹ️  Note: API Gateway URL is configured but not displayed for security.
   The frontend uses it internally via environment variables.
```

### Access Your Application

1. **Via CloudFront URL**: The distribution URL is provided in the deployment output
2. **Via Custom Domain**: If configured in `prod.tfvars`

### Security Note

🔒 **The API Gateway URL is intentionally not displayed in deployment outputs** 

**If you need the API Gateway URL for debugging:**

```bash
# Navigate to terraform directory
cd terraform

# Make sure you're in the correct workspace/environment
terraform workspace select dev  # or test/prod

# Get the API Gateway URL
terraform output -raw api_gateway_url
```

**Important**: Keep the API Gateway URL private. Direct access to the API bypasses:
- CloudFront caching
- Potential WAF rules (if configured)
- Frontend-based rate limiting

### Verify Deployment

Test via the CloudFront URL (recommended):
```bash
curl https://your-cloudfront-url.cloudfront.net/api/health
```

Or directly via API Gateway (for debugging only):
```bash
# Navigate to terraform directory
cd terraform

# Select the correct workspace
terraform workspace select dev  # or test/prod

# Get the URL and test
API_URL=$(terraform output -raw api_gateway_url)
curl $API_URL/health
```

---

## CI/CD with GitHub Actions

The project includes a GitHub Actions workflow for automated deployment.

### Automatic Deployments

- **Push to `main`**: Automatically deploys to `dev` environment
- **Manual trigger**: Deploy to any environment via workflow dispatch

### Required GitHub Secrets

Configure these in your GitHub repository settings:

**AWS Configuration:**
- `AWS_ROLE_ARN`: ARN of the IAM role for GitHub OIDC
- `AWS_ACCOUNT_ID`: Your AWS account ID
- `DEFAULT_AWS_REGION`: AWS region (e.g., `eu-central-1`)

**Data Management (for private repo approach):**
- `PRIVATE_DATA_PAT`: GitHub Personal Access Token for private data repo
- `DATA_KEY`: Encryption key for data files

**Variables:**
- `PRIVATE_DATA_REPO`: Name of private data repository (e.g., `username/repo-name`)

### Manual Deployment via GitHub Actions

1. Go to **Actions** tab in your repository
2. Select **Deploy Digital Twin** workflow
3. Click **Run workflow**
4. Choose environment (`dev`, `test`, or `prod`)
5. Optionally enable **Use local data** if not using private repo

---

## Security Considerations

### API Gateway Access Control

By default, the API Gateway endpoint is publicly accessible but:
- Rate limiting is configured in the backend application
- The API URL is not publicly displayed to reduce exposure


### Data Protection

- Personal data in S3 is encrypted at rest (AES256)
- Terraform state is encrypted in S3
- Use separate AWS accounts for dev/prod for isolation
- Regularly rotate AWS credentials

### Monitoring

Enable CloudWatch alarms for:
- Unusual API request patterns
- Lambda errors
- High data transfer costs
- Failed authentication attempts

---

## Troubleshooting

### Common Issues

**"Terraform state bucket not found"**
- Make sure you've run the Terraform backend setup steps
- Verify bucket name matches: `digital-twin-terraform-state-<account-id>`

**"Access Denied" errors**
- Check your IAM user permissions
- Run `aws sts get-caller-identity` to verify you're using the correct user
- Ensure you're not using the root user

**"Lambda deployment package too large"**
- This is normal for the first deployment
- The Lambda layer is optimized to reduce package size

**Frontend not updating after deployment**
- CloudFront cache may need to be invalidated
- The deployment script handles this automatically
- Manual invalidation: `aws cloudfront create-invalidation --distribution-id <ID> --paths "/*"`

**API Gateway 403 errors**
- Check CORS configuration in `backend/app/core/config.py`
- Verify `CORS_ORIGINS` environment variable

### Getting Help

For additional help:
- Check the [main README](../README.md) for local development setup
- Review Terraform logs: `cd terraform && terraform plan`
- Check AWS CloudWatch logs for Lambda errors

---

## Cleanup / Destroy Resources

### Destroying an Environment

To remove all deployed resources for a specific environment:

```bash
./scripts/destroy.sh dev
# or
./scripts/destroy.sh test
# or
./scripts/destroy.sh prod
```

**What gets destroyed:**
- Lambda function
- API Gateway
- CloudFront distribution
- S3 buckets (frontend, data, memory)
- IAM roles and policies
- Route53 records (if configured)
- CloudWatch log groups

**What is NOT destroyed:**
- ✅ Terraform state bucket (`digital-twin-terraform-state-<account-id>`)
- ✅ DynamoDB lock table (`digital-twin-terraform-locks`)

These Terraform backend resources are shared across all environments and are intentionally preserved. They should only be manually deleted if you're completely removing the project from your AWS account.

### Complete Cleanup (Manual)

If you want to remove **everything** including the Terraform backend:

```bash
# 1. Destroy all environments first
./scripts/destroy.sh dev
./scripts/destroy.sh test
./scripts/destroy.sh prod

# 2. Manually delete the Terraform state bucket
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 rb s3://digital-twin-terraform-state-${AWS_ACCOUNT_ID} --force

# 3. Manually delete the DynamoDB lock table
aws dynamodb delete-table --table-name digital-twin-terraform-locks
```

**⚠️ Warning**: 
- This will delete all resources including data buckets and conversation history
- Make sure to backup any important data before destroying
- The destroy operation is irreversible

---

## Cost Optimization

The serverless architecture is cost-effective:

- **Lambda**: Pay per request (free tier: 1M requests/month)
- **S3**: Pay for storage and transfer (minimal for small sites)
- **CloudFront**: Pay per request and data transfer
- **API Gateway**: Pay per request (free tier: 1M requests/month)
- **DynamoDB**: On-demand billing (pay per request)

**Estimated monthly cost** for low-traffic usage: $5-10/month

