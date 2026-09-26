# 🚀 EXECUTE K6 LOAD TEST - Complete Instructions

## Setup Status: ✅ COMPLETE

All K6 load testing infrastructure is configured and ready to execute.

---

## 🎯 Quick Start (3 Commands)

```bash
# Command 1: Ensure app is running (Terminal 1)
PORT=5000 npm run dev:observe

# Command 2: Run automated test (Terminal 2)
cd /home/labuser/Downloads/Day4_Claude_Code
bash start-k6-load-test.sh

# Command 3: View results in browser
# Open: http://localhost:3000 (admin/admin)
```

---

## 📋 What You're Running

### Load Test Script: `local-load-test.js` ✅

**Syntax Validated**: JavaScript ES6 modules with k6 API

**Test Profile**:
```
Duration: 1 minute
Virtual Users: 10 (with ramp-up/down)
Target: http://localhost:5000/api/sip
Metrics Storage: InfluxDB
Visualization: Grafana
```

**Test Stages**:
1. **0-10s**: Ramp-up from 0 → 5 VUs
2. **10-40s**: Sustained load at 10 VUs
3. **40-55s**: Ramp-down from 10 → 5 VUs
4. **55-60s**: Cooldown from 5 → 0 VUs

**Performance Thresholds**:
- ✅ Error rate < 1%
- ✅ p(95) latency < 500ms
- ✅ p(99) latency < 1000ms

**Test Cases**:
- SIP Calculation API (full flow)
- Health Check endpoint (fast)
- Error Handling (invalid parameters)

---

## 🐳 Infrastructure Stack

### Docker Services (All Pre-configured)

| Service | Container | Port | Status |
|---------|-----------|------|--------|
| InfluxDB | `influxdb-k6` | 8086 | ✅ Ready |
| Grafana | `grafana-k6` | 3000 | ✅ Ready |
| K6 Runner | `k6-runner` | - | ✅ Ready |

### Auto-Provisioned Grafana

- ✅ InfluxDB datasource configured
- ✅ K6 dashboard pre-created
- ✅ 5-panel real-time visualization
- ✅ Auto-refresh enabled

---

## 🔧 Manual Execution (If Not Using Quick Start Script)

### Prerequisites

**Terminal 1 - Start Your App**:
```bash
cd /home/labuser/Downloads/Day4_Claude_Code
PORT=5000 npm run dev:observe
```

Wait for output:
```
✓ [OpenTelemetry] SDK initialized
✓ SIP calculator server running on http://localhost:5000
```

---

### Infrastructure Setup

**Terminal 2 - Start Docker Services**:
```bash
cd /home/labuser/Downloads/Day4_Claude_Code

# Start InfluxDB and Grafana
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana

# Wait for services to initialize
sleep 15

# Verify services are running
sudo docker compose -f docker-compose-k6.yaml ps
```

Expected output:
```
NAME           SERVICE   STATUS
influxdb-k6    influxdb  Up 15 seconds
grafana-k6     grafana   Up 15 seconds
```

---

### Run Load Test

**Terminal 3 - Execute K6 Test**:
```bash
cd /home/labuser/Downloads/Day4_Claude_Code

# Run the k6 load test
sudo docker compose -f docker-compose-k6.yaml run --rm k6 \
  run /scripts/local-load-test.js \
  --out influxdb=http://influxdb:8086/k6
```

You'll see k6 output like:
```
execution: local
script: /scripts/local-load-test.js
output: influxdb (http://influxdb:8086/k6)

scenarios: (100.00%) 1 executing, ~0-10 VUs, 1m0s total
...
```

The test will run for **1 minute**. Once complete:
```
checks.........................: 95.47% ✓ 2143   ✗ 101
data_received..................: 892 kB 14 kB/s
data_sent.......................: 156 kB 2.6 kB/s
http_req_blocked...............: avg=2.45ms  min=0s     med=0s     max=456ms p(90)=0s     p(95)=0s     p(99)=4.56ms
http_req_connecting............: avg=0.86ms  min=0s     med=0s     max=10ms  p(90)=0s     p(95)=0s     p(99)=0s
http_req_duration..............: avg=145ms   min=2ms    med=45ms   max=1245ms p(90)=456ms p(95)=587ms p(99)=987ms
http_req_failed................: 0.50%
http_reqs......................: 2244 in 1m0s
iteration_duration.............: avg=12.46s  min=10.25s med=12.58s max=14.33s
iterations......................: 374 in 1m0s
vus............................: 0 min=0 max=10
vus_max.........................: 10
```

---

## 📊 View Results in Grafana

### Access Dashboard

1. **Open Browser**: http://localhost:3000
2. **Login**: 
   - Username: `admin`
   - Password: `admin`
3. **Navigate**: Dashboards → "K6 Load Test - Real-time Metrics"

### Dashboard Panels

**Panel 1: Active Virtual Users (VUs)**
- Gauge showing current concurrent users
- Should show: 5 → 10 → 5 → 0 (ramp pattern)

**Panel 2: Request Rate Over Time**
- Line chart of requests per second
- Peak during sustained load phase (40 requests/sec at 10 VUs)

**Panel 3: HTTP Request Duration**
- Shows p50, p95, p99 latency percentiles
- Green zone: <500ms
- Yellow zone: 500-1000ms
- Red zone: >1000ms

**Panel 4: Error Rate Over Time**
- Percentage of failed requests
- Should stay at 0% (green)

**Panel 5: Current Error Rate**
- Final gauge showing error rate
- Green if < 1%

---

## 🔍 Interpreting the Results

### Healthy Performance
```
✅ VUs: Follows ramp pattern (5 → 10 → 5 → 0)
✅ Request Rate: 5-15 req/s (proportional to VUs)
✅ p50 Latency: 50-150ms
✅ p95 Latency: 150-400ms (< 500ms threshold)
✅ p99 Latency: 200-600ms (< 1000ms threshold)
✅ Error Rate: 0%
✅ All thresholds: PASSED ✓
```

### Performance Issues to Watch For
```
⚠️ p95 Latency > 500ms → API might be slow
⚠️ p99 Latency > 1000ms → Some requests are very slow
⚠️ Error Rate > 1% → Check error logs
⚠️ Request Rate drops → Resource exhaustion or bottleneck
```

---

## 📁 File Structure

```
/Day4_Claude_Code/
│
├── 📄 local-load-test.js                    ← K6 test script
├── 📄 docker-compose-k6.yaml                ← Infrastructure
├── 📄 start-k6-load-test.sh                 ← Automated runner
├── 📄 K6_LOAD_TEST_GUIDE.md                 ← Full docs
├── 📄 K6_SETUP_COMPLETE.md                  ← Setup summary
├── 📄 EXECUTE_K6_TEST.md                    ← THIS FILE
│
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── datasources.yaml              ← InfluxDB config
        └── dashboards/
            └── k6-dashboard.json             ← Grafana dashboard
```

---

## 🛑 Stop Services

### Stop Infrastructure (Keep Data)
```bash
sudo docker compose -f docker-compose-k6.yaml stop
```

### Stop and Remove Containers (Keep Volumes)
```bash
sudo docker compose -f docker-compose-k6.yaml down
```

### Clean Up Everything (Remove Data)
```bash
sudo docker compose -f docker-compose-k6.yaml down -v
```

---

## 🔄 Re-run Tests

### Run Again (Same Setup)
```bash
# Data persists in InfluxDB
sudo docker compose -f docker-compose-k6.yaml run --rm k6 \
  run /scripts/local-load-test.js \
  --out influxdb=http://influxdb:8086/k6
```

### Compare Results
- First run metrics visible in Grafana
- Second run adds new data points
- Both runs appear on same dashboard
- Compare before/after timestamps

### Fresh Start
```bash
# Clean up everything
sudo docker compose -f docker-compose-k6.yaml down -v

# Start fresh
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana
sleep 15

# Run test
sudo docker compose -f docker-compose-k6.yaml run --rm k6 \
  run /scripts/local-load-test.js \
  --out influxdb=http://influxdb:8086/k6
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused" to App
```bash
# Check if app is running
curl http://localhost:5000/api/health

# If not running, start it
PORT=5000 npm run dev:observe
```

### Issue: InfluxDB Connection Error
```bash
# Wait longer for InfluxDB startup
sleep 30

# Verify InfluxDB is healthy
sudo docker compose -f docker-compose-k6.yaml ps influxdb

# Check logs
sudo docker compose -f docker-compose-k6.yaml logs influxdb
```

### Issue: Grafana Shows No Data
```bash
# 1. Wait 30 seconds for data to arrive
sleep 30

# 2. Refresh Grafana (F5 in browser)

# 3. Verify test ran successfully
sudo docker compose -f docker-compose-k6.yaml logs k6

# 4. Check InfluxDB has data
curl -s http://localhost:8086/query?db=k6 \
  --data-urlencode "q=SELECT * FROM http_reqs LIMIT 1" | jq .
```

### Issue: Port Already in Use
```bash
# Find what's using port 3000
lsof -i :3000

# Find what's using port 8086
lsof -i :8086

# Kill the process
kill -9 <PID>

# Or use a different port
PORT=3001 sudo docker run -d grafana/grafana
```

---

## 📈 Performance Optimization Workflow

### 1. Baseline Run
```bash
bash start-k6-load-test.sh
# Capture metrics in Grafana
# Screenshot the results
```

### 2. Analyze Results
```
Look for:
- Highest latency percentiles
- Any errors
- Request rate limitations
- Resource bottlenecks
```

### 3. Optimize Code
```bash
# Make improvements to API/app
# Commit changes
git add .
git commit -m "Optimize API performance"
```

### 4. Run Again
```bash
bash start-k6-load-test.sh
# Compare new metrics
# Verify improvements
```

### 5. Measure Improvement
```
Compare:
- p95 latency: Before → After
- p99 latency: Before → After
- Error rate: Before → After
- Request rate: Before → After
```

---

## 🎯 Next Steps

1. **Run the test now**:
   ```bash
   bash start-k6-load-test.sh
   ```

2. **View results**: http://localhost:3000 (admin/admin)

3. **Analyze performance** in the dashboard

4. **Identify bottlenecks** from the metrics

5. **Optimize your API** based on findings

6. **Re-run test** to measure improvements

---

## 📚 Documentation References

| Document | Purpose |
|----------|---------|
| `K6_LOAD_TEST_GUIDE.md` | Complete guide with all options |
| `K6_SETUP_COMPLETE.md` | Setup summary and validation |
| `EXECUTE_K6_TEST.md` | THIS FILE - Execution instructions |
| `local-load-test.js` | Load test source code |

---

## ✅ Execution Checklist

Before running the test:
- [ ] App is running on port 5000
- [ ] Docker is running
- [ ] No services on port 3000 or 8086
- [ ] You have sudo access
- [ ] `start-k6-load-test.sh` is executable

Before interpreting results:
- [ ] Test completed (watch for 1 minute)
- [ ] Grafana dashboard opens
- [ ] Data appears in graphs (wait 30 sec if not)
- [ ] Refresh browser if needed

---

## 🎉 You're Ready!

**Everything is configured, validated, and ready to execute.**

### Start now with:
```bash
bash start-k6-load-test.sh
```

Then open: **http://localhost:3000**

Happy load testing! 🚀
