# 数据库环境模型（DATABASE_ENVIRONMENT_MODEL）

> 定义本仓库**每个数据库是干什么的**，以及为什么「按名字猜」不够。
> 轮次：`PRODUCTION_DATA_ISOLATION_AND_INTEGRITY_CLOSURE_R1`。

## 1. 为什么有这个文件

`petaccess` 在 `R2-FINAL-R3-BATCH-01B` 真实发布后就不再是草稿库了。但仓库的 `.env`
指向它，pytest / Playwright / 视觉套件都从 `.env` 解析连接串，于是整整一周的 QA 把
夹具写进了受治理的库：`place` 1249、`access_rule` 1119（`current` 843）、`user` 1759，
而真实试点只有 **10 个场所 + 4 个账号**。

三个原因缺一不可：

1. 只有拒绝名单，没有正白名单（`FORBIDDEN_DB_NAMES` 只会拒绝别人想到的名字）；
2. 每个脚本各自造一份策略，策略之间漂移；
3. 事后警告而不是拒绝——警告不是控制手段。

## 2. 角色表（唯一权威：`services/api/app/db/safety.py`）

| ROLE | 规范库名 | 夹具 | 破坏 | 真实发布 | 真实数据 | 用途 |
|---|---|---|---|---|---|---|
| `PRODUCTION` | `petaccess` | ✗ | ✗ | ✓ | ✓ | 唯一承载真实发布对象、Human Signature 与只读消费答案 |
| `RESTORE` | `petaccess_restore_<stamp>` | ✗ | ✓ | ✗ | ✓ | 从 production 备份还原后做只读核对 |
| `REHEARSAL` | `petaccess_publish_rehearsal_<rev>` | ✓ | ✓ | ✗ | ✓ | clone 自 production，验证 batch 计划与幂等 |
| `VISUAL` | `petaccess_visual` | ✓ | ✓ | ✗ | ✗ | 每次运行从固定 demo 种子重建，保证截图可比 |
| `E2E` | `petaccess_e2e` | ✓ | ✓ | ✗ | ✗ | Playwright 自己创建与消耗业务对象 |
| `TEST` | `petaccess_test` | ✓ | ✓ | ✗ | ✗ | pytest / integration：夹具、回滚、supersession 自由写入 |
| `DEVELOPMENT` | `petaccess_dev` | ✓ | ✓ | ✗ | ✗ | 本地手工调试 |
| `INFRASTRUCTURE` | `postgres` / `template*` | ✗ | ✗ | ✗ | ✗ | 仅用于 `CREATE DATABASE` 之类的管理动作 |
| `UNKNOWN` | （任何未登记名） | ✗ | ✗ | ✗ | ✗ | **不承担任何角色，任何写操作都被拒绝** |

业务库名允许按需带后缀（`petaccess_test_run42`、`petaccess_publish_rehearsal_r3`），
但角色由**全匹配正则**判定，不在表里的名字一律 `UNKNOWN`。

`TEST / E2E / VISUAL / REHEARSAL` 合称 **测试负载角色**（`TEST_WORKLOAD_ROLES`）：
只有它们可以写夹具、可以被 drop/recreate。`PRODUCTION` 的
`destructive_allowed` 恒为 `False`——**任何通用工具都不能破坏它**。

## 3. 判定依据：服务端，不是 URL

URL 会错、会过期、会从 shell profile 里继承。唯一权威是
`SELECT current_database()`，再由上表分类。

```python
from app.db.safety import guard_for_psycopg, classify_database_name

classify_database_name("petaccess")         # PRODUCTION
classify_database_name("petaccess_test_42") # TEST
classify_database_name("petaccess_typo")    # UNKNOWN  -> 拒绝，不是容忍
```

`DB_ROLE` 环境变量只是**声明**，一旦与服务端事实不一致就 `RoleMismatchRefused`
（声明不能覆盖事实）。

## 4. 生产清理是独立入口，不是放宽角色

受治理的生产清理（把泄漏的夹具删掉）**不能**借 `assert_destructive_allowed`——那等于
为了清一次数据就给所有工具开一个破坏正式库的洞。它有自己的入口：

```python
guard.assert_production_cleanup_allowed(
    "生产库夹具清理",
    backup_path=...,        # 必须已存在的物理备份
    reviewed_plan_path=..., # 必须已存在的已审阅 dry-run
)
```

该入口只认「目标是 PRODUCTION + 备份已落盘 + 计划已审阅」。
`assert_destructive_allowed` / `assert_fixture_write_allowed` / `assert_not_production`
对 PRODUCTION **依旧全部拒绝**（有测试锁定，见 `tests/isolation/`）。

## 5. 每个负载用什么库

| 负载 | 库 | 隔离手段 |
|---|---|---|
| pytest / integration | `petaccess_test` | `tests/conftest.py` 的 `pytest_sessionstart`：角色不是 `TEST` 直接 exit 4 |
| Playwright E2E | `petaccess_e2e` | `tests/e2e/global-setup.ts` 打 `/health/database`，不是 E2E 就抛 |
| 视觉回归 | `petaccess_visual` | `visual_db_reset.py` 走 `classify_database_name`，只认 VISUAL |
| 发布演练 | `petaccess_publish_rehearsal_*` | `rehearsal_db.py` 只认 REHEARSAL 目标、只认 PRODUCTION 源 |
| Celery | 跟随所在库 | `task_default_queue = <db name>`，Redis DB 索引按负载分（TEST=1、VISUAL=2） |
| 备份恢复 | `petaccess_restore_*` | `db_cleanup_accidental.py` 把「非 UNKNOWN」一律视为受保护 |
| 本地调试 | `petaccess_dev` | `dev_api_server.py --db-name` |

## 6. 本地命令

```bash
export PATH="/c/Program Files/Git/cmd:/c/Program Files/Git/mingw64/bin:/usr/bin:/bin:$PATH"

python scripts/isolated_db.py --role TEST --reset          # 或 --role E2E
python scripts/visual_db_reset.py                          # petaccess_visual
python scripts/rehearsal_db.py --db-name <clone> --clone --confirm
python scripts/dev_api_server.py --db-name petaccess_test --role TEST --port 8010
python scripts/dev_api_server.py --db-name petaccess --role PRODUCTION --production-confirm --port 8012
```

只确认某个库的角色（不连服务端、改不了任何东西）：

```bash
python -m app.db.safety --describe
```
