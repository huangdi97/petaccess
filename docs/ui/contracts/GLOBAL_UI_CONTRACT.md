# Global UI Contract — PetAccess Consumer

> 机器可读契约：`docs/ui/contracts/json/global.json`
> 来源：Goal v0.2.2 §20–§24、§47、§52；UI_RECONSTRUCTION_DESIGN_FREEZE.md（v0.10-R1 + Approved Reference）。
> 优先级：Canonical Master > Design Freeze > 本契约。本契约只定义可测量的实现约束，不重定义产品语义。

## 1. 适用对象

所有 Consumer 页面：Home / Search / Map / Place / Reality / Evidence / Contribution。

## 2. 语义不变量（Consumer 可见层）

1. 用户可见文本禁止出现：
   - UUID（完整 8-4-4-4-12 或 `id.slice(0,8)` 前缀片段）；
   - snake_case 内部枚举（`ordinary_pet`、`pet_area`、`dining_area`、`service_dog`、`pending_review`、`superseded` 等）；
   - ALL_CAPS 工程状态码（`NO_RECENT_RECORD`、`INSUFFICIENT_OBSERVATION`…）；
   - 工程不变量原文（`NO_RECENT_RECORD ≠ NO_ANIMAL_PRESENCE`、`UNKNOWN ≠ ALLOWED` 等）。
2. 工程不变量必须转译为自然语言，例如：
   - `暂无近期现场记录。这并不代表现场没有动物。`
3. 原始 enum 只能存在于不可见 data attribute，不得出现在文本节点。
4. Rule 与 Reality 必须分离呈现（Observation 不是 Rule）。

## 3. 全局 Typography 契约（token 为 SSOT）

| 角色 | 桌面 | 移动 | 字重 |
|---|---|---|---|
| Page / Place identity | 26–30px（token `--pa-font-size-26/30`） | 22–24px（`--pa-font-size-22`） | 600–700 |
| Primary decision | 26–32px | 22–26px | 600–700 |
| Section title | 17–19px（`--pa-font-size-17/18/19`） | 同 | 500–600 |
| Body | 14–16px（`--pa-font-size-14/base/lg`） | 同 | 400 |
| Metadata / Evidence | 12–13px（`--pa-font-size-sm/md`） | 同 | 400 |

约束：
- 禁止所有文本同为 14px；
- 禁止只靠颜色区分层级；
- 禁止 mobile 等比缩小所有桌面字号；
- 页面不得 invent 字号，一律引用 token。

## 4. 全局 Surface 契约

页面结构只有：Canvas → Section → Divider → Row。
仅以下允许 elevation/card treatment：map preview、popover、dialog、bottom sheet、真正重要的决策面。
禁止：section card、card in card、每 result card、每 timeline item card、每 field card。
radius：row=0、section=0、inspector=0、input/button 6–8px、floating map preview 10–12px、bottom sheet top 16px。
shadow：默认 none；仅 map preview / dialog / popover / bottom sheet 允许轻阴影（`--pa-elevation-1/2/3`）。

## 5. 全局 Spacing 契约（token 为 SSOT）

token 阶梯：4/8/12/16/20/24/32/40/48（`--pa-space-1..7`）。
- inline gap：8–12px
- row internal gap：8–12px
- section internal gap：12–20px
- section ↔ section：24–32px
- major block：32–48px
禁止：无意义 80–200px 空洞；所有间距都是 16；mobile 与 desktop 完全相同。

## 6. 全局 Density 契约（Dense but Quiet）

**Desktop 主要信息区（view 主体，非地图页）**
- 900px 高 viewport 内至少出现 3–5 个有意义信息 block；
- 主要区域（非地图）空白占比 ≤ 60%；
- 相邻 semantic section 之间无意义垂直空白 ≤ 180px。

**Mobile 首屏（932px viewport）**
- 目标显示：Page identity + Current context + Primary decision + 1 个关键 supporting block；
- 禁止首屏只有标题 + 巨空态。

## 7. Empty / Error / Offline 契约

- Empty：与页面任务相关；1 个 primary next action（最多 1 个 secondary）；非居中巨卡。
- Error：inline / page-contextual；提供 retry；保留 navigation/context。
- Offline：global banner + cached content；无 cache 才进入 dedicated offline empty。

## 8. A11y 契约（延续 §47）

- 每页单一 h1；语义化标题层级；label 关联；keyboard 可操作；focus visible；
- Esc 关闭 dialog；prefers-reduced-motion；触控目标 ≥44px（`--pa-layout-touch-target`）；
- status = icon + 文字 + 颜色（非颜色唯一信号）；rail 有 aria-label；bottom sheet 有语义。

## 9. 稳定 data-ui 契约（机器可测）

关键语义区域必须带稳定 `data-ui` 属性（值见各页面契约 / `json/*.json` 的 region selector）。
属性只服务测试与机器检查，不改变视觉，不携带 domain enum。