# Observability (OpenTelemetry → Prometheus/Loki/Tempo/Grafana)

Same 5-service stack pattern used elsewhere on this machine, but on **its own
ports and its own Compose project name** (`case-study-3-observability`) so it
can run alongside a similarly-named stack from a sibling project without a
container-name collision (both directories happen to be named
`observability`, which is exactly what Compose uses for its default project
name — hence the explicit `name:` override in `docker-compose.yml`).

| Service | Default port (sibling project) | This project |
|---|---|---|
| Grafana | 3000 | **3010** |
| Prometheus | 9090 | **9091** |
| Loki | 3100 | **3101** |
| Tempo | 3200 | **3201** |
| OTel collector gRPC | 4317 | **4327** |
| OTel collector HTTP | 4318 | **4328** |

Only the host-side port mappings changed — every config file
(`otel-collector-config.yaml`, `prometheus.yml`, `loki-config.yaml`,
`tempo.yaml`, `grafana/provisioning/**`) is unmodified from the reference
pattern because they all refer to service names on the Compose-internal
Docker network (`otel-collector:8889`, `loki:3100`, `tempo:3200`, etc.),
which are unaffected by host remapping.

## Running

```bash
docker compose up -d          # from this directory
```

Then point the backend's OTel exporter at `localhost:4327` (already the
default in `backend/app/observability.py` — see `backend/.env.example`).

Grafana: http://localhost:3010 (anonymous admin access enabled for this demo
— see `GF_AUTH_ANONYMOUS_*` in `docker-compose.yml`, not appropriate for a
real deployment). Dashboards: **"Carta Extraction - App Overview"** and
**"k6 Load Test"** (see `../loadtest/README.md`).

## Stopping

```bash
docker compose down            # stops this project's containers only
```
