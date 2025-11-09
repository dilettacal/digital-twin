#!/bin/bash
# Setup local data files for development
# This script helps users set up their personal data files from templates

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TWIN_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$TWIN_DIR/backend/data/personal_data"
TEMPLATES_DIR="$TWIN_DIR/backend/data/personal_data_templates"
PROMPTS_DIR="$TWIN_DIR/backend/data/prompts"
PROMPTS_TEMPLATES_DIR="$TWIN_DIR/backend/data/prompts_template"

echo "🔧 Setting up local data files for development..."
echo ""

# Ensure personal data directory exists
if [ ! -d "$DATA_DIR" ]; then
    echo "Creating personal data directory..."
    mkdir -p "$DATA_DIR"
fi

# Ensure prompts directory exists
if [ ! -d "$PROMPTS_DIR" ]; then
    echo "Creating prompts directory..."
    mkdir -p "$PROMPTS_DIR"
fi

# Ensure template directories exist
if [ ! -d "$TEMPLATES_DIR" ]; then
    echo "❌ Error: Personal data templates directory not found at $TEMPLATES_DIR"
    echo "   Please make sure the repository includes template files."
    exit 1
fi

if [ ! -d "$PROMPTS_TEMPLATES_DIR" ]; then
    echo "❌ Error: Prompts templates directory not found at $PROMPTS_TEMPLATES_DIR"
    echo "   Please make sure the repository includes prompt template files."
    exit 1
fi

# Check existing personal data files
if [ -f "$DATA_DIR/facts.json" ] && [ -f "$DATA_DIR/summary.txt" ] && [ -f "$DATA_DIR/style.txt" ]; then
    echo "ℹ️  Personal data files already exist in $DATA_DIR"
    echo "   Missing files (if any) will be created from templates."
    echo ""
fi

# List of required template files (now in same directory)
REQUIRED_TEMPLATES=("facts_template.json" "summary_template.txt" "linkedin_template.pdf" "style_template.txt")
OPTIONAL_TEMPLATES=("me_template.txt")
PROMPT_TEMPLATES=("system_prompt.txt" "critical_rules.txt" "proficiency_levels.json")

# Check which files need to be created
FILES_TO_CREATE=()
PROMPTS_TO_CREATE=()

for template in "${REQUIRED_TEMPLATES[@]}"; do
    base_name="${template/_template/}"
    if [ ! -f "$DATA_DIR/$base_name" ]; then
        if [ -f "$TEMPLATES_DIR/$template" ]; then
            FILES_TO_CREATE+=("$template")
        else
            echo "⚠️  Warning: Template $template not found in $TEMPLATES_DIR"
        fi
    fi
done

if [ ${#FILES_TO_CREATE[@]} -eq 0 ]; then
    echo "✅ All required data files already exist in $DATA_DIR"
    echo ""
    echo "Files found:"
    ls -1 "$DATA_DIR"/*.{json,txt,pdf} 2>/dev/null | xargs -n1 basename || echo "  (none)"
fi

for template in "${PROMPT_TEMPLATES[@]}"; do
    if [ ! -f "$PROMPTS_DIR/$template" ]; then
        if [ -f "$PROMPTS_TEMPLATES_DIR/$template" ]; then
            PROMPTS_TO_CREATE+=("$template")
        else
            echo "⚠️  Warning: Prompt template $template not found in $PROMPTS_TEMPLATES_DIR"
        fi
    fi
done

if [ ${#FILES_TO_CREATE[@]} -eq 0 ] && [ ${#PROMPTS_TO_CREATE[@]} -eq 0 ]; then
    echo "✅ All required prompt files already exist in $PROMPTS_DIR"
    exit 0
fi

echo "📋 Will create the following files from templates:"
for template in "${FILES_TO_CREATE[@]}"; do
    base_name="${template/_template/}"
    echo "  - $base_name (from $template)"
done
for template in "${PROMPTS_TO_CREATE[@]}"; do
    echo "  - prompts/$template (from prompts_template/$template)"
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
    if [ -f "$TEMPLATES_DIR/$template" ]; then
        cp "$TEMPLATES_DIR/$template" "$DATA_DIR/$base_name"
        echo "✅ Created $base_name"
    fi
done

# Copy optional me.txt
for template in "${OPTIONAL_TEMPLATES[@]}"; do
    base_name="${template/_template/}"
    if [ -f "$TEMPLATES_DIR/$template" ] && [ ! -f "$DATA_DIR/$base_name" ]; then
        cp "$TEMPLATES_DIR/$template" "$DATA_DIR/$base_name"
        echo "✅ Created $base_name (optional)"
    fi
done

if [ ${#PROMPTS_TO_CREATE[@]} -gt 0 ]; then
    echo ""
    echo "📝 Creating prompt files from templates..."
    for template in "${PROMPTS_TO_CREATE[@]}"; do
        if [ -f "$PROMPTS_TEMPLATES_DIR/$template" ]; then
            cp "$PROMPTS_TEMPLATES_DIR/$template" "$PROMPTS_DIR/$template"
            echo "✅ Created prompts/$template"
        fi
    done
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "📝 Next steps:"
echo "  1. Edit the files in $DATA_DIR with your personal information"
echo "  2. Required files: facts.json, summary.txt, style.txt, linkedin.pdf"
echo "  3. Optional: me.txt"
echo "  4. Customize prompt files in $PROMPTS_DIR as needed"
echo ""
echo "💡 These files are gitignored and won't be committed to the repository."

