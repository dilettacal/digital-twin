#!/bin/bash
# Clean Terraform artifacts and state files

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../terraform"

echo "🧹 Cleaning Terraform artifacts..."

cd "$TERRAFORM_DIR"

# Remove Terraform cache and state files
if [ -d ".terraform" ]; then
    echo "  Removing .terraform directory..."
    rm -rf .terraform
fi

if ls terraform.tfstate* 1> /dev/null 2>&1; then
    echo "  Removing terraform.tfstate files..."
    rm -rf terraform.tfstate.d
    rm -f terraform.tfstate*
fi

if [ -d ".terraform.lock.hcl" ]; then
    echo "  Removing lock file..."
    rm -f .terraform.lock.hcl
fi

echo "✅ Terraform artifacts cleaned!"
