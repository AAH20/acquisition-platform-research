# Wave 2 — CI/CD & Automation Gaps

**Repository:** hermes-agent  
**Date:** 2026-10-04  
**Scope:** CI/CD infrastructure, automation tooling, containerization, and repo hygiene

---

## 1. Checklist Results

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | `.github/workflows/` | ✅ **EXISTS** | 50+ workflow files — mature CI/CD |
| 2 | `Makefile` | ❌ **MISSING** | No top-level task runner |
| 3 | `setup.py` / `setup.cfg` | ⚠️ **PARTIAL** | `setup.py` exists but is a build guard only; `setup.cfg` missing; `pyproject.toml` is the real build config |
| 4 | `tox.ini` | ❌ **MISSING** | No tox multi-env testing |
| 5 | `.pre-commit-config.yaml` | ❌ **MISSING** | No pre-commit hooks |
| 6 | `Dockerfile` | ✅ **EXISTS** | 31KB multi-stage build (Debian 13 + SQLite) |
| 7 | `docker-compose.yml` | ✅ **EXISTS** | 3.4KB gateway service with s6-overlay |
| 8 | `.gitignore` | ✅ **EXISTS** | 300+ lines, extremely comprehensive |

---

## 2. Detailed Findings

### 2.1 GitHub Actions CI/CD — ✅ Mature

The repository has an extensive CI/CD pipeline with **50+ workflow files** in `.github/workflows/`. Key workflows:

| Workflow | Purpose |
|----------|---------|
| `ci.yaml` | Orchestrator — runs `detect-changes`, conditionally calls sub-workflows, aggregates via `all-checks-pass` gate |
| `lint.yml` | Ruff + ty (advisory diff + blocking `ruff check .`) |
| `tests.yml` | Two 32-core parallel slices, 30-min timeout |
| `docker.yml` | Docker image build (34KB) |
| `docker-lint.yml` | Dockerfile linting |
| `stable-release.yml` | Stable release pipeline (25KB) |
| `desktop-bundled-release.yml` | Desktop app release (128KB) |
| `e2e-desktop.yml` | Desktop E2E tests |
| `e2e-desktop-core.yml` | Desktop core E2E |
| `e2e-desktop-update.yml` | Desktop update E2E |
| `install-e2e.yml` | Installer E2E (23KB) |
| `install-e2e-macos-run.yml` | macOS installer E2E |
| `install-e2e-windows-run.yml` | Windows installer E2E |
| `install-e2e-red.yml` | Installer red tests |
| `js-tests.yml` | JavaScript tests |
| `js-autofix.yml` | JS auto-fix |
| `rust-tests.yml` | Rust tests |
| `plugin-catalog-ci.yml` | Plugin catalog CI |
| `supply-chain-audit.yml` | Supply chain audit |
| `osv-scanner.yml` | OSV vulnerability scanning |
| `uv-lockfile-check.yml` | UV lockfile verification |
| `lockfile-diff.yml` | Lockfile diff check |
| `skills-index.yml` | Skills index generation |
| `skills-index-freshness.yml` | Skills index freshness |
| `docs-site-checks.yml` | Documentation site checks |
| `deploy-site.yml` | Site deployment |
| `canary-release.yml` | Canary releases |
| `contributor-check.yml` | Contributor verification |
| `history-check.yml` | History checks |
| `case-collision-check.yml` | Case collision detection |
| `icons-freshness-check.yml` | Icon freshness |
| `infographic-check.yml` | Infographic checks |
| `lazy-deps-guard.yml` | Lazy dependency guard |
| `live-providers.yml` | Live provider tests |
| `nix.yml` | Nix build |
| `sandbox-image.yml` | Sandbox image build |
| `termux-verify.yml` | Termux verification |
| `tests-os.yml` | OS-specific tests |
| `windows-bundle-sdk.yml` | Windows bundle SDK |
| `windows-install-update-e2e.yml` | Windows install/update E2E |
| `windows-venv-e2e.yml` | Windows venv E2E |
| `ci-review-comment.yml` | CI review comments |
| `label-rerun.yml` | Label-based rerun |
| `archive-inputs.yml` | Archive inputs |
| `bootstrap-installer.yml` | Bootstrap installer |
| `bootstrap-installer-build.yml` | Bootstrap installer build |
| `pm-bundle.yml` | PM bundle |
| `profile-artifact-check.yml` | Profile artifact check |
| `stable-release-publication.yml` | Stable release publication |

**Architecture:** The CI uses an orchestrator pattern (`ci.yaml`) that runs `detect-changes` once, then conditionally calls sub-workflows via `workflow_call`. A final `all-checks-pass` gate job aggregates results so branch protection only needs to require a single check.

**Supporting infrastructure:**
- `.github/CODEOWNERS` — code ownership
- `.github/dependabot.yml` — dependency updates
- `.github/actionlint.yaml` — action linting config
- `.github/actions/` — 12 custom composite actions
- `.github/scripts/` — CI helper scripts
- `scripts/ci/` — CI Python scripts (change classification, test running)
- `tests/ci/` — CI-specific tests

### 2.2 Makefile — ❌ Missing

No `Makefile` at the repository root. Common tasks (lint, test, build, clean) must be run individually or via CI. This is a **minor gap** — the project uses `scripts/run_tests.sh`, `scripts/run_tests_parallel.py`, and `pyproject.toml` scripts instead, but a Makefile would improve developer ergonomics.

### 2.3 Packaging — ⚠️ Partial

- **`setup.py`** — Exists but is a **build guard only**. It overrides `bdist_wheel` and `sdist` to raise an error when run outside a Nix build. The docstring explicitly states: "pip/PyPI and Homebrew are no longer supported distribution methods."
- **`setup.cfg`** — Missing.
- **`pyproject.toml`** — Exists (48KB). This is the real build configuration with all project metadata, dependencies, and tool configs.
- **`uv.lock`** — Exists (1.2MB). UV is the package manager.
- **`package-lock.json`** — Exists (716KB). For the web/desktop JS components.
- **`.python-version`** — Exists (Python version pinning).
- **`.nvmrc`** — Exists (Node version pinning).

**Assessment:** The packaging setup is intentional and well-documented. The project is distributed via shell installer, Docker image, or Nix — not pip/PyPI. This is a **design decision, not a gap**.

### 2.4 tox.ini — ❌ Missing

No `tox.ini` for multi-environment testing. The project relies on CI matrices (ubuntu-latest-32-core, macOS, Windows) and `scripts/run_tests_parallel.py` for parallel test execution. This is a **minor gap** — tox would simplify local multi-Python-version testing, but the CI covers this need.

### 2.5 Pre-commit Hooks — ❌ Missing

No `.pre-commit-config.yaml`. The project enforces code quality through CI (ruff, ty, actionlint) rather than pre-commit hooks. This is a **moderate gap** — pre-commit hooks would catch issues before CI, reducing feedback loop time. However, the CI is comprehensive enough that this is not critical.

### 2.6 Dockerfile — ✅ Exists

**31KB multi-stage Dockerfile** with:
- **Stage 1 (`sqlite_build`):** Builds SQLite 3.53.0400 from source with SHA-256 verification, pinned to Debian 13.4 digest. Compiles with FTS3/4/5, RTREE, GEOPOLY, MATH_FUNCTIONS, SESSION, etc.
- **Stage 2 (`runtime_base`):** Debian 13.4 base with the built SQLite.
- **Security:** Digest-pinned base images, SHA-256 verified downloads, retry logic for network operations.
- **Purpose:** Production container image for Hermes Agent.

### 2.7 docker-compose.yml — ✅ Exists

**3.4KB compose file** with:
- **Gateway service:** Builds from Dockerfile, host networking, s6-overlay process supervision.
- **Security notes:** Dashboard binds to 127.0.0.1 by default, API server off unless explicitly enabled.
- **User mapping:** HERMES_UID/HERMES_GID for host user file ownership.
- **Extensibility:** Commented options for Teams gateway, API server exposure.

### 2.8 .gitignore — ✅ Comprehensive

**300+ lines** covering:
- Python: `__pycache__/`, `*.pyc`, `.venv/`, `.pytest_cache/`, `*.egg-info/`
- Node: `node_modules/`, `package-lock.json` (not ignored), build outputs
- Rust: `target/`, `Cargo.lock` (not ignored)
- Go: `*.test`, `*.out`
- Secrets: `.env`, `*.pem`, `*.ppk`, `auth.json`, `vault.json.enc`
- IDE: `.vscode/`, `.idea/`, `.zed/`, `.cursor/`
- OS: `.DS_Store`, `Thumbs.db`
- Build artifacts: `dist/`, `build/`, `*.tsbuildinfo`
- Hermes runtime: `.hermes/`, `*.db`, `*.db-wal`, `sessions/`, `cron/`, `gateway.lock`
- Web UI: `web_dist/`, `tui_dist/`, `web/public/fonts/`
- Desktop: `apps/desktop/build/`, `apps/desktop/dist/`, `apps/desktop/release/`
- Nix: `.direnv/`, `.nix-stamps/`, `result`
- Docs: `website/static/api/*.json` (generated)
- Infographics: `infographic/`, `infographics/`, `infograficos/`
- Sandbox: `.hermes-sandbox/`, `.hermes-sandbox-e2e*/`
- Update state: `.update-incomplete`, `.update-incomplete.lock`, `.install_method`

**Assessment:** Exceptionally thorough. One of the most comprehensive `.gitignore` files observed.

---

## 3. Additional Observations

### 3.1 Missing Community Files
| File | Status |
|------|--------|
| `CHANGELOG.md` | ❌ Missing |
| `CODE_OF_CONDUCT.md` | ❌ Missing |
| `SUPPORT.md` | ❌ Missing |
| `.editorconfig` | ❌ Missing |
| `CONTRIBUTING.md` | ✅ Exists (54KB) |
| `SECURITY.md` | ✅ Exists (15KB) |
| `LICENSE` | ✅ Exists |
| `README.md` | ✅ Exists (16KB) |

### 3.2 Task Runners
| Tool | Status |
|------|--------|
| `Makefile` | ❌ Missing |
| `noxfile.py` | ❌ Missing |
| `justfile` / `Justfile` | ❌ Missing |
| `Taskfile.yml` | ❌ Missing |

### 3.3 Lockfiles
| File | Status |
|------|--------|
| `uv.lock` | ✅ Exists (1.2MB) |
| `package-lock.json` | ✅ Exists (716KB) |
| `poetry.lock` | ❌ Not used |
| `Pipfile.lock` | ❌ Not used |

### 3.4 Version Pinning
| File | Status |
|------|--------|
| `.python-version` | ✅ Exists |
| `.nvmrc` | ✅ Exists |
| `.node-version` | ❌ Missing |
| `.tool-versions` | ❌ Missing |

---

## 4. Gap Summary & Prioritization

| Gap | Severity | Impact | Recommendation |
|-----|----------|--------|----------------|
| No `.pre-commit-config.yaml` | **Medium** | Slower feedback loop; issues caught in CI instead of locally | Add pre-commit with ruff, ty, actionlint, trailing whitespace, EOF |
| No `Makefile` | **Low** | Developer ergonomics; common tasks not standardized | Add Makefile with `lint`, `test`, `build`, `clean` targets |
| No `tox.ini` | **Low** | Local multi-Python testing harder | Add tox with py310, py311, py312, py313 envs |
| No `.editorconfig` | **Low** | Inconsistent editor settings across contributors | Add standard `.editorconfig` |
| No `CHANGELOG.md` | **Low** | No user-facing change history | Generate from git log or GitHub releases |
| No `CODE_OF_CONDUCT.md` | **Low** | Community standards not documented | Add standard contributor covenant |
| No `SUPPORT.md` | **Low** | Support channels not documented | Add support documentation |

---

## 5. Overall Assessment

**CI/CD Maturity: HIGH**

The hermes-agent repository has a **production-grade CI/CD pipeline** with 50+ GitHub Actions workflows covering testing (unit, integration, E2E, OS-specific), linting (ruff, ty, actionlint), security (OSV scanner, supply chain audit), building (Docker, Nix, desktop bundles), and deployment (stable releases, canary releases, site deployment). The orchestrator pattern with change detection and aggregated gating is well-designed.

**Automation Gaps: LOW**

The missing items (Makefile, tox.ini, pre-commit hooks, .editorconfig) are **developer convenience tools**, not critical infrastructure. The project compensates with:
- Comprehensive CI that catches all issues
- `scripts/run_tests.sh` and `scripts/run_tests_parallel.py` for local testing
- `pyproject.toml` for all tool configuration
- `CONTRIBUTING.md` (54KB) with detailed development instructions

**Containerization: COMPLETE**

Both Dockerfile and docker-compose.yml exist and are production-ready with security best practices (digest pinning, SHA-256 verification, least-privilege users).

**Repo Hygiene: EXCELLENT**

The `.gitignore` is one of the most comprehensive observed, covering not just standard patterns but project-specific runtime state, build artifacts, and edge cases documented with issue references.

---

## 6. Recommendations

1. **Add `.pre-commit-config.yaml`** — Highest value addition. Include:
   - `ruff` (lint + format)
   - `ty` (type checking)
   - `actionlint` (workflow validation)
   - Standard hooks (trailing whitespace, EOF, large files, merge conflict markers)

2. **Add `Makefile`** — Standardize common tasks:
   ```makefile
   lint: ruff check . && ty check
   test: pytest
   build: docker build -t hermes-agent .
   clean: find . -type d -name __pycache__ -exec rm -rf {} +
   ```

3. **Add `.editorconfig`** — Ensure consistent editor settings:
   ```ini
   root = true
   [*]
   charset = utf-8
   end_of_line = lf
   insert_final_newline = true
   trim_trailing_whitespace = true
   indent_style = space
   indent_size = 4
   ```

4. **Add `tox.ini`** — For local multi-version testing:
   ```ini
   [tox]
   envlist = py310, py311, py312, py313
   [testenv]
   deps = pytest
   commands = pytest
   ```

5. **Consider `CHANGELOG.md`** — Generate from git log or GitHub releases for user-facing change tracking.

---

*Report generated by Wave 2 research agent.*
