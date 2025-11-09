#!/bin/bash
# Decrypt encrypted data files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TWIN_DIR="$(dirname "$SCRIPT_DIR")"
ENCRYPTED_DIR="$TWIN_DIR/backend/data-encrypted"
ENCRYPTED_PERSONAL_DATA_DIR="$ENCRYPTED_DIR/personal_data"
ENCRYPTED_PROMPTS_DIR="$ENCRYPTED_DIR/prompts"

DATA_DIR="$TWIN_DIR/backend/data/personal_data"
PROMPTS_DIR="$TWIN_DIR/backend/data/prompts"

# Load .env file first (before checking for DATA_KEY)
# Try multiple .env locations
if [ -f "$TWIN_DIR/backend/.env" ]; then
    # shellcheck source=../backend/.env
    # shellcheck disable=SC1091
    source "$TWIN_DIR/backend/.env"
elif [ -f "$TWIN_DIR/.env" ]; then
    # shellcheck source=../.env
    # shellcheck disable=SC1091
    source "$TWIN_DIR/.env"
fi

# Check for encryption key
if [ -z "$DATA_KEY" ]; then
    echo "❌ Error: DATA_KEY not set"
    echo ""
    echo "Set it as environment variable:"
    echo "  export DATA_KEY='your-key'"
    echo ""
    echo "Or create .env file in backend/ or project root:"
    echo "  DATA_KEY=your-key"
    echo ""
    echo "Checked locations:"
    echo "  - $TWIN_DIR/backend/.env"
    echo "  - $TWIN_DIR/.env"
    echo ""
    echo "Get the key from:"
    echo "  - Repository owner"
    echo "  - GitHub Secrets (for CI/CD)"
    exit 1
fi

# Ensure target directories exist
mkdir -p "$DATA_DIR"
mkdir -p "$PROMPTS_DIR"
touch "$DATA_DIR/__init__.py" "$PROMPTS_DIR/__init__.py"

# Clean target directories (preserve __init__.py)
quiet="${DEPLOY_QUIET:-false}"

log() {
    if [ "$quiet" = false ]; then
        echo "$@"
    fi
}

log "🧹 Cleaning existing personal data files..."
find "$DATA_DIR" -mindepth 1 ! -name '__init__.py' -exec rm -rf {} +

log "🧹 Cleaning existing prompt files..."
find "$PROMPTS_DIR" -mindepth 1 ! -name '__init__.py' -exec rm -rf {} +

# Check if encrypted personal data files exist
if [ ! -d "$ENCRYPTED_PERSONAL_DATA_DIR" ] || [ -z "$(find "$ENCRYPTED_PERSONAL_DATA_DIR" -type f -name '*.encrypted' 2>/dev/null)" ]; then
    echo "❌ Error: Encrypted personal data files not found in $ENCRYPTED_PERSONAL_DATA_DIR"
    echo ""
    echo "Download them first:"
    echo "  ./scripts/download-encrypted-data.sh"
    exit 1
fi

log "🔓 Decrypting personal data files..."
log ""

DECRYPTED_COUNT=0
FAILED_COUNT=0
UPDATED_PROMPTS=false

set +e  # allow loop to continue on individual failures
while IFS= read -r -d '' encrypted_file; do
    relative_path="${encrypted_file#"$ENCRYPTED_PERSONAL_DATA_DIR"/}"
    relative_path="${relative_path%.encrypted}"
    output_file="$DATA_DIR/$relative_path"

    log "  Decrypting $relative_path..."

    mkdir -p "$(dirname "$output_file")"

        openssl enc -aes-256-cbc \
            -d \
            -salt \
            -pbkdf2 \
            -in "$encrypted_file" \
            -out "$output_file" \
            -pass "pass:$DATA_KEY"
        status=$?

        if [ $status -eq 0 ]; then
            log "  ✅ Decrypted to $relative_path"
            ((DECRYPTED_COUNT++))
        else
            echo "  ❌ Failed to decrypt $relative_path (exit code $status)"
            ((FAILED_COUNT++))
        fi
done < <(find "$ENCRYPTED_PERSONAL_DATA_DIR" -type f -name '*.encrypted' -print0)
set -e

if [ -d "$ENCRYPTED_PROMPTS_DIR" ]; then
    log ""
    log "📚 Decrypting prompt files..."
    if [ -n "$(find "$ENCRYPTED_PROMPTS_DIR" -type f -name '*.encrypted' 2>/dev/null)" ]; then
        while IFS= read -r -d '' encrypted_prompt; do
            relative_path="${encrypted_prompt#"$ENCRYPTED_PROMPTS_DIR"/}"
            relative_path="${relative_path%.encrypted}"
            output_file="$PROMPTS_DIR/$relative_path"

            log "  Decrypting prompt $relative_path..."

            mkdir -p "$(dirname "$output_file")"

            openssl enc -aes-256-cbc \
                -d \
                -salt \
                -pbkdf2 \
                -in "$encrypted_prompt" \
                -out "$output_file" \
                -pass "pass:$DATA_KEY"
            status=$?

            if [ $status -eq 0 ]; then
                log "  ✅ Decrypted prompt to $relative_path"
                UPDATED_PROMPTS=true
            else
                echo "  ❌ Failed to decrypt prompt $relative_path (exit code $status)"
                ((FAILED_COUNT++))
            fi
        done < <(find "$ENCRYPTED_PROMPTS_DIR" -type f -name '*.encrypted' -print0)
    else
        log "  ⚠️  Warning: No encrypted prompt files found in $ENCRYPTED_PROMPTS_DIR"
    fi
else
    log ""
    log "ℹ️  No prompts directory found in $ENCRYPTED_DIR (skipping prompt decrypt)"
fi

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "$timestamp" > "$DATA_DIR/last_updated.txt"
echo "$timestamp" > "$TWIN_DIR/backend/data/last_updated.txt"
if [ "$UPDATED_PROMPTS" = true ]; then
    echo "$timestamp" > "$PROMPTS_DIR/last_updated.txt"
fi

if [ "$quiet" = false ]; then
    echo ""
    if [ $DECRYPTED_COUNT -gt 0 ]; then
        echo "🎉 Decryption complete!"
        echo "   Decrypted $DECRYPTED_COUNT file(s) to $DATA_DIR"
    fi
fi

if [ $FAILED_COUNT -gt 0 ]; then
    echo "⚠️  Warning: $FAILED_COUNT file(s) failed to decrypt"
    echo "   Check that DATA_KEY is correct"
    exit 1
fi

if [ "$quiet" = false ]; then
    echo ""
    echo "✅ All files decrypted successfully!"
fi
