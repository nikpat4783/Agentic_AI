#!/bin/bash

# K6 Load Test Quick Start Script
# Runs the complete k6 load testing setup

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   K6 Local Load Test with Grafana Visualization       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"

# Step 1: Verify SIP Calculator App is running
echo -e "${YELLOW}[Step 1/4] Checking if SIP Calculator app is running...${NC}"
if curl -s http://localhost:5000/api/health > /dev/null; then
    echo -e "${GREEN}✓ SIP Calculator app is running on port 5000${NC}\n"
else
    echo -e "${RED}✗ SIP Calculator app is not running on port 5000${NC}"
    echo -e "${YELLOW}Start it in another terminal:${NC}"
    echo -e "${YELLOW}  PORT=5000 npm run dev:observe${NC}\n"
    exit 1
fi

# Step 2: Start infrastructure
echo -e "${YELLOW}[Step 2/4] Starting InfluxDB and Grafana...${NC}"
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana 2>&1 | grep -E "(Creating|Starting|Already)"

echo -e "${YELLOW}⏳ Waiting for services to initialize... (15 seconds)${NC}"
for i in {15..1}; do
    echo -ne "\r  Initializing... ${i}s remaining"
    sleep 1
done
echo -e "\r${GREEN}✓ Services initialized!${NC}\n"

# Step 3: Verify services are healthy
echo -e "${YELLOW}[Step 3/4] Verifying service health...${NC}"
if curl -s http://localhost:4000/api/health > /dev/null; then
    echo -e "${GREEN}✓ Grafana is ready${NC}"
else
    echo -e "${RED}✗ Grafana not responding${NC}"
    exit 1
fi

if curl -s http://localhost:8086/ping > /dev/null; then
    echo -e "${GREEN}✓ InfluxDB is ready${NC}\n"
else
    echo -e "${RED}✗ InfluxDB not responding${NC}"
    exit 1
fi

# Step 4: Run the load test
echo -e "${YELLOW}[Step 4/4] Running K6 load test...${NC}"
echo -e "${YELLOW}Test Details:${NC}"
echo -e "  • Duration: 1 minute"
echo -e "  • Virtual Users: 10 (ramp-up/down)"
echo -e "  • Endpoint: http://localhost:5000/api/sip"
echo -e "  • Metrics: Sent to InfluxDB\n"

sudo docker compose -f docker-compose-k6.yaml run --rm k6 run /scripts/local-load-test.js --out influxdb=http://influxdb:8086/k6

# Step 5: Results
echo -e "\n${GREEN}✓ Load test completed!${NC}\n"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   View Your Results in Grafana                        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════╝${NC}\n"

echo -e "${YELLOW}📊 Grafana Dashboard:${NC}"
echo -e "  • URL: ${GREEN}http://localhost:4000${NC}"
echo -e "  • Username: ${GREEN}admin${NC}"
echo -e "  • Password: ${GREEN}admin${NC}"
echo -e "  • Dashboard: ${GREEN}K6 Load Test - Real-time Metrics${NC}\n"

echo -e "${YELLOW}📈 Metrics Available:${NC}"
echo -e "  ✓ Virtual Users (VUs)"
echo -e "  ✓ Request Rate (req/s)"
echo -e "  ✓ HTTP Request Duration (p50, p95, p99)"
echo -e "  ✓ Error Rate (%)"
echo -e "  ✓ Request Count\n"

echo -e "${YELLOW}💡 Next Steps:${NC}"
echo -e "  1. Open http://localhost:4000 in your browser"
echo -e "  2. Log in with admin/admin"
echo -e "  3. Navigate to Dashboards → K6 Load Test"
echo -e "  4. Analyze the performance metrics\n"

echo -e "${YELLOW}🛑 To Stop Services:${NC}"
echo -e "  sudo docker compose -f docker-compose-k6.yaml down\n"

echo -e "${YELLOW}📚 For More Information:${NC}"
echo -e "  See: K6_LOAD_TEST_GUIDE.md\n"
