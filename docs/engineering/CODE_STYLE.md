# Code Style

> 规则由工具强制执行，不是靠自觉。本文件只记录**为什么**，规则本身在 `pyproject.toml`
> 与 `eslint.config.js` / `.prettierignore` 里。

## Python

| 项 | 规则 | 命令 |
|---|---|---|
| 行宽 | 100 | `ruff format` |
| Lint | `E F I W UP B SIM C4` | `ruff check services/api services/worker tests scripts` |
| 类型 | mypy，`services/api/app` 必须 0 错误 | `mypy services/api/app` |
| Python 版本 | 3.11+ target（本机 3.12/3.13） | — |
| 导入顺序 | isort，`known-first-party = ["app", "worker"]` | ruff `I` |
| 测试可导入性 | `pythonpath = ["scripts"]`，测试直接 `import` 治理脚本常量 | — |

### 已刻意允许的例外

| 例外 | 位置 | 原因 |
|---|---|---|
| `B008` | 全局 | FastAPI `Depends()` 写在默认值里是惯用法 |
| `C408 B017` | `tests/**` | 测试构造 kwargs 字典、断言领域异常 |
| `E501` | `services/api/migrations/versions/**` | alembic autogenerate 输出的长列定义 |

### 禁止的写法

- 裸 `# noqa` —— 必须带具体 rule code，并且注释说明为什么。
- `type: ignore` 不带具体错误码；能收紧类型的必须收紧。
- `except Exception: pass` —— 吞异常会让「失败」变成「静默成功」，在治理代码里等同缺陷。
- `raise ValueError("...")` 作为对外错误 —— 用 `app.core.errors` 的领域异常（见 ERROR_MODEL.md）。

### 约定的惯用法

- 路径一律 `pathlib.Path`，不拼字符串。
- 时间一律 timezone-aware（`datetime.now(UTC)`）；数据库列全部 `DateTime(timezone=True)`，
  由 `tests/unit/test_temporal_invariants.py` 机器校验（当前 119 列，0 个 naive）。
- 领域枚举复用 `app/models/enums.py` 的 canonical enum，**不在脚本/测试里重复字符串**。
  决策词表在 `scripts/human_decisions.py`（单一来源）。
- 复杂公共函数写 docstring：purpose / parameters / return / raises / invariants。
  不写 `x += 1  # x 加 1` 这类复述代码的注释；要写就写 **WHY / INVARIANT / ADR**。

## TypeScript / Vue

| 项 | 规则 | 命令 |
|---|---|---|
| Lint | `eslint .`（flat config + vue-ts recommended） | `pnpm lint:fe` |
| 格式 | Prettier | `pnpm format:check:fe` |
| 类型 | `vue-tsc --noEmit`（在 `admin:build` 内） | `pnpm --filter @petaccess/admin build` |
| 严格模式 | `strict: true`；`@typescript-eslint/no-unused-vars` 为 error（`^_` 前缀豁免） | — |

- 业务逻辑抽离页面：可复用判定放 `packages/`，不放进 `.vue` 里重复一份。
- 状态映射只在展示层做一次：resolver 的 `MATCH/CONDITIONAL/...` 经
  `ANSWER_STATUS_TO_SEMANTIC` 归一化，前端不再自己判断。

## 注释的语言

代码注释与标识符用英文；**面向用户的文案与文档用中文**。
治理/法条相关的注释必须能回答「为什么这条不能简化」。
