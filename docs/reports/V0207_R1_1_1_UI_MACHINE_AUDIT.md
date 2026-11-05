# V0207_R1_1_1_UI_MACHINE_AUDIT

Round: **v0.2.7-R1.1.1 — UI Machine Audit（只读，UI 未改动）**

触发：用户对 Human Review Pack 给出人工否决（`UI_HUMAN_VISUAL_ACCEPTANCE` 未通过，需重做/修改 UI）。
在修改任何 UI 之前，按用户选择先做一轮只读机器审计，产出可疑缺陷清单供人工勾选。
本轮 **没有修改任何产品 UI**，`apps/` 零变更，master 未动。

## 运行方式（全部实测）

- Stage：`UI_ORACLE_STAGE=r111-audit`
- Stack：`petaccess_visual` 库重建（pg16 @ 127.0.0.1:55432）+ API :8012 + H5 preview :5176
  （本机 PG 在 55432 而非 config 默认 5432；以 `reuseExistingServer: true` 复用预启动服务，未改任何配置）。
- Probe：`pnpm exec playwright test -c playwright.ui-oracle.config.ts tests/ui-oracle/oracle.spec.ts --workers=1`
  → **11 passed / 0 failed / 11 skipped**（skip = 各 project 视口不匹配的合约页，预期行为）。
- 产物：
  - probes：`artifacts/blind-ui-recovery/probes/r111-audit-*.json`（11 个合约组原始测量）
  - screens：`artifacts/blind-ui-recovery/screens/r111-audit/*.png`（29 张逐页截图，证据供人工指认）
  - reports：`artifacts/blind-ui-recovery/reports/r111-audit-compare-all.json`、`density-r111-audit.json`

## 审计结果

### 1. 契约对比 compare（实测值 vs 契约值，逐目标）

```
contribution 55 · evidence 35 · global 33 · home 18 · map 22 · map.mobile 37 ·
place.desktop 64 · place.mobile 35 · reality 36 · search.desktop 54 · search.mobile 38
TOTAL  PASS=427  WARN=0  FAIL=0
```

→ 全部 427 个契约目标（布局/断点/间距/溢出/aria/文本 等）通过，0 WARN、0 FAIL。

### 2. 语言扫描 language

```
total=29  FAIL=0
```

→ 无 UUID / snake_case / 全大写 / 不变式 可见文本违规。

### 3. 密度 density

```
total=28  FAIL=0
```

唯 1 条 WARN（候选缺陷）：
- `place.mobile/place-mobile-rules`：`lines=WARN(34)`（信息行数 34，略超密度阈值，未到 FAIL）

其余全部 PASS（信息块为 0 的页面 gap 不可测，记为 n/a，非违规）。

## 逐页截图索引（人工指认用）

`artifacts/blind-ui-recovery/screens/r111-audit/`：

| 页面 | 截图 |
|---|---|
| Home | `home-home-ready.png`（= `global-home.png` 65048 B） |
| Search desktop | `search.desktop-search-ready.png` / `search.desktop-search-selected.png` |
| Search mobile | `search.mobile-search-mobile-ready.png` / `search.mobile-search-mobile-filter.png` |
| Map desktop | `map-map-ready.png`（= `global-map.png`） |
| Map mobile | `map.mobile-map-mobile-ready.png` / `-selected-half.png` / `-expanded.png` |
| Place desktop | `place.desktop-place-ready.png` / `place.desktop-place-rules.png` / `place.desktop-place-unknown.png` |
| Place mobile | `place.mobile-place-mobile-ready.png` / `place.mobile-place-mobile-rules.png` |
| Contribution | `contribution-contribute-entry.png`（= `global-contribute.png`）/ `-contribute-step-1.png` / `-contribute-step-2.png` / `-contribute-needs-place.png` |
| Reality | `reality-reality-ready.png` / `reality-reality-empty.png` |
| Evidence | `evidence-evidence-records.png` / `evidence-evidence-empty.png` |
| 全局导航 | `global-*.png`（rail/导航 7 路由公共框架） |

## 结论

- 机器层：**未发现可量化视觉缺陷**（427/0/0、29 FAIL=0、28 FAIL=0）。
- 唯一候选：`place.mobile-place-mobile-rules` 行数密度 WARN（34 行）。
- 用户“完全不行”的否决属于契约覆盖之外的视觉/主观判断，需要人工指认具体页面/问题后，
  才能进入 UI 修改（新 UI 修复轮次）；在此之间 UI 保持冻结。
- 状态：`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING_REVIEW`（用户未签字）· `MASTER = UNCHANGED` ·
  `CANONICAL_BASELINE_PROMOTION = NOT_PERFORMED` · `MASTER_FF = NOT_PERFORMED`。