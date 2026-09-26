#!/usr/bin/env bash
# Runs the safe smoke scenario and pushes metrics into this project's own
# Prometheus (observability/docker-compose.yml must already be up).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
K6_BIN="$SCRIPT_DIR/bin/k6"

if [ ! -x "$K6_BIN" ]; then
  echo "k6 not installed -- run ./install-k6.sh first." >&2
  exit 1
fi

TESTID="smoke-$(date +%s)"
K6_PROMETHEUS_RW_SERVER_URL="http://localhost:9091/api/v1/write" \
K6_PROMETHEUS_RW_TREND_STATS="p(95),p(99),avg" \
"$K6_BIN" run --out experimental-prometheus-rw --tag "testid=$TESTID" \
  "$SCRIPT_DIR/scripts/smoke.js" "$@"

echo "Done. View at http://localhost:3010/d/k6-load-test (testid=$TESTID)"
