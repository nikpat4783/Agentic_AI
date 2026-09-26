# 🚀 Deployment Guide: OTel + Grafana on Custom Port

This guide will help you deploy the SIP Calculator API on port 5000 with full OpenTelemetry observability via Grafana dashboards.

## Prerequisites

- Docker & Docker Compose installed
- Node.js 16+ installed
- 8GB+ available RAM
- Ports available: 3000, 5000, 4317, 4318, 8888, 9090, 3200, 16686

## Architecture

```
┌─────────────────────────────────┐
│  SIP Calculator App (Port 5000) │
│  with OpenTelemetry Tracing     │
└──────────────┬──────────────────┘
               │ OTLP HTTP (4318)
               ▼
┌─────────────────────────────────┐
│  OpenTelemetry Collector        │
│  • Port 4317 (gRPC)             │
│  • Port 4318 (HTTP)             │
│  • Port 8888 (Prometheus)       │
└──────────────┬──────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
 ┌─────┐  ┌──────┐  ┌──────┐
 │Prom │  │Tempo │  │Jaeger│
 │9090 │  │3200  │  │16686 │
 └──┬──┘  └──┬───┘  └──────┘
    │        │
    └────┬───┘
         ▼
    ┌──────────────┐
    │   Grafana    │
    │  Port 3000   │
    │  Dashboards  │
    └──────────────┘
```

## Step 1: Start the Observability Stack

```bash
cd /path/to/Day4_Claude_Code

# Start all backend services (Prometheus, Tempo, Grafana, Collector, etc.)
npm run observe:start

# Verify services are running
docker ps | grep -E "(otel-collector|prometheus|grafana|tempo|jaeger)"

# Wait for Grafana to be ready
sleep 30
```

## Step 2: Start the App on Port 5000

```bash
# In a new terminal
export PORT=5000
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318

# Run with file watching for development
npm run dev:observe

# Or run in production mode
npm start

# You should see:
# ✓ [OpenTelemetry] SDK initialized
# ✓ SIP calculator server running on http://localhost:5000
```

## Step 3: Generate Observability Data

```bash
# In another terminal - Generate traces and metrics
bash -c '
for i in {1..20}; do
  curl -s "http://localhost:5000/api/sip?monthlyInvestment=$((RANDOM % 50000 + 1000))&expectedReturn=$((RANDOM % 20))&years=$((RANDOM % 20 + 5))&annualStepUp=$((RANDOM % 10))" > /dev/null
  echo "Request $i sent..."
  sleep 2
done
'
```

## Step 4: Access Grafana Dashboard

**URL:** http://localhost:3000
**Login:** admin / admin

### View the SIP Calculator Dashboard

1. Click on **Dashboards** (left sidebar)
2. Select **SIP Calculator API Overview**
3. You'll see:
   - **HTTP Request Duration** - Request latency over time
   - **Request Rate** - Requests per minute
   - **Trace Visualization** - Individual traces from Tempo
   - **Service Health** - Health indicators

### Expected Dashboard Elements

| Panel | Shows | Source |
|-------|-------|--------|
| **Request Duration (5m rate)** | Latency percentiles (p50, p95, p99) | Prometheus |
| **Request Rate (5m)** | Requests per second | Prometheus |
| **Traces** | Distributed traces with spans | Tempo |
| **Error Rate** | Failed requests percentage | Prometheus |
| **Response Time Distribution** | Histogram of response times | Prometheus |

## Step 5: Explore Detailed Traces

**Jaeger UI:** http://localhost:16686

1. Select Service: **sip-calculator-api**
2. View traces organized by operation
3. Click on any trace to see:
   - Full span hierarchy
   - Timing of each operation
   - Trace duration breakdown
   - Error details (if any)

## Step 6: Query Raw Metrics in Prometheus

**URL:** http://localhost:9090

### Sample Queries

```promql
# Request rate (requests/sec over 5 minutes)
rate(http_requests_total[5m])

# 95th percentile latency (milliseconds)
histogram_quantile(0.95, http_request_duration_seconds_bucket)

# Error rate percentage
100 * (rate(http_requests_total{status=~"[45].."}[5m]) / rate(http_requests_total[5m]))

# Request count by endpoint
sum by (path) (http_requests_total)
```

## Running Multiple Instances (Optional)

To test with multiple instances on different ports:

```bash
# Terminal 1: App on port 5000
PORT=5000 npm run dev:observe

# Terminal 2: App on port 5001
PORT=5001 npm run dev:observe

# Terminal 3: App on port 5002
PORT=5002 npm run dev:observe

# All instances send to the same OpenTelemetry Collector
# Grafana shows aggregated metrics and traces from all instances
```

## Stopping Everything

```bash
# Stop the observability stack
npm run observe:stop

# Stop the app (Ctrl+C in its terminal)

# Verify everything is stopped
docker ps | grep -E "(otel-collector|prometheus|grafana|tempo|jaeger)" || echo "All stopped"
```

## Troubleshooting

### Grafana shows "No data"

```bash
# Wait another 30 seconds and refresh
# Make sure you've generated API traffic

# Check if Prometheus is scraping the app
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets'

# Check if app is exporting metrics
curl http://localhost:5000/metrics 2>/dev/null | head -20
```

### Collector not receiving data

```bash
# Check collector logs
docker-compose logs otel-collector | tail -50

# Verify OTLP endpoint is reachable
curl -v http://localhost:4318/v1/health

# Check app environment variable
echo $OTEL_EXPORTER_OTLP_ENDPOINT
```

### Port already in use

```bash
# Find what's using the port
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or use a different port
PORT=6000 npm run dev:observe
```

## Performance Tuning

### Reduce CPU/Memory Usage

Edit `otel-collector-config.yaml`:

```yaml
processors:
  batch:
    send_batch_size: 256  # Reduce from 1024
    timeout: 10s           # Increase from 5s
  memory_limiter:
    limit_mib: 256        # Reduce from 512
```

### Increase Data Retention

Edit `prometheus.yml`:

```yaml
global:
  scrape_interval: 30s      # Increase interval
  storage.tsdb.retention.time: 90d  # Increase retention
```

## Advanced: Custom Dashboards

### Create a New Dashboard in Grafana

1. Click **+** → **Dashboard**
2. Click **Add Panel**
3. Select **Prometheus** as data source
4. Enter a query:
   ```
   rate(http_requests_total[5m])
   ```
5. Visualize and save

### Example Dashboard Queries

```promql
# Requests by HTTP method
sum by (method) (rate(http_requests_total[5m]))

# P99 latency by endpoint
histogram_quantile(0.99, sum by (path, le) (rate(http_request_duration_seconds_bucket[5m])))

# Memory usage over time
process_resident_memory_bytes

# CPU usage
rate(process_cpu_seconds_total[5m])
```

## Next Steps

1. ✅ Deploy on port 5000
2. ✅ View Grafana dashboard (port 3000)
3. ✅ Explore traces in Jaeger (port 16686)
4. ✅ Query metrics in Prometheus (port 9090)
5. 📈 Create custom dashboards
6. 🔔 Set up alerting rules
7. 📊 Add business metrics

## Command Reference

```bash
# Start everything
npm run observe:start && PORT=5000 npm run dev:observe

# View logs
npm run observe:logs

# Stop everything
npm run observe:stop

# Verify setup
./verify-observability.sh

# Check specific service
docker-compose logs grafana | tail -20
docker-compose logs prometheus | tail -20
docker-compose logs otel-collector | tail -20
```

## URLs Reference

| Service | URL | Purpose |
|---------|-----|---------|
| **App API** | http://localhost:5000 | SIP Calculator API |
| **Grafana** | http://localhost:3000 | Dashboards (admin/admin) |
| **Prometheus** | http://localhost:9090 | Metrics queries |
| **Jaeger** | http://localhost:16686 | Trace visualization |
| **Tempo** | http://localhost:3200 | Trace storage |
| **Collector** | http://localhost:4318 | OTLP endpoint |

---

**Ready to deploy?** Start with Step 1!
