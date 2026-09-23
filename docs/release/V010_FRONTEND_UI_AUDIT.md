# V010 FRONTEND UI AUDIT — 2026-09-24

> 状态标记 (Status Legend): **CURRENT VERIFIED** 本会话(2026-09-24)实际执行并核验 | **HISTORICAL** 此前会话执行、本轮未重跑 | **NOT RERUN** 未重跑(原因已注明) | **BLOCKED** 无法执行(原因已注明)

## 状态总表 (Status Table)

| 项 | 结果 | 标记 |
|---|---|---|
| client-h5 build (vue-tsc + vite) | PASS | CURRENT VERIFIED |
| Consumer 屏幕评审（13 screens） | 完成 | CURRENT VERIFIED |
| Design tokens / 硬编码色 | tokens 生效，explorer 核验 0 硬编码 hex 色 | CURRENT VERIFIED |
| Empty-First 文案 (Phase K) | 已提交 M3 (b04777c) | CURRENT VERIFIED |
| loading / empty / error 三态 | 所有主要屏幕具备 | HISTORICAL（prior survey） |
| offline banner | Home / Search / Map / Contribute / Pets / Boundary | HISTORICAL（prior survey） |

## 1. 评审范围 (Consumer Screens)

Home / Search / Map / Place / Rule trace / Reality trace / Contribution / Settings / Privacy / Notifications / Boundary / Pets / Mine — 共 13 屏逐一走查。

## 2. Design Tokens

- 消费端统一使用 design-tokens 语义色；explorer 核验 0 硬编码 hex 色。
- 注：遗留 uni-app 客户端（apps/client）28 处硬编码色仍登记为 TD-018，属历史债，不影响本 release H5 主路径。

## 3. Empty-First 文案（Phase K，M3 提交）

- **HomeView**：全局空态 StateMessage kind=EMPTY，title=`当前还没有已发布的场所数据`，description=`你仍可浏览产品功能，或提交第一个现场/规则线索。`，actions `探索地图`(/map) + `贡献线索`(/contribute)，data-testid=`home-empty`。
- **SearchView**：no-results 文案 `没有找到已收录场所。未收录不代表该场所没有规则。`（testid `search-empty`）。
- **RealityPanel**：`暂无经核验的处理记录（≠ 未处理）。` / `暂无经核验的设施记录（设施 ≠ 入场政策）。` / `暂无足够现场记录（暂无记录 ≠ 没有动物）。`
- **PlaceView**：`暂无可靠规则结论（未收录 ≠ 没有规则）。` / `暂无足够现场记录（暂无记录 ≠ 没有动物）。`
- **StateMessage**：新增可选 `title` prop（向后兼容）。

## 4. loading / empty / error / offline

- 所有主要屏幕均具备 loading / empty / error 三态（prior survey）。
- offline banner 覆盖：Home / Search / Map / Contribute / Pets / Boundary 六屏。
- 已知局限：Place / Rule trace / Reality trace / Settings / Privacy / Notifications / Mine 无 offline banner，离线时退化为普通错误态呈现（已记录，纳入后续收口面）。

## 5. 结论

**结论: UI_UX_AUDIT = PASS with noted limitations**（主要屏幕三态齐备 + Empty-First 文案落地；offline 未覆盖全部屏幕为已知局限）。
