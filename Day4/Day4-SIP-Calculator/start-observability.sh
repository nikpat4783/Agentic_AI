#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  OpenTelemetry + Grafana Observability Stack Launcher   ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}\n"

APP_PORT=${1:-5000}

echo -e "${YELLOW}Configuration:${NC}"
echo -e "  • App Port: ${GREEN}${APP_PORT}${NC}"
echo -e "  • Grafana: ${GREEN}http://localhost:3000${NC} (admin/admin)"
echo -e "  • Prometheus: ${GREEN}http://localhost:9090${NC}"
echo -e "  • Jaeger: ${GREEN}http://localhost:16686${NC}"
echo -e "  • Tempo: ${GREEN}http://localhost:3200${NC}\n"

# Step 1: Start Docker Compose
echo -e "${YELLOW}[Step 1/3] Starting observability backend...${NC}"
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ docker-compose not found${NC}"
    echo -e "${YELLOW}Install Docker Desktop or docker-compose CLI${NC}"
    exit 1
fi

docker-compose up -d 2>/dev/null

if [ $? -ne 0 ]; then
    echo -e "${RED}✗ Failed to start Docker Compose${NC}"
    echo -e "${YELLOW}Make sure Docker is running${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Backend services starting...${NC}"
echo -e "${YELLOW}⏳ Waiting 20 seconds for services to initialize...${NC}\n"

for i in {20..1}; do
    echo -ne "\r  Initializing... ${i}s remaining"
    sleep 1
done

echo -e "\r${GREEN}✓ Services initialized!${NC}\n"

# Step 2: Display service status
echo -e "${YELLOW}[Step 2/3] Service Status:${NC}"
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "(otel-collector|prometheus|grafana|tempo|jaeger)" | while read -r line; do
    name=$(echo "$line" | awk '{print $1}')
    status=$(echo "$line" | awk '{print $2, $3}')
    if echo "$status" | grep -q "Up"; then
        echo -e "  ${GREEN}✓${NC} $name (${status})"
    else
        echo -e "  ${RED}✗${NC} $name (${status})"
    fi
done

echo -e "\n${GREEN}✓ Backend ready!${NC}\n"

# Step 3: Start the app
echo -e "${YELLOW}[Step 3/3] Starting SIP Calculator on port ${APP_PORT}...${NC}\n"

export PORT=$APP_PORT
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export NODE_ENV=development

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo -e "${RED}✗ npm not found${NC}"
    echo -e "${YELLOW}Install Node.js 16+${NC}"
    exit 1
fi

# Run the app
npm run dev:observe

# Cleanup on exit
trap 'echo -e "\n${YELLOW}Shutting down...${NC}"; npm run observe:stop' EXIT
