#!/usr/bin/env bash
# Migravio AI Chat — Promptfoo Test Runner
#
# Prerequisites:
#   npm install -g promptfoo   (or uses npx automatically)
#   export OPENROUTER_API_KEY=sk-or-...
#
# Usage:
#   ./tests/promptfoo/run-tests.sh           # Run all tests
#   ./tests/promptfoo/run-tests.sh eval      # Run only manual tests (25)
#   ./tests/promptfoo/run-tests.sh redteam   # Run only red-team tests (~12)
#   ./tests/promptfoo/run-tests.sh view      # Open results viewer

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Check for OPENROUTER_API_KEY
if [ -z "${OPENROUTER_API_KEY:-}" ]; then
  ENV_FILE="$PROJECT_ROOT/apps/ai-service/.env"
  if [ -f "$ENV_FILE" ]; then
    echo "[info] Loading OPENROUTER_API_KEY from $ENV_FILE"
    export OPENROUTER_API_KEY=$(grep OPENROUTER_API_KEY "$ENV_FILE" | cut -d'=' -f2)
  else
    echo "[error] OPENROUTER_API_KEY not set and no .env file found"
    echo "        Set it with: export OPENROUTER_API_KEY=sk-or-..."
    exit 1
  fi
fi

MODE="${1:-all}"

echo "============================================"
echo "  Migravio AI Chat — Promptfoo Test Suite"
echo "============================================"
echo ""

case "$MODE" in
  eval)
    echo "[1/1] Running manual tests (business logic + quality)..."
    npx promptfoo@latest eval \
      -c "$SCRIPT_DIR/promptfooconfig.yaml" \
      --no-cache
    echo ""
    echo "Done. Run '$0 view' to see results."
    ;;

  redteam)
    echo "[NOTE] Red-team tests require email verification with promptfoo."
    echo "       Run 'npx promptfoo@latest redteam generate' interactively first."
    echo ""
    echo "[1/2] Generating red-team adversarial tests..."
    npx promptfoo@latest redteam generate \
      -c "$SCRIPT_DIR/promptfooconfig.redteam.yaml"
    echo ""
    echo "[2/2] Running red-team evaluation..."
    npx promptfoo@latest redteam eval \
      -c "$SCRIPT_DIR/promptfooconfig.redteam.yaml"
    echo ""
    echo "Done. Run '$0 view' to see results."
    ;;

  all)
    echo "[1/3] Running manual tests (business logic + quality)..."
    npx promptfoo@latest eval \
      -c "$SCRIPT_DIR/promptfooconfig.yaml" \
      --no-cache
    echo ""
    echo "[2/3] Generating red-team adversarial tests..."
    npx promptfoo@latest redteam generate \
      -c "$SCRIPT_DIR/promptfooconfig.redteam.yaml"
    echo ""
    echo "[3/3] Running red-team evaluation..."
    npx promptfoo@latest redteam eval \
      -c "$SCRIPT_DIR/promptfooconfig.redteam.yaml"
    echo ""
    echo "Done. Run '$0 view' to see results."
    ;;

  view)
    npx promptfoo@latest view
    ;;

  *)
    echo "Usage: $0 [eval|redteam|all|view]"
    exit 1
    ;;
esac
