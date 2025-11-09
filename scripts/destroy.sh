#!/bin/bash
set -euo pipefail

if [ $# -eq 0 ]; then
  echo "❌ Usage: $0 <environment> (dev|test|prod)"
  exit 1
fi

ENVIRONMENT=$1
PROJECT_NAME=${2:-digital-twin}
AWS_REGION=${DEFAULT_AWS_REGION:-eu-central-1}
export AWS_DEFAULT_REGION=$AWS_REGION

echo "🗑️ Destroying ${PROJECT_NAME}-${ENVIRONMENT}..."

cd "$(dirname "$0")/../terraform"

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
STATE_BUCKET="${PROJECT_NAME}-terraform-state-${AWS_ACCOUNT_ID}"
LOCK_TABLE="${PROJECT_NAME}-terraform-locks"

terraform init -input=false -reconfigure \
  -backend-config="bucket=${STATE_BUCKET}" \
  -backend-config="key=${PROJECT_NAME}/${ENVIRONMENT}.tfstate" \
  -backend-config="region=${AWS_REGION}" \
  -backend-config="dynamodb_table=${LOCK_TABLE}" \
  -backend-config="encrypt=true"

terraform workspace select "$ENVIRONMENT"

# Dummy lambda zip (needed in CI for destroy)
[ ! -f "../backend/lambda-deployment.zip" ] && echo "dummy" | zip ../backend/lambda-deployment.zip -

terraform destroy \
  -var="project_name=$PROJECT_NAME" -var="environment=$ENVIRONMENT" -auto-approve

echo "✅ Destroy complete for ${ENVIRONMENT}"
echo "ℹ️ Terraform backend resources (state bucket and lock table) remain in your account."
echo "   Delete them manually if you intend to remove the Terraform backend."