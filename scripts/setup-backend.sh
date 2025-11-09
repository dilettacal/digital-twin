#!/bin/bash
set -euo pipefail

PROJECT_NAME=${1:-digital-twin}
AWS_REGION=${DEFAULT_AWS_REGION:-eu-central-1}
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

STATE_BUCKET="${PROJECT_NAME}-terraform-state-${AWS_ACCOUNT_ID}"
LOCK_TABLE="${PROJECT_NAME}-terraform-locks"

log() {
  echo "[backend-setup] $1"
}

log "Ensuring Terraform backend for project '${PROJECT_NAME}' (account ${AWS_ACCOUNT_ID}, region ${AWS_REGION})"

if aws s3api head-bucket --bucket "$STATE_BUCKET" 2>/dev/null; then
  log "S3 bucket '$STATE_BUCKET' already exists"
else
  log "Creating S3 bucket '$STATE_BUCKET'"
  if [ "$AWS_REGION" = "us-east-1" ]; then
    aws s3api create-bucket --bucket "$STATE_BUCKET"
  else
    aws s3api create-bucket --bucket "$STATE_BUCKET" --create-bucket-configuration LocationConstraint="$AWS_REGION"
  fi
  aws s3api put-bucket-versioning --bucket "$STATE_BUCKET" --versioning-configuration Status=Enabled
  aws s3api put-bucket-encryption \
    --bucket "$STATE_BUCKET" \
    --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
  aws s3api put-public-access-block \
    --bucket "$STATE_BUCKET" \
    --public-access-block-configuration BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
  log "S3 bucket '$STATE_BUCKET' created and hardened"
fi

if aws dynamodb describe-table --table-name "$LOCK_TABLE" >/dev/null 2>&1; then
  log "DynamoDB table '$LOCK_TABLE' already exists"
else
  log "Creating DynamoDB table '$LOCK_TABLE'"
  aws dynamodb create-table \
    --table-name "$LOCK_TABLE" \
    --billing-mode PAY_PER_REQUEST \
    --attribute-definitions AttributeName=LockID,AttributeType=S \
    --key-schema AttributeName=LockID,KeyType=HASH \
    --tags Key=Project,Value="$PROJECT_NAME" Key=ManagedBy,Value=terraform
  log "Waiting for DynamoDB table '$LOCK_TABLE' to become active..."
  aws dynamodb wait table-exists --table-name "$LOCK_TABLE"
  log "DynamoDB table '$LOCK_TABLE' created"
fi

log "Terraform backend resources are ready."
