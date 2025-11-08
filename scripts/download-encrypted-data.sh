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

echo "📥 Downloading encrypted data files from GitHub Release..."
echo "   Repository: $PRIVATE_REPO_NAME"
echo ""

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
            echo "❌ Error: GITHUB_TOKEN is required in CI environments to download private assets."
            exit 1
        fi

        echo "⚠️  Warning: GITHUB_TOKEN not set"
        echo "   This is required for private repositories."
        echo "   Set it as environment variable or in .env file:"
        echo "   export GITHUB_TOKEN=your-token"
        echo "   or add to .env: GITHUB_TOKEN=your-token"
        echo ""
        echo "   For public repositories, you can continue without a token."
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
    echo "Using GitHub CLI..."
    
    # Authenticate if needed
    if [ -n "$GITHUB_TOKEN" ]; then
        export GH_TOKEN="$GITHUB_TOKEN"
    fi
    
    # Get latest release
    echo "Fetching latest release..."
    LATEST_RELEASE=$(gh release list --repo "$PRIVATE_REPO_NAME" --limit 1 --json tagName -q '.[0].tagName' 2>/dev/null || echo "")
    
    if [ -z "$LATEST_RELEASE" ]; then
        echo "❌ Error: No releases found in repository $PRIVATE_REPO_NAME"
        echo "   Make sure the repository exists and has at least one release."
        exit 1
    fi
    
    echo "   Latest release: $LATEST_RELEASE"
    echo ""
    
    # Download the zip file
    echo "Downloading release asset..."
    gh release download "$LATEST_RELEASE" \
        --repo "$PRIVATE_REPO_NAME" \
        --pattern "data-encrypted-*.zip" \
        --dir "$DOWNLOAD_DIR" \
        --clobber
    
    echo "✅ Download complete!"
    
elif command -v curl &> /dev/null && command -v jq &> /dev/null; then
    echo "Using curl and GitHub API..."
    
    # Build API URL
    API_URL="https://api.github.com/repos/$PRIVATE_REPO_NAME/releases/latest"
    
    # Get latest release info
    echo "Fetching latest release info..."
    if [ -n "$GITHUB_TOKEN" ]; then
        RELEASE_INFO=$(curl -s -H "Authorization: token $GITHUB_TOKEN" "$API_URL")
    else
        RELEASE_INFO=$(curl -s "$API_URL")
    fi
    
    if echo "$RELEASE_INFO" | jq -e '.message' > /dev/null 2>&1; then
        echo "❌ Error: $(echo "$RELEASE_INFO" | jq -r '.message')"
        exit 1
    fi
    
    TAG_NAME=$(echo "$RELEASE_INFO" | jq -r '.tag_name')
    echo "   Latest release: $TAG_NAME"
    echo ""
    
    # Find the zip asset
    ZIP_URL=$(echo "$RELEASE_INFO" | jq -r '.assets[] | select(.name | startswith("data-encrypted")) | .browser_download_url' | head -1)
    
    if [ -z "$ZIP_URL" ] || [ "$ZIP_URL" = "null" ]; then
        echo "❌ Error: No encrypted data zip file found in release"
        exit 1
    fi
    
    # Download the zip file
    echo "Downloading: $(basename $ZIP_URL)"
    if [ -n "$GITHUB_TOKEN" ]; then
        curl -L -H "Authorization: token $GITHUB_TOKEN" "$ZIP_URL" -o "$DOWNLOAD_DIR/data-encrypted.zip"
    else
        curl -L "$ZIP_URL" -o "$DOWNLOAD_DIR/data-encrypted.zip"
    fi
    
    echo "✅ Download complete!"
    
else
    echo "❌ Error: Need either 'gh' CLI or 'curl' + 'jq' installed"
    echo ""
    echo "Install GitHub CLI:"
    echo "  brew install gh  # macOS"
    echo ""
    echo "Or install jq:"
    echo "  brew install jq  # macOS"
    exit 1
fi

# Extract zip file
ZIP_FILE=$(find "$DOWNLOAD_DIR" -name "data-encrypted*.zip" | head -1)
if [ -z "$ZIP_FILE" ]; then
    echo "❌ Error: Zip file not found after download"
    exit 1
fi

echo ""
echo "📦 Extracting encrypted files..."
mkdir -p "$ENCRYPTED_DIR"
unzip -q -o "$ZIP_FILE" -d "$ENCRYPTED_DIR"

# Clean up download directory
rm -rf "$DOWNLOAD_DIR"

echo "✅ Encrypted files extracted to: $ENCRYPTED_DIR"
echo ""
echo "Next: Run decryption script to decrypt the files"

