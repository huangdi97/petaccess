# 测试（TESTING）

> 本文件是测试方针的入口。完整的矩阵与用例清单在
> `docs/engineering/TEST_MATRIX.md`；逐阶段测试计划在 `docs/TEST_PLAN_v0.5.md`。
> 本文件不重复它们，只规定**什么断言才算数**，以及签署之后测试该怎么演化。

## 1. 跑测试

```powershell
# 全量（PYTHONPATH= 是必须的：沙箱 sitecustomize 拦截 os.renames，
# Hypothesis 建 charmap 缓存会 ENOTEMPTY，表现为中途超时）
$env:PYTHONPATH=""; uv run pytest -q --basetemp=$env:TEMP\petaccess-pytest

# 单文件
$env:PYTHONPATH=""; uv run pytest tests/unit/test_publish_plan.py -q

# 静态门禁
uv run ruff check services/api services/worker tests scripts
uv run ruff format --check services/api services/worker tests scripts
cd services/api; uv run mypy .
```

`--basetemp` 必须放仓库外，否则临时目录会被当成源码收集。

## 2. 断言层级（按价值排序）

优先写这些，而不是追求数量：

| 断言 | 例子 |
|---|---|
| Human > AI | 机器建议 APPROVE + 人类 HOLD ⇒ 不可发布 |
| Approved ≠ publishable | 签署通过但闸门失败 ⇒ `BLOCKED`，且 Human Decision 不被改写 |
| HOLD / REJECTED 永不发布 | 也不得被 base / 依赖 / 例外 helper 间接带入 |
| 例外 ≠ 普通规则 | carve-out 计划为 `CREATE_RULE_EXCEPTION`，不是第二条 `AccessRule` |
| base 先于 exception | 例外步骤的 base 必须排在它之前 |
| LEGAL 不被 OPERATOR 放宽 | 跨层绑定在写入边界被拒绝并回滚 |
| dry-run 真实 | 闸门真的跑了；`NOT_RUN` 不得被报成 `PASS` |
| dry-run 零写入 | 前后行数一致，子进程级也一致 |

「`517 passed` → `600 passed`」不是目标。**测试数量不是证据，断言内容才是。**

## 3. 生命周期的状态迁移会打红测试——这是设计使然，不是回归

签署之前，若干测试断言「签署字段必须为空」——那是当时唯一正确的状态。
签署之后再去断言它，等于断言一件假事。正确做法是**演化**，不是删除：

| 签署前的断言 | 签署后的形态 |
|---|---|
| 所有签署字段为空 | 所有签署字段齐备、reviewer 唯一且为具名人类、`reviewed_at` 带时区 |
| 登记表与 baseline 摘要相同 | 「签署之后没动过」（对比 post-signature 快照）+「签署只动了签署字段」（对比 pre/post 非签署投影） |
| 决策表为空 | 决策表与登记表逐条一致且无空缺 |
| （无） | 生成器重跑不得抹掉签署；formatter 不得争夺签署文件 |

演化时必须保留原意图。删除断言等于连保护一起删掉。

## 4. 与 DB 有关的测试

- 需要真实 Postgres：`petaccess-db-1`（PostGIS）。Docker 未起时相关用例会失败，
  这是 `BLOCKED_EXTERNAL`，不是 PASS。
- 单测优先用 `tests/unit/conftest.py::db_session`（用例结束回滚）。
- 集成测试若必须 commit（例如要走 HTTP），必须在 `finally` 里删干净自己造的数据，
  **不得触碰签署登记表所描述的 pilot 数据**。
- 视觉回归必须跑在专用可重置库上（`scripts/visual_db_reset.py`），否则基线永远对不上。

## 5. 时间相关断言

时效（freshness）与审计时间戳不得依赖挂钟：

- 被测逻辑接受注入的 `now`，测试固定它；
- 不得在断言里写 `datetime.now()`，否则测试成为 time bomb；
- dry-run 的 freshness 结果**是**日期相关的，因此报告里必须写明测量时刻。

## 6. 生成物与 formatter

生成物（`docs/reality_audit/**/*.json`、`HUMAN_REVIEW_DECISIONS_*.json`、签署包与速填表 `*.md`）
在 `.prettierignore` 中。生成物不进前端格式闸门，也不得被 Prettier 重新排版——
否则「人类的裁决」会变成两个工具互相覆盖的文件。

## 7. 变异探针

`scripts/mutation_probe.py` 用来确认关键断言真的会失败（例如把 HOLD 短路去掉）。
新增治理断言后，值得同步加一条探针，否则无法区分「断言在保护」与「断言恰好成立」。
