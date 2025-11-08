#!/bin/bash
# Decrypt encrypted data files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TWIN_DIR="$(dirname "$SCRIPT_DIR")"
ENCRYPTED_DIR="$TWIN_DIR/backend/data-encrypted"
DATA_DIR="$TWIN_DIR/backend/data"

# Load .env file first (before checking for DATA_KEY)
# Try multiple .env locations
if [ -f "$TWIN_DIR/backend/.env" ]; then
    source "$TWIN_DIR/backend/.env"
elif [ -f "$TWIN_DIR/.env" ]; then
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

# Check if encrypted files exist
if [ ! -d "$ENCRYPTED_DIR" ] || [ -z "$(ls -A $ENCRYPTED_DIR/*.encrypted 2>/dev/null)" ]; then
    echo "❌ Error: Encrypted files not found in $ENCRYPTED_DIR"
    echo ""
    echo "Download them first:"
    echo "  ./scripts/download-encrypted-data.sh"
    exit 1
fi

# Create data directory
mkdir -p "$DATA_DIR"

echo "🔓 Decrypting data files..."
echo ""

# Decrypt each encrypted file
DECRYPTED_COUNT=0
FAILED_COUNT=0

set +e  # allow loop to continue on individual failures
for encrypted_file in "$ENCRYPTED_DIR"/*.encrypted; do
    if [ -f "$encrypted_file" ]; then
        filename=$(basename "$encrypted_file" .encrypted)
        output_file="$DATA_DIR/$filename"
        
        echo "  Decrypting $filename..."
        
        openssl enc -aes-256-cbc \
            -d \
            -salt \
            -pbkdf2 \
            -in "$encrypted_file" \
            -out "$output_file" \
            -pass "pass:$DATA_KEY"
        status=$?

        if [ $status -eq 0 ]; then
            echo "  ✅ Decrypted to $filename"
            ((DECRYPTED_COUNT++))
        else
            echo "  ❌ Failed to decrypt $filename (exit code $status)"
            ((FAILED_COUNT++))
        fi
    fi
done
set -e

echo ""
if [ $DECRYPTED_COUNT -gt 0 ]; then
    echo "🎉 Decryption complete!"
    echo "   Decrypted $DECRYPTED_COUNT file(s) to $DATA_DIR"
fi

if [ $FAILED_COUNT -gt 0 ]; then
    echo "⚠️  Warning: $FAILED_COUNT file(s) failed to decrypt"
    echo "   Check that DATA_KEY is correct"
    exit 1
fi

echo ""
echo "✅ All files decrypted successfully!"

