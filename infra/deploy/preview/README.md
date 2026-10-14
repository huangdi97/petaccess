# PetAccess Public Preview Backend

这个目录把 **Android Phone Preview 的外部 API blocker** 收敛成一个可重复部署的
Preview/Staging 栈。

它不是 Production 架构，也不会自动发布真实规则数据。

## 目标

在一台具有公网 IP 的 Linux 主机上提供：

- Caddy 自动 HTTPS；
- PetAccess FastAPI；
- PostGIS；
- Redis；
- S3-compatible object storage；
- Celery worker + beat；
- 与 Android Phone Preview 兼容的
  `https://<domain>/api/v1`。

公网只暴露 80/443。API、数据库、Redis、对象存储均不直接发布宿主端口。

## 前提

- Linux host；
- Docker Engine + Docker Compose v2；
- 一个你控制的域名；
- 域名 A/AAAA 已指向该主机；
- TCP 80 / 443 与 UDP 443 可从公网访问。

Caddy 会自动申请和续期 HTTPS 证书。

## 1. 配置

```bash
cp infra/deploy/preview/env.example infra/deploy/preview/.env.preview
```

生成随机值：

```bash
openssl rand -hex 24
openssl rand -hex 32
```

把所有 `CHANGE_ME_...` 和 `preview-api.example.com` 替换掉。

**不要**把 `.env.preview` 提交到 Git；目录内的 `.gitignore` 已禁止它。

`POSTGRES_PASSWORD` 与 `DATABASE_URL` 中的密码必须一致。建议使用上面的 hex 形式，
避免 URL 编码歧义。

## 2. Fail-closed 条件

容器在启动前会拒绝：

- 缺失域名；
- `example.com` / `example.invalid` 示例域；
- `CHANGE_ME` 占位值；
- 非 `APP_ENV=staging`；
- `API_BASE_URL` 不是
  `https://<PETACCESS_PREVIEW_DOMAIN>/api/v1`；
- 开启 `FEATURE_REAL_MAP=true` 却没有腾讯 client/server Key。

API 自身还会拒绝 staging 环境使用仓库公开的 dev JWT 默认值或非 HTTPS public base。

## 3. 启动

在仓库根目录执行：

```bash
docker compose \
  --env-file infra/deploy/preview/.env.preview \
  -f infra/deploy/preview/compose.yaml \
  up -d --build
```

API 容器默认在启动时执行：

```text
alembic upgrade head
```

这个 Preview compose 预期只有一个 API replica。若未来扩成多副本，migration 应拆成独立
deployment job，而不是让多个 API replica 并发迁移。

## 4. 验证 HTTPS/API

```bash
DOMAIN="<your-domain>"

curl -fsS "https://$DOMAIN/health"
curl -fsS "https://$DOMAIN/health/ready"
curl -fsS "https://$DOMAIN/api/v1/ping"
```

再使用仓库与 signed Release 共用的真实 API preflight：

```bash
PETACCESS_PUBLIC_API_BASE="https://$DOMAIN/api/v1" \
  node scripts/release/verify_public_api.cjs
```

这会检查 PetAccess identity、health/ping、Tauri WebView CORS；真实腾讯地图配置存在时还可
继续验证 map provider / GCJ-02 转换。

## 5. 数据原则

新建数据库只执行 schema migration，**不会自动灌入虚构场所 / 规则 / Reality / 照片**。

因此：

- 空数据库出现 Empty-First 产品状态是正常事实；
- 想在公网 Preview 看到真实试点数据，必须导入经过允许的真实 pilot 数据；
- 不得为了“看起来丰富”执行 E2E/visual synthetic seed；
- 不得把 CI fixture 媒体当真实场所照片；
- GOV-01 未签署的数据不能借 Preview 绕过治理发布门。

## 6. 媒体

对象存储只在 Docker 内网监听。

Consumer 的公开场景媒体继续走：

```text
/api/v1/evidence-bundles/<id>/public-media/content
```

API 每次重新检查治理资格；对象存储 endpoint/presigned topology 不暴露给 Consumer。

## 7. 连接 Android Phone Preview

当上面的 preflight PASS 后，把：

```text
https://<domain>/api/v1
```

配置为 GitHub Repository Variable：

```text
PETACCESS_PHONE_PREVIEW_API_BASE
```

然后运行/等待：

```text
Android Phone Preview APK
```

readiness 应从：

```text
BLOCKED_BY_API_BASE
```

变为：

```text
READY
```

之后 workflow 才会生成不需要 adb reverse 的 ARM64 standalone Debug Preview。

## 8. 腾讯真实地图

默认：

```text
MAP_PROVIDER=mock
FEATURE_REAL_MAP=false
```

所以产品必须如实显示 provider-neutral fallback。

拿到真实腾讯 client/server Key 后，再改：

```text
MAP_PROVIDER=tencent
FEATURE_REAL_MAP=true
TENCENT_MAP_KEY_CLIENT=...
TENCENT_MAP_KEY_SERVER=...
```

并用 Phone Preview 的 `require_real_map=true` 再做 packaged validation。

## 9. 停止 / 日志

```bash
docker compose \
  --env-file infra/deploy/preview/.env.preview \
  -f infra/deploy/preview/compose.yaml \
  logs -f api worker edge
```

```bash
docker compose \
  --env-file infra/deploy/preview/.env.preview \
  -f infra/deploy/preview/compose.yaml \
  down
```

默认 `down` 不删除数据卷。

若明确要销毁 Preview 数据：

```bash
docker compose \
  --env-file infra/deploy/preview/.env.preview \
  -f infra/deploy/preview/compose.yaml \
  down -v
```

## 10. GitHub 一键部署 + 自动生成 Phone Preview

仓库提供：

```text
.github/workflows/public-preview-deploy.yml
Public Preview Deploy
```

它只允许 `workflow_dispatch`，不会在普通 push / PR 上自动修改公网环境。

首次使用前，建议把部署 secrets 放进 GitHub Environment **`petaccess-public-preview`**（workflow 的 readiness 与 deploy job 都绑定该 Environment）；非敏感默认值可放 Repository Variables：

Repository variable（可用 workflow 输入临时覆盖 domain）：

```text
PETACCESS_PREVIEW_DOMAIN
PETACCESS_PREVIEW_SSH_PORT        # 可选，默认 22
PETACCESS_PREVIEW_REMOTE_ROOT     # 可选，默认 petaccess-public-preview
PETACCESS_PREVIEW_POSTGRES_DB     # 可选
PETACCESS_PREVIEW_POSTGRES_USER   # 可选
PETACCESS_PREVIEW_S3_BUCKET       # 可选
PETACCESS_PREVIEW_MAP_PROVIDER    # 可选，默认 mock
PETACCESS_PREVIEW_FEATURE_REAL_MAP # 可选，默认 false
```

Secrets：

```text
PETACCESS_PREVIEW_SSH_HOST
PETACCESS_PREVIEW_SSH_USER
PETACCESS_PREVIEW_SSH_KEY
PETACCESS_PREVIEW_SSH_KNOWN_HOSTS
PETACCESS_PREVIEW_POSTGRES_PASSWORD
PETACCESS_PREVIEW_S3_ACCESS_KEY
PETACCESS_PREVIEW_S3_SECRET_KEY
PETACCESS_PREVIEW_JWT_SECRET
PETACCESS_PREVIEW_TENCENT_MAP_KEY_CLIENT   # 仅真实地图需要
PETACCESS_PREVIEW_TENCENT_MAP_KEY_SERVER   # 仅真实地图需要
```

workflow 会按当前 commit 建立不可变远端目录：

```text
<REMOTE_ROOT>/releases/<GITHUB_SHA>
```

再执行 compose build/up、验证公网 HTTPS PetAccess identity，并把：

```text
https://<domain>/api/v1
```

作为显式 `workflow_dispatch` 输入触发 **Android Phone Preview APK**。因此部署成功后不需要人工再复制 API URL 到第二条 workflow。

缺少 domain / SSH / secrets 时，workflow 只产生：

```text
BLOCKED_BY_DOMAIN
BLOCKED_BY_SSH
BLOCKED_BY_SSH_TRUST
BLOCKED_BY_SECRETS
```

并明确不部署。它不会用临时 tunnel、localhost、假 URL 或静态 fixture 绕过外部依赖。

`PETACCESS_PREVIEW_SSH_KNOWN_HOSTS` 必须保存预先核验过的 SSH host key 行（例如在可信网络/控制台核验后得到的 known_hosts 内容）；workflow 不会在部署时用 `ssh-keyscan` 临时接受未知主机。远端部署 secret 只写入 `<REMOTE_ROOT>/shared/.env.preview`，权限固定为 600，不复制进历史 release 目录。

> GitHub 的手动 `workflow_dispatch` 入口要求 workflow 已存在于默认分支。当前功能分支可以接受 CI 验证；正式通过 GitHub UI 执行前，需要先让这条 workflow 进入默认分支。

## 11. 不是 Production


这个栈的目标是解除 **standalone Phone Preview / staging** 的基础设施缺口。

正式 Production 仍需要至少单独评估：

- 托管数据库与备份；
- Redis 高可用；
- 对象存储与生命周期；
- secret manager；
- observability / alerting；
- horizontal scaling；
- migration job；
- WAF / rate-limit / abuse control；
- 正式域名、备案与法务主体；
- platform/store release。

不要把 Preview compose 的 PASS 写成 Production Ready。
