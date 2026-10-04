# Wave 2: Deployment & Packaging Gaps Research

**Date:** 2026-10-04  
**Scope:** Hermes Agent repository at `/home/aah/.hermes/hermes-agent`

---

## 1. Dockerfile

**Status: PRESENT**

- **Location:** `/home/aah/.hermes/hermes-agent/Dockerfile`
- **Size:** 530 lines, ~31KB
- **Architecture:** Multi-stage build with 6 stages:
  1. `sqlite_build` — Builds pinned SQLite 3.53.4 from source (Debian 13.4 base, sha256-verified)
  2. `runtime_base` — System deps, s6-overlay init system, non-root user
  3. `python_deps` — Python dependency install via PM (layer-cached, extras: all/messaging/otlp/matrix/google-chat)
  4. `icons` — Icon generation stage
  5. `frontend_build` — Node.js build for TUI and web dashboard
  6. `runtime` — Final assembled image with source code, exec shim, provenance stamps
- **Key features:**
  - Multi-arch support (amd64/arm64) via BuildKit `TARGETARCH`
  - Two variants: `slim` (default) and `desktop` (with Xvnc/Xfce/Chromium)
  - s6-overlay for process supervision (replaces tini)
  - Pinned toolchain from `pm/lock.json` (uv, Chromium, Node, ffmpeg, ripgrep)
  - Install stamp + image provenance for version tracking
  - Privilege-drop shim for `docker exec`
  - Volume at `/opt/data` for persistent state
- **Additional Dockerfiles:** `docker/sandbox-desktop.Dockerfile`, `scripts/termux/termux-builder.Dockerfile`, plus sub-project Dockerfiles in `genetic-engineering-platform/` and `agtech-unified/`

---

## 2. docker-compose.yml

**Status: PRESENT**

- **Location:** `/home/aah/.hermes/hermes-agent/docker-compose.yml`
- **Size:** 76 lines
- **Services:**
  - `gateway` — Main Hermes gateway (build from source, host networking, `~/.hermes` volume mount)
  - `dashboard` — Web dashboard (localhost-only, depends on gateway)
- **Configuration:** HERMES_UID/GID remapping, optional API server, Teams/Google Chat integration hooks
- **Security notes:** Dashboard binds to 127.0.0.1, API server off by default, SSH tunnel recommended for remote access
- **Additional compose files:** `docker-compose.windows.yml`, `genetic-engineering-platform/docker-compose.yml`, `agtech-unified/docker-compose.yml`

---

## 3. Makefile

**Status: MISSING (Gap)**

- **No root-level Makefile exists.** The project has no `Makefile` at the repository root.
- Sub-project Makefiles exist only in:
  - `genetic-engineering-platform/Makefile`
  - `agtech-unified/Makefile`
  - `optional-skills/research/research-paper-writing/templates/neurips2025/Makefile`
- **Impact:** No standardized `make build`, `make test`, `make lint`, `make install` tasks for the main project. Developers must know individual commands (e.g., `python -m pm.build_env`, `scripts/run_tests.sh`, `ruff check`, `pytest`).
- **Recommendation:** A root Makefile with common dev tasks would improve contributor onboarding and CI readability.

---

## 4. .env.example

**Status: PRESENT**

- **Location:** `/home/aah/.hermes/hermes-agent/.env.example`
- **Size:** 554 lines, ~27KB
- **Coverage:** Comprehensive template covering:
  - 15+ LLM providers (Fireworks, OpenRouter, NovitaAI, Google, Ollama, GLM/Kimi, Arcee, MiniMax, OpenCode Zen/Go, Hugging Face, DeepInfra, Qwen, Xiaomi, Upstage, Ramp Router, Nebius, Tencent)
  - Tool API keys (Exa, Parallel, Firecrawl, FAL.ai, Honcho, Browserbase)
  - Terminal configuration (local/docker/singularity/modal/ssh backends)
  - SSH remote execution settings
  - Browser tool configuration (Browserbase, Camofox, agent-browser)
  - Voice/TTS (OpenAI, Groq, ElevenLabs, local Whisper)
  - Messaging platforms (Discord, Slack, Telegram, WhatsApp, Email, Teams, Google Chat)
  - Session logging, response pacing, debug options
  - Skills Hub (GitHub), context compression, STT provider selection
  - Reddit skill credentials
- **Note:** One line contains a redacted GitHub token placeholder (`GITHUB_TOKEN=«redacted:ghp_…»`) — this is a display redaction, not a leak.

---

## 5. requirements.txt vs pyproject.toml

**Status: pyproject.toml is the sole dependency authority (No requirements.txt)**

- **No root-level `requirements.txt` exists.** The project uses modern Python packaging exclusively.
- **`pyproject.toml`** (941 lines, ~48KB):
  - **Build system:** setuptools 83.0.0 + wheel
  - **Python requirement:** `>=3.11,<3.15` (3.14 is primary target)
  - **Dependencies:** ~40+ exact-pinned core deps (supply-chain security policy from 2026-01-12 Mini Shai-Hulud incident)
  - **Optional dependency groups:** 30+ extras (anthropic, exa, firecrawl, matrix, mcp, web, voice, wake, google, youtube, etc.)
  - **Dependency groups:** `dev` (pytest, ruff, ty, debugpy) and `test`
  - **UV configuration:** `exclude-newer = "14 days"`, extensive `exclude-newer-package` exemptions for exact-pinned deps
  - **Platform gates:** Per-extra platform markers (matrix=linux-only, google-chat/mem0=no win_arm64, etc.)
  - **Package data:** Declares assets, plugin manifests, PM lock files, bot desktop resources
  - **Entry points:** `hermes`, `hermes-agent`, `hermes-acp` CLI scripts
  - **Tool config:** pytest, ruff, ty settings
- **`uv.lock`** exists for deterministic resolution
- **Verdict:** pyproject.toml + uv.lock is sufficient and follows modern Python best practices. No requirements.txt needed.

---

## 6. CI/CD Pipeline

**Status: PRESENT — Extensive GitHub Actions setup**

- **66+ workflow files** in `.github/workflows/`
- **Key workflows:**
  - **`ci.yaml`** — Orchestrator with `detect-changes` classifier, lane-gated sub-workflows, and `all-checks-pass` aggregate gate. Runs on PR and push to main.
  - **`docker.yml`** — Docker build/test/publish with multi-arch matrix (amd64/arm64, slim/desktop variants). Standalone triggers + release-phase workflow_call. Publishes to Docker Hub as `nousresearch/hermes-agent`.
  - **`stable-release.yml`** — Full stable release pipeline (see section 7)
  - **`canary-release.yml`** — Canary release builds
  - **`desktop-bundled-release.yml`** — Signed desktop bundle releases (darwin-arm64/x64, win32-arm64/x64, termux)
  - **`tests.yml` / `tests-os.yml`** — Python test matrices (Linux, macOS, Windows)
  - **`lint.yml`** — Python linting (ruff)
  - **`js-tests.yml`** — JavaScript/TypeScript checks
  - **`rust-tests.yml`** — Rust crate tests
  - **`e2e-desktop-core.yml` / `e2e-desktop-update.yml`** — Desktop E2E suites
  - **`install-e2e.yml`** — Install and update E2E tests
  - **`uv-lockfile-check.yml`** — Lockfile consistency check
  - **`supply-chain-audit.yml`** — Supply chain security scanning
  - **`docker-lint.yml`** — Docker script linting
  - **`sandbox-image.yml`** — Sandbox image builds
  - **`nix.yml`** — Nix build verification
  - **`termux-verify.yml`** — Termux/Android verification
  - **`bootstrap-installer.yml`** — Bootstrap installer tests
  - **`skills-index.yml` / `skills-index-freshness.yml`** — Skills index validation
  - **`plugin-catalog-ci.yml`** — Plugin catalog validation
  - **`lazy-deps-guard.yml`** — Prevents production imports of lazy_deps stub
  - **`icons-freshness-check.yml`** — Icon asset freshness
  - **`case-collision-check.yml`** — Filename case collision detection
  - **`profile-artifact-check.yml`** — Profile artifact validation
  - **`live-providers.yml`** — Live LLM provider canary tests
  - **`windows-venv-e2e.yml`** — Windows venv E2E
  - **`windows-install-update-e2e.yml`** — Windows install/update E2E
  - **`windows-bundle-sdk.yml`** — Windows bundle SDK
  - **`js-autofix.yml`** — JS auto-fix
  - **`archive-inputs.yml`** — Archive input validation
  - **`label-rerun.yml`** — Label-based rerun
  - **`history-check.yml`** — Deny unrelated histories
  - **`contributor-check.yml`** — Contributor validation
  - **`infographic-check.yml`** — No committed infographics
  - **`docs-site-checks.yml`** — Documentation site checks
  - **`lockfile-diff.yml`** — package-lock.json diff
- **Composite actions:** `detect-changes`, `setup-pm`, `plugin-validate`, `setup-windows-build-deps`, `desktop-build-cache`, `retry`, `get-app-token`
- **Dependabot:** `.github/dependabot.yml` configured
- **CI timing report:** Built-in timing collection with HTML gantt chart and baseline caching

---

## 7. Release Process

**Status: PRESENT — Sophisticated multi-stage release system**

- **Release documentation:** `website/docs/developer-guide/stable-releases.md`
- **Release scripts:**
  - `scripts/release.py` (707 lines) — Main entrypoint with `release`, `publish`, `abandon` subcommands
  - `scripts/releases/` — Release management modules (stable, docker, sequencer, authors, stamping, etc.)
  - `scripts/write_install_stamp.py` — Install stamp generation
  - `scripts/render_builds_table.py` — Build table rendering
  - `scripts/ci/required_results.py` — CI gate evaluation
  - `scripts/ci/timings_report.py` — CI timing reports
  - `scripts/ci/classify_changes.py` — Change classification
  - `scripts/ci/check_profile_archive_boundary.py` — Profile archive boundary check
- **Stable release workflow (`stable-release.yml`):**
  1. **Admit** — Validates release claim tag, resolves commit/version
  2. **CI** — Full CI pipeline (strict mode, all lanes forced)
  3. **Docker** — Build and test Docker image (release-phase: test)
  4. **Nix** — Nix build verification
  5. **PM Bundle** — Bundle acceptance tests
  6. **Termux checks** — Termux verification
  7. **Windows live** — Windows venv E2E
  8. **Install E2E** — Install and update E2E (3 tag lookback)
  9. **Candidate builds** — Signed release candidates for darwin-arm64/x64, win32-arm64/x64, win32-bundle, termux
  10. **Transitions** — Pin old/new signed packages (Cloudflare R2)
  11. **Candidate manifest** — Stage verified artifacts
  12. **Packaged acceptance** — Windows/macOS signed-package acceptance tests
  13. **Bootstrap version** — Bootstrap installer release identity
  14. **Acceptance gate** — All release acceptance checks
  15. **Publish Docker** — Publish tested Docker image (release-phase: publish)
  16. **Publish bundles** — Publish tested bundle artifacts
  17. **Publication gate** — All artifact publication succeeded
  18. **Complete** — Final gate, candidate archive validation, ordered stable publication (Docker Hub alias promotion)
- **Release channels:** Stable, canary, commit, dynamic channels (via `hermes_cli/release_channels.py` and `hermes_cli/source_releases.py`)
- **Artifact storage:** Cloudflare R2 (bucket + public URL)
- **Docker publishing:** Multi-arch manifest lists, immutable version tags, ordered stable/latest alias promotion
- **Signing:** macOS/Windows signed packages with protected environment secrets
- **Release sequencer:** `scripts.releases.sequencer` for ordered publication

---

## Summary of Gaps

| Item | Status | Notes |
|------|--------|-------|
| Dockerfile | Present | Comprehensive multi-stage, multi-arch, dual-variant |
| docker-compose.yml | Present | Gateway + dashboard services |
| **Makefile** | **Missing** | No root-level Makefile for common dev tasks |
| .env.example | Present | Very comprehensive (554 lines, 15+ providers) |
| requirements.txt | Not needed | pyproject.toml + uv.lock is the modern standard |
| CI/CD pipeline | Present | 66+ GitHub Actions workflows, extensive |
| Release process | Present | Sophisticated multi-stage with signing, multi-arch, multi-platform |

### Identified Gaps

1. **No root Makefile** — The only packaging/deployment gap found. A root `Makefile` with targets like `build`, `test`, `lint`, `install`, `docker-build`, `docker-run` would improve developer experience and provide a common entry point for contributors who expect it.

2. **No container orchestration beyond compose** — No Kubernetes manifests, Helm charts, or Nomad jobs for the main project (sub-projects have some K8s configs). This may be intentional given the single-container design.

3. **No `.dockerignore` verification** — While `.dockerignore` exists (referenced in Dockerfile comments), there's no explicit CI check that it stays in sync with the build context requirements.

4. **No package publishing to PyPI** — The project uses `uv` and PM for dependency management but doesn't publish itself to PyPI. This appears intentional (installed via `install.sh`, desktop bundles, or Docker).

---

*Research completed. All findings based on direct file inspection of the repository.*
