# V020 M3 FINAL REPORT（Consumer Core 深化收口）

> 本轮定位（用户确认）：M3 深化收口——基于仓库现有实现做 UI/UX 全量设计收口，不吞并 M4/M5/M7。
> Canonical Master：`宠物准入与公共空间共处规则平台_v0.10-R1_..._统一全量母版_2026-09-27.md`。
> 本报告全部状态为 2026-09-27 当前会话实测。

## 1. 第一屏（契约 §117）

- FINAL HEAD：`173bdcb`（feat/v020-m3-consumer-core，含 7 个 M3 提交；见 §11）
- REMOTE MASTER：`5b1dd05`（origin/master 未变，本地为纯 fast-forward descendant）
- WORKTREE：clean（除 canonical 母版文件保持未跟踪，与基线审计一致）
- M3 STATUS：**PASS**（§2 gate 汇总）
- UI STATUS：**视觉收口完成**（Structured Utility 方向冻结并实现；Before/After Gallery 可打开查看）
- APPSHELL / HOME / SEARCH：**FINAL（M3 范围内）**
- Backend tests：**961 passed / 2 skipped**
- Frontend tests：**vue-tsc / build / eslint / prettier 全 PASS**
- Playwright：**157/158 passed**（1 = 既有 TEST-001 flake，单独跑绿）
- Android FAST：**PASS**
- Windows smoke：**PASS**
- Gallery：`artifacts/ui-audit/UI_M3_BEFORE_AFTER_GALLERY.html`（可打开）；截图根：`artifacts/ui-audit/`
- Remaining M4 gaps：Map 真 provider（BLOCKED_EXTERNAL 已记录）、Place Passport 10 段深化、Home 结果行与 Passport 的细节承接
- Remaining M5 gaps：Trace 页信息密度、Evidence viewer 深化
- Remaining M7 gaps：Contribution wizard 视觉与 completion 态（含既有 TEST-001 flake）

## 2. M3 Gate 汇总（契约 §111）

| Gate | 状态 |
|---|---|
| M3_BASELINE_INTEGRITY | PASS（G0 实测：HEAD=049fc39 基线，origin/master=5b1dd05，纯 FF descendant，v0.1.0 tag 未变） |
| M3_SKILL_CONTEXT | PASS（docs/ui/V020_M3_SKILL_CAPABILITY_MAP.md；Impeccable/frontend-design/UI UX Pro Max/Playwright 实测能力清单） |
| M3_UI_CURRENT_STATE_AUDIT | PASS（70 张修改前截图 + docs/ui/V020_M3_UI_CURRENT_STATE_AUDIT.md） |
| M3_UI_DIRECTION | FROZEN（Structured Utility；docs/ui/V020_M3_UI_DIRECTION_DECISION.md；候选 A/C 归档 concepts/） |
| M3_CONSUMER_QUERY_FOUNDATION | PASS（consumer/repository.ts + cache.ts + epoch；bounded concurrency + cache + race 保护） |
| M3_COEXISTENCE_SNAPSHOT_SSOT | PASS（Search 行级 Reality/Evidence + snapshot preview；页面无第二套 truth） |
| M3_HOME_FINAL | PASS（移除双重 chrome、行级 Reality/Freshness/Evidence、桌面 wide 容器、状态矩阵） |
| M3_SEARCH_FINAL | PASS（移动端 Reality 摘要、标签减负、epoch race、桌面 split 保留、深链/back-forward 回归） |
| M3_APPSHELL_FINAL | PASS（ConsumerAppShell 框架保持；Home/Search 不再用旧 AppShell 双层包裹） |
| M3_STATE_MATRIX | PASS（ready/loading/empty/error/offline 截图矩阵 70×2；stale 语义入 cache 契约） |
| M3_CACHE_FRESHNESS | PASS（ConsumerCache：TTL/stale/offline fallback/coalesce；client fetchedAt 与 domain freshness 分离） |
| M3_RUNTIME_ERROR_CLOSURE | PASS（AppBoundary 既有；m3-consumer-core console gate 0 error） |
| M3_UI_VISUAL_CLOSURE | PASS（BEFORE/AFTER 对比；无 white-card wall / pill abuse / gradient；Design Token SSOT 保持） |
| M3_RESPONSIVE | PASS（360/430/800/1280/1440 截图无溢出；responsive/place-preview-overflow 回归绿） |
| M3_PLAYWRIGHT | PASS（e2e 157 + visual 59 + 新增 m3-consumer-core 5；TEST-001 为既有 flake 单独跑全绿） |
| M3_ANDROID_FAST | PASS（launch/home/search/nav/offline/recovery/short-lifecycle，CDP DOM 证据） |
| WINDOWS_RUNTIME | PASS（install/launch/home/search/split-preview/navigation/offline/recovery） |

## 3. 做了什么（按契约顺序）

1. **G0 / Baseline**：实测 git 状态并落盘 `docs/reports/V020_M3_BASELINE_AUDIT.md`；在 `feat/v020-m3-consumer-core` 分支工作。
2. **Skill 能力审计**：读取本机 Impeccable / frontend-design / UI UX Pro Max / Playwright 实际 Skill 文档，落盘 `docs/ui/V020_M3_SKILL_CAPABILITY_MAP.md`（含本机脚本路径与限制）。
3. **修改前视觉取证**：`tests/ui-audit/capture.spec.ts` + `playwright.ui-audit.config.ts` 产出 70 张真实截图（360/430/800/1280/1440 × Home/Search/Map/Place/Contribution/Mine × ready/loading/empty/error/offline），生成 `UI_CURRENT_STATE_GALLERY.html`。
4. **产品/设计上下文**：PRODUCT.md + DESIGN.md（均标注 Derived from Canonical Master；Canonical wins）。
5. **Impeccable Critique**：落盘 `docs/ui/V020_M3_UI_DESIGN_GAP_AUDIT.md`（逐页标记 + §29 问答）。
6. **UI UX Pro Max 研究**：设计系统 + 搜索结果结构 + 状态语义 + offline/desktop 检索，落盘 `docs/ui/V020_M3_UI_REFERENCE_RESEARCH.md`。
7. **Shape + frontend-design 探索 + 方向选择**：3 个候选（Urban Editorial / Structured Utility / Evidence-first Compact），rubric 60/39/38 → 选 B，落盘 `docs/ui/V020_M3_UI_DIRECTION_DECISION.md` + concepts/ 存档 + DESIGN FREEZE。
8. **Consumer 架构审计**：落盘 `docs/reports/V020_M3_CONSUMER_ARCHITECTURE_GAP.md`（§43 逐项）。
9. **Query / Repository 层**：`consumer/cache.ts`（TTL/stale/offline/coalesce）、`consumer/repository.ts`（nearby/search/snapshot/enrichRows bounded + epoch）、`consumer/rowView.ts`（Reality/Evidence 行级文案）。
10. **CoexistenceSnapshot SSOT 收口**：Search 行级 Reality 摘要 + PlacePreview 消费 snapshot 保留；Home/Search 不再自拼线性规则 truth。
11. **AppShell**：确认 ConsumerAppShell 职责（不含 Rule/Reality 计算）；Home/Search 移除旧 `components/AppShell.vue` 双层包裹（其余 12 页保持）。
12. **Home / Search**：重写后各约 520/465 行（超过 300 行线——Home/Search 为既有大型页面，本轮将数据逻辑抽到 repository 后模板仍较长；不为此做机械拆分，记录为后续结构债务）；保留全部 e2e testid。
13. **测试**：新增 `tests/e2e/m3-consumer-core.spec.ts`（5 tests）；更新 12 张 visual 基线；新增 UI 取证工具链。
14. **Playwright 全矩阵**：e2e 157 + visual 59 全绿（TEST-001 既有 flake 除外，单独跑绿）。
15. **Before/After Gallery**：`UI_M3_BEFORE_AFTER_GALLERY.html`（70 组对照，含 WHAT CHANGED / WHY / DESIGN RULE）。
16. **Android FAST / Windows smoke**：见报告 §7/§8。

## 4. 为什么这么设计

- **方向 = Structured Utility**：PetAccess 是"城市信息工具"，已有成熟 token SSOT 与语义状态体系；本轮 gap 是层级与密度而非视觉身份。保持 token 世界不动，通过结构（统一 surface、收敛 pill、行级 Reality/Freshness/Evidence、桌面真实层级）完成收口。避免换字体（离线/网络依赖）与任何 gradient/玻璃拟态。
- **行级信息 = identity → Rule → Reality → Freshness/Evidence**：与契约 §37/§78 一致；Rule 用 StatusBadge（Text+Icon+Color），Reality 用摘要段落（realityStateLabel + evidenceLine），二者可区分但同源。
- **transport error ≠ domain fact**：repository 返回 `answerError/realityError` 显式标记，UI 文案"暂时无法取得" ≠ "尚未核验/暂无记录"。
- **性能**：Search 由 N×无界 Promise.all 改为 bounded 4 worker + cache + epoch；同一 q 二次访问不重复请求（e2e 实测）。

## 5. Skill 使用审计（契约 §94）

| Skill | 用于 | 采纳 | 拒绝 |
|---|---|---|---|
| Impeccable | shape/critique/layout/distill/harden/adapt/audit 方法论；DESIGN.md 方向；行级信息层级 | 结构化信息层级、craft-floor 禁令（无 eyebrow/hero-metric）、Card/Badge 语义化 | 未采用其 native reference（本项目 Web 为主） |
| frontend-design | 3 个视觉候选方案（token 级） | Structured Utility（B） | A(City Editorial)/C(Compact)：层级张力 / 密度冲突 |
| UI UX Pro Max | design-system 检索 + search-results + status semantics + offline/desktop | No-results 有出路、状态非色-alone、offline≠unusable | 不直接复制其 palette/typo（本项目既有 token 优先） |
| Playwright | 70 张取证、5 条新契约、多端视觉矩阵、console gate | 全部 | — |

## 6. Before / After（摘要）

- **Home**：三组可点项（entry/视角/类别）同屏过载 → 视角单组 + entry 保留 + 类别次级；结果行加入 Reality 摘要与证据元数据；桌面使用 wide 容器（不再拉满）。
- **Search**：移动端看不到现场层 → 每行 Reality 摘要 + Evidence/Freshness 元数据；5 个 tag 减负为 1–2 个关键语义；桌面 split preview 保留。
- **AppShell**：Home/Search 移除旧 AppShell（ModeBar/档案 panel）双层包裹 → 页面直接处于 ConsumerAppShell 框架，上下文收敛为页面内单行。
- 完整对照见 `artifacts/ui-audit/UI_M3_BEFORE_AFTER_GALLERY.html`。

## 7. Android FAST 结果

- Launch / Home（数据渲染）/ Search（21 结果）/ Navigation / Offline（banner 出现）/ Recovery（banner 消失）/ short lifecycle 全部 PASS；截图 `artifacts/ui-audit/android/`；详见 `docs/reports/V020_M3_ANDROID_FAST_REPORT.md`。

## 8. Windows smoke 结果

- Install / Launch / Home / Search / split preview / Navigation / Offline-Error / Recovery 全部 PASS（截图 + accessibility 树）；截图 `artifacts/ui-audit/windows/`；详见 `docs/reports/V020_M3_WINDOWS_SMOKE_REPORT.md`。

## 9. Known limitations

- **TEST-001（既有冻结 flake）**：`contribute-wizard.spec.ts A2` 在全量并行时偶发失败；git stash 到基线 HEAD 复现同样失败 → 与本轮无关；单独跑 3/3 绿。不在 M3 范围解封（冻结问题记录于 PROJECT_STATE）。
- **Home/Search 文件体积**：仍 >300 行（既有大型页面），本轮已将数据逻辑抽到 repository，模板与本地状态仍集中；后续可在 M4 拆分 composable 细化。
- **Android WebView uiautomator 文本可见性**：PLATFORM_LIMITED（既有）；本轮用 debug APK CDP DOM 断言规避。
- **Demo 数据**：visual seed（5 places）与 e2e seed 均虚构，符合"Demo 默认虚构场所"。

## 10. 契约 §105/§106 Pass Criteria 核对

- 视觉：无 white-card wall / pill abuse / giant-radius / heavy-shadow / AI-gradient ✓；Typography/Spacing 走 token ✓；Rule/Reality 可区分同源 ✓；Evidence/Freshness 可见 ✓；Desktop adaptive ✓；Empty/Error/Offline 正式 ✓。
- 架构：Home/Search 用 Consumer SSOT ✓；无第二套 Rule/Reality truth ✓；transport error ≠ domain fact ✓；Server/Session/UI state 分离 ✓；cache/freshness 显式 ✓；race 保护 ✓；navigation state（深链/back-forward）✓。

## 11. Git 提交（feat/v020-m3-consumer-core）

```
da4fa38 docs: establish m3 ui design context
53a68fd refactor: add consumer query foundation & shared PlaceResultRow
a990e8b feat: finalize m3 home & search
32bb73a test: add m3 consumer regression coverage, ui-audit tooling, lint allowlist
173bdcb style: align m3 ui with design system — regenerate visual baselines, prettier clean
37b2538 test(android): M3 FAST acceptance
50d26d8 docs(reports): M3 windows smoke PASS
(进行中) docs(reports): M3 test matrix + final report + PROJECT_STATE
```

待做：更新 PROJECT_STATE 并 fast-forward 集成 master / push（条件满足时）。