# V020 Home UX Report

Status: M2 Product Experience Foundation — Home first-round productization (§19–§22)
Last updated: 2026-09-24
Evidence: `apps/client-h5/src/views/HomeView.vue` (implemented), `tests/visual/consumer.spec.ts` (home-fixture / home-empty baselines), `V020_M2_SCREENSHOT_REVIEW.md` (per-shot DOM audit), `tests/e2e` (copy pinned).

## 1. Product direction (what Home must be)

PetAccess Home answers, in this order:

1. 这是哪里 → coverage header 「上海 · 试点」.
2. 我能搜索什么 → search-first input with one agreed placeholder.
3. 我能查什么 → 2×2 entry grid to the four question areas.

Only below that: recent information (近期查看 / 已核验场所), then Rule/Reality explainability copy. No technical card wall on the first screen, no fake places, no wall of badges.

## 2. First-screen hierarchy (verified in code + screenshot)

| Slot | Copy (as implemented) | testid |
|---|---|---|
| Coverage | 「上海 · 试点」 + 看地图 → | `coverage-area` / `go-map` |
| h1 | 去之前，先看看这里的规则和现场。 | `home-title` |
| Subtitle | 了解场所规则，也参考经核验的现场记录。 | `home-subtitle` |
| Search | placeholder 搜索场所、商圈或地址 (visually-hidden label), submit → /#/search?q=… | `home-search-input` |
| Entry grid (2×2) | 现场是否有动物出现 · 看近期现场记录 · eye<br>室内空间情况 · 商场 · 餐厅 · 场馆室内 · building<br>餐饮区域情况 · 堂食区 · 户外座位 · map<br>完整规则 · 场所全部规则与来源 · document | `entry-presence` / `entry-indoor` / `entry-dining` / `entry-rules` |
| Perspectives | 看场所规则 (default) / 携带动物 / 共处偏好 | `perspective-*` |

The 2×2 grid is rectangular (radius-md), not capsule; icons come from the fixed `PaIcon` family (`packages/design-tokens/src/icons.ts`), not emoji. Desktop (≥768px) turns the grid into a 4-column row inside the real desktop layout (rail left, content full width — no 390px column centered on a 1600px screen).

## 3. Empty state (0 Place must still be a product)

When no published places exist (API returns empty), the first screen above stays intact and below it renders the unified empty state (§26):

- title: 当前还没有已发布的场所数据
- description: 你仍然可以了解 PetAccess 如何区分规则与现场，或者提交第一条线索。
- primary CTA: 探索地图 → /map
- secondary CTA: 贡献线索 → /contribute

Copy comes from the SSOT dictionary `packages/design-tokens/src/copy-empty.ts` (key `HOME`); the page does not invent its own wording. No fake place is ever rendered; the visual `home-empty` baseline asserts `home-empty` is visible and no fixture rows exist.

## 4. Data-present sections (implemented, fixture-verified)

- 最近查看 (`recent-section`): recent rows re-evaluate on open — 「打开时重新求值 —— 规则更新后会以最新结果呈现，不复用旧答案。」 with a 清空 action.
- Category chips (`category-*`) for browsing.
- 附近已核验 / 规则待核实 style sections with explicit semantics notice: 「已核验 = 有规则依据。核验范围写清楚（动物 · 区域），不写成对整个场所的结论。」 — the notice keeps the rule-verdict distinction honest.
- `verified-empty`: 这一区域暂无已核验场所。可切换类别、看地图，或改用搜索指定场所名。

## 5. What is deliberately absent

- No 宠物友好/避雷/黑榜 style judgement copy (§36).
- No internal enum surfaced to the user (§35): statuses render via the unified dictionary/labels, never raw `INSUFFICIENT_OBSERVATION`-style identifiers.
- No technical explanation cards occupying the first screen.
- Production builds never seed fake places (DEV_FIXTURE_MODE is fail-closed, see `V020_REALITY_CONTRIBUTION_GAP_AUDIT.md` and `tests/isolation/test_production_fail_closed.py`).

## 6. QA evidence (this M2 round)

- Visual baselines: `home-fixture` + `home-empty` at 390 / 768 / 1440, light theme — green (see screenshot review).
- DOM audit at 390×844 and 1440×900: 0px horizontal overflow, h1 present, all interactive controls ≥44px.
- Copy pinned by e2e assertions (`tests/e2e/empty-state.spec.ts`).

## 7. Known follow-ups (honest, not done in M2)

- Richer data-present Home (你可能关心 / 近期现场 / 差异) is designed in the goal §21 but not built — it needs production data, which M2 intentionally does not fabricate. Tracked for M3 integration.
