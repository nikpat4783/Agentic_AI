# 🚀 K6 Load Testing - Deployment Summary

## Deployment Options Available

You now have **2 complete deployment options** for your k6 load testing setup.

---

## 📍 Option 1: Default Ports

### Quick Start
```bash
bash start-k6-load-test.sh
```

### Service Ports
| Service | Port | URL |
|---------|------|-----|
| **Grafana** | 3000 | http://localhost:3000 |
| **InfluxDB** | 8086 | http://localhost:8086 |
| **App** | 5000 | http://localhost:5000 |

### Infrastructure File
```bash
docker-compose-k6.yaml
```

### Stop Services
```bash
sudo docker compose -f docker-compose-k6.yaml down
```

---

## 📍 Option 2: Alternative Ports

### Quick Start
```bash
bash start-k6-load-test-alt.sh
```

### Service Ports
| Service | Port | URL |
|---------|------|-----|
| **Grafana** | 3001 | http://localhost:3001 |
| **InfluxDB** | 8087 | http://localhost:8087 |
| **App** | 5000 | http://localhost:5000 |

### Infrastructure File
```bash
docker-compose-k6-alt.yaml
```

### Stop Services
```bash
sudo docker compose -f docker-compose-k6-alt.yaml down
```

---

## 🎯 Run Both Simultaneously

You can run **both deployments at the same time** on different ports:

### Terminal 1: Run Default Deployment
```bash
cd /home/labuser/Downloads/Day4_Claude_Code
bash start-k6-load-test.sh
```

### Terminal 2: Run Alternative Deployment
```bash
cd /home/labuser/Downloads/Day4_Claude_Code
bash start-k6-load-test-alt.sh
```

### Browser Tabs
- **Tab 1**: http://localhost:3000 (Default - admin/admin)
- **Tab 2**: http://localhost:3001 (Alternative - admin/admin)

---

## 📊 Port Allocation

### Currently in Use (Observability Stack)
```
Port 4000  → Grafana (Observability)
Port 3100  → Loki
Port 9090  → Prometheus
Port 5000  → SIP Calculator App
```

### Available for K6 Setup
```
✅ Port 3000 (Default)    ← K6 Grafana
✅ Port 8086 (Default)    ← K6 InfluxDB
✅ Port 3001 (Alt)        ← K6 Grafana Alt
✅ Port 8087 (Alt)        ← K6 InfluxDB Alt
```

---

## 🔄 Manual Deployment Steps

### Option 1: Default Ports (Ports 3000/8086)

**Start Infrastructure**:
```bash
cd /home/labuser/Downloads/Day4_Claude_Code
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana
sleep 15
```

**Run Load Test**:
```bash
sudo docker compose -f docker-compose-k6.yaml run --rm k6 \
  run /scripts/local-load-test.js \
  --out influxdb=http://influxdb:8086/k6
```

**View Results**:
```
http://localhost:3000 (admin/admin)
```

---

### Option 2: Alternative Ports (Ports 3001/8087)

**Start Infrastructure**:
```bash
cd /home/labuser/Downloads/Day4_Claude_Code
sudo docker compose -f docker-compose-k6-alt.yaml up -d influxdb-alt grafana-alt
sleep 15
```

**Run Load Test**:
```bash
sudo docker compose -f docker-compose-k6-alt.yaml run --rm k6-alt \
  run /scripts/local-load-test.js \
  --out influxdb=http://influxdb-alt:8086/k6
```

**View Results**:
```
http://localhost:3001 (admin/admin)
```

---

## 📁 File Structure

```
/Day4_Claude_Code/
│
├── 🎯 Default Deployment
│   ├── docker-compose-k6.yaml
│   ├── start-k6-load-test.sh
│   └── grafana/provisioning/
│       ├── datasources/datasources.yaml
│       └── dashboards/k6-dashboard.json
│
├── 🎯 Alternative Deployment
│   ├── docker-compose-k6-alt.yaml
│   ├── start-k6-load-test-alt.sh
│   └── grafana-alt/provisioning/
│       ├── datasources/datasources.yaml
│       └── dashboards/k6-dashboard.json
│
├── 📊 Load Test Script
│   └── local-load-test.js
│
└── 📚 Documentation
    ├── K6_LOAD_TEST_GUIDE.md
    ├── K6_SETUP_COMPLETE.md
    ├── EXECUTE_K6_TEST.md
    ├── TOKEN_CONSUMPTION_REPORT.md
    └── DEPLOYMENT_SUMMARY.md (this file)
```

---

## 🚀 Execution Comparison

### Automated Execution (Recommended)

**Option 1**:
```bash
bash start-k6-load-test.sh
```

**Option 2**:
```bash
bash start-k6-load-test-alt.sh
```

Both scripts:
- ✅ Verify app is running
- ✅ Start infrastructure
- ✅ Wait for service initialization
- ✅ Run load test
- ✅ Print dashboard URL

---

## 📈 Monitoring Multiple Tests

### Same Grafana Instance
```
Scenario 1: Test on Default (Port 3000)
├─ Run 1: Baseline test
├─ Run 2: After optimization
└─ Compare metrics on same dashboard

Scenario 2: Test on Alternative (Port 3001)
├─ Run 3: Different load profile
├─ Run 4: Stress test
└─ Compare with baseline

Scenario 3: Side-by-Side Comparison
├─ Default (Port 3000): New code version
├─ Alternative (Port 3001): Old code version
└─ Compare performance in real-time
```

---

## 🛑 Cleanup Commands

### Stop Default Deployment (Keep Data)
```bash
sudo docker compose -f docker-compose-k6.yaml stop
```

### Stop Alternative Deployment (Keep Data)
```bash
sudo docker compose -f docker-compose-k6-alt.yaml stop
```

### Remove Default (Delete Data)
```bash
sudo docker compose -f docker-compose-k6.yaml down
sudo docker compose -f docker-compose-k6.yaml down -v  # With data
```

### Remove Alternative (Delete Data)
```bash
sudo docker compose -f docker-compose-k6-alt.yaml down
sudo docker compose -f docker-compose-k6-alt.yaml down -v  # With data
```

### Remove Both
```bash
sudo docker compose -f docker-compose-k6.yaml down -v
sudo docker compose -f docker-compose-k6-alt.yaml down -v
```

---

## 🔍 Service Verification

### Check Default Services
```bash
sudo docker compose -f docker-compose-k6.yaml ps
```

### Check Alternative Services
```bash
sudo docker compose -f docker-compose-k6-alt.yaml ps
```

### Check All Services (Both Deployments)
```bash
sudo docker ps | grep -E "k6|influxdb|grafana"
```

---

## 📊 Dashboard Access

### Default Deployment
```
URL: http://localhost:3000
Username: admin
Password: admin
Dashboard: K6 Load Test - Real-time Metrics
```

### Alternative Deployment
```
URL: http://localhost:3001
Username: admin
Password: admin
Dashboard: K6 Load Test - Real-time Metrics
```

---

## 🎯 Use Cases

### Use Case 1: Baseline Testing
```bash
bash start-k6-load-test.sh
# Run load test, capture baseline metrics
# Screenshot results
```

### Use Case 2: Before/After Comparison
```bash
# Terminal 1: Default deployment
bash start-k6-load-test.sh

# Make code optimizations

# Terminal 2: Alternative deployment (to compare)
bash start-k6-load-test-alt.sh

# Both dashboards open simultaneously
# http://localhost:3000 vs http://localhost:3001
```

### Use Case 3: Stress Testing
```bash
# Run default deployment with standard load
bash start-k6-load-test.sh

# Separately run alternative with higher load
# Edit local-load-test.js: increase VUs to 20-50
bash start-k6-load-test-alt.sh

# Compare stress test results
```

### Use Case 4: Continuous Integration
```bash
# Run in CI pipeline on default ports (3000/8086)
docker compose -f docker-compose-k6.yaml run --rm k6 \
  run /scripts/local-load-test.js \
  --out influxdb=http://influxdb:8086/k6

# Check thresholds
# If pass: continue deployment
# If fail: block deployment
```

---

## 📈 Performance Metrics to Track

### Per Deployment
- Virtual Users (VUs)
- Request Rate (req/s)
- HTTP Duration (p50, p95, p99)
- Error Rate (%)
- Request Count
- Check Pass Rate

### Comparison Between Deployments
- Latency improvement
- Error rate change
- Throughput difference
- Threshold compliance

---

## 🔧 Custom Configuration

### Modify Load Profile

Edit `local-load-test.js`:
```javascript
export const options = {
  vus: 20,        // Change to 20 VUs instead of 10
  duration: '2m', // Change to 2 minutes instead of 1
  stages: [
    { duration: '20s', target: 10 },
    { duration: '60s', target: 20 },
    { duration: '20s', target: 10 },
    { duration: '10s', target: 0 },
  ],
};
```

Then run with either deployment option:
```bash
bash start-k6-load-test.sh
# or
bash start-k6-load-test-alt.sh
```

---

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Find what's using the port
lsof -i :3000
lsof -i :8086
lsof -i :3001
lsof -i :8087

# Kill the process
kill -9 <PID>
```

### Services Won't Start
```bash
# Check Docker is running
docker ps

# View logs
sudo docker compose -f docker-compose-k6.yaml logs

# Force restart
sudo docker compose -f docker-compose-k6.yaml restart
```

### No Data in Grafana
```bash
# Wait longer
sleep 30

# Refresh browser (F5)

# Check test completed successfully
sudo docker compose -f docker-compose-k6.yaml logs k6
```

---

## ✅ Deployment Checklist

Before running tests:
- [ ] App running on port 5000
- [ ] Docker is running
- [ ] Ports 3000/8086 available (default) OR 3001/8087 (alt)
- [ ] You have sudo access
- [ ] Scripts are executable

Before interpreting results:
- [ ] Test completed (1 minute duration)
- [ ] Grafana dashboard accessible
- [ ] Data appears in charts (wait 30s)
- [ ] Refresh browser if needed

---

## 📞 Quick Commands Reference

### Default Deployment
```bash
# Start
bash start-k6-load-test.sh

# Manual start
sudo docker compose -f docker-compose-k6.yaml up -d influxdb grafana

# Manual test
sudo docker compose -f docker-compose-k6.yaml run --rm k6 \
  run /scripts/local-load-test.js --out influxdb=http://influxdb:8086/k6

# Stop
sudo docker compose -f docker-compose-k6.yaml down

# Dashboard
http://localhost:3000
```

### Alternative Deployment
```bash
# Start
bash start-k6-load-test-alt.sh

# Manual start
sudo docker compose -f docker-compose-k6-alt.yaml up -d influxdb-alt grafana-alt

# Manual test
sudo docker compose -f docker-compose-k6-alt.yaml run --rm k6-alt \
  run /scripts/local-load-test.js --out influxdb=http://influxdb-alt:8086/k6

# Stop
sudo docker compose -f docker-compose-k6-alt.yaml down

# Dashboard
http://localhost:3001
```

---

## 🎉 Ready to Deploy!

You now have two complete deployment options:

**Option 1**: Default ports (3000/8086)
```bash
bash start-k6-load-test.sh
```

**Option 2**: Alternative ports (3001/8087)
```bash
bash start-k6-load-test-alt.sh
```

Both are fully configured, automated, and ready to use.

Choose your deployment and start load testing! 🚀
