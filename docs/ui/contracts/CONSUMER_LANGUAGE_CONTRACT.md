# Consumer Language Contract

> 来源：Goal v0.2.2 §20、§38、§43；CONSUMER_VISIBLE_LANGUAGE_MAP.md；consumer/labels.ts（统一 mapper）。

## 1. 绝对禁止出现在用户可见文本

### 1.1 UUID
任何完整 UUID 或 `id.slice(0,8)` 前缀片段（8+ 位 hex 后随 `-`）。命中 = FAIL。

### 1.2 snake_case 内部 token
示例（完整 denylist 见 `json/*.json language.enums` 与 `language-scan.ts`）：
`ordinary_pet`、`pet_area`、`dining_area`、`children_area`、`service_dog`、
`pending_review`、`superseded`、`withdrawn`、`reality_report`、`candidate`、
`explicitly_allowed`、`no_interaction_observed`、`operator_discretion`、
`temporarily_unavailable`、`outdoor_holding_cage`、`pet_waiting_area` 等。

### 1.3 ALL_CAPS 工程状态码 / 不变量
`NO_RECENT_RECORD`、`INSUFFICIENT_OBSERVATION`、`OBSERVED_RECENTLY`、
`MULTI_EVIDENCE_OBSERVED`、`RULE_REALITY_ALIGNED`、`POTENTIAL_CONFLICT`、
`REVIEW_REQUIRED`、`UNKNOWN`、`ALLOWED`、`PROHIBITED`、`VERIFIED` 等原文。

### 1.4 工程不变量句子
`NO_RECENT_RECORD ≠ NO_ANIMAL_PRESENCE`、`Observation != Rule`、`UNKNOWN != ALLOWED` 等不得原文出现。

## 2. 必须转译的不变量 → 消费者文案

| 不变量 | 消费者文案 |
|---|---|
| NO_RECENT_RECORD ≠ NO_ANIMAL_PRESENCE | `暂无近期现场记录。这并不代表现场没有动物。` |
| Observation != Rule | `现场观察是事实记录，不代表正式准入规则。` |
| UNKNOWN != ALLOWED/PROHIBITED | `该项信息暂不明确，不代表允许进入或禁止进入。` |
| StaffResponse != OperatorPolicy | `这是现场工作人员的实际做法，不等同于场所正式规则。` |

## 3. 统一 Mapping Layer（唯一转换点）

所有 enum → 消费者文案的转换必须集中在：
- `apps/client-h5/src/consumer/labels.ts`（zone / animal / action / status / layer / mandatory / staff / facility / coexistence / entrance / source）
- `apps/client-h5/src/reality.ts`（reality state / divergence / freshness / candidate type / contribution status）
- `apps/client-h5/src/consumer/rowView.ts`（行级投影）

页面不得自行拼 raw enum。mapper fallback 必须为消费者安全词，绝不允许 `?? rawValue` 回溯到屏幕（现有 `rowView.ts:21`、`reality.ts:63/113` 的 `?? state` 回退必须清除）。

## 4. Zone 消费者命名（Place / Search / Map）

| 原始 zone_type | 消费者显示 |
|---|---|
| `area` | 公共区域 |
| `pet_area` | 携宠区 |
| `dining_area` | 堂食区 |
| `children_area` | 儿童区 |
| `lawn` | 草坪 |
| `plaza` | 广场 |
| `road` | 道路 |
| `supermarket` | 超市 |
| `entrance` | 入口 |
| `elevator` | 电梯 |
| `other` | 其他区域 |
| floor_ref | `楼层 {value}`，禁止裸显 `floor` |

推荐消费者空间描述（Freeze §27.5）：`一层公共区域` / `餐饮堂食区` / `户外区域`。

## 5. 扫描口径

- 只扫描用户可见文本（`document.body.innerText`）。
- 代码 / data-testid / data-ui / JSON fixture 中的内部词不算命中。
- 结果写入 `artifacts/blind-ui-recovery/language-scan.json`。
- 任何用户可见命中 = 该页面语言 Gate FAIL。