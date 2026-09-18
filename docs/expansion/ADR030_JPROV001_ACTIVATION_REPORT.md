# ADR-030 辖区级法定但书激活报告（JPROV-001）

- 时间：2026-09-18（UTC 11:46，容器时钟）
- 执行：`scripts/apply_jurisdiction_proviso.py --db-name petaccess --activate --reviewer huangdi97 --production-confirm`
- 授权：Human Reviewer `huangdi97` 明确要求执行（本轮对话）
- 结果：`staged=1 / activated=1 / skipped=0`

## 一、激活了什么

`jurisdiction_exception` 新增 1 行（此前 0 行）：

| 字段 | 值 |
|---|---|
| `id` | `JPROV-001` |
| 法律文件 | 上海市养犬管理条例 第二十三条 |
| 但书原文 | 盲人携带导盲犬的，不受本条规定的限制。 |
| 辖区 / 层级 | `310000`（市级）/ `LEGAL` |
| 主体 | `animal_scope=service_dog`，`subject_scope_normalized=guide_dog`，`normalization_type=exact` |
| 效果 | `prohibited` → `allowed`，`holder_scope=person_with_disability` |
| 绑定 | `instrument`，`instrument_source_ids = [f20bdb2c…, a11aff10…]` |
| 状态 | `status=current` / `review_status=reviewed_active` / `reviewed_by=huangdi97` |

`instrument_source_ids` 覆盖《上海市养犬管理条例》在本库的两个 source 行，因为 5 条 LEGAL 基底
分别引用不同的那一个。激活后，`in_instrument=True` 命中这 5 条全部。

## 二、它改变了哪些答案（A/B 对照，同一批实时行跑两遍）

新脚本 `scripts/verify_adr030_production_activation.py`（只读）对每个有 LEGAL 规则的场所解析两次：
A = 从例外集中去掉辖区但书（即激活前状态），B = 带上激活后的但书。

| 场所 | 区域 | 普通犬 A→B | 导盲犬 A→B |
|---|---|---|---|
| 上海博物馆东馆 | 全馆 | prohibited → prohibited | allowed → allowed |
| 上海图书馆东馆 | 全馆 | prohibited → prohibited | allowed → allowed |
| 兴业太古汇 | 商场室内公共区域 | prohibited → prohibited | allowed → allowed |
| 和平饭店（费尔蒙） | 全酒店 | prohibited → prohibited | allowed → allowed |
| 星巴克臻选上海烘焙工坊 | 全店 | prohibited → prohibited | allowed → allowed |

**当前答案的 delta = 0。** 原因不是但书没生效，而是这 5 条基底**每条都已经有一条场所级
`rule_exception`**（`rule_exception=5`），导盲犬本来就是 `allowed`。

不变式校验 `verdict = PASS`：普通犬在 A/B 中必须一致（但书不得外溢到导盲犬以外）；
导盲犬若仍 `prohibited` 且没有 inert 说明即为失败。两条都满足。

## 三、那这次激活的价值是什么（前瞻证明）

在生产克隆 `petaccess_publish_rehearsal_adr030b` 上跑 `verify_adr030_proviso_drill.py`，
**移除 5 条场所级例外**——这正是"一条新发布的 LEGAL 基底还没有手写例外"的状态：

```
place                 zone        ordinary    A guide     B guide
上海博物馆东馆          全馆         prohibited  prohibited  allowed
上海图书馆东馆          全馆         prohibited  prohibited  allowed
兴业太古汇            商场室内公共区域  prohibited  prohibited  allowed
和平饭店（费尔蒙）       全酒店        prohibited  prohibited  allowed
星巴克臻选上海烘焙工坊     全店         prohibited  prohibited  allowed

A_guide_dog_prohibited          = 5     ← Wave01 阻塞态复现
B_guide_dog_prohibited          = 0
B_guide_dog_allowed             = 5
B_ordinary_dog_still_prohibited = 5     ← 普通犬不受影响
```

即：**新发布的 LEGAL 禁犬基底现在可以不再依赖逐场所手写例外**。这正是被
`REQUIRED_LEGAL_EXCEPTION_NOT_EXECUTABLE` 拦下的 6 条候选所需的路径。

## 四、数据完整性

| 项 | 激活前 | 激活后 |
|---|---|---|
| `jurisdiction_exception` | 0 | **1** |
| `access_rule` | 8 | 8 |
| `rule_exception` | 5 | 5 |
| `rule_candidate` | 68 | 68 |
| `audit_log` | 9618 | 9618 |
| alembic | `f2a1c7d9e034` | `f2a1c7d9e034` |
| 生产语义指纹 | `480873e9…` | `a4f55b14…` |

指纹对比（`production_fingerprint.py --compare`）：**唯一差异 = `jurisdiction_exception`
0→1 行**。其余表摘要一致。基线指纹与 Wave01 发布后的 `480873e9…` 相符，说明本轮之前无漂移。

## 五、已知缺口

- **激活不写 `audit_log`**：`apply_jurisdiction_proviso.py` 落表但不追加审计行，所以这次
  辖区级法律效力变更在审计流里唯一的痕迹是表自身的 `reviewed_by` / `reviewed_at`。
  未擅自补写（补审计需决定 actor 语义，属代码变更 + 数据写入），记为待办。
- **激活 ≠ 发布**：6 条被拦下的候选仍需新的 batch manifest + 新人工审查才能发布。

## 六、回退

删除 `JPROV-001` 行即回到激活前状态（`resolver` 只读 `current` + `reviewed_active`，
一旦删除或不满足绑定五条件就完全不生效）。回退同样属 Human Decision，不得由 AI 自行执行。

## 七、产物

- `scripts/verify_adr030_production_activation.py`（新增，只读 A/B 探针；ruff check/format PASS）
- `artifacts/adr030_activation/fingerprint_before.json`（`480873e9…`）
- `artifacts/adr030_activation/fingerprint_after.json`（`a4f55b14…`）
