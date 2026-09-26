# K6 Local Load Testing with Grafana Visualization

Complete setup for load testing your SIP Calculator API with real-time metrics visualization.

## Setup Overview

This setup includes:
- **k6**: Grafana's load testing tool (runs in Docker)
- **InfluxDB**: Time-series database for storing metrics
- **Grafana**: Real-time visualization dashboard
- Pre-configured dashboard showing VUs, latency, error rates, and request throughput

---

## Quick Start (2 Steps)

### Step 1: Start the Observability Stack

```bash
cd /home/labuser/Downloads/Day4_Claude_Code

# Start InfluxDB and Grafana (keep running)
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana
```

Wait 10 seconds for services to initialize:
```bash
sleep 10
```

### Step 2: Run the Load Test

In a new terminal:
```bash
cd /home/labuser/Downloads/Day4_Claude_Code

# Run the k6 load test (sends metrics to InfluxDB)
sudo docker compose -f docker-compose-k6.yaml run --rm k6 run /scripts/local-load-test.js --out influxdb=http://influxdb:8086/k6
```

---

## What the Load Test Does

**Duration**: 1 minute
**Virtual Users**: 10 VUs with gradual ramp-up and ramp-down

### Test Stages:
1. **Ramp-up (0-10s)**: 0 → 5 VUs
2. **Sustained Load (10-40s)**: Hold at 10 VUs
3. **Ramp-down (40-55s)**: 10 → 5 VUs
4. **Cooldown (55-60s)**: 5 → 0 VUs

### Tests Included:
1. **SIP Calculation API**: Full calculation request
2. **Health Check**: Fast endpoint test
3. **Error Handling**: Invalid parameter handling

### Performance Thresholds:
- ✅ HTTP error rate < 1%
- ✅ p(95) latency < 500ms
- ✅ p(99) latency < 1000ms

---

## Access the Visualization

### Grafana Dashboard
- **URL**: http://localhost:3000
- **Username**: admin
- **Password**: admin
- **Dashboard**: Look for "K6 Load Test - Real-time Metrics" in the dashboards

### What You'll See:
1. **Active Virtual Users (VUs)** - Gauge showing current load
2. **Request Rate Over Time** - Requests per second over the test duration
3. **HTTP Request Duration** - p50, p95, p99 latency percentiles
4. **Error Rate Over Time** - Error percentage throughout the test
5. **Current Error Rate** - Gauge showing final error rate

---

## Full Commands Reference

### Start Infrastructure Only
```bash
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana
```

### Check Service Status
```bash
sudo docker compose -f docker-compose-k6.yaml ps
```

### View Logs
```bash
# All services
sudo docker compose -f docker-compose-k6.yaml logs -f

# Specific service
sudo docker compose -f docker-compose-k6.yaml logs -f influxdb
sudo docker compose -f docker-compose-k6.yaml logs -f grafana
```

### Run Load Test
```bash
# Basic run (metrics to InfluxDB)
sudo docker compose -f docker-compose-k6.yaml run --rm k6 run /scripts/local-load-test.js --out influxdb=http://influxdb:8086/k6

# With additional output to stdout
sudo docker compose -f docker-compose-k6.yaml run --rm k6 run /scripts/local-load-test.js --out influxdb=http://influxdb:8086/k6 --out json=results.json
```

### Stop All Services
```bash
sudo docker compose -f docker-compose-k6.yaml down
```

### Clean Up (Remove Data)
```bash
sudo docker compose -f docker-compose-k6.yaml down -v
```

---

## Step-by-Step Workflow

### Terminal 1: Ensure App is Running
```bash
cd /home/labuser/Downloads/Day4_Claude_Code
PORT=5000 npm run dev:observe
```

The app should be running at: http://localhost:5000

### Terminal 2: Start Infrastructure
```bash
cd /home/labuser/Downloads/Day4_Claude_Code
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana

# Wait for services to be ready
sleep 15
```

### Terminal 3: Run the Load Test
```bash
cd /home/labuser/Downloads/Day4_Claude_Code

# Run the test
sudo docker compose -f docker-compose-k6.yaml run --rm k6 run /scripts/local-load-test.js --out influxdb=http://influxdb:8086/k6
```

### Browser: View Results in Grafana
1. Open: **http://localhost:3000**
2. Login: **admin / admin**
3. Navigate to: **Dashboards** → **K6 Load Test - Real-time Metrics**
4. Watch the metrics update in real-time as the test runs

---

## Understanding the Metrics

### VUs (Virtual Users)
- Shows how many concurrent users are hitting your API
- Should match the test stage (ramp-up, sustained, ramp-down)

### Request Rate (req/s)
- Number of requests per second
- Higher VUs = higher request rate
- Should be stable during sustained load phase

### Latency Percentiles (p50, p95, p99)
- p50: 50% of requests complete in this time or less
- p95: 95% of requests complete in this time or less  
- p99: 99% of requests complete in this time or less
- Yellow threshold at 500ms, Red at 1000ms

### Error Rate
- Percentage of requests that failed
- Green: <1%, Yellow: 1-5%, Red: >5%
- Threshold: Should stay < 1%

### Request Count
- Total HTTP requests sent
- Should show ramp patterns matching VU changes

---

## Customizing the Test

### Edit Load Profile
Edit `local-load-test.js`:

```javascript
export const options = {
  vus: 10,          // Change number of virtual users
  duration: '1m',   // Change test duration
  stages: [         // Modify load stages
    { duration: '10s', target: 5 },
    { duration: '30s', target: 10 },
    { duration: '15s', target: 5 },
    { duration: '5s', target: 0 },
  ],
};
```

### Modify Thresholds
```javascript
thresholds: {
  'http_req_duration': ['p(95)<500', 'p(99)<1000'],  // Change latency thresholds
  'http_req_failed': ['rate<0.01'],  // Change error threshold
},
```

### Add More Test Cases
Add new test groups in the default function to test different endpoints or scenarios.

---

## Performance Interpretation

### Good Performance
```
VUs: 10
Request Rate: 5-10 req/s
p95 Latency: 200-400ms
p99 Latency: 300-500ms
Error Rate: 0%
```

### Acceptable Performance
```
VUs: 10
Request Rate: 5-8 req/s
p95 Latency: 400-600ms
p99 Latency: 600-900ms
Error Rate: <1%
```

### Needs Optimization
```
VUs: 10
p95 Latency: >1000ms
Error Rate: >5%
Requests failing during load
```

---

## Troubleshooting

### "Cannot connect to localhost:8086"
- InfluxDB might not be ready. Wait 10 seconds and retry:
```bash
sleep 10 && sudo docker compose -f docker-compose-k6.yaml run --rm k6 ...
```

### "Connection refused" to app
- Ensure your SIP Calculator app is running on port 5000:
```bash
PORT=5000 npm run dev:observe
```

### No data in Grafana
1. Wait 30 seconds for InfluxDB to receive data
2. Refresh Grafana browser (F5 or Ctrl+R)
3. Check if the test ran successfully (look for output in terminal)

### Services won't start
```bash
# Clean up and restart
sudo docker compose -f docker-compose-k6.yaml down -v
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana
sleep 15
```

---

## Advanced Usage

### Run Multiple Times with Baseline Comparison
```bash
# Run 1: Baseline
sudo docker compose -f docker-compose-k6.yaml run --rm k6 run /scripts/local-load-test.js --out influxdb=http://influxdb:8086/k6

sleep 60

# Make code changes...

# Run 2: After optimization
sudo docker compose -f docker-compose-k6.yaml run --rm k6 run /scripts/local-load-test.js --out influxdb=http://influxdb:8086/k6
```

Compare results on Grafana by zooming in on different time ranges.

### Export Results
```bash
# Save JSON results
sudo docker compose -f docker-compose-k6.yaml run --rm k6 run /scripts/local-load-test.js \
  --out influxdb=http://influxdb:8086/k6 \
  --out json=results-$(date +%Y%m%d-%H%M%S).json
```

### View Summary Report
```bash
# The k6 output shows a summary like:
# http_req_duration..............: avg=145ms, min=2ms, med=45ms, max=1245ms, p(90)=456ms, p(95)=587ms
# http_req_failed................: 0.50%
# http_reqs......................: 450 in 60s
# vus............................: 0-10
```

---

## Service Port Mapping

| Service | Port | URL |
|---------|------|-----|
| **SIP Calculator App** | 5000 | http://localhost:5000 |
| **Grafana** | 3000 | http://localhost:3000 |
| **InfluxDB** | 8086 | http://localhost:8086 |
| **InfluxDB Admin UI** | 8083 | http://localhost:8083 (optional) |

---

## Next Steps

1. ✅ Run the baseline test and capture baseline metrics
2. ✅ Make performance improvements to your API
3. ✅ Run the test again and compare results
4. ✅ Identify bottlenecks using the Grafana dashboard
5. ✅ Optimize based on the latency and error insights

---

## Files Created

```
/Day4_Claude_Code/
├── local-load-test.js                 # K6 load test script
├── docker-compose-k6.yaml             # Docker Compose config
├── grafana/
│   └── provisioning/
│       ├── datasources/
│       │   └── datasources.yaml       # Grafana datasource config
│       └── dashboards/
│           └── k6-dashboard.json      # Grafana dashboard definition
└── K6_LOAD_TEST_GUIDE.md             # This guide
```

---

**Ready to load test?**

```bash
# Terminal 1: Start app
PORT=5000 npm run dev:observe

# Terminal 2: Start infrastructure
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana && sleep 15

# Terminal 3: Run test
sudo docker compose -f docker-compose-k6.yaml run --rm k6 run /scripts/local-load-test.js --out influxdb=http://influxdb:8086/k6

# Browser: View results
open http://localhost:3000
```

🚀 Load testing dashboard is ready!
