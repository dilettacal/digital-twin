#!/bin/bash
# Initial setup script for new machines
# This script sets up local data files (from encrypted files or templates)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TWIN_DIR="$(dirname "$SCRIPT_DIR")"
ENCRYPTED_DIR="$TWIN_DIR/backend/data-encrypted"
DATA_DIR="$TWIN_DIR/backend/data"

echo "🚀 Setting up Digital Twin project..."
echo ""

# Check if we're in a git repository
if [ ! -d "$TWIN_DIR/.git" ]; then
    echo "❌ Error: Not a git repository. Please clone the repository first."
    exit 1
fi

# Check if data files already exist
if [ -f "$DATA_DIR/facts.json" ] && [ -f "$DATA_DIR/summary.txt" ] && [ -f "$DATA_DIR/style.txt" ]; then
    echo "✅ Data files already exist in $DATA_DIR"
    echo ""
    echo "Files found:"
    ls -1 "$DATA_DIR"/*.{json,txt,pdf} 2>/dev/null | xargs -n1 basename || echo "  (none)"
    echo ""
    echo "Setup complete!"
    exit 0
fi

# Try to download and decrypt encrypted files (if using GitHub Releases)
if [ -f "$TWIN_DIR/scripts/download-encrypted-data.sh" ]; then
    echo "📥 Checking for encrypted data files from GitHub Release..."
    
    # Check if we have the required configuration
    # Try to load .env from multiple locations
    if [ -f "$TWIN_DIR/backend/.env" ]; then
        source "$TWIN_DIR/backend/.env"
    elif [ -f "$TWIN_DIR/.env" ]; then
        source "$TWIN_DIR/.env"
    fi
    
    if [ -n "$PRIVATE_REPO_NAME" ] || [ -n "$DATA_KEY" ]; then
        
        # Try to download encrypted files
        if "$TWIN_DIR/scripts/download-encrypted-data.sh" 2>/dev/null; then
            echo ""
            echo "🔓 Decrypting downloaded files..."
            
            # Try to decrypt
            if [ -f "$TWIN_DIR/scripts/decrypt-data.sh" ]; then
                if "$TWIN_DIR/scripts/decrypt-data.sh" 2>/dev/null; then
                    echo ""
                    echo "✅ Setup complete! Data files decrypted from encrypted release."
                    exit 0
                else
                    echo "⚠️  Could not decrypt files (missing or incorrect DATA_KEY)"
                    echo "   Falling back to template files..."
                fi
            fi
        else
            echo "ℹ️  No encrypted files available (or download failed)"
            echo "   Falling back to template files..."
        fi
    fi
fi

# Fall back to templates if encrypted files not available
echo ""
echo "📝 Setting up local data files from templates..."
if [ -f "$TWIN_DIR/scripts/setup-local-data.sh" ]; then
    "$TWIN_DIR/scripts/setup-local-data.sh"
else
    echo "⚠️  Warning: setup-local-data.sh not found"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Review and edit personal data files in backend/data/"
echo "  2. Install backend dependencies: cd backend && uv sync"
echo "  3. Install frontend dependencies: cd frontend && npm install"
echo "  4. Start development: See README.md for instructions"

