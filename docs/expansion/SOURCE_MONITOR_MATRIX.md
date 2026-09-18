# SOURCE_MONITOR_MATRIX — 来源监控矩阵

- expansion_run_id: `EXP-R1-W01-20260918`
- review_revision: `EXP-R1-W01-REVIEW-R1`
- generated_at: 2026-09-18T03:43:17.580156+00:00
- 生成方式：由 `scripts/expansion_w01_reports.py` 从生产库与运行清单派生，非手写

## 1. 必监控判定口径

```
required = source_type ∈ {official_operator_policy, statute_or_regulation,
                          government_service}
           AND source_url IS NOT NULL
```

豁免（逐来源记录理由，非静默豁免）：

- `external_web_reference`：已定稿的第三方新闻报道，不含「当前政策值」，不存在可复检的在位内容。
- `ordinary_user`：无规范可抓取 URL。

## 2. 覆盖

- 必监控来源：13 / 13
（覆盖率 100%）
- SourceMonitor 总数：13
- `next_check_at` 为空：0（必须为 0，否则调度器永不拾取）

## 3. 基线扫描结果（真实抓取）

- 成功取得 content_hash：8
- 被目标站拒绝（401/403/429）：5

| source_type | url | status | HTTP | 延迟ms | hash | 失败数 | 周期(分) |
|---|---|---|---|---|---|---|---|
| government_service | https://www.meet-in-shanghai.net/tc/news/another-new-landmar | active | 403 | 483 | 无 | 1 | 10080 |
| government_service | https://www.shhuangpu.gov.cn/xw/001009/20250902/c7186bba-d3f | active | 202 | 468 | 有 | 0 | 10080 |
| official_operator_policy | https://www.fairmont.com/zh/hotels/shanghai/fairmont-peace-h | active | 200 | 1780 | 有 | 0 | 1440 |
| official_operator_policy | https://www.langhamhotels.com/sc/the-langham/shanghai/offers | active | 200 | 609 | 有 | 0 | 1440 |
| official_operator_policy | https://www.library.sh.cn/guide/xuzhi | active | 403 | 406 | 无 | 1 | 1440 |
| official_operator_policy | https://www.shanghaidisneyresort.com/zh-cn/legal/park-rules/ | active | 200 | 671 | 有 | 0 | 1440 |
| official_operator_policy | https://www.shanghaimuseum.net/mu/frontend/pg/m/service/visi | active | 200 | 530 | 有 | 0 | 1440 |
| official_operator_policy | https://www.shanghaizoo.cn/sites/shanghaizoo/shanghaizoo_wap | active | 200 | 531 | 有 | 0 | 1440 |
| official_operator_policy | https://www.starbucks.com.cn/en/about/news/starbucks-red-boo | active | 200 | 421 | 有 | 0 | 1440 |
| official_operator_policy | https://www.taikooliqiantan.com/detail/58.html | active | 403 | 468 | 无 | 1 | 1440 |
| official_operator_policy | https://www.xintiandi.com/en/event/%e7%be%8e%e5%a5%bd%e9%9b% | active | 200 | 2235 | 有 | 0 | 1440 |
| statute_or_regulation | https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd441 | active | 403 | 391 | 无 | 1 | 1440 |
| statute_or_regulation | https://www.shanghai.gov.cn/gwk/affairs/content/0033@641a604 | active | 403 | 405 | 无 | 1 | 10080 |

### 被拒绝的来源

| url | HTTP |
|---|---|
| https://www.meet-in-shanghai.net/tc/news/another-new-landmark-this-wee | 403 |
| https://www.library.sh.cn/guide/xuzhi | 403 |
| https://www.taikooliqiantan.com/detail/58.html | 403 |
| https://gaj.sh.gov.cn/shga/wzXxfbGj/detail?pa=eabcee2b5dd4411bf89cd8d0 | 403 |
| https://www.shanghai.gov.cn/gwk/affairs/content/0033@641a604d24ef4395a | 403 |

**这 5 个站点的反爬拦截是外部条件，不是本流水线缺陷。** 处理原则：

1. 403 记录为 `failure_count + 1` 与 `last_http_status=403`，**绝不**被当成「内容变了」——不可达 ≠ 来源说了新话。
2. 连续失败达阈值（3 次）后 `status` 转为 `failing`（MONITOR_DEGRADED），并指数退避（上限 24 小时）。
3. 失败**不撤回任何已发布规则、不删除任何已捕获证据**——页面没了不等于我们没读过它。
4. 已捕获的历史证据继续有效，人工复核不受影响。

## 4. 条件请求与退避

- 条件 GET：携带 `If-None-Match` / `If-Modified-Since`；304 不产生新证据，但保留 validator 以换取下一次 304。
- 429/503：优先遵守 `Retry-After`；无该头时指数退避，上限 `MAX_BACKOFF_MINUTES`。
- 单次 sweep 有 `limit` 上界，避免一次扫描打爆来源。

## 5. 变更处理链路

`变更 → diff artifact → bundle → candidate → 人工复核`，**绝不直接改规则**。重复检出同一内容状态只产出一个候选（dedup_key 去重）。

## 6. 本轮新增的实现

| 项 | 说明 |
|---|---|
| `POST /admin/monitors/sweep` | 扫描所有到期监控 |
| `GET /admin/monitors/due` | 只读查看下次会扫哪些，不产生出站流量 |
| `next_check_at` 创建时初始化 | 此前仅 sweep 后才写，导致监控建而不跑 |
| Celery `source-monitor-sweep` | 每小时调度 |
| `Retry-After` 支持 | 429/503 遵守服务端窗口 |
