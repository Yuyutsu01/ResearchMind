# Observability & Monitoring Architecture

ResearchMind features a production-grade telemetry pipeline powered by Prometheus metrics collection, Sentry error tracking, latency histograms, token usage counters, and Grafana dashboard visualization.

---

## 1. Metrics Endpoint (`/metrics`)

The FastAPI backend exposes Prometheus-formatted metrics at **`http://localhost:8001/metrics`**:

### Collected Metrics Matrix

| Metric Name | Type | Description |
| :--- | :--- | :--- |
| `api_requests_total` | Counter | Total HTTP API request count partitioned by `method`, `endpoint`, and `status`. |
| `api_request_duration_seconds` | Histogram | Request latency histogram for HTTP operations. |
| `llm_requests_total` | Counter | LLM API completions count grouped by `provider` and `model`. |
| `llm_request_duration_seconds` | Histogram | Latency histogram for external LLM API calls. |
| `llm_tokens_total` | Counter | Token counter tracked by `provider`, `model`, and `token_type` (`prompt` vs `completion`). |
| `agent_failures_total` | Counter | Swarm agent task failure counts. |
| `cache_hits_total` / `cache_misses_total` | Counter | L1 Redis cache performance hit/miss counts. |
| `db_query_duration_seconds` | Histogram | PostgreSQL query execution duration. |
| `embedding_duration_seconds` | Histogram | Qdrant vector embedding calculation duration. |

---

## 2. Infrastructure Setup & Dashboards

### 2.1 Prometheus Scraping
Prometheus scrapes the API server every 15 seconds as configured in `deploy/prometheus.yml`:
* Access Prometheus UI at **`http://localhost:9090`**

### 2.2 Grafana Dashboards
Grafana runs as part of the `docker-compose` stack:
* Access Grafana UI at **`http://localhost:3000`**
* Default Credentials: User `admin`, Password `admin`
* Connect Prometheus datasource targeting `http://prometheus:9090`.

### 2.3 Sentry Error Tracking
Configure `SENTRY_DSN` in your `.env` file to send backend exception tracebacks and error events directly to your Sentry dashboard.
