# Wave 2: pyproject.toml Completeness Analysis

**File:** `/home/aah/.hermes/hermes-agent/pyproject.toml`  
**Lines:** 941  
**Size:** 48,360 bytes  
**Date:** 2026-10-04

---

## 1. File Read — Summary

The `pyproject.toml` is a comprehensive, well-documented build and dependency configuration for the `hermes-agent` project. It uses:

- **Build backend:** `setuptools.build_meta` (with `setuptools==83.0.0` + `wheel`)
- **Package discovery:** `[tool.setuptools.packages.find]` with explicit include list
- **Entry points:** 3 console scripts (`hermes`, `hermes-agent`, `hermes-acp`)
- **Tool configs:** pytest, ruff, ty, uv, setuptools

---

## 2. Dependencies Verification

### Core Dependencies (`[project].dependencies`)

**Status: COMPLETE — 40+ direct dependencies, all exact-pinned**

| Category | Packages |
|----------|----------|
| HTTP/Network | `httpx[socks]`, `requests`, `urllib3`, `certifi`, `truststore` |
| AI/LLM | `openai`, `pydantic`, `firecrawl-anydoc` |
| CLI/UI | `rich`, `prompt_toolkit`, `fire`, `python-dotenv` |
| Web Framework | `fastapi`, `uvicorn`, `httptools`, `watchfiles`, `python-multipart` |
| Document Processing | `firecrawl-anydoc`, `jinja2`, `Markdown`, `ruamel.yaml` |
| Security/Crypto | `cryptography`, `PyJWT[crypto]` |
| Browser/CDP | `websockets`, `browser-harness` |
| Image Processing | `Pillow`, `pillow-heif`, `resvg-py` |
| Scheduling | `croniter` |
| System | `psutil`, `ptyprocess`, `pywinpty`, `pywin32` |
| Windows-specific | `winrt-*` (4 packages), `concurrent-log-handler` |
| Native runtime | `nemo-relay` (platform-gated) |

**Pinning policy:** All core deps use exact `==X.Y.Z` pins (no ranges). Rationale documented in comments — supply-chain attack prevention after the Mini Shai-Hulud worm incident (2026-05-12).

### Optional Dependencies (`[project.optional-dependencies]`)

**Status: COMPLETE — 30+ extras defined**

Key extras: `anthropic`, `exa`, `firecrawl`, `parallel-web`, `ddgs`, `fal`, `edge-tts`, `messaging`, `matrix`, `mcp`, `web`, `voice`, `wake`, `google`, `youtube`, `telegram`, `discord`, `slack`, `dingtalk`, `feishu`, `bedrock`, `vertex`, `azure-identity`, `langfuse`, `otlp`, `mem0`, `computer-use`, `acp`, `mistral`, `modal`, `daytona`, `vercel`, `google-meet`, `teams`, `sms`, `wecom`, `tts-premium`, `silk`, `doc-extract`, `trace-upload`, `uvloop`, `piper`, `neutts`, `kittentts`, `termux`, `termux-all`, `all`.

**Notable:** The `[all]` extra follows a strict policy — only includes extras that genuinely cannot be prepared on demand by PM. Opt-in backends are lazy-installed.

### Dependency Groups (`[dependency-groups]`)

**Status: COMPLETE**

- `dev`: `debugpy`, `pytest`, `pytest-asyncio`, `mcp`, `httpx2`, `starlette`, `ty`, `ruff`, `setuptools`
- `test`: `distlib` (win32), `anthropic`

---

## 3. Pytest Configuration

**Status: CORRECT**

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
  "integration: marks tests requiring external services",
  "live: secrets-gated canaries against REAL LLM provider APIs",
  "real_concurrent_gate: opt out of the autouse stub",
  "real_agent_prewarm: opt out of the autouse stub",
  "real_retry_backoff: opt out of the autouse stub",
  "requires_wal: needs the runtime to actually enable SQLite WAL mode",
  "no_isolate: opt out of per-file subprocess isolation",
  "ssh: marks tests requiring a reachable SSH server",
  "platforms(*specs, arch=None, arch_negate=False): run only on hosts matching",
]
addopts = "-m 'not integration and not live'"
```

**Assessment:**
- `testpaths` correctly points to `tests/`
- 9 custom markers defined for fine-grained test selection
- Default addopts exclude `integration` and `live` tests (costly/network-dependent)
- `pytest-asyncio==1.3.0` is in dev dependencies
- No issues found

---

## 4. Mypy/Ruff Configuration

### Mypy

**Status: NOT PRESENT**

No `[tool.mypy]` section exists in `pyproject.toml`. The project does not use mypy for type checking.

### Ruff

**Status: PRESENT — Configured**

```toml
[tool.ruff]
preview = true

[tool.ruff.lint]
select = ["PLW1514", "ASYNC210", "ASYNC220", "ASYNC221", "ASYNC251", "TID251"]
```

**Assessment:**
- Only 6 rules selected (most lints intentionally disabled)
- `PLW1514` (unspecified-encoding) — load-bearing for Windows encoding safety
- `ASYNC210/220/221/251` — blocking calls in async functions (event loop freeze prevention)
- `TID251` — banned API usage (PM internal APIs)
- Per-file ignores for `pm/**`, `tests/**`, `skills/**`, `plugins/**`, and specific legacy files
- `ruff==0.15.10` pinned in dev dependencies

### Ty (Alternative Type Checker)

**Status: PRESENT**

```toml
[tool.ty.environment]
python-version = "3.13"

[tool.ty.rules]
unknown-argument = "warn"
redundant-cast = "ignore"
```

The project uses `ty` (Astral's type checker) instead of mypy, with `ty==0.0.82` in dev dependencies.

---

## 5. Package Discovery — `src/acquisition_platform`

**Status: NOT APPLICABLE**

- **No `src/` directory exists** in the repository
- **No `acquisition_platform` package exists** anywhere in the codebase
- The project uses a **flat layout** with packages at the root:
  - `agent/`, `tools/`, `hermes_cli/`, `gateway/`, `tui_gateway/`, `cron/`, `acp_adapter/`, `plugins/`, `providers/`, `hermes_platform/`, `pm/`
- `[tool.setuptools.packages.find]` explicitly includes these root-level packages
- `setup.py` dynamically derives root single-file modules (e.g., `run_agent.py`, `hermes_state.py`, `toolsets.py`) via `_root_py_modules()`

**Conclusion:** The `src/acquisition_platform` path is not relevant to this repository. The project does not use a `src/` layout.

---

## 6. Missing Dev Dependencies

**Status: COMPLETE — No critical gaps**

Present in `[dependency-groups].dev`:
- `pytest==9.1.1` — test runner
- `pytest-asyncio==1.3.0` — async test support
- `ruff==0.15.10` — linter
- `ty==0.0.82` — type checker
- `debugpy==1.8.20` — debugger
- `setuptools==83.0.0` — build tool
- `mcp==2.0.0`, `httpx2==2.7.0`, `starlette==1.3.1` — test fixtures for MCP/computer-use

**Potentially missing (minor):**
- No `pytest-cov` / `coverage` — no coverage reporting configured
- No `pytest-xdist` — no parallel test execution
- No `pre-commit` — no pre-commit hook framework
- No `bandit` or `safety` — no security linting in dev deps
- No `vulture` or `pyflakes` — no dead code detection

These are minor gaps; the project relies on `ruff` for linting and `ty` for type checking.

---

## 7. Python Version Requirement

**Status: CORRECT**

```toml
requires-python = ">=3.11,<3.15"
```

**Assessment:**
- **Lower bound (`>=3.11`):** Serves as an install bridge for pre-PM updaters on older Python. The updater contract (see `tests/compat/README.md`) allows old Hermes installs on <3.14 to get through their update step.
- **Upper bound (`<3.15`):** 3.14 is the newest Python with known wheel availability for all dependencies.
- **Comment rationale:** "3.14 is the newest python we know we have wheels for. We *only* support 3.14, BUT we need to allow old hermes installs on <3.14 to get thru their update step on old python."
- **uv environment:** `environments = ["python_version >= '3.14'"]` — the lock file covers 3.14 only
- **ty environment:** `python-version = "3.13"` — type checking targets 3.13

**Note:** The `requires-python` range is intentionally wider than the actual runtime target (3.14) to support the updater bridge pattern.

---

## Summary Table

| Check | Status | Notes |
|-------|--------|-------|
| Dependencies listed | COMPLETE | 40+ core deps, all exact-pinned; 30+ extras |
| Pytest config | CORRECT | testpaths, 9 markers, addopts exclude integration/live |
| Mypy config | NOT PRESENT | Project uses `ty` instead |
| Ruff config | PRESENT | 6 rules selected, per-file ignores configured |
| Package discovery (src/acquisition_platform) | N/A | No src/ layout; flat root-level packages |
| Missing dev dependencies | MINOR GAPS | No coverage, parallel exec, pre-commit, security linting |
| Python version requirement | CORRECT | >=3.11,<3.15 (3.14 is runtime target) |

---

## Overall Assessment

The `pyproject.toml` is **production-grade and exceptionally well-documented**. Every dependency pin has a rationale comment. The configuration reflects a mature project with strong supply-chain security practices (exact pins, exclude-newer, override-dependencies). The only notable absence is mypy (replaced by `ty`) and some standard dev tooling (coverage, pre-commit). No critical issues found.
