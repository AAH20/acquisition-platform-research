# W2 — API & Serialization Gap Analysis

**Scope:** `acquisition-platform-research` (`src/acquisition_platform/`, 8 modules, 1,911 LOC source + tests)
**Date:** 2026-10-04
**Method:** Static read of every source/test file, `pyproject.toml`, docs, and dependency manifest; grep sweep for web/RPC/serde/validation patterns.

---

## Executive Summary

The project is a **pure Python library with no service surface whatsoever**. It exposes 8 NP-hard solver classes through a single `__init__.py` re-export. There is **no REST API, no JSON serialization, no web framework, no CLI, no request/response validation, and no API documentation**.

The most important finding is a **docs/code mismatch**: `docs/wiki/architecture.md:15` explicitly states the system has an *"API Layer — REST API, MCP server, WebSocket"*, and `docs/archify-system.html` renders an "API Layer (REST, MCP, WebSocket)" component — but **none of this exists in code**. The README's "API Reference" section is only a dataclass field table, not an HTTP contract.

This is a library-to-platform gap, not a bug: the solvers are sound and tested (62 tests), but they are unreachable by anything other than a direct Python `import`.

---

## (1) REST API Endpoints

**Finding: NONE.**

- No route definitions anywhere: zero matches for `@app.get/post/put/delete`, `@app.route`, `APIRouter`, `add_url_rule`, `BaseHTTPRequestHandler`.
- No web framework dependency. `pyproject.toml` `[project.optional-dependencies] dev` = pytest, pytest-cov, mypy, ruff only. No FastAPI/Flask/Django/aiohttp/Starlette/uvicorn/gunicorn.
- No HTTP server, no socket code, no `urllib`/`httpx`/`requests` usage in `src/`.
- No `__main__.py`, no `console_scripts`/`entry_points` in `pyproject.toml` → `python -m acquisition_platform` is a no-op.

The only "interface" is `src/acquisition_platform/__init__.py:9-21`, which re-exports classes for Python consumers.

---

## (2) JSON Serialization / Deserialization

**Finding: NONE.**

- Zero matches across `src/` and `tests/` for `json.dumps/loads/dump/load`, `jsonify`, `JSONEncoder/Decoder`, `asdict`, `astuple`, `fields()`, `model_dump`, `model_validate`, `to_dict`, `from_dict`, `__dict__`, `marshmallow`, `pydantic`.
- All 14 data types are plain `@dataclass` (e.g. `Buyer`, `Seller`, `Match`, `ValuationResult`, `FraudScore`, `Asset`, `Portfolio`, `PriceRecommendation`, `EntityCluster`, `Listing`, `RankedListing`, `Benchmark`, `EvolutionResult`, `EvaluationResult`). They have **no wire format** — no way to convert to/from JSON, MessagePack, or any external representation.
- Untyped `dict`/`list` fields are the core serialization risk:
  - `matching.py:31` — `Buyer.preferences: dict` (untyped)
  - `matching.py:40` — `Seller.attributes: dict` (untyped)
  - `search_ranking.py:44` — `user_preferences: dict | None` (untyped)
  - `fraud_detection.py:10` — `from typing import Any`; `analyze_graph(graph: dict[str, Any])` (untyped)
  - `entity_resolution.py:33,41` — `entities: list[dict]` (untyped)
  These cannot be validated, versioned, or safely deserialized without a schema.

---

## (3) FastAPI / Flask App

**Finding: NONE.**

- No `FastAPI(...)`, `Flask(...)`, `APIRouter`, `make_app`, `create_app`, `app =` anywhere (grep across all `.py`/`.toml`).
- No ASGI/WSGI entry point, no `uvicorn`/`gunicorn`/`waitress` reference.
- `pyproject.toml` build backend is `setuptools.build_meta` with `[tool.setuptools.packages.find] where = ["src"]` — a library layout, not an app layout. No `[project.scripts]` table.

---

## (4) Modules Needing Service Exposure

**Finding: All 8 solver modules are unreachable outside Python.**

| Module | Class(es) | Current exposure | Missing to be a service |
|---|---|---|---|
| `matching.py` | `BuyerSellerMatcher` | Python import only | HTTP/gRPC endpoint, request/response DTOs |
| `valuation.py` | `ValuationEngine` | Python import only | Endpoint + input validation (rates, years) |
| `fraud_detection.py` | `FraudDetector` | Python import only | Endpoint + signal schema |
| `portfolio_optimizer.py` | `PortfolioOptimizer` | Python import only | Endpoint + budget/asset validation |
| `dynamic_pricing.py` | `PricingEngine` | Python import only | Endpoint + enum validation (`market_condition`) |
| `entity_resolution.py` | `EntityResolver` | Python import only | Endpoint + entity-dict schema |
| `search_ranking.py` | `SearchRanker` | Python import only | Endpoint + query validation |
| `evolution.py` | `EvolutionEngine`, `Benchmark` | Python import only | Endpoint + fitness-fn serialization problem |

The architecture diagram (`docs/wiki/architecture.md:22-24`) shows `User → API Layer → Core Engine → Storage`, but the entire `API Layer` and `Storage Layer` are **aspirational** — only the Core Engine exists.

**Note on `EvolutionEngine.evolve`** (`evolution.py:94-98`): it accepts a `fitness_fn: Callable[[float], float]`. A function pointer is **not serializable** and cannot cross a process boundary — this method is fundamentally un-exposable as a remote call without a registry/DSL for fitness functions.

---

## (5) Request / Response Validation

**Finding: NONE.**

- Zero matches in `src/` for `raise ValueError`, `raise TypeError`, `assert`, `isinstance(`, `try:/except`, or any validation helper.
- Inputs are trusted blindly. Examples of unvalidated, dangerous inputs:
  - `valuation.py:38-45` `dcf_valuation(... discount_rate, terminal_growth ...)` — no check that `discount_rate > terminal_growth` (line 68 divides by `discount_rate - terminal_growth` → `ZeroDivisionError` or negative value if violated).
  - `dynamic_pricing.py:26-32` `recommend_price(... market_condition: str)` — silently falls back to multiplier `1.0` for any unknown string (line 52); no enum/range check on `demand_level`/`competition_level` (documented [0,1] but unenforced).
  - `portfolio_optimizer.py:44` `PortfolioOptimizer(budget, max_assets)` — no guard against negative budget or `max_assets <= 0`.
  - `fraud_detection.py:50` `score(signals)` — no check for duplicate signal names or out-of-range values.
- `pyproject.toml` sets `[tool.mypy] strict = true`, but that is **static** type checking only — it does no runtime validation and does not serialize.

---

## (6) API Documentation (OpenAPI / Swagger)

**Finding: NONE.**

- No OpenAPI/Swagger spec file (no `openapi.yaml`, `swagger.yaml`, `.json` spec).
- No Swagger UI, no Redoc, no `/docs` route.
- README `## API Reference` (`README.md:588`) is a **data-types table** mapping dataclass fields to modules — it documents Python class signatures, not HTTP endpoints, request/response schemas, status codes, or examples.
- No endpoint documentation, no error-code catalog, no versioning scheme.

---

## Consolidated Gap Matrix

| # | Gap | Severity | Evidence |
|---|---|---|---|
| 1 | No REST/RPC/HTTP surface at all | **Critical** | grep: zero web framework/handler matches |
| 2 | No JSON (or any) serde for dataclasses | **Critical** | zero `json`/`asdict`/`model_dump` matches |
| 3 | No web framework / app entry point | **Critical** | `pyproject.toml` has no deps/scripts; no `__main__.py` |
| 4 | Docs promise API Layer that doesn't exist | **High** | `architecture.md:15` vs. empty `src/` |
| 5 | No request/response validation | **High** | zero `raise`/`assert`/`isinstance` in `src/` |
| 6 | No OpenAPI/Swagger docs | **Medium** | README "API Reference" = field table only |
| 7 | No CLI (`__main__`, argparse, console_scripts) | **Medium** | no entry point; `python -m` is a no-op |
| 8 | Untyped `dict`/`Any` fields block safe DTOs | **Medium** | `matching.py:31,40`, `fraud_detection.py:10`, etc. |
| 9 | `EvolutionEngine.evolve` takes unserializable `Callable` | **Medium** | `evolution.py:94-98` |
| 10 | No error model / domain exceptions | **Medium** | no custom exceptions, no error envelope |
| 11 | No async support | **Low** | all solvers synchronous; no `async def` |
| 12 | No conftest.py / pytest fixtures | **Low** | `tests/` has no shared fixtures |
| 13 | No API versioning | **Low** | `__version__ = "0.1.0"` only |

---

## Recommended Target Shape (minimal, library-first)

The project is a library, so the lowest-footprint path is **not** a heavyweight service. Recommended order:

1. **Add serde to dataclasses** (highest value, zero new surface): give each `@dataclass` a `to_dict()` / `from_dict()` (or adopt `dataclasses.asdict` + a `from_dict` classmethod). This unblocks every later step and fixes the untyped-`dict` risk.
2. **Add runtime validation** in `__post_init__` or explicit `validate()` on each dataclass and on engine methods (e.g. enforce `discount_rate > terminal_growth`, `market_condition ∈ {bull,bear,normal}`, `demand_level ∈ [0,1]`).
3. **Add a thin FastAPI app** (`src/acquisition_platform/api.py`) exposing one `POST /v1/{match,valuation,fraud,portfolio,pricing,resolve,rank,evolve}` per solver, with Pydantic request/response models generated from the dataclasses. This produces **OpenAPI/Swagger for free** and satisfies the documented "API Layer."
4. **Add a CLI** (`python -m acquisition_platform` or a `hermes`-style console_script) for local/library use.
5. **Make `evolve` serializable** by replacing the raw `Callable` with a named fitness registry or a gene-based DSL before exposing it remotelyely.
6. **Write an OpenAPI spec** (auto-generated by FastAPI) and a real endpoint reference doc to replace the README field table.

---

## Files Reviewed

- `src/acquisition_platform/{__init__,matching,valuation,fraud_detection,portfolio_optimizer,dynamic_pricing,entity_resolution,search_ranking,evolution}.py`
- `tests/test_*.py` (8 files), `tests/__init__.py`
- `pyproject.toml`
- `README.md`, `docs/ARCHITECTURE.md`, `docs/wiki/{architecture,getting-started}.md`
- `docs/archify-system.html`, `docs/dashboard.html` (static HTML, no live API)
