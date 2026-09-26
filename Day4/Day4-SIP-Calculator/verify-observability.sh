#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== OpenTelemetry & Grafana Observability Verification ===${NC}\n"

# Counter for checks
CHECKS_PASSED=0
CHECKS_FAILED=0

# Function to check if a port is responding
check_service() {
  local service=$1
  local port=$2
  local path=${3:-/}

  echo -ne "Checking ${service}... "

  if curl -s "http://localhost:${port}${path}" > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
    ((CHECKS_PASSED++))
    return 0
  else
    echo -e "${RED}✗${NC}"
    ((CHECKS_FAILED++))
    return 1
  fi
}

# Function to check Docker container status
check_container() {
  local container=$1

  echo -ne "Checking container ${container}... "

  if docker ps | grep -q "$container"; then
    echo -e "${GREEN}✓ Running${NC}"
    ((CHECKS_PASSED++))
    return 0
  elif docker ps -a | grep -q "$container"; then
    echo -e "${YELLOW}⚠ Stopped${NC}"
    ((CHECKS_FAILED++))
    return 1
  else
    echo -e "${RED}✗ Not found${NC}"
    ((CHECKS_FAILED++))
    return 2
  fi
}

echo -e "${YELLOW}Step 1: Checking Docker Containers${NC}"
check_container "otel-collector"
check_container "prometheus"
check_container "tempo"
check_container "grafana"
check_container "jaeger"
echo ""

echo -e "${YELLOW}Step 2: Checking Service Endpoints${NC}"
check_service "Grafana" "3000" "/api/health"
check_service "Prometheus" "9090" "/-/healthy"
check_service "Tempo" "3200" "/ready"
check_service "Jaeger" "16686"
check_service "OTel Collector Health" "13133"
echo ""

echo -e "${YELLOW}Step 3: Checking Prometheus Targets${NC}"
echo -ne "Checking Prometheus targets... "
TARGETS=$(curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length')
if [ "$TARGETS" -gt 0 ]; then
  echo -e "${GREEN}✓${NC} ($TARGETS active)"
  ((CHECKS_PASSED++))
else
  echo -e "${RED}✗${NC} (No targets found)"
  ((CHECKS_FAILED++))
fi
echo ""

echo -e "${YELLOW}Step 4: Checking OpenTelemetry Setup${NC}"
echo -ne "Checking otel-setup.js exists... "
if [ -f "./otel-setup.js" ]; then
  echo -e "${GREEN}✓${NC}"
  ((CHECKS_PASSED++))
else
  echo -e "${RED}✗${NC}"
  ((CHECKS_FAILED++))
fi

echo -ne "Checking otel-collector-config.yaml... "
if [ -f "./otel-collector-config.yaml" ]; then
  echo -e "${GREEN}✓${NC}"
  ((CHECKS_PASSED++))
else
  echo -e "${RED}✗${NC}"
  ((CHECKS_FAILED++))
fi
echo ""

echo -e "${YELLOW}Step 5: Checking Grafana Datasources${NC}"
echo -ne "Checking Prometheus datasource... "
DATASOURCE=$(curl -s -H "Authorization: Bearer $(curl -s -X POST http://localhost:3000/api/auth/login -H 'Content-Type: application/json' -d '{"user":"admin","password":"admin"}' 2>/dev/null | jq -r '.token' 2>/dev/null)" http://localhost:3000/api/datasources 2>/dev/null | jq -r '.[] | select(.name=="Prometheus") | .id' 2>/dev/null)
if [ -n "$DATASOURCE" ] && [ "$DATASOURCE" != "null" ]; then
  echo -e "${GREEN}✓${NC} (ID: $DATASOURCE)"
  ((CHECKS_PASSED++))
else
  echo -e "${YELLOW}⚠ Not accessible (may need time to initialize)${NC}"
fi

echo -ne "Checking Tempo datasource... "
TEMPO=$(curl -s http://localhost:3000/api/datasources 2>/dev/null | jq -r '.[] | select(.name=="Tempo") | .id' 2>/dev/null)
if [ -n "$TEMPO" ] && [ "$TEMPO" != "null" ]; then
  echo -e "${GREEN}✓${NC} (ID: $TEMPO)"
  ((CHECKS_PASSED++))
else
  echo -e "${YELLOW}⚠ Not accessible (may need time to initialize)${NC}"
fi
echo ""

echo -e "${YELLOW}Step 6: Application Test${NC}"
echo -ne "Testing SIP Calculator API health endpoint... "
HEALTH=$(curl -s http://localhost:3000/api/health 2>/dev/null | jq -r '.ok' 2>/dev/null)
if [ "$HEALTH" == "true" ]; then
  echo -e "${GREEN}✓${NC}"
  ((CHECKS_PASSED++))
else
  echo -e "${YELLOW}⚠ API may not be running yet${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}=== Verification Summary ===${NC}"
echo -e "Checks passed: ${GREEN}${CHECKS_PASSED}${NC}"
echo -e "Checks failed: ${RED}${CHECKS_FAILED}${NC}\n"

if [ $CHECKS_FAILED -eq 0 ]; then
  echo -e "${GREEN}✓ All checks passed! Observability stack is ready.${NC}\n"
  echo -e "${BLUE}Access Points:${NC}"
  echo -e "  Grafana:     ${GREEN}http://localhost:3000${NC} (admin/admin)"
  echo -e "  Prometheus:  ${GREEN}http://localhost:9090${NC}"
  echo -e "  Tempo:       ${GREEN}http://localhost:3200${NC}"
  echo -e "  Jaeger:      ${GREEN}http://localhost:16686${NC}"
  echo -e "  SIP App:     ${GREEN}http://localhost:3000${NC}"
  exit 0
else
  echo -e "${YELLOW}⚠ Some checks failed. Starting services may be needed.${NC}"
  echo -e "\n${BLUE}To start the observability stack:${NC}"
  echo -e "  ${YELLOW}npm run observe:start${NC}\n"
  echo -e "${BLUE}To run the app with observability:${NC}"
  echo -e "  ${YELLOW}npm run dev:observe${NC}\n"
  exit 1
fi
