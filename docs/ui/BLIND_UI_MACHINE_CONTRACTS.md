# Blind-Model UI — Machine Contracts（机器契约文档）

> 机器可读契约 = `docs/ui/contracts/json/*.json`（10 份）；人类可读版本 = `docs/ui/contracts/*.md`（12 份）。测量工具 = `tools/ui-oracle/`。

## 1. 契约文件清单

| JSON | 页面/状态 | viewport | 契约规则数（element/structure/density） |
|---|---|---|---|
| global.json | app-shell 全局（home/search/map/place/reality/evidence/contribute 7 页） | 1440×900 | 若干（含 NO_GLOBAL_HORIZONTAL_OVERFLOW） |
| search.desktop.json | ready / selected | 1440×900 | 22 PASS |
| search.mobile.json | mobile-ready / mobile-filter | 430×932 | 15 PASS |
| place.desktop.json | place-ready | 1440×900 | 15 PASS |
| place.mobile.json | place-mobile-ready | 430×932 | 11 PASS + 1 WARN |
| home.json | home-ready | 1440×900 | 12 PASS |
| map.json | map-ready | 1440×900 | 13 PASS |
| reality.json | reality-ready（星河咖啡）/ reality-empty（云栖中心） | 1440×900 | 14 PASS |
| evidence.json | evidence-ready / evidence-records | 1440×900 | 16 PASS |
| contribution.json | contribute-needs-place / contribute-entry（auth） | 1440×900 | 14 PASS |

## 2. 规则模型

```jsonc
// element：几何 / computed style
{ "id": "SEARCH_DETAIL_CONTENT_WIDTH", "ui": "search-detail-content",
  "props": { "maxChildWidth": { "min": 680, "max": 760 } }, "severity": "FAIL" }

// structure：DOM 结构 / class / 文本 / 数量
{ "id": "REALITY_EVENT_NOT_CARD", "selector": "[data-ui='reality-event'], .trace-row",
  "forbiddenClass": ["panel", "card"], "severity": "FAIL", "pages": ["reality-ready"] }

// density：区域内聚合度量
{ "id": "PLACE_MOBILE_FIRST_VIEWPORT_LINES", "selector": "body",
  "metric": "firstViewportVisibleTextLines", "max": 40, "warnAt": 30, "severity": "WARN" }

// language：可见文本泄漏扫描（uuid / enums / invariants / allcapsTokens）
"language": { "uuid": true, "enums": true, "invariants": true, "allcapsTokens": true }
```

## 3. 关键约束锚点（实测锚点，来自契约）

- Search desktop：rail 64–72px、top context 56–64px、result pane 380–420px、detail 内容 maxChildWidth 680–760px、detail 左距 32–48px、顶距 24–32px、detail 首屏 ≥360px、result row 高 108–136px 且 radius=0、selected 行 tint + 左指示 2px、决策锚点 label 12–13px / decision 28–32px / supporting 14–16px。
- Search mobile：row 104–132px、决策高于 metadata、filter bottom sheet（top radius 16px + drag handle + title + 选项 + action）。
- Place desktop：dossier 65–72% + sticky inspector 300–360px（sticky top = context bar + 20–24px）、identity name 28–30px、Current Decision 为第一核心 section。
- Place mobile：首屏 place name + 决策 + 至少一项 supporting fact；禁止超长 schema dump。
- Map：≥3 road path、≥2 block polygon、river 面积元素、≥4 markers、selected marker、zoom 控件；filter 为「筛选 N」入口而非 pill wall。
- Reality：事件为非卡片 timeline 行；空态带 1 个 primary action。
- Evidence：provenance 恰好 5 步、三时间分离（≥3 行）、无 UUID 文本。
- Contribution：entry 页「你刚刚知道了什么？」+ 5 选项；guard 页隐藏 query context。

## 4. Final 门禁结果（UI_ORACLE_STAGE=final）

```
[final] contribution: PASS=14 WARN=0 FAIL=0
[final] evidence:     PASS=16 WARN=0 FAIL=0
[final] global:       PASS=32 WARN=0 FAIL=0
[final] home:         PASS=12 WARN=0 FAIL=0
[final] map:          PASS=13 WARN=0 FAIL=0
[final] place.desktop:PASS=15 WARN=0 FAIL=0
[final] place.mobile: PASS=11 WARN=1 FAIL=0
[final] reality:      PASS=14 WARN=0 FAIL=0
[final] search.desktop: PASS=22 WARN=0 FAIL=0
[final] search.mobile:  PASS=15 WARN=0 FAIL=0
[final] TOTAL PASS=164 WARN=1 FAIL=0
```

产物：`artifacts/blind-ui-recovery/reports/final-compare-all.json`（逐规则 target/actual/detail）、`compare-<contractId>.json`、`final.json`（report 汇总）、`density-final.json`、`language-scan.json`（21 页 FAIL=0）。

## 5. Page 级规则与 auth

- `pages: ["pageId"]`：规则仅对指定页面生效（如 contribution 的 guard 规则只在 `contribute-needs-place`，entry 规则只在 `contribute-entry`；reality 的行数规则只在 `reality-ready`，空态 action 规则只在 `reality-empty`）。
- `auth: true`：oracle 先注册+登录（`/auth/register` + `/auth/login` → `localStorage.pa_token`）再导航，保证测量的是真实交易流而非登录守卫。

## 6. 复现命令

```powershell
pnpm --filter @petaccess/client-h5 build
$env:UI_ORACLE_STAGE="final"; $env:PLAYWRIGHT_CHANNEL="chrome"
pnpm exec playwright test -c playwright.ui-oracle.config.ts
node --experimental-strip-types tools/ui-oracle/compare.ts final
node --experimental-strip-types tools/ui-oracle/run-language.ts final
node --experimental-strip-types tools/ui-oracle/run-density.ts final
node --experimental-strip-types tools/ui-oracle/report.ts final
```
