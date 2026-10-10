# UI_DIRECT_CRAFT_V8_LOCAL_RUNTIME_ACCEPTANCE_REPORT

> PetAccess — Local Runtime Acceptance / Evidence Closure
> Date: 2026-10-04 · Branch: `feat/ui-direct-craft-v8`

---

## 1. GIT_TRUTH

```
branch   = feat/ui-direct-craft-v8
head     = d2eeba2fe5ffbfba31f244881f6e1705a07f84c2
           (latest origin/feat/ui-direct-craft-v8 at run start; fix commits appended)
master   = 42ed4e34158a566b2574b7176d3d12ddf12a20e1 (origin/master, unchanged)
worktree = D:\pa-fix (dedicated PetAccess worktree; started clean)
```

## 2. ENVIRONMENT

| Component | Version / Value |
|---|---|
| OS | Windows 11 专业版 |
| Node | v22.15.0 |
| pnpm | 12.4.1 |
| Python | 3.13.14 (venv 3.12.9 via uv) |
| uv | 0.9.18 |
| rustc / cargo | 1.97.1 |
| MSVC | VS 2022 toolchain (vcvars64) |
| WebView2 | 154.0.4258.53 |
| PostgreSQL | 16.4 @ 127.0.0.1:55432 (DB `petaccess_visual`, role VISUAL) |
| Redis | 127.0.0.1:6379 |
| Android | AVD `main` emulator-5554, API 36, x86_64, 1080×2400 @ 420dpi |
| API endpoints | Web `:8012`, Windows `:8016`, Android `10.0.2.2:8016` (VITE_TAURI_API_BASE / VITE_TAURI_ANDROID_API_BASE) |

## 3. STATIC_BUILD

| Gate | Result |
|---|---|
| `pnpm install --frozen-lockfile` | PASS |
| `pnpm lint:fe` (eslint .) | PASS |
| `pnpm format:check:fe` (prettier --check) | PASS |
| `pnpm --filter @petaccess/client-h5 build` (vue-tsc + vite) | PASS |
| `pnpm --filter @petaccess/admin build` | PASS |

## 4. WEB_RUNTIME

- 80 captures: desktop 1440×900 (26) + mobile 430×932 / 390×844 (54), covering Home, Search ready/selected, Place overview/space/rules/reality/evidence, Map ready/selected/expanded(mobile), Reality, Evidence, Contribution choose/step1/step2, Mine, Settings, Privacy, Notifications, Pet Profile, Pet New, Boundary, Why, About, Onboarding, Not Found.
- Every capture has same-basename JSON metadata (gitSha/route/page/state/viewport/dpr/documentClientWidth/documentScrollWidth/horizontalOverflow/consoleErrors/networkErrors).
- Hard condition: `document.scrollWidth <= document.clientWidth + 1` → PASS on all 80.
- Console errors: 0 after D-01 fix. Network errors: 0.

## 5. WINDOWS_RUNTIME

- Real Tauri v2 debug build (`D:\pa-fix-target-win\debug\petaccess.exe`), real WebView2 (no Chrome substitute), default window 1120×760.
- 19 pages captured via WebView2 CDP: 01_home … 14_why, 15_desktop_rail_closeup, 16_pets, 17_boundary, 18_onboarding, 19_not_found.
- Per-page metrics recorded (inner/outer dimensions, dpr, visualViewport, document widths, rail widths).
- Contribution @1120 = `WIDE_DESKTOP`: main (664px) | context (280px) same row — `CONTRIBUTION_WIDE_COMPOSITION = PASS`.

## 6. ANDROID_RUNTIME

- Debug APK rebuilt from current branch (`app-universal-debug.apk`), installed on AVD `main` (emulator-5554, API 36).
- 23 real runtime captures: Home, Search, Place Overview/Rules, Map half/expanded sheet, Reality, Evidence, Contribution choose/step1/step2, Mine, Settings, Privacy, Pet Profile, Boundary, Why, Onboarding, Not Found + interaction-smoke steps.
- 0 horizontal overflow on all captures.

## 7. CORE_PAGE_VISUAL_ACCEPTANCE

Core 7 pages (Home / Search / Place / Map / Reality / Evidence / Contribution) captured on Web (desktop+mobile), Windows, and Android — screenshots in `artifacts/ui-direct-craft-v8-local-acceptance/`. Machine-verifiable: no overflow, no console errors, correct data-ui state per page (oracle PASS counts in §14).

## 8. SECONDARY_PAGE_VISUAL_ACCEPTANCE

Mine, Settings, Privacy, Notifications, Pet Profile, Pet New, Boundary, Why, About, Onboarding, Not Found — all captured on Web desktop/mobile and Windows; Android covers the §21 secondary set. All 0 overflow / 0 console.

## 9. RESPONSIVE_ACCEPTANCE

| Viewport | Result |
|---|---|
| 1440×900 (web desktop) | PASS, 0 overflow |
| 430×932 (web mobile) | PASS, 0 overflow |
| 390×844 (web mobile) | PASS, 0 overflow |
| 1120×760 (Windows WebView2) | PASS, 0 doc overflow, 0 rail overflow |
| 1080×2400 (Android AVD) | PASS, 0 overflow |

## 10. INTERACTION_ACCEPTANCE

- Web: Search selected state, Place view switching (`?view=`), Map sheet expand, Contribution choose→step1→step2 — captured.
- Windows: full page sweep via real WebView2.
- Android §22 smoke (real clicks): Home→Search (via home search form), Search→Place, Place tab switching, Map marker→half sheet→expanded sheet, Contribution choose→step1→step2 (signed in), Mine→Pets, Mine→Settings, Why→decision explanation — 8 steps, 0 overflow, each with screenshot + metric JSON.

## 11. OVERFLOW_ACCEPTANCE

`document.scrollWidth <= document.clientWidth + 1` verified on every capture: Web 80/80, Windows 19/19, Android 23/23 → PASS.

## 12. CONSUMER_LANGUAGE_ACCEPTANCE

- UI Oracle language scan: 29/29 PASS (UUID/snake_case/ALL_CAPS/invariant checks).
- Real-UI scan (reality/evidence/map/place-rules/contribute/why): 0 forbidden tokens (UUID, raw enum, UNKNOWN, PROHIBITED, CONDITIONAL, ADR-*, rule_id, target_id, supersession, lead-only, raw JSON, resolver trace, debug stack).
- Why page shows consumer sections: 当前结论 / 判断过程 / 与我的共处边界比对 — no engine debug trace.

## 13. CRASH_LOGS

- Windows: 0 Vue runtime errors, 0 blank WebView, 0 raw API error JSON.
- Android logcat (`android/logcat/full.logcat.txt`): NO_FATAL_CRASH, NO_UNRECOVERED_ANR, NO_WEBVIEW_RENDERER_CRASH, no Tauri panic, no app-level ERR_CONNECTION. (System-process `HeterodyneSyncer` ERR_TIMED_OUT noise unrelated to the app.)

## 14. RUNTIME_DEFECTS

- UI Oracle compare: `TOTAL PASS=424 WARN=0 FAIL=2` — both FAIL rows are `reality` spacing rhythm (`REALITY_DATE_GROUP_SEP`, `REALITY_EVENT_GAP`), introduced by main workflow commits `1f3bede`/`f4307c9`/`0d5cdd8`. These are design-rhythm decisions → recorded in `RUNTIME_DEFECT_LEDGER.md` (D-02/D-03) and handed back to the main UI workflow; not open runtime defects.
- D-01 (MockMap rect geometry → SVG console errors) fixed and retested; D-04 (boundary-match 400 for fresh users) is expected, consumer-safe.
- `OPEN_RUNTIME_DEFECTS = 0` (0 critical / 0 major open).

## 15. FIXES_MADE

`fix(runtime-ui): mock-map basemap rect geometry` — `apps/client-h5/src/components/MockMap.vue`: `MASS` entries were 4-point polygon tuples bound as `<rect x/y/width/height>`; converted to `x,y,width,height` rect tuples and bound directly. Rebuilt, re-ran UI Oracle (13/13, map PASS=22 / map.mobile PASS=37), re-captured web (0 console errors on all 80 shots).

## 16. KNOWN_LIMITATIONS

- Web evidence stack uses API `:8012` (oracle stack) while Windows/Android use `:8016` — same DB/data (`petaccess_visual`), both documented in manifest.
- WebView2 reports `outerWidth 1121x761` (1px window chrome offset) vs configured 1120×760.
- `boundary-match` requires a boundary profile; fresh demo users see the consumer note (expected).
- UI Oracle Playwright suite runs 13 tests (oracle + secondary-craft); legacy human-review-*.spec.ts files are v4/v5/v7-era artifacts not part of the current v8 expected suite — not run to avoid producing stale-phase noise. (`WHY_TEST_COUNT_CHANGED` recorded in §14/§16.)

## 17. OUT_OF_SCOPE_RUFF_DEBT

Repo-wide Python Ruff debt (W292/E501/F401/I001/F841/E731 in `services/ worker/ tests/ scripts/`) predates direct-v8; `git diff` on this branch's Python files shows no new Python issues introduced by direct-v8 → `PYTHON_RUFF_EXISTING_DEBT = OUT_OF_SCOPE`. PR CI Python failures are unrelated to this UI runtime acceptance.

## 18. ARTIFACT_MANIFEST

`artifacts/ui-direct-craft-v8-local-acceptance/manifest/LOCAL_ACCEPTANCE_MANIFEST.json` — branch/head/master, tool versions, Windows/WebView2/AVD facts, API endpoints, all screenshot paths, SHA256 for 245 files, gate results, limitations.

## 19. HUMAN_REVIEW_PACK

`artifacts/ui-direct-craft-v8-local-acceptance/HUMAN_REVIEW/` — curated cards (platform / viewport / route / state / git SHA / valid) per §30–31.

## 20. FINAL_VERDICT

```
UI_DIRECT_CRAFT_V8_LOCAL_BUILD       = PASS
WEB_RUNTIME_ACCEPTANCE               = PASS
WINDOWS_RUNTIME_ACCEPTANCE           = PASS
ANDROID_RUNTIME_ACCEPTANCE           = PASS
RESPONSIVE_ACCEPTANCE                = PASS
INTERACTION_ACCEPTANCE               = PASS
CONSUMER_LANGUAGE_ACCEPTANCE         = PASS
NO_CRITICAL_RUNTIME_DEFECT           = PASS
LOCAL_HUMAN_REVIEW_PACK              = READY
```

One runtime defect (D-01) found and fixed in-run; two contract-spacing rows (D-02/D-03) handed back to the main UI workflow as design-rhythm decisions with exact metrics. `CANONICAL_BASELINE_PROMOTION = NOT_PERFORMED`; no master push, no tag, no release.
