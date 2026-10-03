# V0207_R1_1_1_HUMAN_REVIEW_TRUTH_CLOSURE_REPORT

Round: **v0.2.7-R1.1.1 — Human Review Pack Completeness / Final Truth Closure（ARTIFACT_TRUTH_CLOSURE）**

范围：只处理 Human Review artifact truth（P0-1 exact-set 门禁 / P0-2 image-reference 完整性 / P0-3 单一 final writer / P0-4 Git truth / P0-5 重新生成 pack）。
非 UI redesign、非新功能、非发布执行。

## GIT_IDENTITY

- PROJECT = PetAccess
- BRANCH = `feat/ui-product-craft-v7-human-review-final`（自 origin/feat/ui-product-craft-v7-runtime-final 创建，无 merge/rebase/force）
- 本轮完成后已 `git push -u origin feat/ui-product-craft-v7-human-review-final`
- `FINAL_BRANCH_HEAD`：**不在本报告中硬编码**（包含本报告的 commit 自身会在生成后才产生 SHA，写死即自引用死锁）。
  以最终验证时刻 `git rev-parse HEAD` / `git rev-parse origin/feat/ui-product-craft-v7-human-review-final` 实测为准（见 GIT_TRUTH）。

## ROOT_CAUSE

- `tests/ui-oracle/human-review-r1.spec.ts` 中最终 `HUMAN_REVIEW_INDEX.html` 的组装与 `writeFileSync` **没有被 `isDesktopProject` 保护**。
- Playwright 两个 project（oracle-desktop / oracle-mobile）都会执行该段：06/07 web rows 只在 desktop 生成，
  非 desktop 的 `rows = []` → 先（或后）执行的 project 用 01–05 五个 card 覆盖了完整的 7-card Index。
- 实测证实：`HUMAN_REVIEW/*.png` 已是 7 张，但 `HUMAN_REVIEW_INDEX.html` 只有 5 cards（01–05），
  06_web_contribution_1440 / 07_web_contribution_compact 缺失 → `HUMAN_REVIEW_PACK_COMPLETENESS = FAIL_MINOR`。

## FINAL_WRITER_FIX

- **方案 A（推荐，已实施）**：只有 `oracle-desktop` 允许：
  generate web 06/07 → assemble windows 01–05 → 写最终 Index → 跑最终完整性 gates。
  其他 project 在 pack 组装之前 `return`（log：`non-desktop project — skipping pack assembly`）。
- 效果：仓库中唯一可达的 `HUMAN_REVIEW_INDEX.html` 最终写入点在 desktop-only 路径内 → **ONE FINAL WRITER，deterministic**。
- 其它 oracle tests（oracle.spec.ts 等）不受影响。

## EXPECTED_CARD_SET

显式常量 `HUMAN_REVIEW_EXPECTED_CARD_SET`（固定顺序，7 个 logical names，非“目录里有什么就算什么”）：

```
01_windows_map
02_windows_contribution_choose
03_windows_contribution_step1
04_windows_contribution_step2
05_desktop_rail_closeup
06_web_contribution_1440
07_web_contribution_compact
```

生成器按该集合固定顺序组装（`rowByName` + EXPECTED_CARD_SET map），不依赖 filesystem order。

## INDEX_CARD_COUNT

- 实测重跑后重新解析 `HUMAN_REVIEW_INDEX.html`：cards = 7，顺序与 EXPECTED_CARD_SET 完全一致。
- `expect(cardNames).toEqual([...HUMAN_REVIEW_EXPECTED_CARD_SET])` → PASS（exact，非 subset）。
- Index 标题实测包含 `7 VALID / 7 total`（`{valid.length} VALID / {all.length} total` 动态生成），不再出现 5/5。

## PNG_COUNT

- HUMAN_REVIEW 顶层 `*.png` 枚举（排除 before-only 外部引用 / metadata / html）：
  恰好 7 个，logical names（去 `.png`）排序后与 EXPECTED_CARD_SET 完全相等。
- `EXPECTED_REVIEW_CARDS = 7`、`ACTUAL_REVIEW_CARDS = 7` → PASS。
- 各 card → PNG 存在（NO_MISSING_CARD）：7/7。

## IMG_REF_COUNT

- 期望：01 Map（before+after = 2）+ 02 Contribution choose（before+after = 2）+ 03/04/05/06/07（各 1）= **9**。
- `EXPECTED_IMG_REFERENCES = 9`；实测 `<img src>` 共 9 → `ACTUAL_IMG_REFERENCES = 9` → PASS。

## REFERENTIAL_INTEGRITY

- 逐 `<img src>` `existsSync(path.resolve(OUT, src))`：9/9 resolve，`MISSING_IMG_REFS = 0`。
- `.png.png` 计数 = 0（row 统一为 logicalName，HTML 模板只追加一次 `.png`）。
- BEFORE 引用：`../windows-smoke/04_map_before.png`、`../windows-smoke/07_contribution_choose_before.png`
  均存在且被引用（smoke 目录中 04_map_before.png 107262 B / 07_contribution_choose_before.png 65943 B）。

## ORPHAN_CHECK

- Orphan gate（新增）：顶层 `HUMAN_REVIEW/*.png` logical names == expected review card set（双向）。
- `ORPHAN_REVIEW_PNG = 0`、`MISSING_REVIEW_CARD = 0` → PASS。
- 不存在“PNG 已生成但没有对应 card”或“card 存在但 PNG 缺失”的情况。

## STATE_INTEGRITY / 截图内容

- 7/7 card 全部 `valid = true`，来自真实 evidence：01–05 = windows-smoke 真实 WebView2 抓帧（复制），
  06/07 = 本轮 generator 自然重截（第 120 行 state integrity 断言 page/state/fixture/h1 全部通过：
  `06 valid=true mismatches=[]`、`07 valid=true mismatches=[]`）。
- 无任何伪造 valid；metadata JSON 只证明真实页面状态。
- `SCREENSHOT_CONTENT_RECAPTURE`：01–05 与 committed 版本 SHA256 逐字节一致（未重截）；
  06/07 由 generator 重截，像素与 committed 版本一致（git diff 显示 PNG 未变化，仅 JSON metadata 的
  generatedAt 等字段更新）。视觉内容零改动。

## WEB_GATES（本轮实测）

| Gate | 命令 | 结果 |
|---|---|---|
| prettier | `pnpm exec prettier --check tests/ui-oracle/human-review-r1.spec.ts` | PASS（exit 0） |
| eslint | `pnpm exec eslint tests/ui-oracle/human-review-r1.spec.ts` | 0 issues（exit 0） |
| human-review-r1 spec（两个 project） | `pnpm exec playwright test -c playwright.ui-oracle.config.ts tests/ui-oracle/human-review-r1.spec.ts --workers=1` | **2 passed / 0 failed**（desktop：7 shots、7 VALID、0 INVALID；mobile：skip 消息 + 不写 Index） |

- UI-oracle 堆栈说明：本机 PostgreSQL 运行于 55432（pg16，scratch 安装），而 oracle config 默认 5432；
  本轮以 `reuseExistingServer: true` 复用预启动的 :8012 API + :5176 preview 完成测试，未修改任何配置文件。

## REUSED_GATES（诚实复用依据）

- `git diff a83f64fb...HEAD --name-only` 仅包含：`tests/ui-oracle/human-review-r1.spec.ts`、
  `artifacts/ui-product-craft-v7-runtime-final/HUMAN_REVIEW/*`、本报告、`PROJECT_STATE.md`；
  `apps/` 下变更 = 0（含 views/*、DesktopRail.vue、Admin）。
- 因本轮不触碰产品代码，以下结果**复用 R1.1 且未重跑**，不作本轮“实测”宣称：
  - `FULL_PRODUCT_REGRESSION_RERUN = NOT_REQUIRED`（Oracle 427/0/0、Reconstruction 180/180、E2E 189/189、Visual 59/59 均来自 R1.1）
  - `WINDOWS_RUNTIME_RERUN = NOT_REQUIRED`（复用 R1.1 targeted 5/5 PASS；DesktopRail/Contribution 代码未动）
  - `ANDROID_RERUN = NOT_REQUIRED`（无 mobile 布局改动）
  - `BACKEND_CODE_CHANGED = NO`（services/ 零变更）

## GIT_TRUTH

- 工作前后均重新 `git fetch origin` 核验。

| 字段 | SHA |
|---|---|
| BASE_HEAD（origin/master） | `42ed4e34158a566b2574b7176d3d12ddf12a20e1` |
| V7_HEAD（origin/feat/ui-product-craft-v7） | `346abbd378e519b44f08a16557cd0b62216c9843` |
| R1_IMPLEMENTATION_HEAD | `f8c1227d861ec271f73b02281a58cbc05ac661af` |
| R1_1_CODE_HEAD | `2010775ec2fead486f4dff164aa2afaaf9b6572b` |
| R1_1_EVIDENCE_HEAD | `647ecd54121c26a11d6c583f400d3e3aa9bc0f47` |
| R1_1_DOCS_HEAD（上轮最终分支头） | `a83f64fb1e11ff0b796c6555d939e9a25505b0ca` |
| FINAL_BRANCH_HEAD | **最终验证时刻实测**（`git rev-parse HEAD` / `git rev-parse origin/feat/ui-product-craft-v7-human-review-final`），不在本报告内硬编码（避免自引用死锁）；见最终汇报 |

- 前轮报告曾把 `647ecd5…`（evidence commit）写作 FINAL_BRANCH_HEAD，产生歧义；本轮纠正为
  R1_1_EVIDENCE_HEAD，且 FINAL_BRANCH_HEAD 语义唯一 = 分支当前实测 HEAD。
- 最后 push 后重 fetch：`git rev-list --left-right --count origin/master...origin/feat/ui-product-craft-v7-human-review-final` = behind 0（见最终汇报实测输出）。
- 全程无 force / merge / rebase；push 仅限该新分支。

## MASTER_STATUS

- `MASTER = UNCHANGED`（42ed4e34… 未动，push 后重 fetch 复核）
- `CANONICAL_BASELINE_PROMOTION = NOT_PERFORMED`
- `MASTER_FF = NOT_PERFORMED`
- `v0.1.0` tag = `c84b4cf…` 未移动；无 `v0.2.0` tag。
- `PUBLIC_RELEASE = NOT_PERFORMED`（无 GitHub Release / Public Beta / Store Upload）。

## HUMAN_REVIEW_STATUS

- `REVIEW_CARDS = 7/7` · `REVIEW_PNGS = 7/7` · `INDEX_IMG_REFS = 9/9`
- `MISSING_IMG_REFS = 0` · `PNG_PNG = 0` · `ORPHAN_REVIEW_PNG = 0` · `MISSING_REVIEW_CARD = 0`
- `HUMAN_REVIEW_INDEX_EXACT_SET = PASS` · `HUMAN_REVIEW_INDEX_REFERENTIAL_INTEGRITY = PASS`
- `HUMAN_REVIEW_PACK = COMPLETE / READY`
- `UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`（Agent 不代替人工签字）
- 目录：`artifacts/ui-product-craft-v7-runtime-final/HUMAN_REVIEW/HUMAN_REVIEW_INDEX.html`
- **停止线已到达**：exact-set 全绿 + Git truth PASS + pack READY。
  等待用户人工视觉签字后方可进入 Stage B（UI_HUMAN_VISUAL_ACCEPTANCE = PASS → force recapture 批准快照 →
  canonical baseline = 批准外观 → visual compare ×2 → docs truth → verify master ancestor → FF master → V020_RC_READY = YES）。