# V020 Search UX Report

Status: M2 Product Experience Foundation — Search first-round productization (§23–§25)
Last updated: 2026-09-24
Evidence: `apps/client-h5/src/views/SearchView.vue` (implemented), `tests/visual/consumer.spec.ts` (search-fixture / search-empty baselines), `V020_M2_SCREENSHOT_REVIEW.md` (per-shot DOM audit), `packages/design-tokens/src/copy-empty.ts` (SSOT copy).

## 1. Scope (what M2 Search is)

Search is a Home-level feature, not a forced bottom tab (§15). This round implements the full query loop:

query input → clear → submit → loading → results | empty | error

Supported fields: place name, address, district, business area (via the existing search API + alias matching). Filters are kept minimal on purpose (§23): only the necessary ones (verified / pet-zone / service-dog presence, with the hint 「默认不过滤“信息不足”。筛选只影响显示，不改变任何结论。」).

## 2. Page chrome (verified in code)

- h1 (visually hidden for a11y): 搜索场所规则
- Input: placeholder 搜索场所、商圈或地址, `aria-label=搜索场所`, testid `search-input`
- Clear button: `aria-label=清除`, testid `search-clear` — appears once there is text
- Submit button: 搜索, becomes 搜索中… while loading, testid `search-btn`
- 最近搜索 bar (`search-recent`): recent terms as chips (`recent-search-*`), with a 清除 action

## 3. Result anatomy (one row = one decision)

Each result row (`result-<name>`) is a RouterLink to the place page and renders, top to bottom:

1. **Name** + unified **status badge** (from the single answer model — the verdict and its conflict state come from one source, no two-engine-per-row).
2. **所属 branch** (`result-branch`): parent brand / container, shown first so a branch's rules are never read as the whole brand's (「所属」 not 「位于」 — true for both 分店 and 商场里的店铺).
3. **Type · address** (`result-meta`): 咖啡 · 上海市·栖霞路45号; 地址待补充 when missing.
4. **Match reason** (`result-alias`): 以「…」匹配（曾用名／别称） — explains why a place the user never named came back.
5. **Rule summary** (`result-rules`): 生效规则 N 条 · 近期核验 / 尚未收录规则 — the "is there anything to read here" line, never a verdict (the badge is the verdict).
6. **Row tags**: 已核验 / 独立携宠区 / 含服务犬信息 — listing facts, explicitly not conclusions.

Loading uses `SkeletonList` (stable structure, no layout shift); full-page spinner is not used (§27).

## 4. Empty state (pinned by test)

Unified copy from `copy-empty.ts` (key `SEARCH`):

- title: 没有找到已收录场所
- description: 试试其他关键词，或提交一个新的场所线索。
- primary CTA: 提交场所线索 → /contribute
- secondary: 清除筛选 (only when filters are active)

`tests/visual/consumer.spec.ts` asserts the title text in-page; the phrase 这里没有宠物 never appears (§25).

## 5. Error state

Network/API failure renders the unified error presentation (no 500 / SQLAlchemy / FastAPI / stack strings):

- message: 当前无网络连接，搜索需要联网。
- action: 重试 re-runs the search.

## 6. Perspective lens

Search honours the Home perspective (default 看场所规则; when presence perspective is active the lens hint explains the re-ranking): 「正按「现场是否有动物出现」查看 —— 结果将优先展示近期有现场记录的场所」.

## 7. QA evidence (this M2 round)

- Visual baselines: `search-fixture` (咖啡 query) + `search-empty` at 390 / 768 / 1440, light theme — green (screenshot review).
- DOM audit: single-column container at desktop content width (no stretched mobile row), 0px horizontal overflow, tap targets ≥44px.
- e2e pins the empty copy and CTA (tests/e2e).

## 8. Known follow-ups (honest, not done in M2)

- Split-view desktop Search (result list + preview pane) is designed (§17/§33) but deferred to M3 integration with PlacePreview.
- Result rows intentionally carry rule + reality *summary*; the full evidence surface is M5 scope.
