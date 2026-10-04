# Wave 2: Documentation Accuracy Report

**Date:** 2026-10-04  
**Scope:** README.md, website/docs/, wiki docs, benchmark claims  
**Method:** Automated code analysis vs. documentation claims

---

## 1. README.md API Reference Section

**Finding: No API Reference section exists in README.md**

The README.md (243 lines, 16,924 bytes) contains:
- Project description and feature table
- Quick install instructions
- CLI vs Messaging quick reference
- Documentation links
- Migration guide
- Contributing section

**No function signatures, module references, or API documentation found.** The README links to external docs at `hermes-agent.nousresearch.com/docs/` for API reference.

---

## 2. Documented Function Signatures vs Actual Code

### AIAgent Class (run_agent.py)

| Claimed | Actual | Status |
|---------|--------|--------|
| `AIAgent` class in `run_agent.py` | ✅ Found | Accurate |
| `run_conversation()` method | ❌ Not in run_agent.py | **Inaccurate** — lives in `agent/conversation_loop.py` |
| `chat()` method | ❌ Not in run_agent.py | **Inaccurate** — lives in `agent/turn_facade.py` |
| `IterationBudget` class | ❌ Not in run_agent.py | **Inaccurate** — lives in `agent/iteration_budget.py` |
| `_interruptible_api_call()` | ✅ Found in run_agent.py | Accurate |

### Tool System

| Claimed | Actual | Status |
|---------|--------|--------|
| 70+ registered tools | 48 unique tool names in `tools/` | **Understated** — doc says "70+" but only 48 unique names found via registry.register() |
| 28 toolsets | 41 entries in TOOLSETS dict | **Understated** — actual count is higher |
| `_HERMES_CORE_TOOLS` | 56 entries | Not documented in README |

### Provider System

| Claimed | Actual | Status |
|---------|--------|--------|
| 18+ providers | Provider entries in `_REGISTRY_ROWS` | See provider analysis below |

---

## 3. Module Existence Check

**All 63 documented modules/files exist in the codebase.** ✅

Key modules verified:
- `run_agent.py`, `cli.py`, `model_tools.py`, `toolsets.py`
- `hermes_state.py`, `hermes_constants.py`, `batch_runner.py`
- All `agent/*.py` files (prompt_builder, context_engine, etc.)
- All `hermes_cli/*.py` files (main, config, auth, etc.)
- All `tools/*.py` files (registry, terminal_tool, file_tools, etc.)
- All `gateway/*.py` files (run, session, delivery, etc.)
- `acp_adapter/`, `cron/`, `plugins/memory/`, `plugins/context_engine/`

---

## 4. Mermaid Diagrams vs Actual Module Structure

### Files with Mermaid Diagrams (5 total)

| File | Mermaid Blocks | Content |
|------|----------------|---------|
| `checkpoints-and-rollback.md` | 1 | Checkpoint flow: User → AIAgent → Tools → CheckpointManager → Store |
| `software-development-code-wiki.md` | 5 | Generic flowchart, class diagram, sequence diagram |
| `messaging/index.md` | 1 | Gateway platform adapter flowchart |
| `messaging/open-webui.md` | 1 | Open WebUI ↔ Hermes gateway flow |
| `worktree-ui-dev.md` | 1 | Worktree setup flowchart |

### Architecture Diagrams

**`architecture.md` uses text-based ASCII diagrams, NOT mermaid.** Contains 6 `text` code blocks showing:
- System overview (Entry Points → AIAgent → Session Storage/Tool Backends)
- Directory structure
- Data flow (CLI Session, Gateway Message, Cron Job)
- File dependency chain

### Accuracy Issues

1. **Mermaid diagrams are generic/templated** — The code-wiki skill diagrams show generic "Agent → Tool → LLM" patterns, not actual Hermes module structure
2. **No mermaid diagram shows actual module dependencies** — The architecture page uses ASCII art which is accurate but not mermaid
3. **Gateway mermaid diagram lists platforms accurately** — Shows Telegram, Discord, WhatsApp, Slack, Google Chat, Signal, SMS, Email, Home Assistant, Mattermost, Matrix, DingTalk, Feishu, WeCom, Weixin, BlueBubbles, QQ

---

## 5. Wiki Docs Accuracy

### LLM Wiki Skill (`skills/research/llm-wiki/SKILL.md`)

- **Size:** 19,895 chars
- **Function signatures:** 0
- **Module references:** 0
- **Contains benchmark mentions:** Yes

**Finding:** The wiki skill is a procedural guide, not an API reference. No function signatures or module paths documented.

### Wiki Documentation Page (`website/docs/user-guide/skills/bundled/research/research-llm-wiki.md`)

- **Size:** 20,676 chars
- **Contains benchmark mentions:** Yes

**Finding:** Mirrors the SKILL.md content. No API reference material.

---

## 6. Benchmark Claims vs Test Results

### Test Count Claims

| Claimed | Actual | Status |
|---------|--------|--------|
| ~25,000 tests | 44,148 test functions | **Understated** — actual is ~76% higher |
| ~1,250 test files | 5,436 test files | **Significantly understated** — actual is ~4.3x higher |

### Benchmark Claims in Documentation

**No specific benchmark claims found in README.md.** The README contains no performance metrics, latency numbers, or throughput claims.

**115 files in website/docs/ mention "benchmark", "performance", "latency", or "throughput"** — but these are primarily:
- User guide references to performance settings
- Skill documentation mentioning benchmarks in general terms
- No concrete benchmark results or performance metrics documented

### Actual Benchmark/Performance Test Files

Only 2 test files specifically for benchmarks:
- `tests/tools/test_approval_launchctl_performance.py`
- `tests/hermes_cli/benchmark_session_timeline.py`

---

## 7. Detailed Claim Verification

### Architecture Page Claims (`architecture.md`)

| Claim | Verification | Status |
|-------|--------------|--------|
| 70+ tools | 48 unique tool names | ⚠️ Understated |
| 28 toolsets | 41 TOOLSETS entries | ⚠️ Understated |
| 18+ providers | See below | ⚠️ Needs verification |
| 25+ platform adapters | 31 platform files | ✅ Accurate |
| ~25,000 tests | 44,148 test functions | ⚠️ Understated |
| ~1,250 test files | 5,436 test files | ⚠️ Significantly understated |
| 7 terminal backends | 19 environment files | ⚠️ Understated (includes base/helper modules) |
| 5 browser backends | Not found in docs | ❌ Not verifiable |
| 4 web backends | Not found in docs | ❌ Not verifiable |

### Tools Reference Claims (`tools-reference.md`)

| Claim | Actual | Status |
|-------|--------|--------|
| ~100 tools | 86 tool entries in doc | ⚠️ Slightly overstated |
| 30 toolset sections | 30 sections found | ✅ Accurate |
| 10 browser tools (core) | 10 browser_* tools | ✅ Accurate |
| 2 CDP-gated browser tools | browser_cdp, browser_dialog | ✅ Accurate |
| 5 browser-vault tools | browser_vault_* (5 tools) | ✅ Accurate |
| 4 file tools | read_file, write_file, patch, search_files | ✅ Accurate |
| 2 terminal tools | terminal, process_manage | ✅ Accurate |
| 11 desktop-GUI tools | 11 tools listed | ✅ Accurate |
| 2 web tools | web_search, web_extract | ✅ Accurate |
| 5 Feishu tools | feishu_doc_read + 4 feishu_drive_* | ✅ Accurate |
| 7 Spotify tools | 7 spotify_* tools | ✅ Accurate |
| 5 Yuanbao tools | 5 yb_* tools | ✅ Accurate |
| 14 kanban tools | 14 kanban_* tools | ✅ Accurate |
| 2 Discord tools | discord, discord_admin | ✅ Accurate |
| 3 video tools | video_generate, xai_video_edit, xai_video_extend | ✅ Accurate |

---

## 8. Summary of Findings

### Accurate Claims ✅
- All documented module paths exist
- Platform adapter count (25+)
- Toolset section count in tools-reference (30)
- Individual tool counts per toolset (browser, file, terminal, web, etc.)
- Desktop GUI tool count (11)

### Understated Claims ⚠️
- **Tool count:** Docs say "70+" but only 48 unique tool names found (though _HERMES_CORE_TOOLS has 56 entries, and some tools may be registered dynamically)
- **Toolset count:** Docs say "28" but TOOLSETS dict has 41 entries
- **Test count:** Docs say "~25,000 tests across ~1,250 files" but actual is 44,148 tests across 5,436 files
- **Terminal backends:** Docs say "7" but 19 environment files exist (includes base/helper modules)

### Inaccurate Claims ❌
- **run_conversation() location:** Docs imply it's in run_agent.py, but it's in agent/conversation_loop.py
- **chat() location:** Docs imply it's in run_agent.py, but it's in agent/turn_facade.py
- **IterationBudget location:** Docs imply it's in run_agent.py, but it's in agent/iteration_budget.py

### Not Found ❌
- **API Reference section in README:** Does not exist
- **Browser backend count (5):** Not found in documentation
- **Web backend count (4):** Not found in documentation
- **Specific benchmark results:** No concrete performance metrics documented

### Mermaid Diagram Issues ⚠️
- Only 5 files use mermaid diagrams
- Architecture page uses ASCII art, not mermaid
- Mermaid diagrams in code-wiki skill are generic templates, not actual module structure
- No mermaid diagram accurately represents the actual module dependency chain

---

## 9. Recommendations

1. **Update architecture.md** to reflect actual test count (~44,000 tests, ~5,400 files)
2. **Clarify tool registration** — explain the difference between unique tool names (48), core tools (56), and total registered tools
3. **Fix method locations** — document that run_conversation() and chat() live in agent/ modules, not run_agent.py
4. **Add API Reference section** to README.md or create a dedicated API doc page
5. **Add mermaid diagrams** to architecture.md showing actual module dependencies
6. **Document browser/web backend counts** if they exist, or remove the claims
7. **Add benchmark results** section with actual performance metrics from test runs
