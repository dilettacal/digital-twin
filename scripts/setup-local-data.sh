#!/bin/bash
# Setup local data files for development
# This script helps users set up their personal data files from templates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TWIN_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$TWIN_DIR/backend/data"

echo "🔧 Setting up local data files for development..."
echo ""

# Check if data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "Creating data directory..."
    mkdir -p "$DATA_DIR"
fi

# Check if data files already exist
if [ -f "$DATA_DIR/facts.json" ] && [ -f "$DATA_DIR/summary.txt" ] && [ -f "$DATA_DIR/style.txt" ]; then
    echo "✅ Data files already exist in $DATA_DIR"
    echo ""
    echo "Files found:"
    ls -1 "$DATA_DIR"/*.{json,txt,pdf} 2>/dev/null | xargs -n1 basename || echo "  (none)"
    echo ""
    echo "If you want to recreate them from templates, delete the existing files first."
    exit 0
fi

# List of required template files (now in same directory)
REQUIRED_TEMPLATES=("facts_template.json" "summary_template.txt" "linkedin_template.pdf" "style_template.txt")
OPTIONAL_TEMPLATES=("me_template.txt")

# Check which files need to be created
FILES_TO_CREATE=()

for template in "${REQUIRED_TEMPLATES[@]}"; do
    base_name="${template/_template/}"
    if [ ! -f "$DATA_DIR/$base_name" ]; then
        if [ -f "$DATA_DIR/$template" ]; then
            FILES_TO_CREATE+=("$template")
        else
            echo "⚠️  Warning: Template $template not found in $DATA_DIR"
        fi
    fi
done

if [ ${#FILES_TO_CREATE[@]} -eq 0 ]; then
    echo "✅ All required data files already exist in $DATA_DIR"
    echo ""
    echo "Files found:"
    ls -1 "$DATA_DIR"/*.{json,txt,pdf} 2>/dev/null | xargs -n1 basename || echo "  (none)"
    exit 0
fi

echo "📋 Will create the following files from templates:"
for template in "${FILES_TO_CREATE[@]}"; do
    base_name="${template/_template/}"
    echo "  - $base_name (from $template)"
done
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "📝 Creating data files from templates..."

# Copy template files to create data files
for template in "${FILES_TO_CREATE[@]}"; do
    base_name="${template/_template/}"
    if [ -f "$DATA_DIR/$template" ]; then
        cp "$DATA_DIR/$template" "$DATA_DIR/$base_name"
        echo "✅ Created $base_name"
    fi
done

# Copy optional me.txt
for template in "${OPTIONAL_TEMPLATES[@]}"; do
    base_name="${template/_template/}"
    if [ -f "$DATA_DIR/$template" ] && [ ! -f "$DATA_DIR/$base_name" ]; then
        cp "$DATA_DIR/$template" "$DATA_DIR/$base_name"
        echo "✅ Created $base_name (optional)"
    fi
done

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Edit the files in $DATA_DIR with your personal information"
echo "  2. Required files: facts.json, summary.txt, style.txt, linkedin.pdf"
echo "  3. Optional: me.txt"
echo ""
echo "💡 These files are gitignored and won't be committed to the repository."

