# Wave 2 Research: Community and Contribution Gaps

**Date:** 2026-10-04  
**Repository:** `/home/aah/.hermes/hermes-agent`  
**Focus:** Community infrastructure, contribution processes, governance

---

## 1. CONTRIBUTING.md

**Status:** ✅ EXISTS — Comprehensive

**Location:** `/home/aah/.hermes/hermes-agent/CONTRIBUTING.md` (1,037 lines, ~54KB)

**Highlights:**
- Detailed contribution priorities (bug fixes > cross-platform > security > performance > skills > tools > docs)
- "Search First" section to reduce duplicate PRs
- Skill vs. Tool decision framework
- Memory provider and third-party integration policies (ship as standalone plugins)
- Plugin catalog submission process
- Full development setup guide (PM workflow, prerequisites, test environment)
- Project structure overview with architecture diagram
- Code style guide (PEP 8, error handling, cross-platform rules)
- Adding new tools and skills with examples
- Cross-platform compatibility guide (15 critical rules)
- Security considerations and dependency pinning policy
- Pull request process (branch naming, before-submitting checklist, commit conventions)
- Issue reporting guidelines
- Community links (Discord, GitHub Discussions, Skills Hub)
- License agreement (MIT)

**Also available:** `CONTRIBUTING.es.md` (Spanish translation)

---

## 2. CODE_OF_CONDUCT.md

**Status:** ❌ DOES NOT EXIST at repository root

**Finding:** No `CODE_OF_CONDUCT.md` found at the root level. Only exists in subdirectory `agtech-unified/CODE_OF_CONDUCT.md` (a separate project within the workspace).

**Gap:** The main Hermes Agent repository lacks a code of conduct. This is a notable gap for an open-source project with community contributions. A code of conduct sets behavioral expectations for community participation and is often expected by contributors.

---

## 3. LICENSE

**Status:** ✅ EXISTS — MIT License

**Location:** `/home/aah/.hermes/hermes-agent/LICENSE`

**Details:**
- MIT License
- Copyright (c) 2025 Nous Research
- Standard MIT text with permission, conditions, and disclaimer sections
- Referenced in CONTRIBUTING.md: "By contributing, you agree that your contributions will be licensed under the MIT License."

---

## 4. Pull Request Template

**Status:** ✅ EXISTS — Comprehensive

**Location:** `/home/aah/.hermes/hermes-agent/.github/PULL_REQUEST_TEMPLATE.md` (75 lines)

**Sections:**
- What does this PR do? (description)
- Related Issue (Fixes #)
- Type of Change (bug fix, new feature, security fix, docs, tests, refactor, new skill)
- Changes Made (file paths)
- How to Test (reproduction steps)
- Checklist:
  - Code: read contributing guide, conventional commits, searched existing PRs, focused changes, tests pass, added tests, tested on platform
  - Documentation & Housekeeping: updated docs, config example, contributing guide, cross-platform impact, tool descriptions
  - For New Skills: broadly useful, standard format, no external deps, tested end-to-end
- Screenshots / Logs

**Quality:** Well-structured, covers all essential aspects of a good PR.

---

## 5. Issue Templates

**Status:** ✅ EXISTS — Multiple templates

**Location:** `/home/aah/.hermes/hermes-agent/.github/ISSUE_TEMPLATE/`

**Templates:**
1. **bug_report.yml** (162 lines) — Bug report with description, reproduction steps, expected/actual behavior, affected component, platform, debug report, OS/Python/Hermes versions, logs, root cause analysis, proposed fix, PR readiness
2. **feature_request.yml** (85 lines) — Feature request with problem/use case, proposed solution, alternatives, feature type, scope, contribution willingness, debug report
3. **setup_help.yml** (112 lines) — Setup/installation help with description, steps taken, install method, OS, Python/Hermes versions, debug report, error output, tried fixes
4. **config.yml** (14 lines) — Issue template configuration with blank issues enabled and contact links (security vulnerability, Discord, documentation, contributing guide)

**Quality:** Comprehensive, well-structured YAML forms with required fields, dropdowns, and helpful prompts.

---

## 6. Code Review Process

**Status:** ✅ EXISTS — Multi-layered

**Components:**

### a) CODEOWNERS (`.github/CODEOWNERS`)
- Defines code ownership with `@NousResearch/hermes-agent-core` team
- Covers: `.github/`, `scripts/ci/`, eslint configs, MCP catalog, setup files, dependency manifests, installers, SECURITY.md, plugin-catalog
- Uses GitHub's "Require review from Code Owners" ruleset
- Replaces the `ci-reviewed` label gate

### b) PR Template Checklist
- Enforces conventional commits
- Requires tests to pass
- Requires searching for existing PRs
- Cross-platform impact consideration
- Documentation updates

### c) CI/CD Workflows (`.github/workflows/`)
- `ci.yaml` (20KB) — Main CI pipeline
- `ci-review-comment.yml` — Automated review comments
- `contributor-check.yml` — Contributor verification
- `supply-chain-audit.yml` — Dependency security
- `case-collision-check.yml` — Case sensitivity checks
- Multiple E2E test workflows

### d) Automated Triage
- AGENTS.md mentions an "automated triage sweeper" that can close issues based on specific labels (`implemented_on_main`, `cannot_reproduce`, `incoherent`)
- Taste-based closes are reserved for human maintainers

### e) CONTRIBUTING.md Pull Request Process
- Branch naming conventions (fix/, feat/, docs/, test/, refactor/)
- Before-submitting checklist
- PR description requirements
- Conventional Commits format

**Quality:** Mature, multi-layered review process with automation and human oversight.

---

## 7. Governance Model

**Status:** ⚠️ PARTIAL — No formal governance document

**Finding:** No `GOVERNANCE.md` or equivalent formal governance document exists.

**What exists instead:**
- **CODEOWNERS** — Defines who can approve changes to specific paths
- **SECURITY.md** — Defines security governance, trust model, vulnerability reporting scope, and disclosure policy (90-day coordinated disclosure)
- **CONTRIBUTING.md** — Defines contribution governance (what's accepted, what's rejected, how to contribute)
- **AGENTS.md** — Defines development philosophy, design invariants, and decision-making frameworks (Footprint Ladder, contribution rubric)

**Gaps:**
- No formal decision-making process for non-code decisions (product direction, feature prioritization)
- No explicit maintainer roles/responsibilities beyond CODEOWNERS
- No term limits, succession planning, or rotation policies
- No formal RFC (Request for Comments) process for major changes
- No community maintainer program or onboarding path for new maintainers
- No transparency reports or regular community updates process

---

## Summary Table

| Item | Status | Location | Notes |
|------|--------|----------|-------|
| CONTRIBUTING.md | ✅ Exists | Root | Comprehensive (1,037 lines), Spanish translation available |
| CODE_OF_CONDUCT.md | ❌ Missing | — | Not found at root; only in subdirectory |
| LICENSE | ✅ Exists | Root | MIT License, Copyright 2025 Nous Research |
| PR Template | ✅ Exists | `.github/PULL_REQUEST_TEMPLATE.md` | Comprehensive with checklist |
| Issue Templates | ✅ Exists | `.github/ISSUE_TEMPLATE/` | 3 templates (bug, feature, setup) + config |
| Code Review Process | ✅ Exists | Multiple files | CODEOWNERS, CI workflows, PR checklist, triage sweeper |
| Governance Model | ⚠️ Partial | — | No formal GOVERNANCE.md; relies on CODEOWNERS + SECURITY.md + CONTRIBUTING.md |

---

## Key Gaps Identified

1. **No Code of Conduct** — The repository lacks a CODE_OF_CONDUCT.md, which is a standard expectation for open-source communities. This sets behavioral norms and provides a safe environment for contributors.

2. **No Formal Governance Document** — While the project has strong contribution guidelines, there's no formal governance model defining decision-making processes, maintainer roles, succession planning, or community leadership structure.

3. **No RFC Process** — Major decisions appear to be made by the core team without a formal Request for Comments process for community input on significant changes.

4. **No Community Maintainer Program** — No documented path for contributors to become maintainers or take on leadership roles.

5. **No Transparency/Communication Cadence** — No regular community updates, roadmap publication, or transparency reports.

---

## Recommendations

1. **Add CODE_OF_CONDUCT.md** — Adopt a standard code of conduct (e.g., Contributor Covenant) to set community expectations.

2. **Create GOVERNANCE.md** — Document the decision-making process, maintainer roles, and how community members can participate in governance.

3. **Establish RFC Process** — Create a formal process for proposing and discussing major changes (e.g., `.github/RFC/` directory with templates).

4. **Community Maintainer Path** — Define how contributors can progress to maintainer roles with clear responsibilities and expectations.

5. **Regular Community Updates** — Consider monthly or quarterly community updates to share progress, roadmap, and recognize contributors.
