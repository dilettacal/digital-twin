#!/bin/bash
# Download encrypted data files from GitHub Release

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TWIN_DIR="$(dirname "$SCRIPT_DIR")"
ENCRYPTED_DIR="$TWIN_DIR/backend/data-encrypted"
DOWNLOAD_DIR="$TWIN_DIR/backend/data-encrypted-download"

# Configuration
# Try to load from .env first
if [ -f "$TWIN_DIR/backend/.env" ]; then
    source "$TWIN_DIR/backend/.env"
elif [ -f "$TWIN_DIR/.env" ]; then
    source "$TWIN_DIR/.env"
fi

PRIVATE_REPO_NAME="${PRIVATE_REPO_NAME:-dilettacal/friendly-waffle-data}"
GITHUB_TOKEN="${GITHUB_TOKEN:-${GITHUB_PAT:-}}"

quiet="${DEPLOY_QUIET:-false}"

log() {
    local message="$*"
    if [ "$quiet" = true ]; then
        case "$message" in
            ❌*|⚠️*|Error:*|Usage:*|"  "*)
                ;;
            *)
                return
                ;;
        esac
    fi
    echo "$message"
}

log "📥 Downloading encrypted data files from GitHub Release..."
log "   Repository: $PRIVATE_REPO_NAME"
log ""

# Check for GitHub token (needed for private repos)
if [ -z "$GITHUB_TOKEN" ]; then
    # Try multiple .env locations
    if [ -f "$TWIN_DIR/backend/.env" ]; then
        source "$TWIN_DIR/backend/.env"
        GITHUB_TOKEN="${GITHUB_TOKEN:-${GITHUB_PAT:-}}"
    elif [ -f "$TWIN_DIR/.env" ]; then
        source "$TWIN_DIR/.env"
        GITHUB_TOKEN="${GITHUB_TOKEN:-${GITHUB_PAT:-}}"
    fi
    
    if [ -z "$GITHUB_TOKEN" ]; then
        if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ]; then
        log "❌ Error: GITHUB_TOKEN is required in CI environments to download private assets."
            exit 1
        fi

        log "⚠️  Warning: GITHUB_TOKEN not set"
        log "   This is required for private repositories."
        log "   Set it as environment variable or in .env file:"
        log "   export GITHUB_TOKEN=your-token"
        log "   or add to .env: GITHUB_TOKEN=your-token"
        log ""
        log "   For public repositories, you can continue without a token."
        read -p "Continue anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
fi

# Create download directory
mkdir -p "$DOWNLOAD_DIR"

# Check if GitHub CLI is available
if command -v gh &> /dev/null; then
    log "Using GitHub CLI..."
    
    # Authenticate if needed
    if [ -n "$GITHUB_TOKEN" ]; then
        export GH_TOKEN="$GITHUB_TOKEN"
    fi
    
    # Get latest release
    log "Fetching latest release..."
    LATEST_RELEASE=$(gh release list --repo "$PRIVATE_REPO_NAME" --limit 1 --json tagName -q '.[0].tagName' 2>/dev/null || echo "")
    
    if [ -z "$LATEST_RELEASE" ]; then
        log "❌ Error: No releases found in repository $PRIVATE_REPO_NAME"
        log "   Make sure the repository exists and has at least one release."
        exit 1
    fi
    
    log "   Latest release: $LATEST_RELEASE"
    log ""
    
    # Download the zip file
    log "Downloading release asset..."
    gh release download "$LATEST_RELEASE" \
        --repo "$PRIVATE_REPO_NAME" \
        --pattern "data-encrypted-*.zip" \
        --dir "$DOWNLOAD_DIR" \
        --clobber
    
    log "✅ Download complete!"
    
elif command -v curl &> /dev/null && command -v jq &> /dev/null; then
    log "Using curl and GitHub API..."
    
    # Build API URL
    API_URL="https://api.github.com/repos/$PRIVATE_REPO_NAME/releases/latest"
    
    # Get latest release info
    log "Fetching latest release info..."
    if [ -n "$GITHUB_TOKEN" ]; then
        RELEASE_INFO=$(curl -s -H "Authorization: token $GITHUB_TOKEN" "$API_URL")
    else
        RELEASE_INFO=$(curl -s "$API_URL")
    fi
    
    if echo "$RELEASE_INFO" | jq -e '.message' > /dev/null 2>&1; then
        log "❌ Error: $(echo "$RELEASE_INFO" | jq -r '.message')"
        exit 1
    fi
    
    TAG_NAME=$(echo "$RELEASE_INFO" | jq -r '.tag_name')
    log "   Latest release: $TAG_NAME"
    log ""
    
    # Find the zip asset
    ZIP_URL=$(echo "$RELEASE_INFO" | jq -r '.assets[] | select(.name | startswith("data-encrypted")) | .browser_download_url' | head -1)
    
    if [ -z "$ZIP_URL" ] || [ "$ZIP_URL" = "null" ]; then
    log "❌ Error: No encrypted data zip file found in release"
        exit 1
    fi
    
    # Download the zip file
    log "Downloading: $(basename $ZIP_URL)"
    if [ -n "$GITHUB_TOKEN" ]; then
        curl -L -H "Authorization: token $GITHUB_TOKEN" "$ZIP_URL" -o "$DOWNLOAD_DIR/data-encrypted.zip"
    else
        curl -L "$ZIP_URL" -o "$DOWNLOAD_DIR/data-encrypted.zip"
    fi
    
    log "✅ Download complete!"
    
else
    log "❌ Error: Need either 'gh' CLI or 'curl' + 'jq' installed"
    log ""
    log "Install GitHub CLI:"
    log "  brew install gh  # macOS"
    log ""
    log "Or install jq:"
    log "  brew install jq  # macOS"
    exit 1
fi

# Extract zip file
ZIP_FILE=$(find "$DOWNLOAD_DIR" -name "data-encrypted*.zip" | head -1)
if [ -z "$ZIP_FILE" ]; then
    log "❌ Error: Zip file not found after download"
    exit 1
fi

log ""
log "📦 Extracting encrypted files..."
mkdir -p "$ENCRYPTED_DIR"
unzip -q -o "$ZIP_FILE" -d "$ENCRYPTED_DIR"

# Clean up download directory
rm -rf "$DOWNLOAD_DIR"

log "✅ Encrypted files extracted to: $ENCRYPTED_DIR"
log ""
log "Next: Run decryption script to decrypt the files"

