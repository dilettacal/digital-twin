#!/bin/bash
set -euo pipefail

# Usage: ./scripts/upload-personal-data.sh [environment] [project_name]
ENVIRONMENT=${1:-dev}          # dev | test | prod
PROJECT_NAME=${2:-digital-twin}

AWS_REGION=${DEFAULT_AWS_REGION:-eu-central-1}
BUCKET_NAME="${PROJECT_NAME}-data-${ENVIRONMENT}"
S3_URI="s3://${BUCKET_NAME}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${PROJECT_ROOT}/backend/data/personal_data"
PROMPTS_DIR="${PROJECT_ROOT}/backend/data/prompts"
PERSONAL_DATA_S3_PREFIX="personal_data"
PROMPTS_S3_PREFIX="prompts"

quiet=${DEPLOY_QUIET:-false}

log() {
  local message="$*"
  if [ "$quiet" = true ]; then
    case "$message" in
      ❌*|⚠️*)
        ;;
      *)
        return
        ;;
    esac
  fi
  echo "$(date +'%Y-%m-%dT%H:%M:%S%z') | $message"
}

log "🔐 Uploading personal data → ${ENVIRONMENT}"
log "📦 Target bucket: ${S3_URI}"
log "🌍 Region: ${AWS_REGION}"

if ! command -v aws >/dev/null 2>&1; then
  log "❌ Error: AWS CLI not found in PATH"
  exit 1
fi

if ! aws sts get-caller-identity >/dev/null 2>&1; then
  log "❌ Error: AWS CLI not configured. Please run 'aws configure'."
  exit 1
fi

if [ ! -d "${DATA_DIR}" ]; then
  log "❌ Error: Expected personal data directory at ${DATA_DIR}"
  exit 1
fi

create_bucket_if_needed() {
  if aws s3api head-bucket --bucket "${BUCKET_NAME}" --region "${AWS_REGION}" >/dev/null 2>&1; then
    log "✅ Bucket already exists"
    return
  fi

  log "🪣 Creating bucket ${BUCKET_NAME}..."
  aws s3api create-bucket \
    --bucket "${BUCKET_NAME}" \
    --region "${AWS_REGION}" \
    --create-bucket-configuration LocationConstraint="${AWS_REGION}"

  aws s3api put-bucket-encryption \
    --bucket "${BUCKET_NAME}" \
    --server-side-encryption-configuration '{
      "Rules": [
        {
          "ApplyServerSideEncryptionByDefault": {
            "SSEAlgorithm": "AES256"
          }
        }
      ]
    }'

  log "✅ Bucket created with encryption enabled"
}

upload_file() {
  local src="$1"
  local key="$2"
  local required="$3"

  if [[ "${src}" == *_template* ]]; then
    log "⏭️  Skipping template file ${src}"
    return
  fi

  if [ -f "${DATA_DIR}/${src}" ]; then
    if [ "$quiet" = true ]; then
      aws s3 cp "${DATA_DIR}/${src}" "${S3_URI}/${PERSONAL_DATA_S3_PREFIX}/${key}" --region "${AWS_REGION}" --only-show-errors --quiet >/dev/null
    else
      aws s3 cp "${DATA_DIR}/${src}" "${S3_URI}/${PERSONAL_DATA_S3_PREFIX}/${key}" --region "${AWS_REGION}"
    fi
    log "✅ Uploaded ${src} to ${PERSONAL_DATA_S3_PREFIX}/${key}"
  elif [ "${required}" = "true" ]; then
    log "❌ Error: required file ${src} not found"
    missing_required=1
  else
    log "ℹ️  Info: optional file ${src} not found"
  fi
}

upload_directory() {
  local dir="$1"
  local key_prefix="$2"

  if [[ "${dir}" == *_template* ]]; then
    log "⏭️  Skipping template directory ${dir}/"
    return
  fi

  if [ -d "${DATA_DIR}/${dir}" ]; then
    local destination_prefix="${S3_URI}/${key_prefix}/"
    if [ -n "${PERSONAL_DATA_S3_PREFIX}" ]; then
      destination_prefix="${S3_URI}/${PERSONAL_DATA_S3_PREFIX}/${key_prefix}/"
    fi
    if [ "$quiet" = true ]; then
      aws s3 sync "${DATA_DIR}/${dir}/" "${destination_prefix}" --delete --region "${AWS_REGION}" --exclude "*_template*" --only-show-errors --no-progress >/dev/null
    else
      aws s3 sync "${DATA_DIR}/${dir}/" "${destination_prefix}" --delete --region "${AWS_REGION}" --exclude "*_template*"
    fi
    log "✅ Synced ${dir}/"
  else
    log "⚠️  Warning: directory ${dir}/ not found"
  fi
}

create_bucket_if_needed

log "📤 Uploading files..."

REQUIRED_FILES=(
  summary.txt
  facts.json
  style.txt
  me.txt
  skills.yml
  education.yml
  experience.yml
  qna.yml
  sources.json
)

OPTIONAL_FILES=(
  linkedin.pdf
  resume.md
)

missing_required=0

for file in "${REQUIRED_FILES[@]}"; do
  upload_file "${file}" "${file}" "true"
done

for file in "${OPTIONAL_FILES[@]}"; do
  upload_file "${file}" "${file}" "false"
done

if [ -d "${PROMPTS_DIR}" ]; then
  log "📚 Syncing prompts directory..."
  if [ "$quiet" = true ]; then
    aws s3 sync "${PROMPTS_DIR}/" "${S3_URI}/${PROMPTS_S3_PREFIX}/" --delete --region "${AWS_REGION}" --only-show-errors --no-progress >/dev/null
  else
    aws s3 sync "${PROMPTS_DIR}/" "${S3_URI}/${PROMPTS_S3_PREFIX}/" --delete --region "${AWS_REGION}"
  fi
  log "✅ Synced prompts/"
else
  log "⚠️  Warning: prompts directory not found at ${PROMPTS_DIR}"
fi

if [[ ${missing_required} -ne 0 ]]; then
  log "❌ Upload failed: missing required files"
  exit 1
fi

log ""
log "🎉 Personal data upload complete!"
log "📋 Files uploaded to: ${S3_URI}"
log ""
log "💡 Next steps:"
log "   1. Update Lambda env var: PERSONAL_DATA_BUCKET=${BUCKET_NAME}"
log "   2. Redeploy for environment: ${ENVIRONMENT}"
log "   3. Lambda will read data from S3 going forward"
log ""
log "🔄 Usage:"
log "   ./scripts/upload-personal-data.sh dev"
log "   ./scripts/upload-personal-data.sh test ${PROJECT_NAME}"
log "   ./scripts/upload-personal-data.sh prod ${PROJECT_NAME}"
