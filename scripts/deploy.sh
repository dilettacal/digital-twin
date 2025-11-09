#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:-dev}          # dev | test | prod
PROJECT_NAME=${2:-digital-twin}

echo "🚀 Deploying ${PROJECT_NAME} → ${ENVIRONMENT}"

# 1. Build Lambda package
cd "$(dirname "$0")/.."         # project root
echo "📦 Building Lambda package..."
(cd backend && uv run deploy.py)

# 2. Terraform init + apply
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

terraform init -input=false -reconfigure \
  -backend-config="bucket=${STATE_BUCKET}" \
  -backend-config="key=${ENVIRONMENT}/terraform.tfstate" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${LOCK_TABLE}" \
  -backend-config="encrypt=true"

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

# 3. Front-end upload
API_URL=$(terraform output -raw api_gateway_url)
FRONTEND_BUCKET=$(terraform output -raw s3_frontend_bucket)
CUSTOM_URL=$(terraform output -raw custom_domain_url 2>/dev/null || true)

cd ../frontend
echo "NEXT_PUBLIC_API_URL=$API_URL" > .env.production
npm ci
npm run build
aws s3 sync ./out "s3://$FRONTEND_BUCKET/" --delete
cd ..

# 4. Done
echo -e "\n✅ Deployment complete!"
echo "🌐 CloudFront: $(terraform -chdir=terraform output -raw cloudfront_url)"
[ -n "$CUSTOM_URL" ] && echo "🔗 Custom domain: $CUSTOM_URL"
echo "📡 API: $API_URL"
