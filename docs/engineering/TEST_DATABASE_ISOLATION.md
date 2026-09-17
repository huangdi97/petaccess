# 测试库隔离（TEST_DATABASE_ISOLATION）

> 目标一句话：**任何测试负载都不可能写到 `petaccess`。**
> 轮次：`PRODUCTION_DATA_ISOLATION_AND_INTEGRITY_CLOSURE_R1`。

## 1. 原则

- 隔离靠**拒绝**，不靠约定。约定要求每个人记得；拒绝只要求守卫在一处正确。
- 判定由服务端 `current_database()` 给出，不解析 URL。
- 未登记的库名 = `UNKNOWN` = 拒绝。黑名单只能拒绝别人想到的名字。

## 2. pytest

`tests/conftest.py` 使用 `pytest_sessionstart` 而不是 fixture：

> fixture 只在测试**请求**它时才跑，那时第一个集成测试已经写完了。
> `pytest_sessionstart` 在第一条用例执行前就拦住。

```python
pytest_sessionstart  ->
    读 DATABASE_URL -> 解析库名
    连服务端 -> current_database() -> classify_database_name()
    角色 != TEST  ->  pytest.exit(header, returncode=4)
```

退出码 `4` 与 1（用例失败）、3（pytest 内部错误）区分开，工具才能分辨。

真实行为（本轮实测）：

```
DATABASE_URL=…/petaccess       -> PRODUCTION_DATABASE_REFUSED，exit 4，0 条用例执行
DATABASE_URL=…/petaccess_test  -> [pytest-guard] TARGET_DB = petaccess_test TARGET_DB_ROLE = TEST
```

## 3. E2E（Playwright）

`playwright.config.ts`：`globalSetup: "./tests/e2e/global-setup.ts"`。
globalSetup 打 `GET /health/database`，库名或角色不是
`petaccess_e2e` / `E2E` 就抛 `E2E_DATABASE_REFUSED`。

`webServer` 自己做两件事，顺序由 `&&` 保证：

```
isolated_db.py --role E2E --reset   # drop + create + migrate + demo seed
dev_api_server.py --db-name petaccess_e2e --role E2E --port 8010
```

`reuseExistingServer: false` 是刻意的：数据库每次都重建，没有可复用的东西；
而"悄悄接管一个别人开着的 dev server"正是套件写错库的方式。
若真有陈旧服务占着端口，globalSetup 会先报出来。

本轮实测输出：

```
[E2E] TARGET_DB = petaccess_e2e
[E2E] TARGET_DB_ROLE = E2E
18 passed
```

## 4. 视觉回归

`playwright.visual.config.ts`：`visual_db_reset.py && dev_api_server.py --db-name petaccess_visual --role VISUAL --port 8011`。
`visual_db_reset.py` 用 `classify_database_name(...)` 只认 `VISUAL`（原先是一份本地
`FORBIDDEN_DB_NAMES`，已删除）。前端 `preview` 与 admin 分别 :5175 / :5173。

## 5. 发布演练

`rehearsal_db.py`：

- 目标库必须 `REHEARSAL`（`check_name`）；
- 克隆源必须 `PRODUCTION`（`check_source_name`）——从演练库克隆演练库毫无意义。

## 6. Celery 与 Redis

- `celery_app.py` 的 `task_default_queue = settings.celery_task_queue`，
  默认跟随库名（`petaccess_test` / `petaccess_e2e` / …）。队列名即 Redis list key，
  所以不同负载的任务天然分开。
- Redis DB 索引按负载分：默认 0、TEST 1、VISUAL 2。
- 起 worker 时要带同一套环境变量：

```bash
cd services/api
DATABASE_URL=…/petaccess_test CELERY_TASK_QUEUE=petaccess_test REDIS_URL=redis://127.0.0.1:6379/1 \
  ../../.venv/Scripts/python.exe -m celery -A app.worker.celery_app worker --pool=solo --concurrency=1 -Q petaccess_test
```

> 没有真实 worker 时，`test_media` / `test_v05_e2e` 会全部 `TimeoutError`，
> 而且耗时几分钟——不是套件挂了，是缺 worker。

## 7. 收尾清单（本轮教训）

**凡是指向 `petaccess` 的 dev 服务都必须在收尾前确认关闭。**
本轮发现端口 8010 上挂着一个上轮遗留的 `dev_api_server.py --db-name petaccess`
（老代码、连 `/health/database` 都返回 404），一直连着正式库并返回
`E2E-A 告示咖啡` 等夹具数据。已终止。

检查方式：

```bash
curl -s http://127.0.0.1:<port>/health/database   # {"database":…,"role":…}
```

角色不是 `PRODUCTION` 就别让它开着；角色是 `PRODUCTION` 更要明确为什么需要。

## 8. 回归证明

`tests/isolation/test_production_fail_closed.py`（本轮新增，18 条）锁定两件事：

- **进程内**：每个负载断言对 PRODUCTION 都必须抛；`UNKNOWN` 必须抛；
  受治理清理缺证据必须抛；测试负载角色必须正白名单通过。
- **进程外**：真的去跑 `pytest`（要求退出码 4 且输出 `PRODUCTION_DATABASE_REFUSED`）、
  `production_fixture_cleanup.py --execute`（无证据 → 非 0；目标是 TEST 库 → 非 0）、
  `visual_db_reset.py --db-name petaccess`、`rehearsal_db.py --db-name petaccess`
  （均非 0）。

只在「正确配置」下验证隔离与没有验证是分不开的——因为要防的正是配置写错的那一刻。
