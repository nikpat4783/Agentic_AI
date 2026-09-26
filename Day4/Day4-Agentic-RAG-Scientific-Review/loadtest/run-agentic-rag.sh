#!/usr/bin/env bash
# Runs the OPT-IN, COST-INCURRING agentic-rag scenario. Requires
# GROQ_API_KEY to be set in the environment -- this script does not
# prompt for it and never echoes it.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -z "${GROQ_API_KEY:-}" ]; then
  echo "Set GROQ_API_KEY before running this script. This scenario" >&2
  echo "makes real, billed Groq calls." >&2
  exit 1
fi

export K6_PROMETHEUS_RW_SERVER_URL="${K6_PROMETHEUS_RW_SERVER_URL:-http://localhost:9090/api/v1/write}"
export K6_PROMETHEUS_RW_TREND_STATS="${K6_PROMETHEUS_RW_TREND_STATS:-p(95),p(99),avg}"

TESTID="agentic-rag-$(date +%s)"
echo "Running agentic_rag.js as testid=$TESTID (VUS=${VUS:-1} ITERATIONS=${ITERATIONS:-3})"
echo "Watch it live at http://localhost:3000/d/k6-load-test"

"$SCRIPT_DIR/bin/k6" run \
  --out experimental-prometheus-rw \
  --tag "testid=$TESTID" \
  "$SCRIPT_DIR/scripts/agentic_rag.js" "$@"
