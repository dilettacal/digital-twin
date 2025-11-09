#!/bin/bash
set -euo pipefail

if [[ "${1:-}" == "--help" ]] || [[ "${1:-}" == "-h" ]]; then
  cat <<'EOF'
Usage: ./scripts/destroy.sh [--verbose] [ENVIRONMENT] [PROJECT_NAME]

Destroy the Digital Twin infrastructure for the given environment.

Options:
  --verbose, -v     Show detailed command output
  ENVIRONMENT       Target environment (dev|test|prod) [default: dev]
  PROJECT_NAME      Project name prefix [default: digital-twin]

Examples:
  ./scripts/destroy.sh dev
  ./scripts/destroy.sh --verbose prod my-digital-twin
EOF
  exit 0
fi

VERBOSE=false
ENVIRONMENT=""
PROJECT_NAME=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    *)
      if [ -z "$ENVIRONMENT" ]; then
        ENVIRONMENT=$1
      elif [ -z "$PROJECT_NAME" ]; then
        PROJECT_NAME=$1
      else
        echo "❌ Unexpected argument: $1" >&2
        exit 1
      fi
      shift
      ;;
  esac
done

ENVIRONMENT=${ENVIRONMENT:-dev}
PROJECT_NAME=${PROJECT_NAME:-digital-twin}

QUIET=false
if [ "${CI:-false}" = "true" ] || [ -n "${GITHUB_ACTIONS:-}" ]; then
  QUIET=true
fi
if [ "$VERBOSE" = true ]; then
  QUIET=false
fi

announce() {
  if [ "$QUIET" = false ]; then
    echo "$@"
  else
    printf '%s\n' "$@" >&2
  fi
}

log() {
  if [ "$VERBOSE" = true ]; then
    echo "$@"
  fi
}

run_cmd() {
  if [ "$QUIET" = false ]; then
    "$@"
  else
    if ! output=$("$@" 2>&1); then
      printf '%s\n' "$output" >&2
      return 1
    fi
  fi
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="${PROJECT_ROOT}/terraform"

announce "🗑️ Destroying ${PROJECT_NAME}-${ENVIRONMENT}..."

AWS_REGION=${DEFAULT_AWS_REGION:-eu-central-1}
export AWS_DEFAULT_REGION=$AWS_REGION
log "Region set to ${AWS_REGION}"

cd "$TERRAFORM_DIR"

if ! AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text); then
  echo "❌ Unable to determine AWS Account ID. Check your AWS credentials." >&2
  exit 1
fi

STATE_BUCKET="${PROJECT_NAME}-terraform-state-${AWS_ACCOUNT_ID}"
LOCK_TABLE="${PROJECT_NAME}-terraform-locks"
REMOTE_KEY="${PROJECT_NAME}/${ENVIRONMENT}.tfstate"
FRONTEND_BUCKET_DEFAULT="${PROJECT_NAME}-${ENVIRONMENT}-frontend-${AWS_ACCOUNT_ID}"
MEMORY_BUCKET_DEFAULT="${PROJECT_NAME}-${ENVIRONMENT}-memory-${AWS_ACCOUNT_ID}"

if ! aws s3api head-bucket --bucket "$STATE_BUCKET" >/dev/null 2>&1; then
  echo "❌ Terraform state bucket ${STATE_BUCKET} not found." >&2
  echo "   Ensure the shared Terraform backend resources exist before running destroy." >&2
  exit 1
fi

if ! aws dynamodb describe-table --table-name "$LOCK_TABLE" >/dev/null 2>&1; then
  echo "❌ Terraform lock table ${LOCK_TABLE} not found." >&2
  echo "   Ensure the shared Terraform backend resources exist before running destroy." >&2
  exit 1
fi

if [ -f "terraform.tfstate" ] && ! aws s3api head-object --bucket "$STATE_BUCKET" --key "$REMOTE_KEY" >/dev/null 2>&1; then
  announce "🌀 Local state detected, migrating to remote backend..."
  run_cmd terraform init -migrate-state \
    -backend-config="bucket=${STATE_BUCKET}" \
    -backend-config="key=${REMOTE_KEY}" \
    -backend-config="region=${AWS_REGION}" \
    -backend-config="dynamodb_table=${LOCK_TABLE}" \
    -backend-config="encrypt=true"
  rm -f terraform.tfstate terraform.tfstate.backup
else
  run_cmd terraform init -input=false -reconfigure \
    -backend-config="bucket=${STATE_BUCKET}" \
    -backend-config="key=${REMOTE_KEY}" \
    -backend-config="region=${AWS_REGION}" \
    -backend-config="dynamodb_table=${LOCK_TABLE}" \
    -backend-config="encrypt=true"
fi

if ! run_cmd terraform workspace select "$ENVIRONMENT"; then
  announce "ℹ️ Terraform workspace '${ENVIRONMENT}' not found. Nothing to destroy."
  exit 0
fi

get_tf_output() {
  local name=$1
  local value
  if ! value=$(terraform output -raw "$name" 2>/dev/null); then
    return 1
  fi

  if [ -z "$value" ]; then
    return 1
  fi
  # Trim trailing whitespace
  value=${value//$'\r'/}
  value=${value//$'\n'/}
  if [[ "$value" == *"│ Warning:"* ]] || [[ "$value" == *"╷"* ]]; then
    return 1
  fi
  if [[ ! "$value" =~ ^[A-Za-z0-9.\-_/]+$ ]]; then
    return 1
  fi
  printf '%s\n' "$value"
  return 0
}

resolve_bucket_name() {
  local output_name=$1
  local fallback_name=$2
  local bucket_name=""
  if bucket_name=$(get_tf_output "$output_name"); then
    echo "$bucket_name"
    return 0
  fi
  echo "$fallback_name"
  return 0
}

empty_bucket() {
  local bucket_name=$1
  local friendly_name=$2

  if [ -z "$bucket_name" ]; then
    log "Skipping ${friendly_name}; bucket name is empty."
    return 0
  fi

  if ! aws s3api head-bucket --bucket "$bucket_name" >/dev/null 2>&1; then
    log "Bucket ${bucket_name} not found; skipping ${friendly_name}."
    return 0
  fi

  announce "🧹 Emptying ${friendly_name} s3://${bucket_name}..."
  if ! run_cmd aws s3 rm "s3://${bucket_name}" --recursive; then
    announce "⚠️ Failed to empty ${friendly_name} ${bucket_name}. Continuing destroy."
    return 1
  fi

  return 0
}

FRONTEND_BUCKET=$(resolve_bucket_name "s3_frontend_bucket" "$FRONTEND_BUCKET_DEFAULT")
MEMORY_BUCKET=$(resolve_bucket_name "s3_memory_bucket" "$MEMORY_BUCKET_DEFAULT")

empty_bucket "$FRONTEND_BUCKET" "frontend bucket" || true
empty_bucket "$MEMORY_BUCKET" "memory bucket" || true

LAMBDA_ZIP="${PROJECT_ROOT}/backend/lambda-deployment.zip"
if [ ! -f "$LAMBDA_ZIP" ]; then
  log "Creating dummy lambda deployment package at ${LAMBDA_ZIP}"
  if ! echo "dummy" | zip -q "$LAMBDA_ZIP" - >/dev/null 2>&1; then
    announce "⚠️ Unable to create dummy lambda package at ${LAMBDA_ZIP}. Terraform may fail if it expects this file."
  fi
fi

DESTROY_CMD=(terraform destroy)
if [ "$ENVIRONMENT" = "prod" ] && [ -f "prod.tfvars" ]; then
  DESTROY_CMD+=(-var-file=prod.tfvars)
fi
DESTROY_CMD+=(-var="project_name=$PROJECT_NAME" -var="environment=$ENVIRONMENT" -auto-approve)

if ! run_cmd "${DESTROY_CMD[@]}"; then
  echo "❌ Terraform destroy failed." >&2
  exit 1
fi

announce "✅ Destroy complete for ${ENVIRONMENT}"
announce "ℹ️ Terraform backend resources (state bucket and lock table) remain in your account."
announce "   Delete them manually if you intend to remove the Terraform backend."
