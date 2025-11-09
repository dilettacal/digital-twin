#!/bin/bash
set -euo pipefail

# Show usage if --help is requested
if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
  cat << 'EOF'
Usage: ./scripts/deploy.sh [--use-local] [--verbose] [--skip-data] [ENVIRONMENT] [PROJECT_NAME]

Deploy the Digital Twin application to AWS.

Options:
  --use-local       Use local data files instead of downloading from private repo
  --verbose         Show detailed command output (Terraform plan, npm, s3 sync)
  --skip-data       Skip data download/decrypt/upload steps (useful if already run)
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
VERBOSE=false
SKIP_DATA=false
ENVIRONMENT=""
PROJECT_NAME=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --use-local)
      USE_LOCAL=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --skip-data)
      SKIP_DATA=true
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

if [ "$VERBOSE" = true ]; then
  export DEPLOY_QUIET=false
else
  export DEPLOY_QUIET=true
fi

log() {
  if [ "$VERBOSE" = true ]; then
    echo "$@"
  fi
}

announce() {
  echo "$@"
}

run_cmd() {
  if [ "$VERBOSE" = true ]; then
    "$@"
  else
    if ! output=$("$@" 2>&1); then
      printf '%s\n' "$output" >&2
      return 1
    fi
  fi
}

announce "🚀 Deploying ${PROJECT_NAME} → ${ENVIRONMENT}"
if [ "$USE_LOCAL" = true ]; then
  announce "📦 Using local data (skipping download/decrypt)"
else
  announce "🔐 Using encrypted data from private repo"
fi
log ""

# 0. Handle data setup
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [ "$SKIP_DATA" = true ]; then
  log "⏩ Skipping data download/decrypt/upload (already handled)."
else
  if [ "$USE_LOCAL" = true ]; then
    log "📂 Using local data files..."
    if [ ! -d "$PROJECT_ROOT/backend/data/personal_data" ] || [ -z "$(ls -A $PROJECT_ROOT/backend/data/personal_data 2>/dev/null)" ]; then
      announce "⚠️  Warning: No personal data found in backend/data/personal_data/"
      announce "   Run './scripts/setup-local-data.sh' to copy templates or add your own files"
      read -p "Continue anyway? (y/n) " -n 1 -r
      echo
      if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
      fi
    fi
  else
    announce "📥 Step 1: Download encrypted data..."
    if [ -f "$SCRIPT_DIR/download-encrypted-data.sh" ]; then
      "$SCRIPT_DIR/download-encrypted-data.sh"
    else
      announce "⚠️  Warning: download-encrypted-data.sh not found, skipping..."
    fi

    log ""
    announce "🔓 Step 2: Decrypt data..."
    if [ -f "$SCRIPT_DIR/decrypt-data.sh" ]; then
      "$SCRIPT_DIR/decrypt-data.sh"
    else
      announce "⚠️  Warning: decrypt-data.sh not found, skipping..."
    fi
  fi

  log ""
  announce "☁️  Step 3: Upload data to S3..."
  if [ -f "$SCRIPT_DIR/upload-personal-data.sh" ]; then
    "$SCRIPT_DIR/upload-personal-data.sh" "$ENVIRONMENT" "$PROJECT_NAME"
  else
    announce "⚠️  Warning: upload-personal-data.sh not found, skipping..."
  fi
fi

log ""
announce "📦 Step 4: Build Lambda package..."
# Build Lambda package
cd "$PROJECT_ROOT"
run_cmd bash -c 'cd backend && uv run deploy.py'

log ""
announce "🏗️  Step 5: Terraform init + apply..."
# Terraform init + apply
cd terraform
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${DEFAULT_AWS_REGION:-eu-central-1}
log "Region set to $AWS_REGION"
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
  announce "🌀 Local state detected, migrating to remote backend..."
  run_cmd terraform init -migrate-state -backend-config="bucket=$STATE_BUCKET" \
    -backend-config="key=${PROJECT_NAME}/${ENVIRONMENT}.tfstate" \
    -backend-config="region=$AWS_REGION" \
    -backend-config="dynamodb_table=$LOCK_TABLE" \
    -backend-config="encrypt=true"
  rm -f terraform.tfstate terraform.tfstate.backup
else
  run_cmd terraform init -input=false -reconfigure \
    -backend-config="bucket=$STATE_BUCKET" \
    -backend-config="key=${PROJECT_NAME}/${ENVIRONMENT}.tfstate" \
    -backend-config="region=$AWS_REGION" \
    -backend-config="dynamodb_table=$LOCK_TABLE" \
    -backend-config="encrypt=true"
fi

# Workspace
if ! terraform workspace list | grep -q "$ENVIRONMENT"; then
  run_cmd terraform workspace new "$ENVIRONMENT"
else
  run_cmd terraform workspace select "$ENVIRONMENT"
fi

# Apply
filter_terraform_outputs() {
  awk '
BEGIN { skip=0 }
$0 == "Outputs:" { skip=1; next }
skip && NF==0 { skip=0; next }
skip { next }
{ print }
'
}

apply_with_filter() {
  local output
  if [ "$VERBOSE" = true ]; then
    "$@"
  else
    if ! output=$("$@" 2>&1 | filter_terraform_outputs); then
      printf '%s\n' "$output" >&2
      return 1
    fi
  fi
}

if [ "$ENVIRONMENT" = "prod" ] && [ -f "prod.tfvars" ]; then
  apply_with_filter terraform apply -var-file=prod.tfvars \
    -var="project_name=$PROJECT_NAME" -var="environment=$ENVIRONMENT" -auto-approve
else
  apply_with_filter terraform apply \
    -var="project_name=$PROJECT_NAME" -var="environment=$ENVIRONMENT" -auto-approve
fi

log ""
announce "🌐 Step 6: Build and upload frontend..."
# Frontend upload
API_URL=$(terraform output -raw api_gateway_url)
FRONTEND_BUCKET=$(terraform output -raw s3_frontend_bucket)
CUSTOM_URL=$(terraform output -raw custom_domain_url 2>/dev/null || true)

cd ../frontend
echo "NEXT_PUBLIC_API_URL=$API_URL" > .env.production
run_cmd npm ci
run_cmd npm run build
if [ "$VERBOSE" = true ]; then
  aws s3 sync ./out "s3://$FRONTEND_BUCKET/" --delete
else
  aws s3 sync ./out "s3://$FRONTEND_BUCKET/" --delete --only-show-errors --no-progress >/dev/null
fi
cd ..

# Done
log ""
announce "============================================"
announce "✅ Deployment complete!"
announce "============================================"
announce "🌐 CloudFront: $(terraform -chdir=terraform output -raw cloudfront_url)"
[ -n "$CUSTOM_URL" ] && announce "🔗 Custom domain: $CUSTOM_URL"
log ""
log "ℹ️  Note: API Gateway URL is configured but not displayed for security."
log "   The frontend uses it internally via environment variables."
