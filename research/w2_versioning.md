# Versioning & Backward Compatibility Analysis — Hermes Agent

**Date:** 2026-10-04  
**Scope:** Root package, CLI, plugin system, config system, memory/secret provider APIs  
**Method:** Static analysis of source files, docs, and manifests

---

## Executive Summary

Hermes Agent has **no formal versioning infrastructure**. The project uses a placeholder `version = "0.0.0"` in `pyproject.toml`, has no root-level CHANGELOG, no deprecation policy, no migration guide, and no SemVer policy. The only meaningful version surface is the **plugin manifest system** (`api_version` / `manifest_version`) and the **install-stamp mechanism** used by the CLI updater. The project is pre-1.0 but already has a large surface area (20+ modules, 365+ tests, plugin ecosystem) that will need a formal versioning strategy before any public release.

---

## 1. Version Number in `__init__.py`

### Finding: Partial — lazy version via install stamp, not a static `__version__`

| Location | Value | Mechanism |
|----------|-------|-----------|
| `hermes_cli/__init__.py` | `__version__: str` (type annotation only) | Served lazily via `__getattr__` → reads `install-stamp.json` → `baseVersion` field. Falls back to `"0.0.0"` if no stamp. |
| `agtech-unified/src/__init__.py` | `__version__ = "1.0.0"` | Hardcoded string literal |
| `pyproject.toml` (root) | `version = "0.0.0"` | Static PEP 440 placeholder — not meaningful |
| `pm/pyproject.toml` | `version = "0.0.0"` | Static placeholder |

**Key observations:**
- The CLI's `__version__` is **not a static string** — it's resolved at runtime from `install-stamp.json` (written during installation). This means `import hermes_cli; hermes_cli.__version__` returns the installed version, not the source version.
- The fallback `"0.0.0"` is used when no install stamp exists (e.g., running from a source checkout without installation).
- There is **no `version_info` module** or `get_version_info()` function in the current tree (referenced in a comment but not present).
- The `agtech-unified` subproject has a hardcoded `__version__ = "1.0.0"` but this is a separate subproject, not the main Hermes package.

**Gap:** No single source of truth for the version. The `pyproject.toml` version is a placeholder, and the CLI version comes from an install-time stamp. There's no `hermes_cli/version_info.py` or equivalent.

---

## 2. CHANGELOG.md

### Finding: No root-level CHANGELOG

| Location | Status |
|----------|--------|
| Root `CHANGELOG.md` | **Does not exist** |
| `agtech-unified/CHANGELOG.md` | Exists — Keep a Changelog 1.1.0 format, SemVer adherence, latest entry `[1.0.0] - 2026-10-04` |

**Key observations:**
- The main Hermes Agent project has **no changelog at all**.
- The `agtech-unified` subproject has a well-formatted changelog following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) with SemVer, but this is a separate subproject.
- No `HISTORY.rst`, `RELEASES.md`, or equivalent exists at the root.
- Release notes are not automated — no `semantic-release`, no GitHub Actions workflow for changelog generation.

**Gap:** No changelog for the main project. Breaking changes, deprecations, and migrations are not documented in a user-facing format.

---

## 3. Deprecation Policy

### Finding: No formal deprecation policy

| Aspect | Status | Evidence |
|--------|--------|----------|
| Deprecation policy document | **None** | No `DEPRECATION.md`, no section in `CONTRIBUTING.md` or `AGENTS.md` |
| `@deprecated` decorator | **None** | No utility exists in the codebase |
| `DeprecationWarning` usage | **None** | No `DeprecationWarning` or `PendingDeprecationWarning` in source |
| Stability tier annotations | **None** | No `@stability: stable\|experimental\|deprecated` in docstrings |
| Compatibility shims | **None** | No compatibility layer for old APIs |
| Plugin API versioning | **Partial** | `api_version` (int) in plugin manifest; registry skips mismatched versions with warning |
| Memory provider API versioning | **Partial** | `pre_compress_checkpoint_api_version = 2` opt-in contract |
| Secret source API versioning | **Partial** | `api_version` with `SECRET_SOURCE_API_VERSION`; registry skips mismatched sources |

**Key observations:**
- The plugin system has the **most mature versioning surface**: `manifest_version` (file format) and `api_version` (runtime API generation) are separate axes. A plugin built against `api_version: 1` can use a v2 manifest.
- The registry **skips** (with a warning, never a crash) plugins/sources built against a different `api_version` — this is a runtime compatibility check, not a deprecation mechanism.
- There is **no deprecation cycle**: no "deprecated → sunset → removal" lifecycle.
- There is **no deprecation timeline**: no "this will be removed in vX.Y.Z" annotations.
- The `hermes_cli/AGENTS.md` mentions that `terminal.cwd` in `.env` is deprecated (loader warns), but this is an isolated case, not a systematic policy.

**Gap:** No deprecation framework. Breaking changes can be made without notice. No mechanism to warn users about upcoming removals.

---

## 4. Migration Guide

### Finding: No migration guide for the main project

| Location | Content |
|----------|---------|
| `optional-skills/migration/openclaw-migration` | Migration guide for migrating from OpenClaw to Hermes |
| `website/docs/user-guide/skills/optional/migration` | User-facing migration skill docs |
| API migration guides | **None** |
| Config migration guides | **None** (config has `_config_version` field but no migration docs) |
| Plugin migration guides | **None** |

**Key observations:**
- The config system has a `_config_version` field (currently `21`) which implies config schema evolution, but there is **no documentation** of what changed between versions or how to migrate.
- The `openclaw-migration` skill is a one-time migration tool, not a general migration framework.
- No codemods, transformers, or automated migration tooling exists.
- No "upgrading from vX to vY" documentation.

**Gap:** No migration path for config schema changes, API changes, or plugin API changes. Consumers have no documentation for upgrading between versions.

---

## 5. API Versioning

### Finding: Plugin system has API versioning; core APIs do not

| Surface | Versioning Mechanism | Status |
|---------|---------------------|--------|
| Plugin manifest | `manifest_version` (int, max 2) | **Present** — file format version |
| Plugin runtime API | `api_version` (int) | **Present** — registry skips mismatched |
| Memory provider | `pre_compress_checkpoint_api_version = 2` | **Present** — opt-in contract |
| Secret source | `api_version` + `SECRET_SOURCE_API_VERSION` | **Present** — registry skips mismatched |
| Core Python API | **None** | No version markers on any public function |
| Config schema | `_config_version` (int, currently 21) | **Present** — but no migration docs |
| REST API (if any) | **None** | No URL versioning (`/v1/`, `/v2/`) |
| Gateway API | **None** | No version markers |
| Tool schema | **None** | No version markers |

**Key observations:**
- The plugin system is the **only surface with formal API versioning**. The `api_version` field in `plugin.yaml` declares which generation of the plugin API (ctx surface / hook signatures) the plugin targets.
- The registry **skips** plugins with mismatched `api_version` (with a warning) rather than crashing — this is a runtime compatibility check.
- The `manifest_version` and `api_version` are **deliberately separate axes** — a plugin can use a v2 manifest while targeting `api_version: 1`.
- The config system has `_config_version` which is bumped on schema changes, but there's no way for users to know what changed.
- There is **no `__all__` export** in any `__init__.py` to define the public API surface.
- There is **no API contract test** that verifies the public API hasn't changed.

**Gap:** Core APIs (Python functions, config schema, gateway messages) have no versioning. Breaking changes in function signatures will silently break downstream code.

---

## 6. SemVer Policy

### Finding: No formal SemVer policy

| Aspect | Status |
|--------|--------|
| SemVer policy document | **None** |
| `pyproject.toml` version | `"0.0.0"` — placeholder, not meaningful |
| Git tags for versioning | **None** found |
| Automated version bumping | **None** |
| SemVer in changelog | Only in `agtech-unified/CHANGELOG.md` (separate subproject) |
| Breaking change policy | **None** documented |

**Key observations:**
- The `agtech-unified` subproject references SemVer in its changelog, but this is not the main Hermes project.
- The main project's `version = "0.0.0"` in `pyproject.toml` is a **placeholder** — it has no semantic meaning and is never bumped.
- There is no `semantic-release`, no `python-semantic-release`, no GitHub Actions workflow for version bumping.
- There is no policy for what constitutes a major/minor/patch change.
- There is no policy for pre-1.0 changes (the project is pre-1.0 but already has a large surface area).

**Gap:** No SemVer discipline. No way for consumers to know if a update is safe to install.

---

## Summary Table

| # | Question | Answer | Evidence |
|---|----------|--------|----------|
| 1 | Version number in `__init__.py`? | **Partial** — lazy via install stamp, not static | `hermes_cli/__init__.py:7` — `__version__: str` served by `__getattr__` from `install-stamp.json` |
| 2 | CHANGELOG.md? | **No** (root) — `agtech-unified/CHANGELOG.md` exists | No root `CHANGELOG.md` |
| 3 | Deprecation policy? | **No** | No `@deprecated`, no `DeprecationWarning`, no policy doc |
| 4 | Migration guide? | **No** (main project) | Only `openclaw-migration` skill exists |
| 5 | API versioning needed? | **Yes** — core APIs lack it | Plugin system has `api_version`; core Python/config/gateway APIs have none |
| 6 | SemVer policy? | **No** | `version = "0.0.0"` placeholder, no policy doc, no automation |

---

## Recommendations

### Short-term (P1)
1. **Add a static `__version__`** to `hermes_cli/__init__.py` (or a `version_info.py` module) that reads from `pyproject.toml` at build time. Keep the install-stamp mechanism for the updater, but have a single source of truth.
2. **Create a root `CHANGELOG.md`** following Keep a Changelog 1.1.0 format. Backfill from git history.
3. **Define a SemVer policy** in `CONTRIBUTING.md` or a dedicated `VERSIONING.md`: what constitutes major/minor/patch, pre-1.0 rules, deprecation cycle.

### Medium-term (P2)
4. **Add a deprecation framework**: `@deprecated` decorator, `DeprecationWarning` usage, stability tier annotations in docstrings.
5. **Document config schema migrations**: what changed between `_config_version` values, how to migrate.
6. **Add `__all__` exports** to all `__init__.py` files to define the public API surface.
7. **Add API contract tests** that verify the public API hasn't changed (not snapshot tests — contract tests).

### Long-term (P3)
8. **Automate version bumping** with `semantic-release` or similar.
9. **Add URL/header versioning** to any REST/gateway API.
10. **Create migration guides** for major version transitions.
11. **Add deprecation headers** (RFC 8594 Sunset) to HTTP responses.

---

## References

- `hermes_cli/__init__.py` — lazy `__version__` via `__getattr__`
- `pyproject.toml` — `version = "0.0.0"` placeholder
- `pm/pyproject.toml` — `version = "0.0.0"` placeholder
- `agtech-unified/CHANGELOG.md` — Keep a Changelog format (subproject only)
- `agtech-unified/src/__init__.py` — `__version__ = "1.0.0"` (subproject only)
- `website/docs/developer-guide/plugins/index.md` — `manifest_version` and `api_version` reference
- `website/docs/developer-guide/memory-provider-plugin.md` — `pre_compress_checkpoint_api_version = 2`
- `website/docs/developer-guide/secret-source-plugin.md` — `api_version` with registry skip
- `hermes_cli/AGENTS.md` — `terminal.cwd` deprecation note
- `optional-skills/migration/openclaw-migration` — OpenClaw migration skill
- `versioning_gap_report.md` — prior gap analysis (apex-autopilot-optimization, not Hermes)
