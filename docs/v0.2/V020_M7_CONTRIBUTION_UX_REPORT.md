# V020 M7 Contribution UX — Report

Status: V020_M7_CONTRIBUTION_UX — 本轮实测完成（M7 Contract 批准后执行；三拍板点：①重建向导+移除 TD-015 豁免 ②现实贡献走父流 createRealityReport、规则贡献保持旧端点不迁移（ADR-029）③新增贡献历史端点（仅本人数据））
Last updated: 2026-09-25
基线：M5 已提交（HEAD `4078520`）；M7 全部改动在本轮真实实测后落盘。

## 1. 按验收项逐条状态（证据 = 本轮实际执行）

### A. 贡献向导（重建，无 TD-015）
- **A1 向导入口 — PASS**：`ContributeView.vue` 重写为编排器（171 行，7 步骤状态机
  entry/quick/signage/rule/experience/reality/done），门禁由 `placeId + signedIn` 承担；
  未选场所走 `contribute-needs-place`（去搜索/看地图 CTA）、未登录走
  `PERMISSION_DENIED`（登录 / 注册 CTA）。新增 `ContributeEntry`（51 行）入口屏。
  e2e `A1/A4`：登录注入 `pa_token` → entry 渲染 entry-quick + 三类 reality 入口 → 点
  现场出现 → reality-date/reality-effort/reality-submit 可见，通过。
- **A2 现实贡献经父流提交 — PASS**：新增 `ContributeRealityForm`（200 行）经
  `client.createRealityReport`（report{origin, place_id, observed_at,
  privacy_state=private} + candidates[realityPayload] + effort{duration_bucket,
  animal_observed, observed_at}），成功文案区分 pending/flagged（进入人工审核队列）与
  直接记录。e2e `A2`：填日期/数量 → 提交 → contribute-result 含「已提交」，通过。
- **A3 规则/拍照/快速确认保持旧端点 — PASS（ADR-029，不迁移）**：ContributeQuickForm /
  ContributeSignageForm / ContributeRuleForm / ContributeObservationForm 分别继续走
  verify / upload+createObservation / createRule 陈述 / createObservation 旧端点；
  现实贡献与规则贡献相互独立，不混流。源检查 + e2e A2 提交的候选
  review_status=REVIEW_PENDING 核实。
- **A4 状态完备 — PASS**：loading/error/empty/offline 覆盖（StateMessage +
  presentDescription，无内部字样；offline 由 shell 承担）；提交中 busy 防重复；
  axe 对成就页（1440 桌面 + 390 移动）：signed-out / entry / reality-form 各态
  **0 critical / 0 serious**（顺带修复全部表单 label/select 的程序化关联）。

### B. 贡献历史
- **B1 仅本人数据端点 — PASS**：新增 `GET /api/v1/me/reality-contributions`
  （reality_reports.py，`my_reality_contributions`）：匿名 401（deny-by-default）；
  只返回 `reporter_id == user.id` 的 report（上限 50），候选按 created_at 升序挂靠；
  复用 RealityReport/RealityCandidate，无新模型。集成测试
  `test_my_reality_contributions_lists_only_own_reports`（真实创建 report → 本人可见、
  匿名 401）通过。
- **B2 我的贡献区块 — PASS**：MineView 增加「我的贡献」区块（contribution-row /
  contributions-empty），候选类型经 CANDIDATE_TYPE_LABELS（现场出现记录/工作人员处理
  记录/动物设施记录）、状态经 contributionStatusLabel（REVIEW_PENDING→等待人工核验，
  优先 reality_decision）上屏，无原始枚举。e2e `B2`：新用户空态文案「还没有贡献记录」
  → 提交后首行含「现场出现记录」「等待人工核验」，通过。
- **B3 状态字典收口 — PASS**：CANDIDATE_TYPE_LABELS / CONTRIBUTION_STATUS_LABELS /
  contributionStatusLabel 落在 `reality.ts` 共享词库；MineView 无原始枚举渲染。

### C. Contract / Backend 边界
- **C1 后端改动最小化 — PASS**：仅新增贡献历史端点（1 端点 + RealityCandidate 导入，
  reality_reports.py）；现实贡献直接复用既有 `createRealityReport`，无新模型/表/
  migration。结束前全量回归重跑：DISCOVERED 947 = **945 passed / 2 skipped / 0 failed**
  （43s；TEST DB + Celery worker 同命令存活）。
- **C2 client 契约不漂移 — PASS**：`client.myRealityContributions()` 以类型化返回接入
  client.ts；contract/version-drift 检查全绿；无新 ts-ignore / exemption（见 D5）。

### D. Engineering Gates（全绿，实测）
- **D1**：`check_engineering_quality.py` **0 FAIL**（60 REVIEW / 34 WARN）；ruff check
  PASS；ruff format（含 docs）PASS；mypy 96 files / 0 errors。
- **D2**：backend 全量回归重跑 → 见 C1。
- **D3**：`pnpm lint:fe` PASS；`pnpm format:check:fe` PASS；client-h5 build
  （vue-tsc + vite）PASS；admin 未触及。
- **D4**：Playwright visual **59 passed**（compare；contribute 家族因向导重构重生成
  contribute-h5-390 + reality-trace 变量）；Playwright e2e 全量 **90 passed / 0 failed**
  （含新增 contribute-wizard 3 条：A1/A4、A2、B2）。
- **D5**：零新增 ignore / exemption / ts-ignore；移除 TD-015 的 ContributeView 豁免后
  豁免数 196→195→196（新增为 my_reality_contributions 死代码豁免，TD-028
  decorator-registered 类别，与其余 @router 端点一致）。

### E. 交付
- **E1 本报告落盘**（此文件）。
- **E2**：PROJECT_STATE.md 更新为 M5 完结 + M7 完结（M6 空缺，见边界；下一
  V020_M8_DESKTOP_FINAL）；无新架构决策，ADR-029 沿用不改写。
- **E3 视觉基线**：contribute-h5-390 重生成（向导重构）+ reality-trace 变量更新；
  compare 59 passed。

## 2. 本轮新增/变更文件

- 新增：`components/contribute/`（ContributeEntry 51 / ContributeQuickForm 91 /
  ContributeSignageForm 195 / ContributeRuleForm 117 / ContributeObservationForm 112 /
  ContributeRealityForm 200 / ContributeDone 22 / contributeSupport.ts 支撑
  proximity/evidenceRefs/reportOrigin/isoAt/presenceStaff/facilityPayload/realityPayload）、
  `tests/e2e/contribute-wizard.spec.ts`（A1/A4、A2、B2 共 3 条）、视觉基线
  contribute-h5-390-win32.png 重生成。
- 修改：`views/ContributeView.vue`（171 行编排器重写，769 行旧单体拆分）、
  `views/MineView.vue`（我的贡献区块）、`views/RealityTraceView.vue`（199 行重写压行、
  移除 scoped 冗余 label 块/合并 margin-top）、`reality.ts`（贡献词库字典）、
  `packages/client-core/src/api/client.ts`（myRealityContributions）、
  `services/api/app/api/v1/reality_reports.py`（GET /me/reality-contributions +
  RealityCandidate 导入）、`tests/integration/test_reality_report_api.py`
  （my_reality_contributions 集成测试）、`scripts/gate_exemptions.json`
  （-TD-015 ContributeView +TD-028 my_reality_contributions）。

## 3. 契约状态表（schema / service / API / client / UI / tests）

| 能力 | schema | service | API | client | UI | tests |
|---|---|---|---|---|---|---|
| 向导编排器（7 步状态机 + 门禁） | — | — | — | — | IMPLEMENTED | IMPLEMENTED (e2e A1/A4) |
| 现实贡献父流（createRealityReport） | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED (RealityForm) | IMPLEMENTED (e2e A2) |
| 规则/拍照/快速确认旧端点 | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED（ADR-029 不迁移） | IMPLEMENTED |
| 贡献历史端点（仅本人） | IMPLEMENTED | IMPLEMENTED | IMPLEMENTED（新，401 匿名） | IMPLEMENTED | IMPLEMENTED（MineView 区块） | IMPLEMENTED (集成 + e2e B2) |
| 状态字典（无原始枚举） | — | — | — | — | IMPLEMENTED | IMPLEMENTED (e2e B2) |
| a11y（贡献态全家） | — | — | — | — | IMPLEMENTED（label 程序化关联） | IMPLEMENTED（axe 0/0） |

状态词仅允许 IMPLEMENTED / PARTIAL / MISSING / NOT_WIRED / NOT_TESTED。

## 4. 边界遵守

- 现实贡献（observed_presence/staff_response/animal_facility）走父流
  createRealityReport；规则/拍照/快速确认保持旧端点不迁移（ADR-029，用户拍板点 ②）。
- 贡献历史为新增契约缺口端点 `GET /me/reality-contributions`，仅本人数据、匿名 401、
  无新模型（复用 RealityReport/RealityCandidate）。
- 未扩 scanner、未重做 M2–M5、未跨里程碑（M6 空缺）；真实腾讯地图无 Key →
  BLOCKED_EXTERNAL（沿用 M4 记录，未触碰）。
- TD-015（ContributeView 豁免）已关闭；新增 my_reality_contributions 豁免仅走
  TD-028 decorator-registered 类别。
- 分片提交：M7-A..C（代码/基线/测试）+ M7-D（报告与状态），不混杂无关格式化。

**Overall: V020_M7_CONTRIBUTION_UX = PASS**（A1–A4 / B1–B3 / C1–C2 / D1–D5 / E1–E3
全部实测通过）。