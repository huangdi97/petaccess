# V020 M2 Screenshot Review

Status: M2 Product Experience Foundation — per-image review
Last updated: 2026-09-24
Method: **not pixel-diff-only**. Every M2 baseline family was rendered again in a
headless browser and audited by DOM measurement per shot (alignment/overflow/
density/hierarchy/tap targets/safe area/empty quality), then the generated
baseline PNGs were visually inspected against those measurements.

## 1. Baseline families generated (light theme)

Regenerated with `playwright.visual.config.ts` (viewports h5-390 / h5-768 /
h5-1440 → mobile + tablet + desktop):

| Family | Mobile | Desktop | Data |
|---|---|---|---|
| home-fixture | ✓ | ✓ | reseeded visual DB (5 places) |
| home-empty | ✓ | ✓ | API intercepted → 0 published places |
| search-fixture | ✓ | ✓ | 咖啡 query results |
| search-empty | ✓ | ✓ | nonexistent query |
| offline | ✓ | ✓ | network dropped after load |
| error | ✓ | ✓ | API forced 500 |
| map / map-sheet | ✓ | ✓ | seeded markers |
| place-unknown / place-conditional | ✓ | ✓ | seeded fixtures |
| rule-trace / contribute / mine / boundary | ✓ | ✓ | seeded data |

Total: **42 consumer shots** + 14 admin shots (admin unchanged by M2 tokens;
verified unchanged against existing baselines). `assertNotErrorState` guard
kept for every shot except the two intentionally-error families (offline,
error) which pass `allowErrorState: true`.

## 2. Per-shot DOM audit (evidence, not diff)

Measured at 390×844 and 1440×900 for every family:

| Dimension | Result | Notes |
|---|---|---|
| Horizontal overflow | **0px everywhere** (18/18 scenes) | `scrollWidth ≤ innerWidth` at both viewports; matches responsive e2e (9 viewports × 5 pages, all PASS) |
| Navigation | mobile → `mobile-tabbar` (57px tall), desktop → `desktop-rail` | correct breakpoint switch at 390 vs 1440; no dual-nav on any shot |
| Page h1 | present on every scene | home title 去之前，先看看这里的规则和现场。 / search 搜索场所规则 (visually hidden) / map 规则地图 / contribute 现场贡献 / mine 我的 |
| Tap targets | **0 elements under 44px** across all scenes (23 buttons on home-fixture mobile, all ≥44px) | a11y floor met on interactive controls |
| Body typography | consistent `13px` muted text, `12px` notice, h1 `20px` | no orphan font sizes in the audited set |
| Home empty quality | `home-empty` block = icon + title 当前还没有已发布的场所数据 + description + 探索地图 / 贡献线索 CTAs | no fake place rendered; copy pinned by e2e too |
| Search empty quality | 没有找到已收录场所 + 试试其他关键词，或提交一个新的场所线索。 + 提交场所线索 CTA | never 这里没有宠物 |
| Offline quality | `global-offline-banner` 当前离线，部分内容可能不是最新状态。 + 重连 | banner above content; cached content stays visible |
| Error quality | unified `[data-state="ERROR"]` block with 重试 | no 500/SQLAlchemy/FastAPI/Tauri/Rust/stack strings in page text |
| Safe area | mobile tabbar `padding-bottom` = computed `env(safe-area-inset-bottom)` length | verified by navigation e2e; desktop rail has safe-bottom padding |

## 3. Visual checks (human-style, per image family)

- **home-fixture**: first screen = coverage header (上海 · 试点 + 看地图) → title
  → subtitle → search field with the exact placeholder → 2×2 entry grid with
  icons; then recent section, category chips, and the two data sections
  (附近已核验 / 规则待核实) below; semantics notice sits under the data, above
  the footer. No technical card wall on the first screen. Desktop: rail left,
  content full-width to the rail edge (no 480px centering), entries become a
  4-column row.
- **home-empty**: identical first screen; below it the empty state block is
  centered with icon circle, title, description, and two buttons. Density is
  calm; no wall of badges.
- **search-fixture**: single-column container; input + clear button + submit;
  recent chips under input; results are RouterLink rows with name/address/rule
  summary/tags; rule status badge right-aligned. Desktop keeps the same column
  at the content width (no stretched mobile row).
- **search-empty**: same chrome with the required copy; CTA to /contribute.
- **offline / error**: the global banner (offline) or error block (error) is
  the primary signal; nav stays visible in both, so recovery is one tap.
- **map / place / rule-trace / contribute / mine / boundary / map-sheet**:
  unchanged views under the new shell; baselines regenerated because the shell
  (tabbar/rail) changed; verified visually consistent — no card-nesting, no
  emoji icons (icons now come from the fixed PaIcon family in the redesigned
  Home/Search; legacy views keep their existing glyph labels, tracked as an
  incremental clean-up for M3).

## 4. Six UI ills check (V020 goal §5 / §8)

| Ill | Status |
|---|---|
| Card-stacking | No new nested-card layouts; Home uses entry grid + flat list sections |
| Pill overuse | Entry cards are rectangular (radius-md), not capsules; pills limited to filters/perspectives |
| Hard-coded spacing/colors | Home/Search scoped styles converted to tokens; scan for hex in views → see engineering report |
| Emoji as icon | Redesigned Home/Search use the fixed PaIcon SVG family; legacy glyphs tracked |
| Over-saturated green/red | Status tints kept muted (allowed green `#2e7d52` on tint, restricted brick `#8f4a3a`); no large fills |
| Desktop whitespace | Desktop rail + content container; no centered-390px look (measured: content spans to rail edge) |

## 5. Conclusion

All 42 consumer baselines regenerated and green in compare mode; DOM audit
above confirms alignment/spacing/density/hierarchy/overflow/tap-target/safe-area
quality per shot. Screenshot review: **PASS**.

## 6. A11y machine-scan closure (axe-core, added during M2-G)

After the per-shot DOM audit, an axe-core 4.10 pass ran over the six M2
families (home-fixture / home-empty / search-fixture / search-empty / offline /
error at 390×844, mobile context). First pass: 4 critical + 6 serious.

Fixed:

- `.home-entries` had `role="list"` with plain `<button>` children (axe
  `aria-required-children`, critical). Removed the bare role — the group is a
  plain div of labelled buttons; nothing is lost to AT.
- `--pa-color-text-muted` was `#69747f` — 4.36:1 on the app background and
  ~4.2:1 on the sunken surface (`.muted` / `.notice` text, serious colour
  contrast). Darkened to `#5c6772`: ≥5.3:1 on app bg, ≥5.0:1 on sunken,
  ≥5.7:1 on white — closing the goal §5 "灰色字过浅" item at token level
  (status colours `reality-historical` / `facility-unverified` /
  `evidence-historical` keep `#69747f`; they are badge tints, not text).

Final pass: **critical = 0, serious = 0** on all six families. Consumer
baselines regenerated to capture the token change (all green in compare mode).
