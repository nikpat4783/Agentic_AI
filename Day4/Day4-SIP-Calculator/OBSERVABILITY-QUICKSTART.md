# 🚀 Quick Start: Run Observability Stack

## 30-Second Setup

```bash
# Terminal 1: Start the observability backend
npm run observe:start

# Wait 15 seconds for containers to start...

# Terminal 2: Start the app with tracing
npm run dev:observe

# Terminal 3: Generate some traffic
for i in {1..5}; do
  curl "http://localhost:3000/api/sip?monthlyInvestment=5000&expectedReturn=12&years=10"
  sleep 1
done
```

## Access Dashboards

| Service | URL | Login |
|---------|-----|-------|
| **Grafana (Main)** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **Jaeger Traces** | http://localhost:16686 | - |
| **Tempo** | http://localhost:3200 | - |
| **App API** | http://localhost:3000/api/health | - |

## Verify Everything Works

```bash
# Run verification script
./verify-observability.sh

# Should output green checkmarks for all services
```

## What You're Seeing

**Grafana Dashboard:**
- HTTP request rates and latencies
- Trace visualization from Tempo
- Service health metrics

**Jaeger:**
- Detailed request traces
- Service dependency graph
- Latency breakdown by operation

**Prometheus:**
- Raw metrics in time-series format
- Query builder for custom metrics
- Alert configuration

## Stop Everything

```bash
npm run observe:stop
```

## Troubleshooting

### Nothing showing in Grafana?
1. Wait 20-30 seconds for data to flow
2. Make some API requests: `curl http://localhost:3000/api/health`
3. Refresh Grafana (Ctrl+R)
4. Check collector logs: `npm run observe:logs | grep otel-collector`

### Port 3000 already in use?
Edit `docker-compose.yaml`:
```yaml
grafana:
  ports:
    - '3001:3000'  # Change to 3001
```

### Containers won't start?
```bash
docker-compose down -v
docker-compose up -d
```

## Next Steps

1. **Explore Traces:** Go to Jaeger (http://localhost:16686) → Service: sip-calculator-api
2. **Custom Dashboard:** Edit dashboard in Grafana
3. **Add Alerts:** Create alert rules in Prometheus
4. **Read Full Docs:** See `OBSERVABILITY.md` for detailed configuration

---

**That's it! You now have production-grade observability.** 🎉
