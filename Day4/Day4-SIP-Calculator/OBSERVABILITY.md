# Full-Stack Observability Setup with OpenTelemetry & Grafana

This guide explains how to run the SIP Calculator with complete observability instrumentation using OpenTelemetry, Prometheus, Tempo, and Grafana.

## Architecture Overview

```
┌─────────────────────────┐
│  SIP Calculator App     │  (Node.js + Express)
│  (Port 3000)            │  - HTTP requests traced
│  [OpenTelemetry SDK]    │  - Metrics exported
└────────────┬────────────┘
             │ OTLP HTTP (4318)
             ▼
┌─────────────────────────────┐
│  OpenTelemetry Collector    │  (Port 4317/4318)
│  - Receives spans/metrics   │
│  - Batch processing         │
│  - Routes to backends       │
└────────────┬────────────────┘
             │
    ┌────────┴────────┬─────────────┐
    ▼                 ▼             ▼
┌─────────┐      ┌────────┐   ┌──────────┐
│Prometheus│    │ Tempo  │   │  Jaeger  │
│(Port9090)│    │(3200)  │   │(16686)   │
└──────┬───┘      └───┬────┘   └──────────┘
       │              │
       └──────┬───────┘
              ▼
        ┌──────────────┐
        │   Grafana    │
        │ (Port 3000)  │
        └──────────────┘
```

## Quick Start

### 1. Start the Observability Stack

```bash
# Start all backend services (Prometheus, Tempo, Grafana, Collector)
npm run observe:start

# This will start:
# - OpenTelemetry Collector (OTLP receivers on 4317/4318)
# - Prometheus (metrics storage, port 9090)
# - Tempo (trace storage, port 3200)
# - Grafana (dashboards, port 3000)
# - Jaeger (trace UI, port 16686)
```

**Wait 10-15 seconds for all containers to start and become healthy.**

### 2. Start the Application with Observability

In a new terminal:

```bash
# Run the app with OpenTelemetry enabled
npm run dev:observe

# Or in production:
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318 npm start
```

### 3. Access Grafana Dashboard

Open your browser and go to:

```
http://localhost:3000
```

**Login credentials:**
- Username: `admin`
- Password: `admin`

You'll see the "SIP Calculator API Overview" dashboard automatically loaded.

### 4. Generate Some Traces

Make requests to the API to generate trace data:

```bash
# Health check
curl http://localhost:3000/api/health

# SIP calculation (generates traces)
curl "http://localhost:3000/api/sip?monthlyInvestment=5000&expectedReturn=12&years=10&annualStepUp=5"

# Multiple requests to generate metrics
for i in {1..10}; do
  curl "http://localhost:3000/api/sip?monthlyInvestment=$((RANDOM % 10000 + 1000))&expectedReturn=$((RANDOM % 20))&years=$((RANDOM % 20 + 5))"
  sleep 0.5
done
```

### 5. View the Data

#### Grafana (Metrics & Traces)
- **URL:** http://localhost:3000
- **Dashboards:** Look for "SIP Calculator API Overview"
- **Data Sources:** Prometheus (metrics) and Tempo (traces)

#### Jaeger (Detailed Traces)
- **URL:** http://localhost:16686
- **Service:** Look for "sip-calculator-api"
- **Traces:** Search for recent spans

#### Prometheus (Raw Metrics)
- **URL:** http://localhost:9090
- **Queries:** Try `rate(http_requests_total[5m])`

## What's Being Instrumented

### Traces Collected
- **HTTP Requests:** Method, path, status code, duration
- **Function Execution:** Call hierarchy and timing
- **Express Middleware:** Request/response phases
- **File System Operations:** Read/write operations

### Metrics Collected
- **HTTP Server Metrics:**
  - Request duration (histogram)
  - Request count (counter)
  - Request size (histogram)
  - Response size (histogram)
- **Process Metrics:**
  - CPU usage
  - Memory usage
  - Event loop lag
- **Custom Metrics:**
  - SIP calculation duration
  - Validation errors

## Configuration Files Explained

### `otel-setup.js`
- Initializes the OpenTelemetry SDK
- Configures trace and metric exporters
- Sets up instrumentations for Express, HTTP, and File System
- **Must be imported FIRST in server.js**

### `otel-collector-config.yaml`
- **Receivers:** OTLP gRPC (4317) and HTTP (4318)
- **Processors:** Batch and memory limiting
- **Exporters:** Routes to Prometheus, Tempo, and Jaeger

### `docker-compose.yaml`
- Orchestrates all backend services
- Network isolation with `observability` network
- Persistent volumes for data retention

### `prometheus.yml`
- Scrape configuration for metrics collection
- 15-second interval collection
- Configures retention (30 days)

### `tempo.yaml`
- Local storage backend for traces
- Service graph metrics generation
- Remote write to Prometheus for metrics

## Stopping the Stack

```bash
# Stop all services
npm run observe:stop

# View logs while running
npm run observe:logs

# Clean up volumes and containers
docker-compose down -v
```

## Environment Variables

```bash
# Override the OTLP endpoint (default: http://localhost:4318)
OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4318

# Enable debug logging
OTEL_LOG_LEVEL=debug

# Set service name (default: sip-calculator-api)
OTEL_SERVICE_NAME=my-sip-service

# Set Node environment
NODE_ENV=production
```

## Troubleshooting

### No traces appearing in Grafana?
1. Check collector logs: `docker-compose logs otel-collector`
2. Verify app is sending data: `docker-compose logs sip-calculator-app`
3. Ensure ports 4317/4318 are accessible from the app
4. Check Tempo is running: `docker-compose logs tempo`

### Grafana won't load?
```bash
# Check if Grafana is running
docker-compose ps | grep grafana

# View Grafana logs
docker-compose logs grafana

# Reset Grafana (CAREFUL - loses settings)
docker-compose down
docker volume rm docker_grafana_data
docker-compose up -d
```

### High memory usage?
- Adjust `memory_limiter` in `otel-collector-config.yaml`
- Reduce trace sample rate in `otel-setup.js`
- Increase batch timeout in collector config

### Port already in use?
Edit `docker-compose.yaml` and change the port mappings:
```yaml
ports:
  - '3001:3000'  # Change 3000 to 3001 or another available port
```

## Performance Impact

The OpenTelemetry instrumentation adds minimal overhead:
- **CPU:** ~2-5% increase under normal load
- **Memory:** ~20-30MB additional per process
- **Network:** ~1-2 Mbps with 10 RPS traffic

## Next Steps

1. **Customize Dashboards:** Edit dashboards in Grafana UI
2. **Set Alerts:** Add alert rules in Prometheus
3. **Add Logs:** Enable Loki for log aggregation (included in docker-compose)
4. **Custom Metrics:** Add business logic metrics to `otel-setup.js`
5. **Sampling:** Implement head-based sampling for high-traffic scenarios

## Resources

- [OpenTelemetry Documentation](https://opentelemetry.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Tempo Documentation](https://grafana.com/docs/tempo/)
