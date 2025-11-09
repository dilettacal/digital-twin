#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$(cd "$SCRIPT_DIR/../frontend" && pwd)"
ESLINT_BIN="$FRONTEND_DIR/node_modules/.bin/eslint"

if [ ! -x "$ESLINT_BIN" ]; then
    echo "❌ Error: eslint not found in frontend/node_modules."
    echo "   Run 'npm ci' (or 'npm install') inside the frontend directory first."
    exit 1
fi

args=()
for path in "$@"; do
    if [[ "$path" == frontend/* ]]; then
        args+=("${path#frontend/}")
    else
        args+=("$path")
    fi
done

cd "$FRONTEND_DIR"

exec "$ESLINT_BIN" \
    --config eslint.config.mjs \
    --max-warnings=0 \
    "${args[@]}"
