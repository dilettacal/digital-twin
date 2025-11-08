#!/bin/bash
set -e

ENVIRONMENT=${1:-dev}
PROJECT_NAME=${2:-digital-twin}

echo "🔄 Importing existing resources into Terraform state..."

cd "$(dirname "$0")/../terraform"

# Make sure we're in the right workspace
if ! terraform workspace list | grep -q "$ENVIRONMENT"; then
  terraform workspace new "$ENVIRONMENT"
else
  terraform workspace select "$ENVIRONMENT"
fi

# Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Import S3 buckets
echo "📦 Importing S3 buckets..."
terraform import aws_s3_bucket.frontend "${PROJECT_NAME}-${ENVIRONMENT}-frontend-${AWS_ACCOUNT_ID}" || echo "  (frontend bucket already in state or doesn't exist)"
terraform import aws_s3_bucket.memory "${PROJECT_NAME}-${ENVIRONMENT}-memory-${AWS_ACCOUNT_ID}" || echo "  (memory bucket already in state or doesn't exist)"

# Import IAM role
echo "👤 Importing IAM role..."
terraform import aws_iam_role.lambda_role "${PROJECT_NAME}-${ENVIRONMENT}-lambda-role" || echo "  (IAM role already in state or doesn't exist)"

# Import Lambda function
echo "⚡ Importing Lambda function..."
terraform import aws_lambda_function.api "${PROJECT_NAME}-${ENVIRONMENT}-api" || echo "  (Lambda already in state or doesn't exist)"

# Import Lambda permission
echo "🔐 Importing Lambda permission..."
terraform import aws_lambda_permission.api_gw "${PROJECT_NAME}-${ENVIRONMENT}-api/AllowExecutionFromAPIGateway" || echo "  (Lambda permission already in state or doesn't exist)"

# Import API Gateway (if it exists)
echo "🌐 Importing API Gateway..."
# You'll need to get the API ID first
API_ID=$(aws apigatewayv2 get-apis --query "Items[?Name=='${PROJECT_NAME}-${ENVIRONMENT}-api-gateway'].ApiId" --output text 2>/dev/null || echo "")
if [ -n "$API_ID" ]; then
    terraform import aws_apigatewayv2_api.main "$API_ID" || echo "  (API Gateway already in state)"
    terraform import aws_apigatewayv2_stage.default "${API_ID}/\$default" || echo "  (API Gateway stage already in state)"
fi

echo "✅ Import complete! You can now run deploy.sh again"

