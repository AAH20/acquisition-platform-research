# Wave 2: Database & Persistence Gaps

**Date:** 2026-10-04  
**Scope:** Hermes Agent codebase — database integration, ORM, data access layer, migration system, and missing persistence patterns

---

## 1. Database Integration

### 1.1 Primary Database: SQLite (state.db)

The **core persistence engine** is SQLite via Python's stdlib `sqlite3` module. There is **no external database server** (PostgreSQL, MySQL, etc.) in the core architecture.

**Key files:**
- `hermes_state.py` — Main `SessionDB` class (1695 lines), the central state store
- `hermes_state_schema.py` — Schema DDL, column reconciliation, FTS management (1367 lines)
- `hermes_state_dbfile.py` — File-level health helpers, WAL management, quarantine (849 lines)
- `hermes_state_common.py` — Shared constants, `SCHEMA_SQL` DDL, `SCHEMA_VERSION` (1328 lines)
- `hermes_state_registry.py` — Process-wide shared SessionDB registry with refcounting (478 lines)
- `hermes_state_fts.py` — FTS5 full-text search setup
- `hermes_state_wal.py` — WAL mode management
- `hermes_state_holders.py` — Cross-process holder detection
- `hermes_state_lockguard.py` — Lock guard
- `hermes_state_lockowners.py` — Write lock holder logging
- `hermes_state_errors.py` — Persistence error classification
- `hermes_state_health.py` — Storage health monitoring
- `hermes_state_repair.py` — DB repair utilities
- `hermes_state_portability.py` — DB portability
- `hermes_state_readpool.py` — Read pool management
- `hermes_state_coverage.py` — Coverage tracking
- `hermes_state_rewind.py` — Session rewind
- `hermes_state_titles.py` — Title management
- `hermes_state_usage.py` — Usage tracking
- `hermes_state_maintenance.py` — Maintenance operations
- `hermes_state_gateway.py` — Gateway routing
- `hermes_state_compression.py` — Compression
- `hermes_state_search.py` — Search
- `hermes_state_sessions.py` — Session management
- `hermes_state_messages.py` — Message operations
- `hermes_state_telegram.py` — Telegram topic bindings
- `hermes_state_profile_repair.py` — Profile repair
- `hermes_state_timeline.py` — Timeline queries
- `hermes_state_pidns.py` — PID namespace tracking

**Architecture:** The `SessionDB` class uses a **mixin pattern** — 20+ mixin classes are composed into one god-class via MRO. This is a deliberate design choice to keep individual modules manageable while sharing a single connection.

**Database location:** `~/.hermes/state.db` (per-profile)

**Schema version:** Currently at `SCHEMA_VERSION` (v30+ based on migration chain)

### 1.2 Secondary SQLite Databases

| Database | Location | Purpose | Schema Management |
|----------|----------|---------|-------------------|
| `kanban.db` | `<root>/kanban.db` or `<root>/kanban/boards/<slug>/` | Kanban board tasks, events, attachments | Inline DDL in `hermes_cli/kanban_db.py` (4585 lines) |
| `runs_idempotency.db` | `<root>/runs_idempotency.db` | API run idempotency reservations | Inline DDL in `gateway/platforms/api_server_run_idempotency.py` |
| `data.db` | `<hermes_home>/plugin-data/<name>/` | Per-plugin generic storage | `plugins/plugin_storage.py` — `plugin_db()` helper |
| `discord_messages` | Plugin-specific | Discord message recovery | `plugins/platforms/discord/recovery.py` |
| `facts_fts` | Plugin-specific | Holographic memory facts | `plugins/memory/holographic/store.py` |
| RetainDB queue | Plugin-specific | Write-behind queue for RetainDB cloud | `plugins/memory/retaindb/__init__.py` |

### 1.3 Non-SQLite Persistence

| Store | Format | Location | Purpose |
|-------|--------|----------|---------|
| Cron jobs | JSON | `~/.hermes/cron/jobs.json` | Scheduled job definitions |
| Cron output | Markdown | `~/.hermes/cron/output/{job_id}/{timestamp}.md` | Job execution output |
| Cron audit | JSONL | `~/.hermes/cron/usage_audit.jsonl` | Usage audit trail |
| Cron errors | JSONL | `~/.hermes/cron/persisted_error_recoveries.jsonl` | Error recovery log |
| Cron TZ migration | JSONL | `~/.hermes/cron/timezone_migration_catchups.jsonl` | TZ migration tracking |
| Sessions mirror | JSON | `~/.hermes/sessions/sessions.json` | Legacy routing index mirror |
| Skill ledger | JSON | Various | Skill usage tracking |
| MCP OAuth | JSON | `~/.hermes/` | OAuth token storage |
| Checkpoint | Git repos | Various | Shadow git repos for checkpoints |
| Web result cache | In-memory | Process-local | Search result memo |

### 1.4 External Database Dependencies (Optional)

- **PostgreSQL/pgvector**: Used optionally by the Mem0 memory plugin for vector storage (`plugins/memory/mem0/_backend.py` — `psycopg2` import)
- **Qdrant**: Used optionally by Mem0 for vector storage
- **Chroma**: Used optionally by Mem0 for vector storage
- **RetainDB Cloud**: External API with SQLite write-behind queue

---

## 2. ORM (Object-Relational Mapping)

### **No ORM is used anywhere in the codebase.**

- **No SQLAlchemy** — not in dependencies, not imported
- **No Alembic** — no migration tool
- **No Peewee, Tortoise, Django ORM, or any other ORM**
- **No `databases` library** (async ORM)

All database access uses **raw SQL via Python's stdlib `sqlite3` module**. The `pyproject.toml` includes `aiosqlite` and `asyncpg` as optional dependencies, but these are not used for ORM purposes — `aiosqlite` provides async SQLite access, and `asyncpg` is for the optional PostgreSQL vector store.

**Implications:**
- All SQL is hand-written string literals
- No query builder, no model definitions, no relationship mapping
- Schema changes require manual DDL and migration code
- No type safety at the database boundary
- No connection pooling (managed manually via `hermes_state_registry`)

---

## 3. Data Access Layer (DAL)

### **No formal data access layer exists.**

The codebase uses a **mixin-based composition pattern** instead of a traditional DAL:

**Pattern:** `SessionDB` is composed of 20+ mixin classes, each providing a domain-specific set of methods that directly execute SQL:

```
SessionDB = SessionSchemaMixin + SessionMessagesMixin + SessionSessionsMixin + 
            SessionFtsSetupMixin + SessionSearchMixin + SessionCompressionMixin + 
            SessionRewindMixin + SessionTitlesMixin + SessionUsageMixin + 
            SessionMaintenanceMixin + SessionGatewayMixin + SessionCoverageMixin + 
            SessionPortabilityMixin + SessionTelegramTopicsMixin + SessionProfileRepairMixin
```

**Characteristics:**
- **No repository pattern** — no `Repository` or `DAO` classes
- **No unit of work** — transactions are managed ad-hoc via `BEGIN IMMEDIATE`
- **No query abstraction** — each method writes its own SQL
- **No data mapper** — rows are returned as raw tuples or converted to dicts inline
- **No connection pooling** — single shared connection per path via registry
- **No prepared statement cache** — SQL strings are constructed per-call

**Positive aspects:**
- The mixin pattern keeps related SQL operations colocated with their domain logic
- The registry (`hermes_state_registry.py`) provides connection lifecycle management
- WAL mode enables concurrent reads with single writer
- Cross-process locking is well-implemented

**Gaps:**
- No abstraction means SQL is scattered across 20+ files
- No way to swap storage backends (e.g., PostgreSQL for large deployments)
- No query logging or performance monitoring layer
- No data validation at the persistence boundary

---

## 4. Modules Needing Persistent Storage

### 4.1 Well-Served by SQLite (state.db)

| Module | Tables | Status |
|--------|--------|--------|
| Session management | `sessions`, `messages`, `system_prompts` | ✅ Complete |
| Full-text search | `messages_fts`, `messages_fts_trigram`, `messages_fts_cjk` | ✅ Complete |
| Model usage tracking | `session_model_usage` | ✅ Complete |
| Gateway routing | `gateway_routing` | ✅ Complete |
| Compression state | `compression_locks`, `session_turn_leases` | ✅ Complete |
| Async delegations | `async_delegations` | ✅ Complete |
| Gateway heartbeats | `gateway_heartbeats` | ✅ Complete |
| Conversation generations | `conversation_generations` | ✅ Complete |
| Gateway hygiene | `gateway_hygiene_state` | ✅ Complete |
| Telegram topics | `telegram_dm_topic_bindings` | ✅ Complete |

### 4.2 Using Separate SQLite Databases

| Module | Database | Status |
|--------|----------|--------|
| Kanban | `kanban.db` | ✅ Complete (tasks, events, attachments, comments, links, runs) |
| API idempotency | `runs_idempotency.db` | ✅ Complete |
| Plugin storage | `plugin-data/<name>/data.db` | ✅ Generic helper available |
| Discord recovery | Plugin DB | ✅ Complete |
| Holographic memory | Plugin DB | ✅ Complete (facts, entities, FTS) |

### 4.3 Using File-Based Persistence (No Database)

| Module | Format | Gap |
|--------|--------|-----|
| Cron jobs | `jobs.json` | ⚠️ JSON file, no concurrent write safety beyond file locking |
| Cron output | Markdown files | ✅ Appropriate for append-only output |
| Cron audit | JSONL | ✅ Appropriate for append-only audit |
| Sessions mirror | `sessions.json` | ⚠️ Legacy mirror, being replaced by `gateway_routing` table |
| Skill ledger | JSON | ⚠️ No concurrent access protection |
| MCP OAuth | JSON | ⚠️ Token storage in JSON files |
| Web result cache | In-memory only | ❌ Lost on restart |
| Process registry | In-memory + JSON | ⚠️ Partial persistence |
| Checkpoint manager | Git repos | ✅ Appropriate (version control) |

### 4.4 Modules with In-Memory Only State (Potential Gaps)

| Module | State | Risk |
|--------|-------|------|
| `gateway/session_transcript.py` | `_MAX_PENDING_PER_SESSION = 200` in-memory pending messages | ❌ Lost on crash |
| `gateway/run.py` | `_consecutive_timeout_failures` counter | ❌ Lost on restart |
| `tools/web_result_cache.py` | Search memo cache | ❌ Lost on restart |
| `gateway/platforms/whatsapp_cloud.py` | Webhook dedup state (FIFO-evicted) | ❌ Lost on restart |
| `gateway/platforms/api_server.py` | `_IdempotencyCache` | ❌ In-memory fallback when DB unavailable |
| `tools/approval_detection.py` | Approval state | ⚠️ May be ephemeral by design |
| `cron/jobs.py` | `_fire_fence_locks` | ⚠️ In-process only, cross-process via file lock |
| `gateway/run_delivery_queue_watch.py` | Delivery queue watch | ⚠️ In-memory |
| `tools/delegation_live_log.py` | Live log stream | ⚠️ Ephemeral by design |

---

## 5. Migration System

### 5.1 Schema Migration Mechanism

The codebase uses a **version-gated migration chain** in `hermes_state_schema.py`:

```python
SCHEMA_VERSION = 30  # Current version

def _run_data_migrations(cursor, current_version, fts5_available):
    if current_version < 16:  # v16: delegate subagent tagging
    if current_version < 18:  # v18: gateway metadata backfill
    if current_version < 20:  # v20: session_model_usage seed
    if current_version < 22:  # v22: task dimension in PK
    if current_version < 23:  # v23: FTS storage redesign (opt-in)
    if current_version < 25:  # v25: system prompt deduplication
    if current_version < 30:  # v29/v30: trigram cron/subagent exclusion
```

**Migration types:**
1. **Declarative column reconciliation** — `_reconcile_columns()` adds missing columns automatically
2. **Version-gated data migrations** — Row backfills and transformations
3. **Table rebuilds** — For PK changes (SQLite cannot ALTER PK)
4. **FTS storage migrations** — Opt-in via `hermes sessions optimize-storage`

### 5.2 Migration Characteristics

| Aspect | Implementation |
|--------|---------------|
| Version tracking | `schema_version` table |
| Column additions | Declarative via `_reconcile_columns()` |
| Data migrations | Version-gated in `_run_data_migrations()` |
| Table rebuilds | `_rebuild_table()` with RENAME + CREATE + COPY + DROP |
| FTS migrations | Separate `fts_storage_version` marker |
| Cross-process safety | `fts_rebuild_admission()` context manager |
| Rollback | Savepoints for repair operations |
| Concurrency | WAL mode + `BEGIN IMMEDIATE` for writes |

### 5.3 Migration Gaps

| Gap | Impact |
|-----|--------|
| **No Alembic or similar tool** | All migrations are hand-written Python |
| **No migration testing framework** | Migrations tested only via integration tests |
| **No schema diff tool** | No way to verify schema matches expected |
| **No automatic migration on version mismatch** | Must be triggered at startup |
| **No migration history log** | Only current version stored, no audit trail |
| **No downgrade path** | Migrations are forward-only |
| **No migration dry-run** | Cannot preview migration effects |
| **Cron jobs.json has no schema version** | TZ migration is ad-hoc, not versioned |
| **Plugin DBs have no migration system** | Each plugin manages its own schema |
| **No schema validation** | No runtime check that schema matches code expectations |

---

## 6. Missing Data Persistence Patterns

### 6.1 No Unit of Work Pattern

Transactions are managed ad-hoc. Each method that needs atomicity must explicitly use `BEGIN IMMEDIATE` / `COMMIT` / `ROLLBACK`. There is no context manager for transactions.

### 6.2 No Repository Pattern

Every mixin directly executes SQL. There is no abstraction layer between business logic and data access. This means:
- Business logic is coupled to SQL
- Cannot easily swap storage backends
- Cannot mock the data layer for testing without mocking `sqlite3`

### 6.3 No Data Validation at Persistence Boundary

Rows are inserted/updated without schema validation. Type checking happens at the SQLite level (loosely typed), not at the application level.

### 6.4 No Connection Pooling

The registry provides one connection per path, but there is no pool for read scaling. All reads go through the same connection.

### 6.5 No Query Builder

All SQL is string concatenation or f-strings. This is a SQL injection risk if user input is not properly parameterized (though most queries do use parameterized statements).

### 6.6 No Audit Trail for Data Changes

There is no general audit log for data modifications. The `state_meta` table stores some metadata, but there is no row-level audit.

### 6.7 No Soft Delete

Most tables use hard deletes. The `messages` table has an `active` flag for soft deletion, but this is not a general pattern.

### 6.8 No Data Retention Policy

There is no automatic data retention or archival mechanism. Old messages and sessions accumulate indefinitely unless manually cleaned.

### 6.9 No Encryption at Rest

The SQLite database is not encrypted. Sensitive data (session content, credentials in `state_meta`) is stored in plaintext.

### 6.10 No Backup Integration

There is no built-in backup system. The `hermes_cli/backup.py` module exists but is not integrated with the database layer.

### 6.11 No Read Replicas

There is no read replica support. All reads go through the single writer connection.

### 6.12 No Database Health Monitoring

While `hermes_state_health.py` exists, there is no continuous health monitoring or alerting for database issues.

### 6.13 No Schema Documentation

The schema is defined in `SCHEMA_SQL` string in `hermes_state_common.py`, but there is no generated documentation or ER diagram.

### 6.14 No Data Migration Testing

There is no framework for testing data migrations. The `evals/` directory has some test scripts, but no systematic migration testing.

### 6.15 No Concurrent Write Safety for Non-DB Stores

The cron `jobs.json` uses file locking, but other JSON-based stores (skill ledger, MCP OAuth) do not have concurrent write protection.

### 6.16 No Data Compression

Message content is stored as plain text. There is no compression for large content (though there is a `_compressed_summary` flag for summaries).

### 6.17 No Full-Text Search for Non-Session Data

FTS5 is used for session messages but not for other data (kanban tasks, cron output, etc.).

### 6.18 No Data Export/Import Standard

There is no standard format for exporting and importing data. The `hermes_state_portability.py` module handles some cases, but there is no general export format.

---

## 7. Summary of Key Findings

### Strengths
1. **Robust SQLite implementation** — WAL mode, cross-process locking, FTS5, quarantine
2. **Sophisticated migration chain** — Version-gated with declarative column reconciliation
3. **Process-wide registry** — Refcounted shared connections with generation-aware retirement
4. **Comprehensive error handling** — `hermes_state_errors.py` classifies persistence errors
5. **File-level health monitoring** — Header probes, WAL sidecar tracking, holder detection

### Critical Gaps
1. **No ORM** — All raw SQL, no abstraction
2. **No data access layer** — Mixin pattern couples business logic to SQL
3. **No migration tooling** — Hand-written migrations, no Alembic
4. **No data validation** — No schema validation at persistence boundary
5. **No encryption at rest** — Sensitive data in plaintext
6. **No backup integration** — No built-in backup system
7. **No data retention** — No automatic archival
8. **No audit trail** — No row-level audit log
9. **No connection pooling** — Single connection per path
10. **In-memory state loss** — Several modules lose state on crash/restart

### Risk Areas
1. **SQL injection** — String concatenation in some queries (mitigated by parameterized statements in most cases)
2. **Concurrent writes** — Non-DB stores lack proper locking
3. **Data loss** — In-memory state in gateway, web cache, WhatsApp dedup
4. **Schema drift** — No runtime schema validation
5. **Migration failures** — No rollback mechanism for failed migrations
6. **Scalability** — Single writer connection may become bottleneck
7. **Security** — No encryption, sensitive data in plaintext

---

## 8. Recommendations

### High Priority
1. **Add a lightweight data access layer** — Even a simple repository pattern would decouple business logic from SQL
2. **Implement data validation** — Add schema validation at the persistence boundary
3. **Add encryption at rest** — Use SQLCipher or similar for sensitive data
4. **Implement backup integration** — Add automated backup for state.db
5. **Add data retention policies** — Implement automatic archival of old sessions

### Medium Priority
6. **Add migration testing framework** — Systematic testing of schema migrations
7. **Implement audit trail** — Row-level audit log for data changes
8. **Add connection pooling** — For read scaling
9. **Document schema** — Generate ER diagram and schema documentation
10. **Add health monitoring** — Continuous database health checks

### Low Priority
11. **Consider ORM for new features** — SQLAlchemy or Peewee for new modules
12. **Add read replicas** — For read-heavy deployments
13. **Implement soft delete** — General pattern for data retention
14. **Add data compression** — For large content
15. **Standardize export/import** — General data export format
