# V020 M4 Map + Place Passport — Report

Status: V020_M4_MAP_AND_PASSPORT — 本轮实测完成（M4 Contract 批准后执行）
Last updated: 2026-09-24
基线：M2/M3 已提交（HEAD `21566c6`）；M4 全部改动在本轮真实实测后落盘。

## 1. 按验收项逐条状态（证据 = 本轮实际执行）

### A. Map Pane
- **A1 桌面 split-view — PASS**：≥md 时 Map 使用 `DesktopContentContainer mode="split"`
  （左地图 + 右 PlacePreview 详情面板），选中标记/簇 → 详情面板，桌面自动预选首条；
  移动端维持地图 + bottom sheet + 列表回退（390 基线形态不变）。e2e
  `A1 — desktop 地图 split-view` 通过；visual `map-split`（768/1440 新家族）compare 全绿。
- **A2 Map 状态收口 — PASS**：empty 走 `EMPTY_STATE_COPY.MAP`（地图暂无已发布场所 +
  返回首页，e2e 断言）；loading 保持 MapLoadingOverlay + SkeletonList；error 改走
  `presentError`（修复 `未能取得附近场所：${error}` 原始泄漏，e2e 拦截 500 断言页面无
  SQLAlchemy/FastAPI/psycopg2 字样）；移除 MapView 本地 offline-banner，offline 由 shell
  GlobalOfflineBanner 单一承担。
- **A3 Map a11y — PASS**：MockMap 簇标记保持 role=button/tabindex/aria-label 键盘可操作，
  选中态经 `selected-id` 高亮 + PlacePreview 面板呈现；列表回退（view=list）对 SR 可达；
  axe 对 map 表面（split 桌面 / 深链预览）**0 critical / 0 serious**。
- **A4 Map 深链 — PASS**：`/#/map?place=<id>` 预选并在桌面面板打开；
  `syncRoutePlace` 将选择写入 query，`watch(route.query.place)` 支持 back/forward
  同步（e2e `A4`：深链→未知 id→goBack 恢复→goForward 恢复空态，通过）。

### B. Place Coexistence Passport（收口，未重建 10 段骨架）
- **B1 Passport 完整性校验 — PASS**：fixture 场所（云栖中心·测试商场）e2e 断言
  section-answer / sources / 7.来源与时效 / reality-panel / observations /
  observation-disclaimer 全部渲染；place-unknown / place-conditional 家族基线
  compare 全绿。
- **B2 Rule vs Reality 视觉分层 — PASS**：Passport 中「当前答案/区域/来源与时效」
  （规则维度）与「Reality 面板/现场记录 + 现场记录 ≠ 场所正式政策 免责声明」
  （现实维度）结构可辨、措辞字典化；e2e B1/B2 断言两维度段均存在且标签清晰。
- **B3 证据视觉语言 — PASS**：Section 7 接入共享 `EvidenceStatus`（
  verified/pending/disputed/historical，经 EVIDENCE_STATE_COPY 渲染）+ `EvidenceMeta`
  （依据条数/来源数）+ `FreshnessStatus`（时效）；`passportEvidence` 将
  `reality_verification_state` 原始枚举映射为视觉状态，e2e 断言页面无
  VERIFIED/PENDING/DISPUTED/HISTORICAL 原始字符串。
- **B4 桌面阅读列 — PASS**：Place 页面接入 `DesktopContentContainer
  mode="single-column"`（桌面居中可读列）；place 家族 1440 基线 compare 全绿。
- **B5 预览→Passport 导航 — PASS**：Search PlacePreview「查看完整场所」→ Place
  页面 Passport（section-answer + reality-panel）e2e 通过。
- **B6 Place a11y — PASS**：axe 对 place passport 表面 **0 critical / 0 serious**
  （顺带修复：`--pa-color-status-allowed #2e7d52 → #277348`，徽章文本在 tint 背景上
  对比度 4.38:1 → 5.06:1；M2 §7 的"平静绿"原则保持，仅加深文本前景）。

### C. Provider / Backend 边界
- **C1 Provider 状态 — PASS（如实记录 BLOCKED_EXTERNAL）**：`get_map_provider`
  工厂保持 mock-first；真实腾讯地图接线需要 `TENCENT_MAP_KEY_*` 密钥，仓库无
  密钥 → 记录 **BLOCKED_EXTERNAL**（不伪造 PASS、不假接线）；本次交付渲染器为
  MockMap（provider-neutral，与 Tencent 行为一致的设计保持）。
- **C2 后端零功能新增 — PASS**：本轮 **backend 0 文件改动**（services/api 未触及），
  无新功能模型；结束前全量回归重跑：DISCOVERED 946 = **944 passed / 2 skipped /
  0 failed**（54.1s；TEST DB reset + Celery + MinIO）。

### D. Engineering Gates（全绿，实测）
- **D1**：`check_engineering_quality.py` **0 FAIL**（60 REVIEW / 29 WARN）；
  ruff check PASS；ruff format（含 docs）469 文件干净；mypy 96 files / 0 errors。
- **D2**：backend 全量回归重跑 → 见 C2。
- **D3**：`pnpm lint:fe` PASS；`pnpm format:check:fe` PASS；client-h5 build
  （vue-tsc + vite）PASS；admin 未触及（D3 按约定豁免）。
- **D4**：Playwright visual（consumer）compare **42 passed**；Playwright e2e 全量
  **82 passed / 0 failed**（新增 7 条 M4 map/passport 测试；2 次并行负载 flake 经
  复跑确认非代码问题；h5-shell 1 条断言从旧文案「加载失败」更新为统一错误标题
  「未能取得场所信息」——这是呈现升级导致的既有断言对齐，非弱化）。
- **D5**：零新增 ignore / exemption / ts-ignore。

### E. 交付
- **E1 本报告落盘**（此文件）。
- **E2**：PROJECT_STATE.md 更新为 M3 完结 + M4 状态；无新架构决策（沿用 ADR-029
  统一消费），不新增 DECISIONS 条目。
- **E3 视觉基线**：map-split（新，768/1440）、map / map-sheet（390 保留）、
  place-unknown / place-conditional（全视口，ALLOWED 徽章色 + 阅读列 + 证据行）、
  search 桌面（ALLOWED 色）重生成，compare 42 passed。

## 2. 本轮新增/变更文件

- 新增：`tests/e2e/map-passport.spec.ts`（A1/A2/A4、B1/B2/B3/B5 共 7 条）、
  视觉基线 `map-split-h5-{768,1440}`。
- 修改：`views/MapView.vue`（split + 深链 + 状态收口 + 移除本地 banner）、
  `views/PlaceView.vue`（阅读列 + 统一错误 + Section 7 证据视觉语言）、
  `packages/design-tokens/src/tokens.css`（status-allowed 对比度）、
  `tests/visual/consumer.spec.ts`（map-sheet 视口分支 → map-split）、
  `tests/e2e/h5-shell.spec.ts`（错误断言对齐新标题）、相关视觉基线。
- 删除：`map-sheet-h5-{768,1440}.png`（被 map-split 家族取代）。

## 3. 契约状态表（schema / service / API / client / UI / tests）

| 能力 | schema | service | API | client | UI | tests |
|---|---|---|---|---|---|---|
| Map 桌面 split（地图+详情） | — | — | IMPLEMENTED (nearby/coexistence) | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED (e2e A1 + visual map-split) |
| Map 深链 / 选择同步 | — | — | — | — | IMPLEMENTED | IMPLEMENTED (e2e A4) |
| Map empty/error/offline 收口 | — | — | — | — | IMPLEMENTED | IMPLEMENTED (e2e A2) |
| Place Passport 10 段 | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED（收口：阅读列 + 证据视觉语言） | IMPLEMENTED (e2e B1/B2/B5) |
| 证据视觉语言（§34） | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED (e2e B3) |
| Map provider（真实） | — | PARTIAL（工厂存在，API 未接线） | NOT_WIRED | — | — | NOT_TESTED → 记录 BLOCKED_EXTERNAL |

状态词仅允许 IMPLEMENTED / PARTIAL / MISSING / NOT_WIRED / NOT_TESTED。

## 4. 边界遵守

- 未重建 PlaceView 10 段骨架；未建 Reality Trace / Evidence viewer（→M5）与完整
  Contribution wizard（→M7）。
- 真实腾讯地图无 Key → **BLOCKED_EXTERNAL 如实记录**，MockMap 为交付渲染器。
- 未引入 AI recommendation / moderation / crawler / 真实数据 seed；未扩 scanner、
  未新增整目录豁免；未重做 M2/M3。

**Overall: V020_M4_MAP_AND_PASSPORT = PASS**（A1–A4 / B1–B6 / C1–C2 / D1–D5 /
E1–E3 全部实测通过；C1 含如实记录的 BLOCKED_EXTERNAL 项）。