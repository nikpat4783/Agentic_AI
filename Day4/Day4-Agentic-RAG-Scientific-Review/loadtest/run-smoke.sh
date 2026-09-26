#!/usr/bin/env bash
# Runs the safe smoke-test scenario and pushes metrics into the Prometheus
# container from observability/docker-compose.yml, tagged so this run is
# distinguishable in Grafana from other runs.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export K6_PROMETHEUS_RW_SERVER_URL="${K6_PROMETHEUS_RW_SERVER_URL:-http://localhost:9090/api/v1/write}"
export K6_PROMETHEUS_RW_TREND_STATS="${K6_PROMETHEUS_RW_TREND_STATS:-p(95),p(99),avg}"

TESTID="smoke-$(date +%s)"
echo "Running smoke.js as testid=$TESTID -- watch it live at http://localhost:3000/d/k6-load-test"

"$SCRIPT_DIR/bin/k6" run \
  --out experimental-prometheus-rw \
  --tag "testid=$TESTID" \
  "$SCRIPT_DIR/scripts/smoke.js" "$@"
