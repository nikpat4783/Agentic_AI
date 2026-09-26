#!/usr/bin/env bash
# Runs the extraction scenario. Safe/free by default (no LLM_API_KEY set --
# LLM-backed fields resolve to "llm_unavailable" rather than calling out).
# Pass LLM_API_KEY to exercise the real LLM extraction path (may incur cost
# depending on the provider behind that key).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K6_BIN="$SCRIPT_DIR/bin/k6"

if [ ! -x "$K6_BIN" ]; then
  echo "k6 not installed -- run ./install-k6.sh first." >&2
  exit 1
fi

TESTID="extraction-$(date +%s)"
K6_PROMETHEUS_RW_SERVER_URL="http://localhost:9091/api/v1/write" \
K6_PROMETHEUS_RW_TREND_STATS="p(95),p(99),avg" \
VUS="${VUS:-1}" ITERATIONS="${ITERATIONS:-3}" \
"$K6_BIN" run --out experimental-prometheus-rw --tag "testid=$TESTID" \
  "$SCRIPT_DIR/scripts/extraction.js" "$@"

echo "Done. View at http://localhost:3010/d/k6-load-test (testid=$TESTID)"
