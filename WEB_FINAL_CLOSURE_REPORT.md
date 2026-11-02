# WEB_FINAL_CLOSURE_REPORT

PetAccess Web Consumer — v11 Urban Spatial Guide final closure sweep.

| Field | Value |
|---|---|
| Source HEAD | `160745e9d279379af927f4dd0d14c1bb360ea7fd` |
| Branch | `feat/ui-direct-craft-v8` |
| PR | #1（OPEN + DRAFT，未 merge / 未 tag / 未 Release） |
| Scope | `apps/client-h5`（canonical Web Consumer） |
| Report date | 2026-11-02 |
| `WEB_IMPLEMENTATION` | **UNCHANGED this round** — no functional, visual or contract code was modified; see §7 |
| `WEB_MACHINE_ACCEPTANCE` | **PASS**（本地独立复核，见 §3） |
| `WEB_VISUAL_CANDIDATE` | **READY_FOR_HUMAN**（Human Review artifact 已绑定本 SHA） |
| `UI_HUMAN_VISUAL_ACCEPTANCE` | **PENDING_REVIEW**（本轮未取得、也不得代签） |

---

## 1. 开工核验（真实远端事实）

- `git fetch --all --prune` 后：`origin/feat/ui-direct-craft-v8` = `160745e9d279379af927f4dd0d14c1bb360ea7fd`。
- PR #1 `head.sha` = `160745e9...`，与本 SHA 一致；相对任务书给出的 SHA **未前进**。
- 进入时本地处于 `master` @ `42ed4e34`（该 SHA 的祖先，落后 3026 commits），工作树干净：
  **没有需要保护的未提交成果**。已建立跟踪远端的本地分支，未执行 `reset --hard`、未 force push、未重写历史。
- 该 SHA 的 GitHub Actions（PR #1 check runs）实测：
  - PR CI / UI Direct Validation / UI Direct Visual / Public Preview Stack = **SUCCESS**；
  - **`Android Preview · API 35 runtime smoke` 与 `API 36 runtime smoke` = FAILURE**（PR 因此 `mergeable_state=unstable`）。
    这是本轮之前就存在的既存状态，不是 Web 改动引入；Android 不在本轮视觉开发范围。**未修复，如实记录。**

## 2. 本地运行环境（本轮从零搭建）

进入时该机器 **没有 Node.js、没有可用 Python、没有 PostgreSQL、没有 Docker**。
为让"机器 PASS"可被独立复现而非引用旧结论，本轮在会话 scratch 内搭建了完整栈（未修改系统、未写入仓库）：

- Node 22.23.4（匹配 CI 的 `node-version: 22`）+ pnpm 12.4.1（匹配 `packageManager`）；
- Python 3.12（uv）+ `uv sync --frozen --all-packages`；
- PostgreSQL 17.7 + PostGIS 3.6（便携二进制）；
- Redis 5.0.14（便携二进制）；
- 用仓库自带脚本灌入确定性数据：`scripts/visual_db_reset.py`（`petaccess_visual`）、`scripts/isolated_db.py --role E2E --reset`（`petaccess_e2e`）。
- 仓库 `.env` 被工具安全策略禁止写入，因此一律通过进程环境变量注入，**未新增任何凭据文件**。
- 浏览器：使用本机已安装的真实 Google Chrome 156（配置已支持 `PLAYWRIGHT_CHANNEL=chrome`），未下载浏览器。

## 3. 机器验收结果（本地真实执行）

| 检查 | 命令 | 结果 |
|---|---|---|
| Lint | `pnpm lint:fe` | **PASS** |
| Format | `pnpm format:check:fe` | **PASS**（All matched files use Prettier code style） |
| Consumer build | `pnpm --filter @petaccess/client-h5 build` | **PASS** |
| Admin build | `pnpm --filter @petaccess/admin build` | **PASS** |
| UI Oracle 采集 | desktop 1440×900 / tablet 800×1080 / mobile 430×932 × `oracle.spec` + `secondary-craft.spec` + `human-review-direct-v8.spec` | **0 failed**（desktop 10 pass、tablet 2 pass、mobile 5 pass，其余按视口 skip） |
| UI Contract | `node --experimental-strip-types tools/ui-oracle/compare.ts ui-direct-v8` | **TOTAL PASS=580 WARN=0 FAIL=0**（11 份合同全 0 WARN / 0 FAIL） |

分合同：`contribution 66 / evidence 36 / global 33 / home 23 / map 59 / map.mobile 62 / place.desktop 93 / place.mobile 70 / reality 36 / search.desktop 60 / search.mobile 42`，均为 0 WARN / 0 FAIL。

## 4. Consumer 路由覆盖

`apps/client-h5/src/router.ts` 实际枚举 **21 条 route**（含 catch-all），全部进入本轮 sweep：

`/`、`/map`、`/onboarding`、`/search`、`/place/:id`、`/pet/new`、`/pets`、`/contribute/:id?`、`/mine`、`/privacy`、`/notifications`、`/settings`、`/about`、`/boundary`、`/place/:id/why`、`/place/:id/reality`、`/place/:id/evidence`、`/place/:id/operator-claim`、`/:pathMatch(.*)*`。

Human Review 截图清单（40 个状态槽）已包含任务书 §45 要求的全部条目，含 Pets / Pet New / Boundary / Operator Claim / Why / About / Onboarding / 404，以及 Contribution 全部步骤与四类 Map lens。

## 5. Human Review artifact

- 本机重新生成，落点 `artifacts/ui-direct-v8/HUMAN_REVIEW/`，**manifests 绑定 `sourceHead = 160745e9d279379af927f4dd0d14c1bb360ea7fd`**，`humanVisualAcceptance = "PENDING"`。
- 截图数量：desktop **40**、tablet **40**、mobile **43**，共 **123** 张 PNG，均来自真实 runtime / 真实 fixture / 真实 DOM。
- 结论：**产物完整且 HEAD 绑定正确**；但见 §7 —— 本轮未做像素级目视复核。

## 6. 独立响应式 / DOM 语义审计（本轮新增证据）

方法：真实 Chrome 渲染 + 页面内测量，**10 个视口 × 19 条路由 = 190 次渲染**。
视口：`320×640、360×780、390×844、430×932、768×1024、800×1080、1024×768、1280×800、1440×900、1920×1080`。

| 维度 | 结果 |
|---|---|
| 横向溢出（`scrollWidth > clientWidth`） | **0** 例 |
| 重复 / 缺失 `<h1>` | **0** 例 |
| 可见 enum 泄漏（`VERIFIED / PENDING / CONDITIONAL / ALLOWED / PROHIBITED / UNKNOWN …`） | **0** 例 |
| 可见 UUID / `snake_case` / 工程语（`source_id`、`resolver`、`HTTP 5xx`、`undefined`、`NaN`） | **0** 例 |
| 硬编码颜色（consumer CSS 中 `#hex` / `rgb()` / `hsl()`） | **0** 处 |
| 影子旧 UI（live 的 `fallback` / `illustrated` 元素） | 仅 2 个合法项：`map-provider-fallback`（§11 要求的一次性"简化空间底图"披露）、`place-dossier__head--illustrated`（无 governed media 时的 text-led 头部修饰类）；均非隐藏旧 UI |

补充定位结论：

- `place-dossier__scene--fallback` 元素在模板中 **从不渲染**（`PlaceSceneFrame` 为 `v-if="placeSceneMedia"`），但对应 CSS 仍存在 4 处 → **死选择器**（见 §8）。
- 每页控制台出现 `GET /api/v1/evidence-bundles/{id}/public-media → 404`：该端点对"无公开媒体"的 bundle 返回 404，客户端 `publicSceneMedia.ts` 已 `catch → null` **fail-closed**，语义正确，属数据相关网络噪声，非缺陷。

## 7. 本轮未能完成 / 明确未做

1. **本地完整 Consumer E2E 套件未跑成。** 原因是本机环境，不是仓库缺陷，已定位到具体数字：
   - `scripts/isolated_db.py --role E2E --reset` 在本机稳定耗时 **≈400 s**（两次计时 400459 ms / 401662 ms），而 `playwright.config.ts` 的 webServer 预算是 **180 s**，故套件无法自举启动；
   - 绕开自举、手工预建库并直接启动 API 后，`uvicorn` 在 **300 s 内仍未绑定端口**（应用导入阶段即超慢），同一台机器期间还出现过 **工作区磁盘整体掉线**（`D:\AI\城市空间\petaccess` 一度不可访问，工具报 `os error 267/3`）。
   - 因此 E2E 的权威证据仍是**同一 SHA 的 PR CI Playwright 结果**，本轮未产生新的本地 E2E 结论，**不以旧结论冒充新执行**。
2. **未做像素级目视复核。** 本轮只有 DOM 测量证据；我不对截图外观作任何"看起来正确"的判断。assistant visual review 在本轮为 **NOT PERFORMED**。
3. **未修改任何功能 / 视觉 / 合同代码。** 期间曾怀疑 `playwright*.config.ts` 的 `JSON.stringify` 路径写法在 Windows 下失效并改了 5 个配置，随后用可复现实验证伪（Windows 会规范化重复反斜杠，cmd 两种写法均正常退出 0），**已全部 `git checkout` 回退**，不留无依据改动。

## 8. 已知剩余问题（debt）

| 级别 | 项 | 位置 | 说明 |
|---|---|---|---|
| P2 | 死选择器 `.place-dossier__scene--fallback`（4 处，元素从不渲染） | `apps/client-h5/src/styles/consumer-discovery-v10.css:997`、`consumer-discovery-v11.css:760`、`src/views/PlaceView.vue:776`、`PlaceView.vue:1027` | §6/§58 允许安全清理；本轮因磁盘退化无法可靠复跑 Oracle 而未改，避免在未复验情况下改动已验证 UI |
| P2 | 移动端部分独立操作控件高度 < 44px | `.query-context__edit` 34×32、`.filter-toggle` 30×32、map lens `<select>` 78×38、reality 筛选 34 高、privacy 120×40 | `GLOBAL_UI_CONTRACT` 声明 `--pa-layout-touch-target: 44px`，实测未达标；仍满足 WCAG 2.2 AA 2.5.8（≥24×24）。抬到 44 会改变 `query-context` / `map-lensbar` 容器高度，需同步更新合同并复跑 123 张截图，风险大于收益，故记录不擅改 |
| P2 | 每页 `public-media` 404 控制台噪声 | `services/api/app/api/v1/public_media.py:26` ↔ `apps/client-h5/src/consumer/publicSceneMedia.ts` | 设计上的 fail-closed；若要去噪需后端改为 200 + `available:false`，属 API 合同变更，超出本轮 |
| 既存 | Android Preview runtime smoke（API 35 / 36）FAILURE | GitHub Actions | 与本轮 Web 范围无关，未处理 |
| 环境 | 本机 D: 卷不稳定（曾整体掉线） | — | 影响本地重型验证的可重复性 |

**P0 = 0 / P1 = 0（Web 范围内，基于本轮实测证据）**：无 Rule/Reality 语义混淆、无伪造媒体、无错位数据竞争、190 次渲染 0 横向溢出、Map 仍为支配表面、Place 有/无照片两条路径均 text-led 或 destination surface、Evidence provenance 可见、Contribution 目标地点上下文存在、无空白/报错路由、build 通过、无重大无障碍阻断（44px 目标见上表 P2）。

## 9. CI 状态约束

依据任务书 §52，最终结论只能绑定**同一 SHA**。本轮**未产生新的源码 HEAD**（无代码改动），因此：

- 当前最终 HEAD 仍为 `160745e9d279379af927f4dd0d14c1bb360ea7fd`；
- 该 SHA 的四条主门禁为 **SUCCESS**（见 §1），Android 两条 runtime smoke 为 FAILURE（既存、范围外）。

若后续提交文档或代码，必须重新取得**新 SHA** 的四条门禁结果，不得复用本次 PASS。

## 10. Release 边界

本轮**没有**：merge master、mark PR ready、tag、GitHub Release、production release、release signing、force push、删除历史证据、修改 Rule/Reality/Evidence domain semantics、大规模 backend rewrite、重做 Android UI。

## 11. 人审状态

```
MACHINE_PASS               = PASS（本地 lint / format / build×2 / Oracle 580-0-0）
ASSISTANT_VISUAL_REVIEW    = NOT PERFORMED（本轮无像素级复核）
USER_HUMAN_ACCEPTANCE      = PENDING_REVIEW
```

`UI_HUMAN_VISUAL_ACCEPTANCE` 继续保持 **PENDING_REVIEW**，直到用户本人对绑定 `160745e9...` 的 Human Review artifact 明确签字。本地 Agent 不代签。
