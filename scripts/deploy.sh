#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
PROJECT_NAME=${2:-digital-twin}

echo "🚀 Deploying ${PROJECT_NAME} to ${ENVIRONMENT}..."

# 1. Build Lambda package
cd "$(dirname "$0")/.."        # project root
echo "📦 Building Lambda package..."

# Set PERSONAL_DATA_BUCKET if we want to download from S3 during build
# This is optional - if not set, local data files will be used
if [ -n "${USE_S3_DATA:-}" ]; then
  export PERSONAL_DATA_BUCKET="digital-twin-data-${ENVIRONMENT}"
  echo "📥 Will download personal data from S3: $PERSONAL_DATA_BUCKET"
else
  echo "📋 Will use local data files (set USE_S3_DATA=true to download from S3)"
fi

(cd backend && uv run deploy.py)

# 2. Terraform workspace & apply
cd terraform
echo "🛠 Ensuring Terraform backend resources exist..."
# ../scripts/setup-backend.sh "$PROJECT_NAME"
export TF_IN_AUTOMATION=true
export TF_CLI_ARGS="-no-color"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=${DEFAULT_AWS_REGION:-eu-west-1}
terraform init -input=false 
# -reconfigure \
#   -backend-config="bucket=digital-twin-terraform-state-${AWS_ACCOUNT_ID}" \
#   -backend-config="key=terraform.tfstate" \
#   -backend-config="region=${AWS_REGION}" \
#   -backend-config="dynamodb_table=${PROJECT_NAME}-terraform-locks" \
#   -backend-config="encrypt=true"

if ! terraform workspace list | grep -q "$ENVIRONMENT"; then
  terraform workspace new "$ENVIRONMENT"
else
  terraform workspace select "$ENVIRONMENT"
fi

# Use prod.tfvars for production environment
if [ "$ENVIRONMENT" = "prod" ]; then
  TF_APPLY_CMD=(terraform apply -var-file=prod.tfvars -var="project_name=$PROJECT_NAME" -var="environment=$ENVIRONMENT" -auto-approve)
else
  TF_APPLY_CMD=(terraform apply -var="project_name=$PROJECT_NAME" -var="environment=$ENVIRONMENT" -auto-approve)
fi

echo "🎯 Applying Terraform..."
"${TF_APPLY_CMD[@]}"

API_URL=$(terraform output -raw api_gateway_url)
FRONTEND_BUCKET=$(terraform output -raw s3_frontend_bucket)
CUSTOM_URL=$(terraform output -raw custom_domain_url 2>/dev/null || true)

# 3. Build + deploy frontend
cd ../frontend

ENV_FILE=".env.production"

if [ -f ".env" ]; then
  cp .env "$ENV_FILE"
  echo "📋 Copied frontend/.env → .env.production"
else
  > "$ENV_FILE"
  echo "⚠️  frontend/.env not found. Creating empty .env.production"
fi

echo "NEXT_PUBLIC_API_URL=$API_URL" >> "$ENV_FILE"
API_URL_SEGMENT=${API_URL##*/}
echo "📝 Building frontend (NEXT_PUBLIC_API_URL ending with /$API_URL_SEGMENT)"

if [ "${DISABLE_CLERK_FOR_EXPORT:-}" = "true" ]; then
  echo "NEXT_PUBLIC_DISABLE_CLERK=true" >> "$ENV_FILE"
  echo "🙈 Clerk auth temporarily disabled for static export build"
fi

npm install
npm run build
aws s3 sync ./out "s3://$FRONTEND_BUCKET/" --delete
cd ..

# 4. Final messages
echo -e "\n✅ Deployment complete!"
echo "🌐 CloudFront URL : $(terraform -chdir=terraform output -raw cloudfront_url)"
if [ -n "$CUSTOM_URL" ]; then
  echo "🔗 Custom domain  : $CUSTOM_URL"
fi
echo "📡 API Gateway    : $API_URL"