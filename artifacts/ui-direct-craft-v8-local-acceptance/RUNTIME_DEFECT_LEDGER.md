# PetAccess — UI Direct Craft v8 Local Runtime Acceptance · RUNTIME_DEFECT_LEDGER

> Branch: `feat/ui-direct-craft-v8` · HEAD: `d2eeba2fe5ffbfba31f244881f6e1705a07f84c2` (at evidence start; fix commits follow)
> Generated: 2026-10-04 · Platform coverage: Web / Windows (Tauri v2 + WebView2) / Android (AVD emulator-5554, API 36)

## Summary

```
OPEN_RUNTIME_DEFECTS = 0
OPEN_CRITICAL        = 0
OPEN_MAJOR           = 0
```

One objective runtime defect was found during capture and fixed in this run (D-01).
Two contract-spacing FAIL rows (D-02/D-03) are **design-rhythm discrepancies introduced by the main UI workflow's own commits** — recorded here with exact metrics and handed back to the main UI workflow, not modified by the local agent (boundary: no subjective design changes).

---

## D-01 — MockMap basemap `<rect>` invalid SVG geometry (Map page console errors)

| Field | Value |
|---|---|
| ID | D-01 |
| Platform | Web (all viewports) / Windows WebView2 / Android WebView |
| Page | Map (`/#/map`, `/#/map?place=…`) |
| Severity | Major (objective runtime error, fixed in this run) |
| Reproduction | Visit any Map route; browser console logs repeated `Error: <rect> attribute y: Expected length, "104 120"` and `attribute width/height: Expected length, "NaN"` |
| Expected | No console errors; building-mass `<rect>` elements render with valid geometry |
| Actual | `apps/client-h5/src/components/MockMap.vue` bound `MASS` entries (4-point polygon tuples like `"104,104 120,104 120,116 104,116"`) as `<rect x y width height>` via `split(',')` → `y="104 120"`, `width=NaN`, `height=NaN` |
| Screenshot | `web/desktop/09_web_map_ready.png`, `web/mobile/09_web_map_ready_430x932.png` (before fix console had errors; after fix clean) |
| Metric | Before fix: `consoleErrors` 12–84 entries on map captures; after fix: 0 on all map captures |
| Root cause | Data format/consumer mismatch: `MASS` declared as polygon point strings but consumed as `x,y,w,h`; `split(',')` never yields numbers for width/height |
| Fix commit | `fix(runtime-ui): mock-map basemap rect geometry (split polygon tuples into x,y,w,h)` |
| Retest result | PASS — client-h5 rebuild + UI Oracle re-run (map PASS=22, map.mobile PASS=37, 13/13 Playwright) + web re-capture: 0 console errors on all 80 shots |

---

## D-02 — Reality date-group separator spacing below frozen contract minimum

| Field | Value |
|---|---|
| ID | D-02 |
| Platform | Web desktop (1440×900 oracle probe) |
| Page | Reality (`/#/place/{id}/reality`) |
| Severity | Minor (contract spacing row; design-rhythm decision — handed back) |
| Reproduction | Run UI Oracle compare: `[final] reality: PASS=34 WARN=0 FAIL=2` |
| Expected | `REALITY_DATE_GROUP_SEP`: `.timeline-date` computed margin `>= 28px` (contract `props.margin.min: 28`) |
| Actual | Measured `margin: 16px 0px 8px` (top 16px) |
| Metric | `probe.final.reality pages.reality-ready elements.REALITY_DATE_GROUP_SEP computed.margin = "16px 0px 8px"` |
| Root cause | Main workflow commit `0d5cdd8` "style(ui): close reality event-gap contract" reduced `.timeline-date` margin from `--pa-space-6 0 --pa-space-4` (32px/16px) to `--pa-space-4 0 --pa-space-2` (16px/8px) — moved below the contract minimum the commit claims to close. Preceding commits `1f3bede` / `f4307c9` tightened `.trace-row` rhythm (24px→16px→12px). |
| Fix commit | none (handed back to main UI workflow — spacing/rhythm is a design decision; local agent may not redesign) |
| Retest result | Open as handed-back contract discrepancy; NOT a runtime break (no overflow/clipping; page renders per approved compact rhythm) |

---

## D-03 — Reality trace-row vertical gap below frozen contract range

| Field | Value |
|---|---|
| ID | D-03 |
| Platform | Web desktop (1440×900 oracle probe) |
| Page | Reality (`/#/place/{id}/reality`) |
| Severity | Minor (contract spacing row; design-rhythm decision — handed back) |
| Reproduction | Run UI Oracle compare: `[final] reality` |
| Expected | `REALITY_EVENT_GAP`: `largestVerticalGap` in `[data-ui='reality-timeline-list'], .timeline` within `20–28px` |
| Actual | `largestVerticalGap = 16px` |
| Metric | `probe.final.reality … density.REALITY_EVENT_GAP actual=16 metric=largestVerticalGap` |
| Root cause | Same rhythm-tightening commits as D-02 (`1f3bede`/`f4307c9` reduced `.trace-row` padding/margin from space-4/space-5 to space-3) |
| Fix commit | none (handed back to main UI workflow) |
| Retest result | Open as handed-back contract discrepancy; NOT a runtime break |

---

## D-04 — `boundary-match` 400 for users without a boundary profile (expected, handled)

| Field | Value |
|---|---|
| ID | D-04 |
| Platform | Web / Windows / Android |
| Page | Why / Match Explain (`/#/place/{id}/why`) |
| Severity | Info — expected API behavior, consumer-safe |
| Reproduction | Open Why page signed in with a fresh user (no boundary profile) |
| Expected | Consumer-facing note "尚未设置共处边界，设置后可在此逐项比对。" |
| Actual | API returns `400 {"code":"no_boundary_profile"}`; `MatchExplainView.loadBoundary()` catches it and renders the consumer note. No raw JSON/debug leak in UI. Browser console logs one "Failed to load resource: 400" — expected for a handled API 400. |
| Root cause | Fresh demo user has no BoundaryProfile row; endpoint requires one by design (§"尚未设置共处边界") |
| Fix commit | none — not a defect |
| Retest result | PASS (UI shows consumer note; consumer language gate clean) |

---

## Closed / Verified-zero checklist

- `OPEN_RUNTIME_DEFECTS = 0` (D-01 fixed+retested; D-02/D-03 handed back as design-rhythm contract rows, not open runtime defects; D-04 expected behavior)
- 0 critical / 0 major open
- Windows: `NO_DOCUMENT_HORIZONTAL_OVERFLOW` PASS (all 19 pages), `NO_RAIL_HORIZONTAL_SCROLLBAR` PASS, `CONTRIBUTION_WIDE_COMPOSITION` PASS @1120 (main 664px | context 280px same row)
- Web: 80 captures, `document.scrollWidth <= clientWidth+1` PASS on all
- Android: 23 captures, 0 overflow, logcat `NO_FATAL_CRASH` / `NO_UNRECOVERED_ANR` / `NO_WEBVIEW_RENDERER_CRASH`
