# Wave 2: Dashboard Accessibility & UX Gap Analysis

**File:** `docs/dashboard.html` (648 lines, 26 KB)  
**Date:** 2026-10-04  
**Scope:** Accessibility (WCAG 2.1), keyboard navigation, color contrast, responsive design, loading states, error handling, mermaid rendering

---

## Executive Summary

The dashboard is a single-page static HTML file with a dark theme, six tab-switchable panels, three mermaid diagrams, and multiple data tables. It has a solid visual foundation but **significant accessibility gaps** — zero ARIA attributes, no focus management, no skip navigation, and several color contrast failures. The JavaScript has a **cross-browser bug** (uses deprecated global `event` object). Mermaid diagrams are syntactically correct but lack fallbacks. Responsive design is partial — good for stats grid but tables will overflow on mobile.

**Severity distribution:** 3 Critical · 5 High · 6 Medium · 4 Low

---

## 1. ARIA Labels & Semantics

### Critical

| # | Issue | Location | WCAG | Impact |
|---|-------|----------|------|--------|
| A1 | **Zero ARIA attributes in entire document** | All | 1.3.1, 4.1.2 | Screen readers get no semantic information beyond native HTML. Nav buttons, panels, progress bars, and mermaid diagrams are all unlabeled. |
| A2 | **Nav buttons have no `aria-label`, `aria-pressed`, or `role="tab"`** | Lines 175–180 | 4.1.2 | Screen reader users cannot determine which tab is active or what each button does beyond the text content. |
| A3 | **Panels have no `role="tabpanel"` or `aria-labelledby`** | Lines 185, 280, 361, 462, 538, 566 | 4.1.2 | Panel content is not associated with its controlling button. Screen readers cannot announce panel switches. |
| A4 | **Progress bars have no `role="progressbar"` or `aria-valuenow`** | Lines 382, 390, 398, etc. | 4.1.2 | Progress bars are invisible to assistive technology. Users cannot determine completion percentage. |
| A5 | **Mermaid diagram containers have no `role="img"` or `aria-label`** | Lines 283, 331, 569 | 1.1.1 | Diagrams are either announced as raw text (the mermaid source) or skipped entirely. |

### Medium

| # | Issue | Location | WCAG | Impact |
|---|-------|----------|------|--------|
| A6 | **Tables have no `<caption>` or `aria-label`** | Lines 207, 364, 465, 541, 602 | 1.3.1 | Table purpose is not programmatically determinable. |
| A7 | **`<th>` elements lack `scope` attribute** | Lines 209–215, 366–373, etc. | 1.3.1 | Screen readers may not correctly associate headers with data cells. |
| A8 | **No `aria-live` region for dynamic panel switching** | Line 640–645 | 4.1.3 | Screen reader users are not notified when panel content changes. |
| A9 | **Stat cards have no `aria-label` associating value with label** | Lines 187–202 | 1.3.1 | "50" and "Research Agents" may be announced as disconnected text. |

### Low

| # | Issue | Location | WCAG | Impact |
|---|-------|----------|------|--------|
| A10 | **No `<meta name="description">`** | `<head>` | — | SEO and document summarization. |
| A11 | **Header `<p>` not associated with heading** | Line 171 | 1.3.1 | Subtitle relationship to `<h1>` is implicit only. |

---

## 2. Keyboard Navigation

### Critical

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| K1 | **No skip-to-content link** | `<body>` start | Keyboard users must tab through all 6 nav buttons before reaching main content on every page load. |
| K2 | **No focus management on panel switch** | `showPanel()` line 640 | When a panel is activated, focus remains on the button. Screen reader users are not moved to the new panel content. The panel change is silent. |

### High

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| K3 | **No `:focus-visible` styles** | CSS | Keyboard users cannot see which element has focus. The default browser focus ring is the only indicator, which may be inconsistent across browsers and hard to see on dark backgrounds. |
| K4 | **`showPanel` uses deprecated global `event` object** | Line 644 | **Cross-browser bug:** `event.target` throws `ReferenceError` in Firefox where `event` is not a global. Panel switching is broken in Firefox. Should use `function showPanel(event, id)` or `event.currentTarget`. |

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| K5 | **No roving tabindex on nav** | Lines 175–180 | All 6 buttons are in the natural tab order. Arrow-key navigation between tabs is not implemented (acceptable for a simple tab pattern but not ideal). |
| K6 | **No `aria-current="page"` or `aria-selected="true"` on active nav** | Line 175 | Active state is visual only (CSS class). Not programmatically determinable. |

### What works

- Nav elements are `<button>` elements — natively focusable and activatable with Enter/Space ✓
- DOM order matches visual order ✓
- No positive `tabindex` values ✓

---

## 3. Color Contrast

### Methodology

Contrast ratios calculated per WCAG 2.1 relative luminance formula. Badge effective backgrounds computed by blending semi-transparent badge background (`#RRGGBB33` ≈ 20% opacity) over the card background `#161b22`.

### High

| # | Element | Foreground | Background | Ratio | WCAG AA | Notes |
|---|---------|------------|------------|-------|---------|-------|
| C1 | `.badge-critical` text | `#f85149` | `#43262a` (blended) | **4.05:1** | ❌ Fail (needs 4.5:1) | Critical severity badges — small text (0.75rem) |
| C2 | `.badge-medium` text | `#1f6feb` | `#172c4c` (blended) | **2.67:1** | ❌ Fail | Medium severity badges — small text |
| C3 | `.badge-low` text | `#238636` | `#183326` (blended) | **3.33:1** | ❌ Fail | Low severity badges — small text |
| C4 | `--color-primary` on `--color-bg` | `#1f6feb` | `#0d1117` | **3.45:1** | ❌ Fail (normal text) | Used for stat values (2rem = large text, passes AAA) and nav hover border |
| C5 | `--color-primary` on `--color-card` | `#1f6feb` | `#161b22` | **3.08:1** | ❌ Fail (normal text) | Stat values are large text so pass, but any small primary-colored text fails |

### Medium

| # | Element | Foreground | Background | Ratio | WCAG AA | Notes |
|---|---------|------------|------------|-------|---------|-------|
| C6 | `--color-muted` on `--color-card` | `#8b949e` | `#161b22` | **6.15:1** | ✅ Pass | Used for `th`, `.stat-card .label`, `header p` — all small text but ratio is sufficient |
| C7 | `--color-muted` on `--color-bg` | `#8b949e` | `#0d1117` | **6.9:1** | ✅ Pass | |
| C8 | `--color-text` on `--color-bg` | `#c9d1d9` | `#0d1117` | **12.1:1** | ✅ Pass (AAA) | Body text — excellent |
| C9 | `--color-text` on `--color-card` | `#c9d1d9` | `#161b22` | **10.4:1** | ✅ Pass (AAA) | Card text — excellent |

### Key finding

**All badge colors fail WCAG AA for small text.** The semi-transparent badge backgrounds (`#RRGGBB33`) reduce contrast below the 4.5:1 threshold when blended over the dark card background. This affects severity indicators throughout the dashboard — a core information channel.

### Recommended fixes

- Darken badge text colors or use opaque backgrounds
- Minimum: increase badge font size to 0.875rem and use `font-weight: 700`
- Alternative: use solid badge backgrounds with dark text (e.g., `#f85149` bg with `#0d1117` text)

---

## 4. Responsive Design

### What works

- `<meta name="viewport" content="width=device-width, initial-scale=1.0">` ✓
- `clamp(1.25rem, 2.5vw, 1.75rem)` for header `<h1>` — fluid typography ✓
- `flex-wrap: wrap` on nav — buttons wrap on narrow screens ✓
- `grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))` for stats grid ✓
- `overflow-x: auto` on `.mermaid` containers ✓
- `overflow-x: hidden` on body ✓

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| R1 | **Tables have no responsive handling** | Lines 207, 364, 465, 541, 602 | Tables with 5–6 columns will overflow horizontally on screens < 768px. No scroll wrapper, no column hiding, no card-based stacked layout. |
| R2 | **No media queries for small screens** | CSS | Only `prefers-reduced-motion` is defined. No `@media (max-width: 768px)` or similar breakpoints. |
| R3 | **Fixed padding on small screens** | `main` padding: 2rem, nav padding: 1rem 2rem | On a 320px screen, 2rem (32px) padding on each side leaves only 256px for content. |
| R4 | **Stats grid minimum 200px** | `minmax(200px, 1fr)` | On screens < 400px, two cards side-by-side would be < 200px each. Cards will overflow or shrink below readable size. |

### Recommended fixes

- Wrap tables in `<div style="overflow-x: auto">` or add `display: block; overflow-x: auto` to table containers
- Add `@media (max-width: 768px)` breakpoint: reduce padding to 1rem, stack stats grid to 1 column, reduce font sizes
- Consider `minmax(150px, 1fr)` or `minmax(180px, 1fr)` for stats grid on mobile

---

## 5. Loading States

### High

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| L1 | **No loading indicator for mermaid CDN** | Line 7 | Mermaid library loads from `cdn.jsdelivr.net`. If the CDN is slow or unreachable, the page appears blank where diagrams should be. No spinner, skeleton, or "Loading..." text. |
| L2 | **No fallback if mermaid fails to render** | Lines 626–638 | If mermaid throws a parse error or the CDN fails, the raw mermaid source code is displayed as plain text — confusing for end users. |
| L3 | **No `startOnLoad` error handling** | Line 627 | `mermaid.initialize({ startOnLoad: true })` will attempt to render on `DOMContentLoaded`. If it fails, there is no catch or retry. |

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| L4 | **No lazy loading for below-fold panels** | All panels | All panel content is in the DOM on page load (hidden with `display: none`). This is acceptable for a small dashboard but could be improved with dynamic loading for larger datasets. |

### Recommended fixes

- Add a loading spinner or skeleton inside `.mermaid` containers that is removed when mermaid renders
- Wrap `mermaid.initialize()` in try/catch and show an error message on failure
- Consider `loading="lazy"` equivalent: render mermaid only when a panel is first activated

---

## 6. Error Handling in UI

### Critical

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| E1 | **`showPanel` uses global `event` object — broken in Firefox** | Line 644 | `event.target.classList.add('active')` throws `ReferenceError: event is not defined` in Firefox. Panel switching is completely broken in Firefox. **This is a functional bug, not just accessibility.** |

### High

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| E2 | **No try/catch around mermaid initialization** | Lines 626–638 | If mermaid throws during initialization, the error is uncaught and may break subsequent script execution. |
| E3 | **No error boundary for panel rendering** | `showPanel()` | If `document.getElementById(id)` returns null (e.g., due to a typo in the panel ID), the error is uncaught. |

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| E4 | **No offline detection** | — | If the user is offline, mermaid CDN fails silently. No `navigator.onLine` check or offline message. |
| E5 | **No `alt` text or fallback for mermaid diagrams** | Lines 283, 331, 569 | If mermaid fails, users see raw diagram source code. No meaningful fallback content. |

### Recommended fixes

```javascript
// Fix E1: Pass event as parameter
function showPanel(event, id) {
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
    const panel = document.getElementById(id);
    if (!panel) return; // Fix E3
    panel.classList.add('active');
    event.currentTarget.classList.add('active'); // Use currentTarget, not target
}

// Fix E2: Wrap in try/catch
try {
    mermaid.initialize({ startOnLoad: true, theme: 'dark', ... });
} catch (e) {
    console.error('Mermaid failed to initialize:', e);
    document.querySelectorAll('.mermaid').forEach(el => {
        el.innerHTML = '<p role="alert">Diagram failed to load. Please refresh the page.</p>';
    });
}
```

---

## 7. Mermaid Diagram Rendering

### What works

- Three diagrams defined: System Architecture (`graph TB`), Module Interactions (`graph TD`), Evolution Framework (`flowchart TD`) ✓
- Mermaid v10 loaded from jsDelivr CDN ✓
- Dark theme configured with custom `themeVariables` matching dashboard palette ✓
- `startOnLoad: true` for automatic rendering ✓
- `overflow-x: auto` on `.mermaid` containers for wide diagrams ✓
- Subgraph syntax `subgraph Name["Title"]` is correct for v10 ✓
- Node shapes: `[]` (rectangle), `[(cylinder)]` (database) — valid ✓
- Edge syntax `-->` — valid ✓

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| M1 | **No `aria-label` on mermaid containers** | Lines 283, 331, 569 | Screen readers cannot describe the diagram purpose. The raw mermaid source may be read aloud. |
| M2 | **No fallback content inside `.mermaid` divs** | Lines 283, 331, 569 | If mermaid fails, raw source is shown. Should include `<noscript>` or fallback text. |
| M3 | **No `role="img"` on rendered mermaid SVGs** | — | Mermaid renders as SVG. Without `role="img"`, screen readers may try to read the SVG text elements individually. |

### Low

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| M4 | **No diagram titles or descriptions** | — | Each diagram could benefit from a heading or `aria-describedby` pointing to a text summary. |
| M5 | **CDN dependency — no SRI hash** | Line 7 | No Subresource Integrity hash on the mermaid script tag. If the CDN is compromised, arbitrary code executes. |

### Recommended fixes

```html
<!-- Add aria-label and fallback -->
<div class="mermaid" role="img" aria-label="System architecture diagram showing data flow from external sources through ingestion, storage, core engine, and evolution">
    graph TB
        ...
    </div>
    <noscript><p>Diagram requires JavaScript. [Text description of architecture]</p></noscript>
</div>

<!-- Add SRI hash -->
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js" 
        integrity="sha384-..." 
        crossorigin="anonymous"></script>
```

---

## 8. Additional UX Issues

### Medium

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| U1 | **No `:focus-visible` styles** | CSS | Keyboard users cannot see focus indicator. Add `:focus-visible { outline: 2px solid var(--color-primary); outline-offset: 2px; }` |
| U2 | **Sticky header may overlap content** | `header { position: sticky; top: 0; }` | When scrolling, the sticky header can cover content. No `scroll-margin-top` on sections. |
| U3 | **No print styles** | CSS | Printing the dashboard produces unreadable output (dark background, hidden panels). |
| U4 | **No dark/light theme toggle** | — | Dark theme is forced. Users who prefer light mode have no option. |
| U5 | **Progress bar widths are inline styles** | Lines 382, 390, etc. | `style="width: 90%"` — not maintainable, not accessible. Should use `aria-valuenow` and CSS custom properties. |

### Low

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| U6 | **No favicon** | `<head>` | Browser tab shows default icon. |
| U7 | **No Open Graph meta tags** | `<head>` | Social media sharing produces poor previews. |
| U8 | **Inline `onclick` handlers** | Lines 175–180 | Mixes HTML and JS. Better to use `addEventListener` in the script block. |
| U9 | **No CSS custom property for focus ring** | — | Inconsistent focus indication across components. |

---

## Priority Fix Roadmap

### Phase 1 — Critical (Functional bugs + screen reader blockers)

1. **Fix `showPanel` event bug** (E1, K4) — pass `event` as parameter, use `event.currentTarget`
2. **Add ARIA roles and labels** (A1–A5) — `role="tablist"`, `role="tab"`, `role="tabpanel"`, `aria-selected`, `aria-labelledby`, `role="progressbar"`, `aria-valuenow`, `role="img"` on mermaid
3. **Add skip navigation link** (K1)
4. **Add focus management on panel switch** (K2) — move focus to panel heading or container

### Phase 2 — High (Contrast + loading + error handling)

5. **Fix badge contrast** (C1–C3) — use opaque backgrounds or darker text
6. **Add mermaid loading state + fallback** (L1–L3, M2) — spinner, try/catch, error message
7. **Add `:focus-visible` styles** (K3, U1)
8. **Wrap mermaid initialization in try/catch** (E2)

### Phase 3 — Medium (Responsive + polish)

9. **Add responsive table handling** (R1) — overflow wrapper or stacked layout
10. **Add media queries for mobile** (R2–R4)
11. **Add table captions and `scope` attributes** (A6–A7)
12. **Add `aria-live` region for panel announcements** (A8)

### Phase 4 — Low (Enhancement)

13. Add SRI hash to mermaid CDN (M5)
14. Add print styles (U3)
15. Add light/dark theme toggle (U4)
16. Add favicon and OG tags (U6–U7)
17. Move inline `onclick` to `addEventListener` (U8)

---

## WCAG 2.1 Conformance Summary

| Criterion | Status | Notes |
|-----------|--------|-------|
| 1.1.1 Non-text Content | ❌ Fail | Mermaid diagrams, progress bars, stat cards lack text alternatives |
| 1.3.1 Info and Relationships | ❌ Fail | No ARIA roles, no table captions, no scope attributes |
| 1.4.1 Use of Color | ⚠️ Partial | Badges use color + text (good), but progress bars use color only |
| 1.4.3 Contrast (Minimum) | ❌ Fail | Badge text fails 4.5:1 ratio |
| 1.4.11 Non-text Contrast | ⚠️ Partial | Focus indicator may not meet 3:1 against adjacent colors |
| 2.1.1 Keyboard | ⚠️ Partial | Buttons are keyboard-accessible but `event` bug breaks Firefox |
| 2.1.2 No Keyboard Trap | ✅ Pass | |
| 2.4.1 Bypass Blocks | ❌ Fail | No skip navigation |
| 2.4.3 Focus Order | ✅ Pass | DOM order matches visual order |
| 2.4.6 Headings and Labels | ⚠️ Partial | Headings exist but panels lack labels |
| 2.4.7 Focus Visible | ❌ Fail | No custom focus styles; relies on browser default |
| 2.5.3 Label in Name | ✅ Pass | Button text matches accessible name |
| 4.1.2 Name, Role, Value | ❌ Fail | No ARIA attributes on interactive elements |
| 4.1.3 Status Messages | ❌ Fail | No `aria-live` for panel switches |

**Overall: Does not conform to WCAG 2.1 Level AA.**

---

## Files Referenced

- `docs/dashboard.html` — the only file analyzed
- No external dependencies beyond mermaid CDN
- No build system, no framework — vanilla HTML/CSS/JS
