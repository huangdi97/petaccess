# BATCH_02 演练报告（ADR-030 但书解锁后的 6 条 LEGAL 犬类基底）

- 时间：2026-09-18
- 批次：`EXP-R1-W01-REVIEW-R1-BATCH-02`
- 清单：`docs/governance/publish_batches/EXP_R1_W01_REVIEW_R1_BATCH_02.json`
- 演练库：`petaccess_publish_rehearsal_b2`（生产库克隆，含已激活的 `JPROV-001`）
- **生产库未写入。** 本报告是发布前的证据，不是发布回执。

## 一、为什么现在多出 6 条可执行

`JPROV-001` 激活后，我把辖区但书接进了预发布闸门（`w01_semantic_bridge.py`）：

- 闸门 `probe_guide_dog_safety_path` **本来就有第三条路径 C**（`jurisdiction`），
  但桥接脚本从没把辖区例外传进去 —— 机制和激活都到位了，线没接。
- 修复：`load_jurisdiction_exceptions()` 只读生产库的
  `status='current' AND review_status='reviewed_active'` 行，作为路径 C 传入。

接线前后（同一份已签署登记表）：

| 指标 | 接线前 | 接线后 |
|---|---|---|
| `HUMAN_APPROVED` | 15 | 15 |
| `FINAL_EXECUTABLE` | 5 | **11** |
| `EXCLUDED_APPROVED` | 10 | **4** |

`legal_dog_blocked` 由 6 变 0。剩下 4 条不可执行的原因与上轮一致：
`SOURCE_SCOPE_*` ×2（迪士尼/动物园，需 B2）、`INREACHABLE_APPROVED_CARVE_OUT` ×1（迪士尼，同因）、
`ADR021_UNVERIFIED_SEARCH_SNIPPET` ×1（世纪公园，需 B4）。

## 二、BATCH_02 的内容

6 条 AccessRule（无 RuleException —— 它们的导盲犬路径就是辖区但书本身）：

| rule_id | 场所 |
|---|---|
| `w01-052d19ccba` | CHARLIE'S 粉红汉堡（马当路店） |
| `w01-7de2f5d75b` | omitofee 上海首店（浦江郊野公园滨江漫步区） |
| `w01-df1645fe68` | 上海新天地朗廷酒店 |
| `w01-8ba2b49b01` | 上海苏河湾万象天地 |
| `w01-d1aee78159` | 前滩太古里 |
| `w01-e951785d1b` | 港汇恒隆广场 |

`BATCH_DEPENDENCY_CLOSED = PASS`。清单里已发布的 5 行以
`ALREADY_PUBLISHED_IN_EARLIER_BATCH` 单列，不与"不可执行"混写 —— 这两件事不能压平。

## 三、演练执行

```bash
.venv/Scripts/python.exe scripts/publish_reviewed_r1.py --execute \
  --batch-file docs/governance/publish_batches/EXP_R1_W01_REVIEW_R1_BATCH_02.json \
  --max-approve 8 --database-name petaccess_publish_rehearsal_b2 \
  --reviewer huangdi97 --token <jwt> \
  --registry docs/expansion/review_decisions_expansion_r1_wave01_publishable.json \
  --snapshot-out artifacts/b2_rehearsal_receipt.json
```

- 第一次：`ACCESS_RULE_CREATE_COUNT = 6`，`failed = []`，6 条均 `layer_preserved=true` /
  `mandatory_preserved=true`。
- 第二次（幂等）：`ACCESS_RULE_CREATE_COUNT = 0`、`NOOP_COUNT = 6`、`BLOCKED_COUNT = 0`。

## 四、答案验证（A/B 探针，同一批实时行跑两遍）

`scripts/verify_adr030_production_activation.py --db-name petaccess_publish_rehearsal_b2`：

| 场所 · 区域 | 普通犬 | 导盲犬 before → after |
|---|---|---|
| CHARLIE'S 粉红汉堡 · 室内用餐区 | prohibited（不变） | prohibited → **allowed** |
| omitofee 上海首店 · 室内空间 | prohibited（不变） | prohibited → **allowed** |
| 上海新天地朗廷酒店 · 客房内部 | prohibited（不变） | prohibited → **allowed** |
| 上海苏河湾万象天地 · 室内商铺及公共区域 | prohibited（不变） | prohibited → **allowed** |
| 前滩太古里 · 商场室内空间 | prohibited（不变） | prohibited → **allowed** |
| 港汇恒隆广场 · 商场室内公共区域 | prohibited（不变） | prohibited → **allowed** |

`verdict = PASS`。两条不变式都成立：

1. 普通犬在带/不带但书两次解析中**完全一致**（但书不得外溢到导盲犬以外）；
2. 导盲犬不再 `prohibited`，且生效来源可追溯（`JPROV-001`，按法律文件同一性绑定）。

室外区域仍是 `unknown` —— 那些 zone 没有基底规则，这不是缺陷，是数据边界。

## 五、发布前待确认的一件事

BATCH_02 发布后，**带已发布规则却没有坐标的场所从 2 个变成 6 个**
（CHARLIE'S / omitofee / 朗廷 / 苏河湾万象天地 均无 `location`），
`/places/nearby` 会继续静默漏掉它们。详见
`docs/expansion/PHASE_B_REMAINING_GATES_B4_B5.md` 的 B5 节。
这不阻断发布，但发布即扩大，需要你知道。

## 六、产物

- `artifacts/b2_rehearsal_receipt.json`、`artifacts/b2_rehearsal_idem.json`
- 代码改动：`scripts/w01_semantic_bridge.py`（路径 C 接线 + `--out/--batch-id/--exclude-published`）
