# Wave 2 — Logging & Observability Analysis

**Date:** 2026-10-04  
**Scope:** Hermes Agent codebase (`/home/aah/.hermes/hermes-agent`)  
**Method:** Source code inspection via grep/read_file across `agent/`, `gateway/`, `tools/`, `cron/`, `hermes_cli/`, `web/`, `tui_gateway/`

---

## Executive Summary

Hermes Agent has a **mature, production-grade logging infrastructure** and a **substantial metrics/health-monitoring layer**, but **lacks structured logging, distributed tracing, and external observability integrations**. The codebase is well-instrumented for debugging via file logs and has a sophisticated OTLP-based gateway health export system, but the agent loop itself has no trace spans, no structured JSON logs, and no SLO-based alerting.

---

## 1. Logging — ✅ Extensive

### Centralized Logging System (`hermes_logging.py` — 980 lines)

| Feature | Status | Details |
|---------|--------|---------|
| Centralized setup | ✅ | `setup_logging()` — idempotent, per-component file handlers |
| Log rotation | ✅ | `RotatingFileHandler` (stdlib) + `ConcurrentRotatingFileHandler` (Windows) |
| Secret redaction | ✅ | `RedactingFormatter` from `agent/redact.py` — secrets never reach disk |
| Async queue | ✅ | `QueueHandler` + `QueueListener` for non-blocking log writes |
| Session context | ✅ | `session_tag` injected via `LogRecordFactory` — every record carries session ID |
| Component routing | ✅ | `COMPONENT_PREFIXES` dict routes to `agent.log`, `gateway.log`, `gui.log`, `cron.log` |
| Noisy logger suppression | ✅ | `_NOISY_LOGGERS` tuple pins httpx/openai/grpc/etc. at WARNING |
| Verbose mode | ✅ | `setup_verbose_logging()` for DEBUG-level with timestamps |
| Windows support | ✅ | Portalocker probe + fallback to stdlib rotation |
| Multi-process safety | ✅ | Cross-process file locking on Windows; profile-scoped log homes |

### Log Files Produced

| File | Level | Scope |
|------|-------|-------|
| `agent.log` | INFO+ | Agent loop, model calls, tool execution |
| `errors.log` | WARNING+ | All warnings and errors |
| `gateway.log` | INFO+ | Gateway adapters, platforms, relay |
| `gui.log` | INFO+ | Dashboard, TUI gateway, desktop |
| `cron.log` | INFO+ | Scheduler, cron jobs |

### Logging Usage Across Codebase

- **agent/** — 40+ modules use `logging.getLogger(__name__)` with appropriate levels
- **gateway/** — Platform adapters, relay, lifecycle all log via standard logging
- **tools/** — Tool execution, browser, environments all log
- **cron/** — Scheduler logs via `setup_logging(mode="cron")`
- **hermes_cli/** — CLI commands, auth, web routers all log

### Structured Logging — ❌ None

```python
# Current format — plain text, not machine-parseable:
_LOG_FORMAT = "%(asctime)s %(levelname)s%(session_tag)s %(name)s: %(message)s"
```

- No JSON formatter, no `structlog`, no `logfmt`, no `python-json-logger`
- No ECS (Elastic Common Schema) or OpenTelemetry semantic conventions
- Log aggregation (Loki, ELK, Splunk) would require custom parsing

---

## 2. Metrics Collection — ✅ Substantial

### Gateway Health Metrics (`agent/monitoring/`)

| Module | Purpose |
|--------|---------|
| `gateway_health.py` | `GatewayHealthSnapshot` — up/active_agents/busy/drainable/restart_requested per platform |
| `gateway_health_export.py` | OTLP export runtime — observable gauges via `MeterProvider` |
| `cron_health.py` | `CronHealthSnapshot` — heartbeat age, last success, catch-up occurrences |
| `events.py` | Typed events: `GatewayHealthEvent`, `GatewayDiagnosticEvent`, `CronExecutionEvent` |
| `emitter.py` | In-process event bus for monitoring events |
| `otlp_exporter.py` | OTLP/HTTP exporter for traces, metrics, and logs |
| `redaction.py` | `redact_bounded()` — bounds and redacts metric attribute values |
| `policy.py` | Monitoring policy configuration |

### Observable Metrics (OTLP Gauges)

```
hermes.gateway.up
hermes.gateway.state
hermes.gateway.active_agents
hermes.gateway.busy
hermes.gateway.drainable
hermes.gateway.restart_requested
hermes.gateway.background_work
hermes.gateway.background_delegations
hermes.platform.up
hermes.platform.degraded
hermes.cron.scheduler.heartbeat_age_seconds
hermes.cron.scheduler.last_success_age_seconds
hermes.cron.scheduler.catch_up_occurrences
hermes.cron.jobs.enabled
hermes.cron.jobs.running
hermes.cron.jobs.overdue
```

### Shared Metrics / Telemetry (`hermes_cli/observability/` — 24 files)

| Feature | Status |
|---------|--------|
| SQLite-backed counter store | ✅ `SharedMetricsStore` with `counter_aggregates` table |
| Daily aggregation | ✅ UTC-day period buckets |
| Delta package export | ✅ Immutable JSON packages with `package_id` |
| Consent gating | ✅ `send_consent_windows` + `consent_marks` tables |
| Install identity | ✅ UUID-based `install_id` |
| Milestone tracking | ✅ Once-ever latches (first run, N days, etc.) |
| Feature adoption | ✅ Once-per-install feature counters |
| Model route tracking | ✅ Per-model call counters |
| Client active heartbeat | ✅ 24-hour rolling window |
| Install snapshot | ✅ Config snapshot once per 24h |
| Send consent | ✅ Explicit intervals with heartbeat confirmation |
| Schema versioning | ✅ `telemetry_state.schema_version` with migrations |
| Outbox pattern | ✅ `package_outbox` with claim tokens, backoff, retry state |
| Local history retention | ✅ 30-day pruning |

### What's Missing in Metrics

- ❌ No per-token cost tracking metrics
- ❌ No rate-limit hit/miss metrics
- ❌ No tool execution duration histograms
- ❌ No model latency percentiles (p50/p95/p99)
- ❌ No queue depth metrics for async delegation
- ❌ No memory usage metrics
- ❌ No error rate metrics by error class

---

## 3. Tracing & Debugging — ⚠️ Limited

### MoA Turn Traces (`agent/moa_trace.py`)

| Feature | Status |
|---------|--------|
| Opt-in trace persistence | ✅ `moa.save_traces` config flag |
| Per-session JSONL traces | ✅ `<hermes_home>/moa-traces/<session_id>.jsonl` |
| Full model I/O capture | ✅ Input messages, output, references |
| Privacy redaction | ✅ Redacted advisor text |
| Failure isolation | ✅ Never breaks a turn — debug-log + swallow |

### OTLP Trace Export

| Feature | Status |
|---------|--------|
| Trace span export | ✅ Via `agent/monitoring/otlp_exporter.py` |
| Gateway health spans | ✅ `EmitterStreamer` subscribes to event bus |
| Diagnostic log spans | ✅ `GatewayDiagnosticLogStreamer` |
| Agent loop spans | ❌ No per-turn or per-tool spans |
| Cross-service tracing | ❌ No trace context propagation |

### Debugging Support

| Feature | Status |
|---------|--------|
| Debug logging | ✅ Pervasive `logger.debug()` with `exc_info=True` |
| Loop liveness watchdog | ✅ `gateway/shutdown_watchdog.py` — dumps all-thread stacks on stall |
| PDB breakpoints | ❌ None in production code |
| Remote debugging | ❌ No debugpy/remote PDB integration |
| Profiling hooks | ❌ No cProfile/py-spy integration points |

---

## 4. Health Check Endpoints — ✅ Multiple Patterns

### API Server (`gateway/platforms/api_server.py`)

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Basic liveness — returns 200 when gateway is up |
| `GET /health/detailed` | Detailed health with component status |
| `GET /api/status` | Full runtime status including `components.storage` |
| `GET /api/sessions` | Session list (uses storage health latch) |

### Readiness Probes (`gateway/readiness.py`)

- `collect_runtime_readiness()` — bounded, non-destructive readiness diagnostics
- Never competes with normal state writers
- Reports storage health, session store status

### Storage Health (`hermes_state_health.py`)

- Process-wide corruption latch per `state.db` path
- `STORAGE_OK` / `STORAGE_CORRUPT` states
- Never clears on its own — recovery boundary is process restart
- Published to `/api/status` → `components.storage`

### Gateway Health Export (`agent/monitoring/gateway_health.py`)

- `GatewayHealthSnapshot` — content-free service-health metrics
- `GatewayDiagnosticLogHandler` — bridges WARNING+ gateway logs to OTLP
- `classify_gateway_error()` — categorizes errors (auth_failed, rate_limited, timeout, network_error, etc.)
- Supervision mode detection: systemd > s6 > container > launchd > manual

### Loop Liveness Watchdog (`gateway/shutdown_watchdog.py`)

- `start_loop_liveness_watchdog()` — asyncio task that probes event loop
- Dumps all thread stacks on consecutive missed probes
- Exit code 75 on liveness failure

### Provider Health (`agent/auxiliary_health.py`)

- Per-provider unhealthy cache with TTL
- `_mark_provider_unhealthy()` / `_is_provider_unhealthy()`
- Rate-limited skip logging (once per minute per provider)

### What's Missing

- ❌ No `/ready` (readiness) endpoint distinct from `/health` (liveness)
- ❌ No health check for individual platform adapters
- ❌ No health check for model provider connectivity
- ❌ No health check for tool execution environments
- ❌ No graceful degradation signaling

---

## 5. Production Observability Gaps

### Critical Gaps

| Gap | Impact | Effort | Recommendation |
|-----|--------|--------|----------------|
| **No structured JSON logging** | Logs unparseable by Loki/ELK/Splunk; no field-based querying | Medium | Add `python-json-logger` or `structlog` with JSON formatter; keep text format for CLI |
| **No distributed tracing** | Cannot trace a turn across model calls, tool execution, compression | High | Add OpenTelemetry spans to agent loop; inject `trace_id` into log records |
| **No SLO-based alerting** | No automated detection of degradation | Medium | Define SLOs (p95 turn latency, error rate, compression failure rate); export to Prometheus |
| **No external log aggregation** | Logs only on local disk; lost on crash/restart | Medium | Add OTLP log export (partially exists for gateway diagnostics only) |
| **No error tracking integration** | No Sentry/Bugsnag for crash aggregation | Low | Add Sentry SDK with redaction hooks |
| **No audit logging** | No security event trail for auth, config changes, tool approval | Medium | Add structured audit log for security-relevant events |
| **No cost tracking** | No per-model/per-token cost visibility | Low | Extend shared metrics with cost counters |
| **No performance profiling** | No visibility into bottlenecks | Medium | Add optional cProfile hooks via CLI flag |

### Medium-Priority Gaps

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| No rate-limit metrics | Cannot detect throttling patterns | Add rate-limit hit/miss counters |
| No tool execution duration | Cannot identify slow tools | Add duration histograms per tool |
| No model latency percentiles | Cannot detect model degradation | Add p50/p95/p99 latency gauges |
| No queue depth metrics | Cannot detect delegation pool exhaustion | Add async delegation pool depth gauge |
| No memory usage metrics | Cannot detect OOM risk | Add RSS/heap gauges |
| No request/response logging | Cannot debug API interactions | Add structured request logging middleware |
| No graceful degradation signal | No way to signal "degraded but alive" | Add `/health?detailed=true` with component states |

### Low-Priority Gaps

| Gap | Impact | Recommendation |
|-----|--------|----------------|
| No remote debugging | Hard to debug production issues | Add debugpy integration behind CLI flag |
| No distributed profiling | Cannot profile across processes | Add py-spy or austin integration |
| No log sampling | High-volume logs may overwhelm | Add configurable sampling for DEBUG logs |
| No log correlation IDs | Hard to follow a request across services | Add `X-Request-ID` propagation |

---

## 6. Structured Logging — ❌ Absent

### Current State

```python
# hermes_logging.py — plain text format
_LOG_FORMAT = "%(asctime)s %(levelname)s%(session_tag)s %(name)s: %(message)s"
_LOG_FORMAT_VERBOSE = "%(asctime)s - %(name)s - %(levelname)s%(session_tag)s - %(message)s"
```

- No JSON output
- No key-value pairs
- No ECS/OpenTelemetry semantic conventions
- No `trace_id` / `span_id` fields
- No `service.name` / `service.version` fields

### What Exists Instead

- `RedactingFormatter` — redacts secrets but outputs plain text
- `session_tag` — `[session_id]` appended to message
- `hermes_home` — attached to LogRecord but not formatted
- Component-based file routing — separate files per component

### Recommendation

Add a JSON formatter option that produces ECS-compatible output:

```json
{
  "@timestamp": "2026-10-04T12:00:00Z",
  "level": "info",
  "service": "hermes-agent",
  "trace_id": "abc123",
  "span_id": "def456",
  "session_id": "sess-789",
  "message": "Model call completed",
  "model": "gpt-4",
  "duration_ms": 1234,
  "tokens": {"input": 500, "output": 200}
}
```

---

## 7. Summary Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| **Logging infrastructure** | 9/10 | Mature, production-grade, multi-process safe |
| **Log redaction** | 9/10 | RedactingFormatter prevents secret leakage |
| **Metrics collection** | 7/10 | Gateway health + shared metrics, but no agent-loop metrics |
| **Health checks** | 8/10 | Multiple patterns, storage health, loop liveness |
| **Tracing** | 3/10 | MoA traces only; no distributed tracing |
| **Structured logging** | 1/10 | Plain text only; no JSON/structured output |
| **External integrations** | 2/10 | OTLP export exists but no Sentry/Datadog/Grafana |
| **Alerting** | 0/10 | No SLO-based alerting |
| **Audit logging** | 2/10 | Ad-hoc audit trails only (curator, cron) |
| **Performance observability** | 2/10 | No profiling, no latency histograms |

**Overall: 4.4/10** — Strong logging foundation, but observability for production operations is incomplete.

---

## 8. Recommended Priority Order

1. **Structured JSON logging** — Highest ROI; enables all log aggregation
2. **Agent loop tracing** — Add OTLP spans for turn execution
3. **SLO-based alerting** — Define and export SLO metrics
4. **External log aggregation** — OTLP log export for all components
5. **Error tracking** — Sentry integration
6. **Audit logging** — Structured security event trail
7. **Cost tracking** — Per-model cost metrics
8. **Performance profiling** — Optional profiling hooks
