# 📊 Grafana Dashboard Visualization Guide

This document shows you what to expect when viewing the OpenTelemetry metrics in Grafana.

## Dashboard: SIP Calculator API Overview

**Access:** http://localhost:3000 → Dashboards → SIP Calculator API Overview

### Panel 1: HTTP Request Duration (5m rate)

```
┌─────────────────────────────────────────────────────────────────┐
│ HTTP Request Duration (5m rate)                          [Edit] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                                          ╱╲      ╱╲  ╱╲        │
│  Latency (ms)   60 ─────────────────────╱  ╲    ╱  ╲╱  ╲      │
│                 50 ─────────────────────────╲  ╱─────────╲     │
│                 40 ─╱─────────────────────────╲╱──────────╲    │
│                 30 ╱───────────────────────────╲─────────────── │
│                 20 ╱─────────────────────────────╲──────────    │
│                 10 ╱───────────────────────────────╲────────    │
│                  0 ─────────────────────────────────────────    │
│                                                                 │
│      12:00    12:15    12:30    12:45    13:00    13:15 Time   │
│                                                                 │
│ Legend:                                                         │
│ ─ p50 (median)  ─ p95 (95th percentile)  ─ p99 (99th perc.)   │
└─────────────────────────────────────────────────────────────────┘
```

**What it shows:**
- Median response time (p50): ~25ms
- 95th percentile (p95): ~45ms
- 99th percentile (p99): ~60ms

---

### Panel 2: Request Rate (5m)

```
┌─────────────────────────────────────────────────────────────────┐
│ Request Rate (5m)                                      [Refresh] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RPS (Requests/sec)   15 ──╱──────────╱─────────────╱──────    │
│                       10 ──╲╱────────╱──────╱─────╱────────    │
│                        5 ──────────╱────────╲──╱──────────     │
│                        0 ────────────────────────────────────   │
│                                                                 │
│      12:00    12:15    12:30    12:45    13:00    13:15 Time   │
│                                                                 │
│ Current: 12 RPS   Average: 8 RPS   Min: 2 RPS   Max: 18 RPS   │
│                                                                 │
│ Legend:                                                         │
│ ─ Request Rate                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**What it shows:**
- Current request rate: 12 requests/second
- Traffic patterns over time
- Peak traffic periods

---

### Panel 3: Traces (Tempo)

```
┌─────────────────────────────────────────────────────────────────┐
│ Traces (Tempo)                                         [Search] │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ Recent Traces:                                                  │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ TRACE ID: a1b2c3d4e5f6g7h8i9j0  [13:15:42]  Duration: 28ms ││
│ │ ├─ HTTP GET /api/sip (28ms)                                ││
│ │ │  ├─ Middleware setup (2ms)                               ││
│ │ │  ├─ Query parsing (1ms)                                  ││
│ │ │  ├─ calculateSipValue() (20ms)                           ││
│ │ │  └─ Response serialization (5ms)                         ││
│ ├─────────────────────────────────────────────────────────────┤│
│ │ TRACE ID: z9y8x7w6v5u4t3s2r1q0  [13:15:41]  Duration: 32ms ││
│ │ ├─ HTTP GET /api/sip (32ms)                                ││
│ │ │  ├─ Middleware setup (2ms)                               ││
│ │ │  ├─ Query parsing (1ms)                                  ││
│ │ │  ├─ calculateSipValue() (25ms)  [SLOW]                   ││
│ │ │  └─ Response serialization (4ms)                         ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**What it shows:**
- Individual request traces with full span hierarchy
- Breakdown of where time is spent in each request
- Identification of slow operations
- Click to drill down into any trace

---

### Panel 4: Error Rate

```
┌─────────────────────────────────────────────────────────────────┐
│ Error Rate                                                 [Edit]│
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Error Rate (%)    5 ─────────────────────────────────────────  │
│                    4 ──╱╲──╱╲────────────────╱─────╱──────     │
│                    3 ─╱──╲╱──╲──╱╲────────╱──╲──╱─────        │
│                    2 ─────────╲╱───╲──╱───────────────        │
│                    1 ──────────────────────────────────        │
│                    0 ─────────────────────────────────────    │
│                                                                 │
│      12:00    12:15    12:30    12:45    13:00    13:15 Time   │
│                                                                 │
│ Current: 0.5%   Average: 1.2%   Max: 4.8%                      │
│                                                                 │
│ Breakdown:                                                      │
│ • 400 Bad Request: 2 errors                                    │
│ • 500 Server Error: 0 errors                                   │
└─────────────────────────────────────────────────────────────────┘
```

**What it shows:**
- Error rate percentage over time
- Error distribution by type
- Spikes in error rate

---

### Panel 5: Response Time Distribution

```
┌─────────────────────────────────────────────────────────────────┐
│ Response Time Distribution                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Frequency                                                      │
│     │       ┌─┐                                                │
│     │       │ │                                                │
│   50│   ┌───┤ │───┐                                            │
│     │   │ ┌─┤ │─┐ │                                            │
│   40│   │ │ │ │ │ │                                            │
│     │   │ │ │ │ │ │   ┌─┐                                      │
│   30│   │ │ │ │ │ │   │ │                                      │
│     │   │ │ │ │ │ │   │ │  ┌─┐                                │
│   20│   │ │ │ │ │ │   │ │  │ │                                │
│     │   │ │ │ │ │ │   │ │  │ │  ┌─┐                          │
│   10│   │ │ │ │ │ │   │ │  │ │  │ │  ┌─┐ ┌─┐ ┌─┐            │
│     │   │ │ │ │ │ │   │ │  │ │  │ │  │ │ │ │ │ │            │
│    0│───┴─┴─┴─┴─┴─┴───┴─┴──┴─┴──┴─┴──┴─┴─┴─┴─┴─┴──          │
│       0 5 10 15 20 25 30 35 40 45 50 55 60 65 70+ ms          │
│                                                                 │
│ 95% of requests complete within 50ms                           │
│ Mean response time: 28ms                                       │
│ Median response time: 25ms                                     │
│ Max response time: 87ms                                        │
└─────────────────────────────────────────────────────────────────┘
```

**What it shows:**
- Distribution of response times
- Identifies slow outliers
- Shows performance consistency

---

## Additional Dashboard Panels Available

### Service Dependency Graph

```
                    Grafana (Dashboard)
                            │
                            ▼
                      Prometheus (Metrics)
                            │
                    ┌───────┼───────┐
                    ▼       ▼       ▼
              OTel Col   Tempo   Jaeger
                    │       │       │
                    └───────┼───────┘
                            ▼
                  SIP Calculator API
                            │
                ┌───────────┼───────────┐
                ▼           ▼           ▼
            Express      HTTP      File System
```

### Request Count by Endpoint

```
┌─────────────────────────────────────────────────────────────────┐
│ Request Count by Endpoint                                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ /api/sip           ████████████████████░░░░░░░░░ 850 (85%)    │
│ /api/health        ██████░░░░░░░░░░░░░░░░░░░░░░░  90 (9%)    │
│ / (index.html)     ████░░░░░░░░░░░░░░░░░░░░░░░░░  60 (6%)    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### CPU & Memory Usage

```
┌─────────────────────────────────────────────────────────────────┐
│ Node Process Metrics                                             │
├────────────────────────────────────┬────────────────────────────┤
│ CPU Usage (%)                      │ Memory Usage (MB)          │
│                                    │                            │
│   40 ────╱╲──╱╲────╱╲──────       │   150 ─────────────────── │
│   30 ───╱──╲╱──╲──╱──╲──────      │   140 ───╱╲──╱╲──╱╲──── │
│   20 ──╱─────────╲────╲────       │   130 ──╱──╲╱──╲╱──╲─── │
│   10 ─╱──────────────────────     │   120 ─╱─────────────── │
│    0 ─────────────────────────    │   110 ─────────────────── │
│      12:00  12:30  13:00  13:30   │      12:00  12:30 13:00   │
│                                    │                            │
│ Current: 12%                       │ Current: 135 MB            │
└────────────────────────────────────┴────────────────────────────┘
```

---

## Real-Time Interaction Examples

### Example 1: Investigating Slow Requests

1. **See the spike** in the HTTP Request Duration panel
2. **Click on the spike** to filter traces during that time
3. **View detailed traces** showing which operation is slow
4. **Optimize the slow operation** based on trace data

### Example 2: Debugging an Error

1. **Notice error rate increase** in Error Rate panel
2. **Search traces** for errors using Tempo search
3. **View full error traces** with stack traces
4. **Identify the cause** and fix it

### Example 3: Performance Analysis

1. **Use Prometheus query editor** to write custom queries
2. **Calculate 99th percentile latency:**
   ```promql
   histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))
   ```
3. **Compare before/after** performance improvements

---

## Creating Custom Dashboards

### Dashboard 1: SIP Calculation Performance

```
┌─────────────────────────────────────────────────────────────────┐
│ SIP Calculation Performance                                      │
├─────────────────────────────────────────────────────────────────┤
│ ┌──────────────────────┐  ┌──────────────────────┐             │
│ │ Avg Calc Time        │  │ Calc Time p95        │             │
│ │      18.5 ms         │  │      35.2 ms         │             │
│ └──────────────────────┘  └──────────────────────┘             │
│                                                                 │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ Calculation Duration over Time                          │  │
│ │                              ╱╲     ╱╲                  │  │
│ │  ms   40 ─────────────────╱──╲───╱──╲─────            │  │
│ │      30 ───────╱╲───╱╲──╱─────╲─────╲────            │  │
│ │      20 ──╱──╱──╲╱──╲╱────────╲─────╲───            │  │
│ │      10 ─╱─╱──────────────────╲─────╲──            │  │
│ │       0 ──────────────────────────────             │  │
│ └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Dashboard 2: API Health Status

```
┌─────────────────────────────────────────────────────────────────┐
│ API Health Status                                                │
├─────────────────────────────────────────────────────────────────┤
│ ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│ │ ✅ Availability  │  │ 📊 Requests/min  │  │ ⚡ Avg Latency│ │
│ │ 99.95%           │  │ 720              │  │ 28ms         │  │
│ └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                 │
│ Endpoint Status:                                                │
│ ✅ /api/sip        - UP   (1250ms response)                    │
│ ✅ /api/health     - UP   (2ms response)                       │
│ ✅ /               - UP   (45ms response)                      │
│                                                                 │
│ Error History (24h):                                            │
│ • 2 errors at 12:15  (Invalid input)                          │
│ • 0 errors at other times                                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Monitoring Alerts (Optional Setup)

Once dashboards are working, you can set up alerts:

### Alert: High Error Rate

```
Alert Name: HighErrorRate
Condition: error_rate > 5%
Duration: 5 minutes
Action: Send notification
```

### Alert: High Latency

```
Alert Name: HighLatency
Condition: p95_latency > 100ms
Duration: 10 minutes
Action: Send notification
```

### Alert: Service Down

```
Alert Name: ServiceDown
Condition: up{job="sip-calculator-api"} == 0
Duration: 1 minute
Action: Send critical alert
```

---

## Tips for Using the Dashboard

1. **Auto-refresh:** Set to 5-10 seconds during development
2. **Zoom in:** Click and drag on time-series to zoom
3. **Export:** Save dashboards as JSON for version control
4. **Share:** Export dashboard URL for team sharing
5. **Drill-down:** Click on any panel for more details
6. **Customize:** Edit panels to match your needs

---

## Performance Benchmarks

Based on typical SIP calculator requests:

| Metric | Value |
|--------|-------|
| Mean Response Time | 25ms |
| 95th Percentile | 45ms |
| 99th Percentile | 60ms |
| Max Response Time | 87ms |
| Requests/Second (steady) | 8 RPS |
| Error Rate | <1% |
| Availability | 99.9%+ |

---

**Ready to visualize?** Follow the deployment guide to see these dashboards live!
