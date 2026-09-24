# V020 Design System Spec

Status: M2 Product Experience Foundation — Design System SSOT
Last updated: 2026-09-24
Owner: PetAccess v0.2.0 M2

> This document is the formal definition of the PetAccess **Design System**.
> It pairs with the implementation in `packages/design-tokens` (tokens SSOT) and
> `apps/client-h5/src/components/ui` (base components) and
> `apps/client-h5/src/components/domain` (domain components).
> Page-level `.vue` files must consume tokens and components from here; they must
> not hard-code hex/rgb/hsl, spacing numbers or radius numbers.

---

## 1. Visual position (frozen)

PetAccess is a **城市公共空间动物共处信息工具** (urban public-space animal
coexistence information tool). It is NOT a pet community, a pet shop, a cute-pet
app, a government portal or an engineering dashboard.

Keywords: **Calm · Neutral · Urban · Evidence-first · Modern · Trustworthy ·
Lightweight**.

Practical rules derived from the position:

1. **No wall of green / wall of red.** ALLOWED is a calm green used sparingly,
   PROHIBITED is a muted brick, UNKNOWN is visually neutral, Divergence uses a
   warm amber — never an alarm.
2. **Colour is never the only signal.** Every status carries an icon and a text
   label in addition to colour (see §12 StatusLabel / §15 icon system).
3. **Structure over decoration.** Layering is expressed with spacing, dividers
   and surface hierarchy, not card-nesting or pill overuse.
4. **Evidence-first**: user-facing copy states what was seen / verified /
   recorded, and explicitly what is NOT known.
5. **Rule 与 Reality 是两个事实维度**: rules render as document-like facts
   (「规则」), reality renders as scene-like facts (「现场」) — distinguished by
   structure and icon, not only by colour.

## 2. Token SSOT

The single source of truth for all tokens is
`packages/design-tokens/src/tokens.css` (CSS custom properties) and
`packages/design-tokens/src/index.ts` (typed exports).

Token families (all formally defined):

| Family | CSS prefix | Examples | Notes |
|---|---|---|---|
| color surfaces | `--pa-color-{bg,surface,...}` | `--pa-color-bg-app`, `--pa-color-surface-raised` | §3 |
| color semantic per domain | `--pa-color-{status|reality|facility|evidence}-*` | `--pa-color-status-allowed` | never the only signal |
| text | `--pa-color-text-*` | `--pa-color-text-primary` | includes `-disabled` |
| border | `--pa-color-border-*`, `--pa-border-width*` | `--pa-color-border-subtle` | |
| typography | `--pa-font-size-*`, `--pa-font-weight-*`, `--pa-line-height-*`, `--pa-letter-spacing-*` | `--pa-font-size-base: 15px` | §4 |
| spacing | `--pa-space-*` (4px base) | `--pa-space-1: 4px` … `--pa-space-7: 48px` | §5 |
| radius | `--pa-radius-*` | `--pa-radius-control: 8px` | §6 |
| border width | `--pa-border-width*` | `--pa-border-width: 1px` | |
| shadow/elevation | `--pa-elevation-*` | `--pa-elevation-2` | |
| motion | `--pa-motion-*` | `--pa-motion-base: 200ms` | §7, reduced-motion handled |
| z-index | `--pa-z-*` | `--pa-z-tabbar: 200` | §9 |
| safe-area | `--pa-safe-*` | `--pa-safe-bottom` | §10 |
| component sizing | `--pa-size-control-*`, `--pa-size-icon-*` | `--pa-size-control-lg: 44px` | §11 |
| layout | `--pa-layout-*` | `--pa-layout-rail-width: 232px` | desktop shell |

Breakpoints are consumed in JS (`BREAKPOINTS` in `index.ts`) and documented in
`tokens.css` (CSS custom properties cannot be used inside `@media`):

```
sm 0–479    mobile portrait
md 480–767  mobile landscape / small tablet
lg 768–1023 tablet        (navigation rail starts here)
xl 1024+    desktop H5 / admin
```

Viewports the product must render correctly at:
`320 / 360 / 390 / 430 / 768 / 1024 / 1280 / 1440 / 1920`.

## 3. Color system

Semantic colour groups (all defined in tokens.css):

- **Surfaces**: `bg-app`, `surface`, `surface-raised`, `surface-muted`,
  `surface-interactive` — every layer of the app is a named surface; components
  never invent another grey.
- **Text**: `text-primary`, `text-secondary`, `text-muted`, `text-disabled`,
  `text-inverse`.
- **Lines**: `border`, `border-subtle`, `border-strong`, `border-focus`.
- **Action**: `accent`, `accent-hover`, `accent-active`, `accent-weak`.
- **Rule status**: `status-{allowed,conditional,restricted,unknown,conflict,stale}`
  (+ `-bg` tint for each).
- **Reality**: `reality-{observed,historical,insufficient,disputed}` (+ `-bg`).
  Reality uses calm blue for observed, neutral grey for insufficient/historical,
  warm amber for disputed — reality is a fact dimension, not a verdict.
- **Facility**: `facility-{confirmed,unverified}` (+ `-bg`).
- **Evidence**: `evidence-{verified,pending,disputed,historical}` (+ `-bg`).

Guidelines: ALLOWED never becomes a large bright-green surface; PROHIBITED never
becomes a full danger-red screen; UNKNOWN stays neutral; Divergence is a warm
warning. Colour must never be the sole information carrier.

## 4. Typography

Chinese reading copy uses ≥ 15px (`--pa-font-size-base`) as the default body
size. Hierarchy names used across the app:

| Role | Font size token | Weight | Line height |
|---|---|---|---|
| Display | `--pa-font-size-4xl` (32px) | bold | tight |
| Title L | `--pa-font-size-3xl` (24px) | bold | tight |
| Title M | `--pa-font-size-2xl` (20px) | medium/bold | tight |
| Title S | `--pa-font-size-xl` (18px) | medium | tight |
| Body | `--pa-font-size-base` (15px) | regular | base |
| Body Secondary | `--pa-font-size-md` (13px) | regular | base |
| Label | `--pa-font-size-sm` (12px) | medium | base |
| Caption | `--pa-font-size-xs` (11px) | regular | base |
| Numeric/Metadata | `--pa-font-size-sm-md` | regular | base |

Font stack: `--pa-font-family` (system Chinese-first stack); numeric values may
use `--pa-font-family-numeric`. Metadata must never shrink to unreadable sizes.
Typography is checked at Windows 100%/125%/150% and Android common densities.

## 5. Spacing

Finite 4px-based scale: **4 / 8 / 12 / 16 / 20 / 24 / 32 / 40 / 48**.
Tokens: `--pa-space-1 (4)`, `--pa-space-2 (8)`, `--pa-space-3 (12)`,
`--pa-space-4 (16)`, `--pa-space-20 (20)`, `--pa-space-5 (24)`,
`--pa-space-6 (32)`, `--pa-space-40 (40)`, `--pa-space-7 (48)`.

Page code must not invent values outside this set (13px, 17px, 23px, 29px … are
forbidden). Tight icon/text alignment inside an ≥8px context may use
`--pa-space-1h (6px)` (documented exception, see §16).

## 6. Radius / border / shadow

- Radius ladder (semantic): `--pa-radius-sm (6px)`, `--pa-radius-control (8px)`
  for buttons/inputs/chips, `--pa-radius-md (10px)` for cards,
  `--pa-radius-lg (12px)` for sheets/modals, `--pa-radius-pill (999px)` only for
  segmented controls / tabs / pills.
- Cards are NOT 24px-radius and are not nested by default. Prefer spacing +
  divider + surface hierarchy on dense information pages.
- Border width: `--pa-border-width (1px)`, `--pa-border-width-strong (2px)`,
  `--pa-border-width-focus (2px)` (focus ring).
- Elevation: `--pa-elevation-0..3`; float/hover-lift is discouraged.

## 7. Motion

Only necessary animations: route, sheet, modal, accordion, skeleton.
`prefers-reduced-motion` is honored globally (tokens become 0ms).
No bounce / particle / decorative hover float.

## 8. Breakpoints

See §2 (sm/md/lg/xl + viewport coverage list). Mobile navigation = bottom tabs
(< 768). Tablet + desktop = navigation rail (≥ 768). Desktop uses
`DesktopContentContainer` (three modes: single-column / wide / split-view) —
the 480px mobile reader must never be center-stretched on a large screen.

## 9. Z-index

One ladder: `--pa-z-sticky` (100) → `--pa-z-tabbar` (200) → `--pa-z-banner`
(300) → `--pa-z-sheet` (400) → `--pa-z-modal` (500) → `--pa-z-toast` (600).

## 10. Safe area

`--pa-safe-top/bottom/left/right` = `env(safe-area-inset-*)`. `--pa-safe-total-bottom`
= safe bottom + tabbar height for content clearance. The app shell applies
safe-area padding to the bottom navigation and the desktop rail; pages must not
re-implement safe-area.

## 11. Component sizing

Controls: `--pa-size-control-sm (32)`, `--pa-size-control-md (40)`,
`--pa-size-control-lg (44)` — 44px is the touch-target floor (TOUCH_TARGET_PX).
Icons: `--pa-size-icon-xs (14)`, `sm (16)`, `md (20)`, `lg (24)`, `xl (32)`.
Layout: `--pa-layout-tabbar-height (56)`, `--pa-layout-rail-width (232)`,
`--pa-layout-header-height (56)`, `--pa-layout-content-max (1200)`,
`--pa-layout-content-narrow (640)`, `--pa-layout-content-gutter (24)`.

## 12. Base component catalog

All base components live in `apps/client-h5/src/components/ui/` (prefix `Pa`),
are typed (`defineProps<T>()/{|withDefaults}`), have consistent variants,
accessibility labels, disabled / loading / focus states, and use tokens only.

| # | Component | Props (key) | Variants | Notes |
|---|---|---|---|---|
| 1 | PaButton | variant, size, loading, disabled, block, icon | primary/secondary/ghost/danger | native `<button>` |
| 2 | PaIconButton | icon, label, size, disabled | tonal/plain | 44px touch target |
| 3 | PaTextInput | modelValue, placeholder, label, error, disabled, type | — | labelled input |
| 4 | PaSearchInput | modelValue, placeholder, clearable, loading | — | form input + icon + clear |
| 5 | PaTextarea | modelValue, label, error, disabled, rows | — | — |
| 6 | PaSelect | modelValue, options, label, disabled | — | native select |
| 7 | PaRadio | modelValue, value, label, disabled | — | bound via group |
| 8 | PaRadioGroup | modelValue, options, inline | — | group wrapper |
| 9 | PaCheckbox | modelValue, label, disabled | — | — |
| 10 | PaSwitch | modelValue, label, disabled | — | — |
| 11 | PaTabs | modelValue, tabs[] | — | underline style |
| 12 | PaSegmentedControl | modelValue, options | — | pill segments |
| 13 | PaBadge | text, tone | neutral/info/success/warn | numbers/read-only |
| 14 | PaStatusLabel | semantic, size | block/inline | status = icon+label+colour |
| 15 | PaDivider | spacing | — | — |
| 16 | PaSurface | elevation, padding, interactive | flat/raised | container |
| 17 | PaDialog | open, title, actions | — | role=dialog |
| 18 | PaModal | open, title, footer | — | overlay + escape |
| 19 | PaBottomSheet | open, title, safe | — | mobile sheet |
| 20 | PaToast | kind, message | success/info/warning/error | host in shell |
| 21 | PaBanner | tone, message, action label | info/warn/error | persistent |
| 22 | PaSkeleton | variant, width, height | line/card/circle | — |
| 23 | PaSpinner | size | sm/md/lg | — |
| 24 | PaEmptyState | icon, title, description, primary, secondary | — | unified empty |
| 25 | PaErrorState | presentation, onRetry | — | from error mapping |
| 26 | PaOfflineState | onReconnect, description | — | — |
| 27 | PaListRow | title, description, meta, leading, trailing, to | — | list row |
| 28 | PaMetadataRow | label, value | — | key/value |
| 29 | PaSectionHeader | title, action, actionLabel | — | — |
| 30 | PaPageHeader | title, description, back | — | page shell header |
| 31 | PaIcon | name, size | — | fixed icon family |

Existing migration notes: `StatusBadge` is retained as the rule-status badge and
re-exports semantics from `@petaccess/design-tokens`; `StateMessage` is folded
into `PaEmptyState`/`PaErrorState`/`PaOfflineState` (kept as thin wrappers for
back-compat where needed).

## 13. Domain component catalog

Domain components live in `apps/client-h5/src/components/domain/`. They consume
client-core types and the copy dictionaries; they do NOT fetch data.

| Component | Input | Renders |
|---|---|---|
| RuleStatus | StatusKey / answer | Rule-side status label + icon |
| RealityStatus | RealityAnswer state | Reality-side status label + icon |
| FreshnessStatus | state or last_verified_at | 「近期核验」/「历史记录」… |
| EvidenceStatus | EvidenceStateKey | verified/pending/disputed/historical |
| PlaceListItem | PlaceSummary + answer | name/area-address/primary fact/rule status/reality meta |
| PlaceSummary | PlaceSummary | name + type + address |
| RuleSummary | AccessAnswer | effect + scope + conditions |
| RealitySummary | RealityAnswer | state label + counts + freshness |
| StaffResponseSummary | staff_response_summary | response counts |
| FacilitySummary | facility_summary | facility facts |
| DivergenceSummary | RuleRealityDivergence | warm warning wording |
| EvidenceMeta | evidence_count/sources | 「N 条依据 · X 天前」 |
| ContributionTypeSelector | modelValue, options | type selection for contribution |

Each domain status must go through the copy dictionary (§15) — no page-local
translation of `INSUFFICIENT_OBSERVATION` / `REALITY_*` etc. is allowed.

## 14. Icon system

- Fixed family: stroke-based 24×24 grid, 1.8px stroke, round caps/joins,
  `currentColor` — defined as data in `packages/design-tokens/src/icons.ts`
  (ICONS + ICON_NAMES allow-list).
- Rendered by `PaIcon` (client). No Lucide / Heroicons / Material / emoji may be
  mixed in; emoji is not a legitimate icon.
- Semantic mapping (`SEMANTIC_ICONS`): RULE → document, REALITY → eye,
  EVIDENCE → shield, FACILITY → building, CONTRIBUTION → plus, NAVIGATION →
  location. Pages must not assign a different glyph to the same concept.

## 15. Status copy dictionary

All user-facing translations live in `packages/design-tokens`:

- `STATUS_SEMANTICS` (design-tokens index.ts) — rule status vocabulary
  (ALLOWED/CONDITIONAL/RESTRICTED/UNKNOWN/CONFLICT/STALE) with label + icon +
  ariaLabel + colour vars.
- `REALITY_STATE_COPY` (copy.ts) — the six RealitySummary states with neutral,
  honest wording; `INSUFFICIENT_OBSERVATION` → 「暂无足够现场记录」,
  `NO_RECENT_RECORD` → 「暂无近期现场记录 (暂无记录≠没有动物)」.
- `FRESHNESS_COPY` (copy.ts) — FRESH → 「近期核验」 etc.
- `EVIDENCE_STATE_COPY`, `FACILITY_STATE_COPY`, `DIVERGENCE_COPY` (copy.ts).
- `ERROR_PRESENTATIONS` (copy.ts) — the six domain errors:
  NETWORK_OFFLINE / SERVICE_UNAVAILABLE / AUTH_EXPIRED / MAP_UNAVAILABLE /
  CONTENT_NOT_FOUND / UNKNOWN_ERROR.
- `EMPTY_STATE_COPY` (copy-empty.ts) — Home/Search/Map/Rule/Reality/Staff/
  Facility/Evidence/ContributionHistory.

Rules: UI never shows internal enum strings; no page-local translation; no
「宠物友好/宠物不友好/避雷/黑榜/员工态度差/管理混乱/卫生堪忧」ー ever
(copy test enforces the forbidden list in design-tokens).

## 16. Documented visual exceptions

Page-level hard-coded values are only allowed when registered here with a
reason. M2 list:

| # | Location | Value | Reason |
|---|---|---|---|
| 1 | `apps/client-h5/src/views/*.vue` | none (M2 closes them) | — |
| 2 | `src-tauri` / platform glue (non-UI) | n/a | outside UI layer |

New exceptions must be added to this table before being used in page code.

## 17. Enforcement

- `scripts/engineering_quality_scan*` include `check_ts_colors` (hard-coded
  colour audit) and file-size / component-size rules; page-level scans must stay
  PASS.
- eslint (root flat config) + `vue-tsc --noEmit` + Playwright visual regression
  + a11y (0 critical) are the standing UI gates.
- No new type escapes (`@ts-ignore`) and no new `noqa` to make a gate pass.