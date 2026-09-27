# UI Reconstruction — Skill Capability Map

> Derived from the **real installed skill docs** on this machine (read 2026-09-28, before use).
> Canonical Master v0.10-R1 + Approved Reference win on conflict. No skill may redefine
> product positioning, Domain or page IA.

## Impeccable

| Item | Value |
|---|---|
| Installed at | `C:\Users\Kaiser\.agents\skills\impeccable\SKILL.md` (+ `reference/*.md`, `scripts/`) |
| Version | no pinned version in SKILL.md; current installed copy |
| Invocation | Skill tool loads SKILL.md; commands: `critique [target]`, `audit`, `layout`, `typeset`, `distill`, `harden`, `adapt`, `polish`, `colorize`, `clarify`, `bolder`, `quieter`, `document`, `extract`, `init`, `onboard`, `animate`, `delight`, `overdrive`, `live`, `shape`, `craft` |
| Inputs | PRODUCT.md / DESIGN.md / surface brief / tokens / CSS / components / screenshots |
| Outputs | critique with heuristic scoring, layout/typography direction, polish guidance; `context.mjs` loads project context |
| Can read browser? | via Playwright screenshots provided by the agent (no built-in browser tool) |
| Can edit code? | instructions only; the agent edits Vue/TS/CSS |
| Can generate artifacts? | reference guidance, not files |
| Known limitations | must not run `context.mjs` blindly in this repo (it expects its own PRODUCT/DESIGN lifecycle); used for direction + critique, not as an independent design authority |

## frontend-design

| Item | Value |
|---|---|
| Installed at | `C:\Users\Kaiser\.agents\skills\frontend-design\SKILL.md` (+ LICENSE) |
| Version | no pinned version |
| Invocation | Skill tool loads SKILL.md; design-lead guidance for production craft |
| Inputs | brief / subject matter / palette / typography / layout concept |
| Outputs | token system (color/type/layout/principles), implementation guidance |
| Can read browser? | no |
| Can edit code? | instructions only |
| Can generate artifacts? | no (guidance) |
| Known limitations | explicitly must NOT introduce new visual theme / font / palette or stack migration here; may not override the frozen Approved Reference / Design Freeze |

## UI UX Pro Max

| Item | Value |
|---|---|
| Installed at | `C:\Users\Kaiser\.agents\skills\ui-ux-pro-max\SKILL.md` (+ `data/*.csv`, `scripts/search.py`) |
| Version | current installed copy |
| Invocation | `python "C:/Users/Kaiser/.agents/skills/ui-ux-pro-max/scripts/search.py" "<query>" --domain <domain>` (or `--design-system` / `--stack`) |
| Inputs | one dominant intent, 2–5 terms, domain/stack; project stack detected (Vue 3) |
| Outputs | ranked patterns (styles/products/colors/typography/UX guidelines/icons/charts/stacks), reasoning, anti-patterns |
| Can read browser? | no |
| Can edit code? | no (research only) |
| Can generate artifacts? | optional `--persist --output-dir` writes `design-system/<slug>/MASTER.md` + pages |
| Known limitations | this round: research only, no persisted MASTER (Design Freeze is the source); must not override PetAccess tokens/freeze; output goes to `docs/ui/UI_RECONSTRUCTION_PATTERN_RESEARCH.md` |

## Playwright (playwright-cli skill)

| Item | Value |
|---|---|
| Installed at | `C:\Users\Kaiser\.agents\skills\playwright-cli\SKILL.md` (+ `references/*.md`) |
| Version | current installed copy |
| Invocation | Skill tool loads SKILL.md; CLI: `playwright-cli open/goto/click/snapshot/screenshot/...`; also project Playwright test configs (`playwright.config.ts`, `playwright.visual.config.ts`, `playwright.ui-audit.config.ts`) |
| Inputs | page URL, selectors/testids, viewports, route mocks |
| Outputs | snapshots, screenshots, console/request traces, test runs |
| Can read browser? | yes (the visual acceptance authority) |
| Can edit code? | no (test specs are written by the agent) |
| Can generate artifacts? | screenshots, traces, videos, gallery inputs |
| Known limitations | Chromium binaries must be installed (`npx playwright install chromium`); WebKit cannot load the app here; screenshot baselines need a deterministic clock/animations-off |

## Usage rules for this round

1. Impeccable = critique/layout/typography direction only, before editing each page.
2. frontend-design = production craft after structure is frozen; never changes IA/theme/copy.
3. UI UX Pro Max = targeted pattern research only for open questions; results appended to `UI_RECONSTRUCTION_PATTERN_RESEARCH.md`.
4. Playwright = rendered reality + visual QA: baseline capture → per-phase gates → full matrix → before/after gallery.
