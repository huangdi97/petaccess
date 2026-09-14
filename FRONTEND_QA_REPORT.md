# FRONTEND_QA_REPORT.md

> P3 前端质量报告 · 对应 `UI_UX_IMPLEMENTATION_SPEC.md` §11
> 执行时间：2026-09-13（GMT+8）· 基准 commit `08ee60c` + 本轮改动

---

## 1. 本轮交付

| 产物 | 位置 | 状态 |
|---|---|---|
| 设计令牌包（此前为**空目录**） | `packages/design-tokens`（`package.json` / `src/index.ts` / `src/tokens.css` / `tsconfig.json`） | ✅ 新增 |
| 令牌消费 | `apps/client-h5/src/styles.css` `@import "@petaccess/design-tokens/tokens.css"` + 局部别名 | ✅ |
| 状态徽标组件（icon + 文字 + 颜色） | `apps/client-h5/src/components/StatusBadge.vue` | ✅ 新增 |
| 来源徽标组件 | `apps/client-h5/src/components/SourceBadge.vue` | ✅ 新增 |
| Place Detail 接入新语义 | `apps/client-h5/src/views/PlaceView.vue` | ✅ |
| 文案中性化（"可进入/限制/信息不足" → "明确允许/明确限制/尚未核验"） | `PlaceView.vue` + `design-tokens` | ✅ |
| 可访问性基线（focus-visible / 44px 触控 / visually-hidden） | `styles.css` | ✅ |
| 机读守卫测试（令牌完整性 + 状态三通道 + 禁用词扫描 + UNKNOWN 语义） | `tests/unit/test_design_tokens.py`（7 项） | ✅ |
| 工作区链接 | `apps/client-h5/node_modules/@petaccess/design-tokens` → `packages/design-tokens` | ✅ |

---

## 2. 构建与产物验证（实测）

### 2.1 H5（`apps/client-h5`）

```
$ vue-tsc --noEmit && vite build
✓ 63 modules transformed.
dist/assets/index-C8nVeOzm.css      6.86 kB │ gzip: 2.10 kB
dist/assets/PlaceView-DfS9nZlt.js  10.25 kB │ gzip: 4.21 kB
dist/assets/index-7wBgUnTt.js     102.03 kB │ gzip: 39.55 kB
✓ built in 4.84s
```

类型检查（`vue-tsc --noEmit`）通过。

### 2.2 令牌确实进入产物

```
$ grep -o "\-\-pa-color-status-[a-z]*" apps/client-h5/dist/assets/*.css | sort -u
--pa-color-status-allowed
--pa-color-status-conditional
--pa-color-status-conflict
--pa-color-status-restricted
--pa-color-status-stale
--pa-color-status-unknown

$ grep -o "status-badge[a-z_-]*" apps/client-h5/dist/assets/*.css | sort -u
status-badge
status-badge--block
status-badge__icon
```

**复核（全新 outDir 重跑）**：`grep -o -- '--pa-[a-z0-9-]*'` 去重后共 **60 个令牌**；
其中状态色令牌 **12 个** = 6 态 × (前景 + `-bg` 底色)，
即 `--pa-color-status-{allowed,conditional,restricted,unknown,stale,conflict}` 及其 `-bg`。

结论：设计系统不是装饰性文档，而是真实进入构建产物。

### 2.3 Admin（`apps/admin`）

```
$ vue-tsc --noEmit && vite build
✓ built in 3.61s   （24 个视图，无回归）
```

### 2.4 构建环境说明（沙箱）

默认 `pnpm build` 写入 `dist/`，会触发本机沙箱的批量删除保护：

```
[safe-delete][SAFE_DELETE_BULK_CONFIRM_REQUIRED] {"count":72,"threshold":50,
 "targets":["...apps\\client-h5\\dist\\assets"],"targetCount":1}
```

原因是 Vite 的 `prepareOutDir` 需清空 `dist/assets` 下 72 个旧文件（超过阈值 50）。
这是**沙箱策略限制，不是代码缺陷**——`vue-tsc` 在清目录之前已通过。改用全新
`--outDir dist-verify` 后两端均构建成功，验证完成后临时目录已删除。

---

## 3. 自动化测试

| 测试 | 结果 |
|---|---|
| `tests/unit/test_design_tokens.py` | ✅ 7 passed |
| 其中：状态必须 icon+文字+颜色 | ✅ |
| 其中：前台源码禁用词零命中（扫描 60+ `.vue`/`.ts`） | ✅ |
| 其中：UNKNOWN 不得表述为允许 | ✅ |
| 其中：令牌组完整性（color/space/radius/font/elevation/motion/layout） | ✅ |

---

## 4. UI_UX_IMPLEMENTATION_SPEC §11 检查项

| 检查项 | 结果 |
|---|---|
| 关键页面无 layout shift | ⏸ **未验证**（需 Playwright 截图基线 + 可运行 API） |
| 不溢出 | 🟡 静态审查未发现；未做自动化 |
| 中文断行合理 | 🟡 依赖系统字体栈；未做自动化 |
| dark/light 若实现则一致 | ❌ **dark 未实现**（令牌已可覆盖，见 `DESIGN_SYSTEM.md` §7） |
| Playwright 截图覆盖 9 个页面 | ❌ **未采集** |

**为何未采集视觉回归**：`playwright.config.ts` 的 `webServer` 依赖 `vite preview`（可独立运行），但 9 个目标页面（home map / list / detail allowed / detail conditional / detail unknown / boundary / contribution / evidence review / admin candidate）中有 6 个需要 API 返回真实数据才能渲染出有意义的状态。当前 ENV-01（无 PostGIS）使 API 不可启动，截图只会得到错误页。**不伪造截图基线。**

---

## 5. 缺口与后续（诚实记录）

| # | 缺口 | 阻塞源 | 建议阶段 |
|---|---|---|---|
| 1 | 地图首页交互壳（marker clustering / bottom sheet / filter chips / 定位 / list-map 切换 / coverage hint） | 地图 provider（B-04）+ 数据层（ENV-01） | P3 续 / P5 |
| 2 | Place Detail 的 10 个 Section 未完整（缺条件 / 共处边界 / 进入方式 / 设施 / 版本历史） | 部分依赖后端字段（Zone/Amenity/Entrance/AccessPath 已有表，需接线） | P3 续 |
| 3 | skeleton / offline 状态 | 无 | P3 续（可立即做） |
| 4 | 视觉回归截图基线 | ENV-01 | P8 |
| 5 | 设计令牌接入 `apps/admin` 与 `apps/client`(uni-app x) | admin 接入无阻塞；uni-app x 需 HBuilderX（B-01） | P4 / P9 |
| 6 | 搜索页筛选 chips（明确允许/有条件/明确限制/已核验/最近核验/独立宠物区/仅户外/推车/服务犬/冲突） | 数据层 | P3 续 |

---

## 6. 判定

```text
UI_FRONTEND_PRODUCTION_GATE = PARTIAL
```

- **PASS 的部分**：设计令牌体系落地并进入产物；状态三通道语义强制化；中性文案机读守卫；可访问性基线；H5 与 Admin 类型检查与构建通过。
- **未 PASS 的部分**：地图交互壳、Place Detail 完整 Section、skeleton/offline、视觉回归基线。
- 未 PASS 项中，第 1、2（部分）、4、6 项**受 ENV-01 / B-04 直接阻塞**；第 3 项可立即实施。

---

## 7. 本轮增量（commit `716b163`）

本节记录在 §1–§6 之后追加的实现，上一节的缺口清单中第 3 项（skeleton / offline）已在本轮消除。

### 7.1 Admin 接入设计系统（此前完全未接入）

| 项 | 前 | 后 |
|---|---|---|
| 令牌依赖 | ❌ 自有 `--bg/--panel/--line/...` 临时变量 | ✅ 依赖 `@petaccess/design-tokens` |
| 令牌入产物 | 0 个 | **65 个** |
| 硬编码颜色 | 9 处 hex + 1 处 rgba | 0 |
| 状态语义 | `.tag.ok/.restricted/.warn` 裸色块（含义只在类名里） | 共享 `StatusBadge.vue`（icon+文字+aria） |
| 来源徽标 | 无 | 共享 `SourceBadge.vue` |

**零标记改动的接入方式**：保留短名（`--bg: var(--pa-color-bg-app)`），因此 24 个存量 Admin 视图无需修改即可切换到单一真源。

### 7.2 状态完整性

新增 `PAGE_STATES`（8 态，强制 icon + title + description）+ 两端 `StateMessage.vue` + H5 `SkeletonList.vue` + `composables/useOnline.ts`。

接入页面：HomeView、SearchView、PlaceView、BoundaryView（H5）；Dashboard、Rules、Sources（Admin）。

**离线的产品决定**：离线**不排队写入**。未经确认的核验会产生假的证据记录，而证据完整性是本产品的全部意义；因此离线时禁用提交并说明原因，而非静默缓存。

### 7.3 消除硬编码颜色

H5 8 处 hex + 2 处阴影 rgba → 令牌（阴影改用 `--pa-elevation-1/2`）；`MatchExplainView.vue` 与 `PlacesView.vue` 的内联样式 → 类。新增地图令牌（`--pa-color-map-*`）与 `--pa-color-skeleton-sheen`。

### 7.4 本轮验证

| 检查 | 结果 |
|---|---|
| `ruff check .` | ✅ All checks passed |
| `mypy services/api/app` | ✅ 74 files, no issues |
| H5 `vue-tsc` + `vite build` | ✅ 65 令牌，状态类全部命中 |
| Admin `vue-tsc` + `vite build` | ✅ 65 令牌 |
| `pytest tests/unit tests/contract`（DB-free） | ✅ **194 passed, 20 deselected** |
| 新增守卫 | `test_ui_states.py`(8) · `test_quality_metrics.py`(19) · `test_design_tokens.py`(10) |

### 7.5 本轮仍未达成

视觉回归截图基线（ENV-01）、地图交互壳（B-04）、Place Detail 完整 10 Section、PARTIAL 与 PERMISSION_DENIED 全页态、多断点与真机 QA、暗色主题、uni-app x 端接入、其余 21 个 Admin 视图的骨架屏。

其中 **PARTIAL 全页态、Place Detail 补齐、暗色主题、其余视图骨架屏** 无外部阻塞，可立即实施。

详见 `UI_UX_IMPLEMENTATION_REPORT.md`、`FRONTEND_ACCEPTANCE.md`、`PRODUCT_IA.md`、`UX_FLOW.md`。
