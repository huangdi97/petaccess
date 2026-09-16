# Security / Privacy Audit

> 静态审计 + 依赖审计的真实结果。工具跑不动的地方明确标注 `NOT_RUN`，不冒充通过。

## 1. 结论

`security_audit = PASS_WITH_FINDINGS`

| 级别 | 数量 | 说明 |
|---|---|---|
| CRITICAL | **0** | — |
| HIGH | **0** | bandit 起始 1 项（硬编码试点密码），本轮已修 |
| MEDIUM | **0** | — |
| LOW | 15 | bandit 实跑结果，见 §5.1；均为开发态或受控项 |
| FALSE_POSITIVE | 1 | `seed.py` 的 f-string SQL（表名来自硬编码白名单） |
| 未跑 | `pip-audit` | 明确 NOT_RUN，见 §5 |

## 2. MEDIUM — 已修：可预测的 JWT 签名密钥

**发现**：`app/core/config.py` 中

```python
jwt_secret: str = "dev_only_change_me_min_32_bytes_0123456789abcdef"
```

这个字符串同时出现在代码仓库里。任何拿到仓库的人都能伪造 token——开发环境可接受，
但一旦以 `app_env=production` 部署而没有覆盖，就是完整认证绕过。这是**默认即危险**，
而不是「配置错了才会危险」。

**修复**：新增 `app/core/config.py::validate_runtime()`，在
`app_env ∈ {production, prod, staging}` 且密钥仍是默认值时**启动时抛
`InsecureDefaultSecret`**；`main.py` 的 `lifespan` 里调用。
开发环境行为完全不变。

**验证**：`tests/unit/test_config_validation.py`（6 例），覆盖开发态放行、
三种生产态拒绝、真实密钥放行、以及「默认值漂移」守卫。

## 3. LOW（记录，不修）

| # | 项 | 现状 | 为何不修 |
|---|---|---|---|
| 1 | CORS `allow_methods=["*"]` / `allow_headers=["*"]` 且 `allow_credentials=True` | `allow_origins` 是 localhost 显式白名单（5173/5174/5175/4173/8080/3000） | 源已收窄，方法/头的通配在此配置下不构成实际风险；收紧需要前端逐端点头，属于部署配置 |
| 2 | Admin 的 JWT 存 `localStorage` | `admin_token` | SPA 常规做法；改 httpOnly cookie 是认证形态变更（新功能），不在本轮 |
| 3 | `seed.py` 内置 `admin12345` 开发账号 | 注释标明 dev-only | 仅 seed 使用；生产不跑 seed |
| 4 | MinIO 默认 `minio/minio_dev_only` | `Settings` 默认值 | 本地对象存储；生产由环境变量覆盖 |

## 4. FALSE_POSITIVE

`services/api/app/db/seed.py:181`

```python
session.execute(text(f"DELETE FROM {table}"))
```

`table` 来自同一函数内的**字面量元组**（含 `"user"` 这类需要引号的标识符），
不是外部输入，无法注入。保留 f-string 是因为 SQL 标识符不能参数化。
标注为已知，避免以后被误读为注入点。

## 5. 扫描覆盖（实测）

| 检查 | 结果 |
|---|---|
| `eval` / `exec` / `pickle` / `yaml.load(` | 0 命中（`services/` `scripts/`） |
| `shell=True` / `os.system` | 0 命中 |
| `subprocess` | 仅 `scripts/mutation_probe.py`，参数列表形式、无 shell |
| 硬编码密钥赋值（正则 `(api_key\|secret\|password\|token)\s*=\s*"…16+"`） | 0 命中（除上表的 Settings 默认值，由 `validate_runtime` 覆盖） |
| 原始 SQL 拼接 | 1（见 FALSE_POSITIVE） |
| 前端 `console.log` / 调试输出 | 0 命中 |
| 统一错误体（§20） | `{"error": {"code","message","request_id","details"}}`，不含 SQL / 栈 / 路径 / 密钥 |
| `pnpm audit --prod` | **PASS** — 0 已知漏洞 |
| `bandit`（本轮补跑） | **PASS_WITH_FINDINGS** — 见 §5.1 |
| `pip-audit` | **NOT_RUN** — 安装失败（`cyclonedx.parser` 依赖冲突，独立 venv 亦失败）；未取回结果，不冒充通过 |

### 5.1 bandit 实跑（本轮补跑，修正上一版的 NOT_RUN）

命令：

```bash
.venv/Scripts/python.exe -m bandit -q -r services/api/app services/worker scripts
```

| | 起始 | 最终 |
|---|---|---|
| HIGH | **1** | **0** |
| MEDIUM | **1** | **0** |
| LOW | 16 | **15** |
| 代码行数 | 18,262 | 18,262 |

本轮修掉的 2 项：

| 文件 | 级别 | 问题 | 处理 |
|---|---|---|---|
| `scripts/real_pilot_ingest.py` | HIGH | 硬编码密码 `PilotAdmin0913!` | 改为读取环境变量 `PILOT_ADMIN_PASSWORD`，缺失时显式失败而不是回退到硬编码值 |
| `scripts/evidence_repair_r2.py` | MEDIUM | `hashlib.md5()` 默认用法（B324） | 该摘要只用于生成维修记录的短 id，不是安全原语——显式声明 `usedforsecurity=False` 并在注释里说明理由 |

另外三处 `except Exception: pass`（`seed.py` / `observability.py` / `mock.py`）此前是无注释的静默吞异常，
补了「为什么这里吞是合理的」的说明——不是 suppress，是让下一个读代码的人不必猜。

剩余 15 项 LOW 全部为开发态或受控项（Flask/EOL 无关项、`try/except/pass` 的开发态兜底、
`rulespec/model.py` 的枚举成员 `PASS_THROUGH = "pass_through"` 被 B105 误判为硬编码密码）。

## 6. 依赖

- `pnpm audit --prod` 无已知漏洞。
- **未做任何 major 升级**（规范 §23 明确禁止无必要的 major 升级）。
- Python 侧依赖审计（`pip-audit`）**仍未跑**，是本案卷的真实缺口，见 §5。

## 7. 建议（下一步，不在本轮）

1. 在 CI 里固定跑 `bandit -r services/api/app` 与 `pip-audit`，把 §5 的两个 NOT_RUN 变成常态门禁。
2. 为生产部署增加 `app_env` 与密钥的部署前校验清单（`validate_runtime` 已在启动期兜底）。
3. 评估把 Admin token 迁移到 httpOnly cookie（认证形态变更，需要独立评估）。
