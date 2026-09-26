# ✅ K6 Load Testing Setup Complete

Your local k6 load testing environment with Grafana visualization is ready to use!

---

## What's Been Set Up

### ✅ Step 1: K6 Environment
- **k6 Script**: `local-load-test.js` - Production-ready load test script
- **Test Duration**: 1 minute with realistic VU ramp-up/down
- **Virtual Users**: 10 VUs with gradual scaling
- **Performance Thresholds**:
  - HTTP error rate < 1% ✓
  - p(95) latency < 500ms ✓
  - p(99) latency < 1000ms ✓

### ✅ Step 2: Docker Stack
- **InfluxDB 1.8**: Time-series metrics database
- **Grafana**: Pre-configured dashboard on port 3000
- **Auto-provisioning**: Datasources and dashboards configured

### ✅ Step 3: Visualization Dashboard
- **Dashboard**: K6 Load Test - Real-time Metrics
- **Panels**: VUs, request rate, latency percentiles, error rate
- **Auto-refresh**: Updates every 5 seconds during test

### ✅ Step 4: Quick Start Scripts
- `start-k6-load-test.sh` - Automated test execution
- `K6_LOAD_TEST_GUIDE.md` - Complete documentation

---

## Files Created

```
/Day4_Claude_Code/
├── local-load-test.js                    ✓ Load test script (validated)
├── docker-compose-k6.yaml                ✓ Infrastructure setup
├── start-k6-load-test.sh                 ✓ Quick start script
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yaml          ✓ Auto-config InfluxDB
│       └── dashboards/
│           └── k6-dashboard.json         ✓ Grafana dashboard
├── K6_LOAD_TEST_GUIDE.md                 ✓ Full documentation
└── K6_SETUP_COMPLETE.md                  ✓ This file
```

---

## Quick Start (60 Seconds)

### Prerequisites
Ensure your SIP Calculator app is running:
```bash
# Terminal 1 - Keep Running
PORT=5000 npm run dev:observe
```

### Run the Test
```bash
# Terminal 2 - Execute this
cd /home/labuser/Downloads/Day4_Claude_Code
bash start-k6-load-test.sh
```

This script will:
1. ✓ Verify app is running
2. ✓ Start InfluxDB and Grafana
3. ✓ Run the k6 load test
4. ✓ Print the dashboard URL

---

## Manual Execution (If Not Using Script)

### Terminal 1: Ensure App is Running
```bash
cd /home/labuser/Downloads/Day4_Claude_Code
PORT=5000 npm run dev:observe
```

### Terminal 2: Start Infrastructure
```bash
cd /home/labuser/Downloads/Day4_Claude_Code
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana
sleep 15  # Wait for services
```

### Terminal 3: Run Load Test
```bash
cd /home/labuser/Downloads/Day4_Claude_Code
sudo docker compose -f docker-compose-k6.yaml run --rm k6 \
  run /scripts/local-load-test.js \
  --out influxdb=http://influxdb:8086/k6
```

### Browser: View Results
Open in browser:
```
http://localhost:3000
Login: admin / admin
Dashboard: K6 Load Test - Real-time Metrics
```

---

## Load Test Details

### Script: `local-load-test.js`

**Validated Syntax**: ✅ Valid JavaScript ES6 modules

**Configuration**:
```javascript
export const options = {
  vus: 10,
  duration: '1m',
  stages: [
    { duration: '10s', target: 5 },    // Ramp-up to 5 VUs
    { duration: '30s', target: 10 },   // Scale to 10 VUs
    { duration: '15s', target: 5 },    // Scale back to 5 VUs
    { duration: '5s', target: 0 },     // Cooldown to 0 VUs
  ],
};
```

**Tests Included**:
1. **SIP Calculation** - Full API calculation
2. **Health Check** - Fast endpoint
3. **Error Handling** - Invalid parameter handling

**Metrics Tracked**:
- HTTP request duration
- Error rate
- Request count
- Custom metrics (errors, duration)

**Performance Thresholds**:
```javascript
thresholds: {
  'http_req_duration': [
    'p(95)<500',    // 95% of requests < 500ms
    'p(99)<1000'    // 99% of requests < 1000ms
  ],
  'http_req_failed': ['rate<0.01'],  // < 1% error rate
  'errors': ['rate<0.01']
}
```

---

## Execution Command Reference

### Run Load Test with Defaults
```bash
sudo docker compose -f docker-compose-k6.yaml run --rm k6 \
  run /scripts/local-load-test.js \
  --out influxdb=http://influxdb:8086/k6
```

### Run Load Test with JSON Export
```bash
sudo docker compose -f docker-compose-k6.yaml run --rm k6 \
  run /scripts/local-load-test.js \
  --out influxdb=http://influxdb:8086/k6 \
  --out json=results.json
```

### Run with Verbose Output
```bash
sudo docker compose -f docker-compose-k6.yaml run --rm k6 \
  run /scripts/local-load-test.js \
  --out influxdb=http://influxdb:8086/k6 \
  -v  # Verbose logging
```

### Start Infrastructure Only (for custom testing)
```bash
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana
```

### Stop All Services
```bash
sudo docker compose -f docker-compose-k6.yaml down
```

### Clean Up Everything (Remove Data)
```bash
sudo docker compose -f docker-compose-k6.yaml down -v
```

---

## Grafana Dashboard Walkthrough

### Access Dashboard
1. Open: **http://localhost:3000**
2. Login: **admin / admin**
3. Navigate to: **Dashboards** → **K6 Load Test - Real-time Metrics**

### Dashboard Panels

**Panel 1: Active Virtual Users (VUs) - Gauge**
- Shows current number of concurrent users
- Should show ramp pattern: 5 → 10 → 5 → 0
- Updates every 5 seconds

**Panel 2: Request Rate Over Time - Line Chart**
- Requests per second over test duration
- Higher during sustained load phase
- Should be stable at ~10-15 req/s during peak

**Panel 3: HTTP Request Duration (Latency) - Line Chart**
- Shows p50, p95, and p99 percentiles
- p50: Half of requests complete by this time
- p95: 95% of requests complete by this time
- p99: 99% of requests complete by this time
- Yellow threshold at 500ms, Red at 1000ms

**Panel 4: Error Rate Over Time - Line Chart**
- Percentage of failed requests
- Should stay green (< 1%)
- Red if any errors occur

**Panel 5: Current Error Rate - Gauge**
- Final error rate from test
- Green: 0%, Yellow: 1-5%, Red: > 5%

---

## Expected Results (Healthy API)

When the test completes, you should see:
```
✓ VUs: 0-10 (follows ramp pattern)
✓ Request Rate: 5-15 req/s (depends on VU count)
✓ p50 Latency: 50-150ms
✓ p95 Latency: 150-400ms
✓ p99 Latency: 200-600ms
✓ Error Rate: 0%
✓ All threshold checks passed
```

---

## Troubleshooting

### "Connection refused" to app
**Solution**: Start your SIP Calculator app
```bash
PORT=5000 npm run dev:observe
```

### "Cannot reach InfluxDB"
**Solution**: InfluxDB might need more time to start
```bash
# Wait longer
sleep 20
# Then run the test again
```

### No data appears in Grafana
**Solution**: 
1. Wait 30 seconds for InfluxDB to receive data
2. Refresh Grafana (F5)
3. Check if test completed successfully
4. Verify InfluxDB is running:
```bash
sudo docker compose -f docker-compose-k6.yaml ps
```

### "Port already in use"
**Solution**: Stop conflicting services
```bash
sudo docker compose -f docker-compose-k6.yaml down
# Or find and kill process using the port
lsof -i :3000  # For Grafana
lsof -i :8086  # For InfluxDB
```

---

## Next Steps

1. **Run the baseline test**:
   ```bash
   bash start-k6-load-test.sh
   ```

2. **Analyze the results** in Grafana at http://localhost:3000

3. **Identify bottlenecks**:
   - High latency? Optimize database queries
   - High error rate? Check error handling
   - Low request rate? Scale your backend

4. **Make improvements** to your API code

5. **Run again** to compare before/after:
   ```bash
   bash start-k6-load-test.sh
   ```

6. **Compare metrics** on the same Grafana dashboard

---

## Performance Optimization Tips

### If Latency is High (p95 > 500ms)
- Add caching to expensive calculations
- Use connection pooling
- Profile the `/api/sip` endpoint
- Check CPU/memory usage

### If Error Rate is High
- Review error logs in Grafana
- Add input validation
- Check for edge cases
- Monitor for timeout issues

### If Request Rate is Low
- Your API might be CPU-bound
- Consider horizontal scaling
- Optimize critical paths
- Use async operations

---

## Docker Service Ports

| Service | Port | URL |
|---------|------|-----|
| **SIP Calculator App** | 5000 | http://localhost:5000 |
| **Grafana** | 3000 | http://localhost:3000 |
| **InfluxDB HTTP** | 8086 | http://localhost:8086 |

---

## Validation Checklist

- ✅ K6 script syntax validated (ES6 modules)
- ✅ Performance thresholds configured
- ✅ Docker Compose stack verified
- ✅ Grafana datasource auto-provisioned
- ✅ Dashboard JSON valid and formatted
- ✅ Load test targets internal app
- ✅ Metrics collection to InfluxDB configured
- ✅ Quick start script executable

---

## Key Files Summary

| File | Purpose | Status |
|------|---------|--------|
| `local-load-test.js` | K6 load test script | ✅ Ready |
| `docker-compose-k6.yaml` | Infrastructure setup | ✅ Ready |
| `start-k6-load-test.sh` | Automated execution | ✅ Ready |
| `grafana/provisioning/datasources/datasources.yaml` | InfluxDB config | ✅ Ready |
| `grafana/provisioning/dashboards/k6-dashboard.json` | Dashboard definition | ✅ Ready |
| `K6_LOAD_TEST_GUIDE.md` | Full documentation | ✅ Ready |

---

## Quick Links

📖 **Full Documentation**: `K6_LOAD_TEST_GUIDE.md`

🚀 **Quick Start**: `bash start-k6-load-test.sh`

📊 **Dashboard**: http://localhost:3000

📋 **API Health**: http://localhost:5000/api/health

---

## You're Ready!

Everything is configured and validated. Your local k6 load testing environment with Grafana visualization is ready to test your SIP Calculator API.

**Next: Run the test!**
```bash
bash start-k6-load-test.sh
```

🎉 Happy load testing!
