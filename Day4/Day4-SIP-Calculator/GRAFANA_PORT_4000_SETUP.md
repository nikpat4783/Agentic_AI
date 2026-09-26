# 📊 Grafana on Port 4000 - Quick Start

Your Grafana dashboard is now configured to run on **port 4000** with full OpenTelemetry visualization.

## 🚀 Quick Start (One Command)

```bash
bash start-observability.sh 5000
```

Then open: **http://localhost:4000** (admin/admin)

---

## 📍 Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Grafana Dashboard** | http://localhost:4000 | 📊 Main visualization (admin/admin) |
| **SIP Calculator API** | http://localhost:5000 | 🔢 App API |
| **Prometheus** | http://localhost:9090 | 📈 Metrics database |
| **Jaeger** | http://localhost:16686 | 🔍 Trace analysis |
| **Tempo** | http://localhost:3200 | 📋 Trace storage |
| **Health Check** | http://localhost:5000/api/health | ✅ API health |

---

## ✨ What You'll See in Grafana

### Dashboard: SIP Calculator API Overview

**Panels:**
1. **HTTP Request Duration** - Latency metrics (p50, p95, p99)
2. **Request Rate** - Requests per second
3. **Traces (Tempo)** - Individual request traces with span hierarchy
4. **Error Rate** - Error percentage over time
5. **Response Time Distribution** - Histogram of latencies

---

## 🛠️ Setup Steps

### Step 1: Verify Docker is Running
```bash
docker ps
```

### Step 2: Start Observability Stack
```bash
npm run observe:start
# Or: docker-compose up -d
```

### Step 3: Wait for Services
```bash
sleep 20
# Check status
docker ps | grep -E "(grafana|prometheus|otel|tempo|jaeger)"
```

### Step 4: Start the App
```bash
PORT=5000 npm run dev:observe
```

You should see:
```
✓ [OpenTelemetry] SDK initialized
✓ SIP calculator server running on http://localhost:5000
```

### Step 5: Generate Data
```bash
# Make some requests to populate dashboards
for i in {1..5}; do
  curl "http://localhost:5000/api/sip?monthlyInvestment=5000&expectedReturn=12&years=10"
  sleep 1
done
```

### Step 6: View Dashboard
Open **http://localhost:4000** and log in:
- **Username:** admin
- **Password:** admin

---

## 🔄 Real-Time Monitoring

Generate continuous traffic:
```bash
watch -n 1 'curl -s "http://localhost:5000/api/sip?monthlyInvestment=5000&expectedReturn=12&years=10" | jq .futureValue'
```

Then refresh Grafana to watch metrics update in real-time!

---

## 🔍 Trace Analysis in Jaeger

1. Go to **http://localhost:16686**
2. Select Service: **sip-calculator-api**
3. Click **Find Traces**
4. Click any trace to see:
   - Full request timeline
   - Span breakdown
   - Timing for each operation
   - Error details (if any)

---

## 📊 Sample Prometheus Queries

Try these in Prometheus (http://localhost:9090):

```promql
# Request rate (requests/sec)
rate(http_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate percentage
100 * rate(http_requests_total{status=~"[45].."}[5m]) / rate(http_requests_total[5m])

# Request count by endpoint
sum by (path) (rate(http_requests_total[5m]))
```

---

## 🛑 Stopping Everything

```bash
# Stop the app (Ctrl+C in app terminal)

# Stop all services
npm run observe:stop
# Or: docker-compose down
```

---

## ✅ Verify Setup

Run the verification script:
```bash
bash verify-observability.sh
```

---

## 🚨 Troubleshooting

### No data in Grafana?
```bash
# 1. Wait 30 seconds for services to initialize
sleep 30

# 2. Make sure you've generated traffic
curl "http://localhost:5000/api/sip?monthlyInvestment=5000&expectedReturn=12&years=10"

# 3. Refresh Grafana browser (Ctrl+R)

# 4. Check if Prometheus is scraping
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets | length'
```

### Port already in use?
```bash
# Check what's using the port
lsof -i :4000
# Or use a different port
PORT=6000 npm run dev:observe
```

### Docker won't start?
```bash
# Verify Docker is running
docker --version
docker ps

# If not, start Docker Desktop or service
# Then retry:
npm run observe:start
```

---

## 📝 Port Configuration Changed

- **Before:** Grafana on port 3000
- **After:** Grafana on port 4000 ✅
- **App:** Port 5000 (configurable)
- **All other services:** Same as before

---

## 🎯 Next Steps

1. ✅ Start observability stack
2. ✅ View Grafana on port 4000
3. ✅ Generate some traffic
4. ✅ Explore traces in Jaeger
5. 📈 Create custom dashboards in Grafana
6. 🔔 Set up alert rules

---

**Status:** ✅ Ready to visualize OpenTelemetry data!

```bash
bash start-observability.sh 5000
# Then open: http://localhost:4000
```
