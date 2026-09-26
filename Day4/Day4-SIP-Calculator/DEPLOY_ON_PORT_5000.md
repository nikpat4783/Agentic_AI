# 🚀 Deploy SIP Calculator on Port 5000 with OpenTelemetry + Grafana

This guide walks you through deploying the SIP Calculator API with full observability on a custom port.

## Quick Start (< 2 minutes)

```bash
cd /path/to/Day4_Claude_Code

# One-liner to start everything
bash start-observability.sh 5000
```

**That's it!** Your dashboard will be available at:
- **Grafana:** http://localhost:3000 (login: admin/admin)
- **API:** http://localhost:5000/api/health

---

## Step-by-Step Manual Deployment

If you prefer to run commands separately:

### Terminal 1: Start the Observability Stack

```bash
cd /path/to/Day4_Claude_Code

# Start all backend services
npm run observe:start

# Verify services
docker ps | grep -E "(otel|prometheus|grafana|tempo|jaeger)"

# Wait ~20 seconds for full initialization
sleep 20

echo "✓ Backend ready on port 4318 (OTLP)"
```

### Terminal 2: Start the App on Port 5000

```bash
cd /path/to/Day4_Claude_Code

# Set environment
export PORT=5000
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318

# Start with file watching
npm run dev:observe

# You should see:
# ✓ [OpenTelemetry] SDK initialized
# ✓ SIP calculator server running on http://localhost:5000
```

### Terminal 3: Generate Trace Data

```bash
# Make API requests to populate dashboards
for i in {1..10}; do
  curl -s "http://localhost:5000/api/sip?monthlyInvestment=$((RANDOM % 50000 + 1000))&expectedReturn=$((RANDOM % 20))&years=$((RANDOM % 20 + 5))&annualStepUp=$((RANDOM % 10))"
  echo "Request $i sent"
  sleep 2
done

# Or use this for continuous traffic
watch -n 1 'curl -s "http://localhost:5000/api/sip?monthlyInvestment=5000&expectedReturn=12&years=10" | jq .futureValue'
```

---

## Accessing Dashboards

### 1. Grafana (Main Dashboard)

**URL:** http://localhost:3000
**Username:** admin
**Password:** admin

**Steps:**
1. Log in
2. Go to Dashboards (left sidebar)
3. Look for "SIP Calculator API Overview"
4. View real-time metrics

**Panels you'll see:**
- HTTP Request Duration (latency over time)
- Request Rate (requests per second)
- Traces (detailed span information from Tempo)
- Error Rate
- Response Time Distribution

### 2. Jaeger (Trace Analysis)

**URL:** http://localhost:16686

**Steps:**
1. Select Service: "sip-calculator-api"
2. Click "Find Traces"
3. Click on any trace to see:
   - Full request timeline
   - Span breakdown by component
   - Timing of each operation
   - Error details (if any)

### 3. Prometheus (Raw Metrics)

**URL:** http://localhost:9090

**Try these queries:**
```promql
# Request rate
rate(http_requests_total[5m])

# Response latency (95th percentile)
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Error rate
100 * rate(http_requests_total{status=~"[45].."}[5m]) / rate(http_requests_total[5m])
```

### 4. API Health Check

```bash
curl http://localhost:5000/api/health | jq .

# Output:
# {
#   "ok": true,
#   "service": "sip-calculator-api"
# }
```

---

## Port Configuration

### Using Different Port

```bash
# Port 5000 (default)
npm run dev:observe

# Port 6000
PORT=6000 npm run dev:observe

# Port 8080
PORT=8080 npm run dev:observe
```

The collector will automatically send data to Grafana on port 3000, regardless of app port.

### Port Mapping

| Service | Port | Purpose |
|---------|------|---------|
| SIP Calculator API | 5000 | Application |
| Grafana | 3000 | Dashboards |
| Prometheus | 9090 | Metrics DB |
| Jaeger | 16686 | Trace UI |
| Tempo | 3200 | Trace Storage |
| OTel Collector | 4317 | gRPC receiver |
| OTel Collector | 4318 | HTTP receiver |

---

## What Gets Measured

### Automatic Traces
✅ Every HTTP request  
✅ Express middleware execution  
✅ File system operations  
✅ Network I/O  
✅ Function call hierarchy  

### Automatic Metrics
✅ Request count  
✅ Request duration (histogram)  
✅ Request size  
✅ Response size  
✅ Process CPU usage  
✅ Process memory usage  
✅ Event loop lag  

---

## Example Workflows

### Workflow 1: Monitor Real-Time Traffic

```bash
# Terminal 1
npm run observe:start

# Terminal 2
PORT=5000 npm run dev:observe

# Terminal 3
# Open Grafana
open http://localhost:3000

# Terminal 4
# Generate continuous traffic
while true; do
  curl -s "http://localhost:5000/api/sip?monthlyInvestment=5000&expectedReturn=12&years=10" > /dev/null
  echo "Request sent at $(date +%H:%M:%S)"
  sleep 1
done
```

**Result:** Watch the dashboard update in real-time with requests flowing through

### Workflow 2: Analyze Performance

```bash
# Generate traffic with different parameters
for investment in 1000 5000 10000 50000; do
  for return in 8 12 15; do
    curl -s "http://localhost:5000/api/sip?monthlyInvestment=$investment&expectedReturn=$return&years=10" > /dev/null
    sleep 1
  done
done

# Go to Jaeger: http://localhost:16686
# Look for traces
# Analyze which parameter combinations are slowest
```

### Workflow 3: Test Error Handling

```bash
# Generate error requests
curl "http://localhost:5000/api/sip?monthlyInvestment=-1000"
curl "http://localhost:5000/api/sip?monthlyInvestment=abc"
curl "http://localhost:5000/api/sip"

# Check Grafana Error Rate panel
# See error spike in real-time
# Go to Jaeger to see error traces
```

---

## Troubleshooting

### Problem: "No data in Grafana"

**Solution:**
```bash
# 1. Wait 30 seconds
sleep 30

# 2. Refresh Grafana (Ctrl+R)

# 3. Make sure you've generated traffic
curl http://localhost:5000/api/sip?monthlyInvestment=5000&expectedReturn=12&years=10

# 4. Check if Prometheus is scraping
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
# Should show 3 or more targets
```

### Problem: "Collector not receiving data"

**Solution:**
```bash
# 1. Verify OTEL_EXPORTER_OTLP_ENDPOINT
echo $OTEL_EXPORTER_OTLP_ENDPOINT
# Should be: http://localhost:4318

# 2. Check collector logs
npm run observe:logs | grep otel-collector

# 3. Test OTLP endpoint
curl -v http://localhost:4318/v1/health

# 4. Restart the app
# (Stop and run: PORT=5000 npm run dev:observe)
```

### Problem: "Port already in use"

**Solution:**
```bash
# Find what's using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use a different port
PORT=6000 npm run dev:observe
```

### Problem: "Docker won't start"

**Solution:**
```bash
# 1. Verify Docker is running
docker ps

# 2. Remove old containers
npm run observe:stop
docker-compose down -v

# 3. Start fresh
npm run observe:start
```

---

## Performance Tuning

### Reduce CPU Usage

Edit `otel-collector-config.yaml`:
```yaml
processors:
  batch:
    send_batch_size: 256    # Reduce from 1024
    timeout: 10s             # Increase from 5s
```

### Reduce Memory Usage

Edit same file:
```yaml
processors:
  memory_limiter:
    limit_mib: 256          # Reduce from 512
```

### Increase Data Retention

Edit `prometheus.yml`:
```yaml
# Change the docker-compose volume retention
# Or add --storage.tsdb.retention.time=90d to prometheus command
```

---

## Docker Compose Files Generated

These files orchestrate your observability stack:

```
docker-compose.yaml         - Main orchestration
├── otel-collector:4318     - Receives OTLP data
├── prometheus:9090         - Stores metrics
├── tempo:3200              - Stores traces
├── grafana:3000            - Dashboard UI
├── jaeger:16686            - Trace visualization
└── loki:3100               - Log aggregation

Supporting configs:
├── prometheus.yml          - Scrape targets
├── tempo.yaml              - Trace storage
├── grafana-datasources.yml - Data source definitions
└── grafana-dashboards.yml  - Dashboard provisioning
```

---

## Stopping Everything

```bash
# Graceful shutdown
npm run observe:stop

# Or in the app terminal, press Ctrl+C

# Verify everything stopped
docker ps | grep -E "(otel|prometheus|grafana)" || echo "All stopped"

# Remove containers and volumes
docker-compose down -v
```

---

## Advanced: Multi-Instance Setup

To monitor multiple instances of the app:

```bash
# Terminal 1: Backend
npm run observe:start

# Terminal 2: App instance 1
PORT=5000 npm run dev:observe

# Terminal 3: App instance 2
PORT=5001 npm run dev:observe

# Terminal 4: App instance 3
PORT=5002 npm run dev:observe

# All send to same collector
# Grafana shows aggregated metrics
```

Then update Prometheus config to scrape all:
```yaml
static_configs:
  - targets: ['host.docker.internal:5000', 'host.docker.internal:5001', 'host.docker.internal:5002']
```

---

## Next Steps

1. ✅ Deploy on port 5000
2. ✅ View Grafana dashboards
3. ✅ Explore traces in Jaeger
4. ✅ Query metrics in Prometheus
5. 📈 Create custom dashboards
6. 🔔 Set up alert rules
7. 📊 Add business metrics

---

## Complete Command Reference

```bash
# Start everything on port 5000
bash start-observability.sh 5000

# Or manually:
npm run observe:start           # Backend
PORT=5000 npm run dev:observe   # App
npm run observe:logs            # Monitor logs
npm run observe:stop            # Stop all

# Verify setup
./verify-observability.sh

# Access points
# Grafana:     http://localhost:3000 (admin/admin)
# Jaeger:      http://localhost:16686
# Prometheus:  http://localhost:9090
# App API:     http://localhost:5000
```

---

## Support Documents

- **DEPLOY_GUIDE.md** - Detailed deployment guide
- **GRAFANA_DASHBOARD_GUIDE.md** - Dashboard visualization examples
- **OBSERVABILITY-QUICKSTART.md** - 30-second quick start
- **OBSERVABILITY.md** - Full reference documentation
- **verify-observability.sh** - Automated verification

---

## URLs at a Glance

| Service | URL |
|---------|-----|
| **SIP Calculator API** | http://localhost:5000 |
| **Grafana Dashboard** | http://localhost:3000 |
| **Prometheus Metrics** | http://localhost:9090 |
| **Jaeger Traces** | http://localhost:16686 |
| **Tempo Trace Store** | http://localhost:3200 |
| **API Health** | http://localhost:5000/api/health |

---

**Ready to deploy?**

```bash
bash start-observability.sh 5000
```

Then open: **http://localhost:3000** (admin/admin)

🎉 That's it! You now have production-grade observability!
