#!/bin/bash
set -euo pipefail

# Show usage if --help is requested
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
  cat << 'EOF'
Usage: ./scripts/deploy.sh [--use-local] [ENVIRONMENT] [PROJECT_NAME]

Deploy the Digital Twin application to AWS.

Options:
  --use-local       Use local data files instead of downloading from private repo
  ENVIRONMENT       Deployment environment (dev|test|prod) [default: dev]
  PROJECT_NAME      Project name [default: digital-twin]

Examples:
  # Deploy dev with encrypted data from private repo
  ./scripts/deploy.sh dev

  # Deploy prod with local data
  ./scripts/deploy.sh --use-local prod

  # Deploy to custom project
  ./scripts/deploy.sh prod my-digital-twin
EOF
  exit 0
fi

# Parse arguments
USE_LOCAL=false
ENVIRONMENT=""
PROJECT_NAME=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --use-local)
      USE_LOCAL=true
      shift
      ;;
    *)
      if [ -z "$ENVIRONMENT" ]; then
        ENVIRONMENT=$1
      elif [ -z "$PROJECT_NAME" ]; then
        PROJECT_NAME=$1
      fi
      shift
      ;;
  esac
done

# Set defaults
ENVIRONMENT=${ENVIRONMENT:-dev}
PROJECT_NAME=${PROJECT_NAME:-digital-twin}

echo "🚀 Deploying ${PROJECT_NAME} → ${ENVIRONMENT}"
if [ "$USE_LOCAL" = true ]; then
  echo "📦 Using local data (skipping download/decrypt)"
else
  echo "🔐 Using encrypted data from private repo"
fi
echo ""

# 0. Handle data setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ "$USE_LOCAL" = true ]; then
  echo "📂 Using local data files..."
  if [ ! -d "$PROJECT_ROOT/backend/data/personal_data" ] || [ -z "$(ls -A $PROJECT_ROOT/backend/data/personal_data 2>/dev/null)" ]; then
    echo "⚠️  Warning: No personal data found in backend/data/personal_data/"
    echo "   Run './scripts/setup-local-data.sh' to copy templates or add your own files"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
      exit 1
    fi
  fi
else
  echo "📥 Step 1: Download encrypted data..."
  if [ -f "$SCRIPT_DIR/download-encrypted-data.sh" ]; then
    "$SCRIPT_DIR/download-encrypted-data.sh"
  else
    echo "⚠️  Warning: download-encrypted-data.sh not found, skipping..."
  fi
  
  echo ""
  echo "🔓 Step 2: Decrypt data..."
  if [ -f "$SCRIPT_DIR/decrypt-data.sh" ]; then
    "$SCRIPT_DIR/decrypt-data.sh"
  else
    echo "⚠️  Warning: decrypt-data.sh not found, skipping..."
  fi
fi

echo ""
echo "☁️  Step 3: Upload data to S3..."
if [ -f "$SCRIPT_DIR/upload-personal-data.sh" ]; then
  "$SCRIPT_DIR/upload-personal-data.sh" "$ENVIRONMENT" "$PROJECT_NAME"
else
  echo "⚠️  Warning: upload-personal-data.sh not found, skipping..."
fi

echo ""
echo "📦 Step 4: Build Lambda package..."
# Build Lambda package
cd "$PROJECT_ROOT"
(cd backend && uv run deploy.py)

echo ""
echo "🏗️  Step 5: Terraform init + apply..."
# Terraform init + apply
cd terraform
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${DEFAULT_AWS_REGION:-eu-central-1}
echo "Region set to $AWS_REGION"
export AWS_DEFAULT_REGION=$AWS_REGION

STATE_BUCKET="${PROJECT_NAME}-terraform-state-${AWS_ACCOUNT_ID}"
LOCK_TABLE="${PROJECT_NAME}-terraform-locks"

if ! aws s3api head-bucket --bucket "$STATE_BUCKET" >/dev/null 2>&1; then
  echo "❌ Terraform state bucket not found."
  echo "   Please ensure the shared Terraform backend resources exist before running deploy."
  exit 1
fi

if ! aws dynamodb describe-table --table-name "$LOCK_TABLE" >/dev/null 2>&1; then
  echo "❌ Terraform lock table not found."
  echo "   Please ensure the shared Terraform backend resources exist before running deploy."
  exit 1
fi

if [ -f "terraform.tfstate" ] && ! aws s3api head-object \
      --bucket "$STATE_BUCKET" \
      --key "${PROJECT_NAME}/${ENVIRONMENT}.tfstate" >/dev/null 2>&1; then
  echo "🌀 Local state detected, migrating to remote backend..."
  terraform init -migrate-state -backend-config="bucket=$STATE_BUCKET" \
    -backend-config="key=${PROJECT_NAME}/${ENVIRONMENT}.tfstate" \
    -backend-config="region=$AWS_REGION" \
    -backend-config="dynamodb_table=$LOCK_TABLE" \
    -backend-config="encrypt=true"
  rm -f terraform.tfstate terraform.tfstate.backup
else
  terraform init -input=false -reconfigure \
    -backend-config="bucket=$STATE_BUCKET" \
    -backend-config="key=${PROJECT_NAME}/${ENVIRONMENT}.tfstate" \
    -backend-config="region=$AWS_REGION" \
    -backend-config="dynamodb_table=$LOCK_TABLE" \
    -backend-config="encrypt=true"
fi

# Workspace
if ! terraform workspace list | grep -q "$ENVIRONMENT"; then
  terraform workspace new "$ENVIRONMENT"
else
  terraform workspace select "$ENVIRONMENT"
fi

# Apply
if [ "$ENVIRONMENT" = "prod" ] && [ -f "prod.tfvars" ]; then
  terraform apply -var-file=prod.tfvars \
    -var="project_name=$PROJECT_NAME" -var="environment=$ENVIRONMENT" -auto-approve
else
  terraform apply \
    -var="project_name=$PROJECT_NAME" -var="environment=$ENVIRONMENT" -auto-approve
fi

echo ""
echo "🌐 Step 6: Build and upload frontend..."
# Frontend upload
API_URL=$(terraform output -raw api_gateway_url)
FRONTEND_BUCKET=$(terraform output -raw s3_frontend_bucket)
CUSTOM_URL=$(terraform output -raw custom_domain_url 2>/dev/null || true)

cd ../frontend
echo "NEXT_PUBLIC_API_URL=$API_URL" > .env.production
npm ci
npm run build
aws s3 sync ./out "s3://$FRONTEND_BUCKET/" --delete
cd ..

# Done
echo ""
echo "============================================"
echo "✅ Deployment complete!"
echo "============================================"
echo "🌐 CloudFront: $(terraform -chdir=terraform output -raw cloudfront_url)"
[ -n "$CUSTOM_URL" ] && echo "🔗 Custom domain: $CUSTOM_URL"
echo ""
echo "ℹ️  Note: API Gateway URL is configured but not displayed for security."
echo "   The frontend uses it internally via environment variables."
