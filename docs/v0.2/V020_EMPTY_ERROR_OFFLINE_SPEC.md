# V020 Empty / Error / Offline / Loading / Toast Spec

Status: M2 Product Experience Foundation — async & edge states
Last updated: 2026-09-24
Owner: PetAccess v0.2.0 M2

## 1. Unified empty state

Every consumer page that can legitimately render nothing maps to one agreed
wording in `@petaccess/design-tokens/src/copy-empty.ts` (`EMPTY_STATE_COPY`):

| Context | Title | Description | Primary | Secondary |
|---|---|---|---|---|
| HOME | 当前还没有已发布的场所数据 | 你仍然可以了解 PetAccess 如何区分规则与现场，或者提交第一条线索。 | 探索地图 | 贡献线索 |
| SEARCH | 没有找到已收录场所 | 试试其他关键词，或提交一个新的场所线索。 | 提交场所线索 | 清除筛选 |
| MAP | 地图暂无已发布场所 | 当前区域还没有已发布的数据。未收录不代表场所没有规则。 | 返回首页 | — |
| RULE | 暂无规则记录 | 尚未收录该场所的规则。未收录不代表场所没有规则。 | 贡献规则线索 | — |
| REALITY | 暂无足够现场记录 | 暂无记录不代表现实中没有动物。 | 贡献现场记录 | — |
| STAFF | 暂无工作人员响应记录 | 今天还没有来自管理方的现场响应记录。 | — | — |
| FACILITY | 暂无设施信息 | 该场所尚未收录设施信息。 | — | — |
| EVIDENCE | 暂无可见证据 | 该场所还没有公开可见的依据条目。 | — | — |
| CONTRIBUTION_HISTORY | 还没有贡献记录 | 你提交的现场记录与规则线索会出现在这里。 | 去贡献 | — |

`PaEmptyState` renders icon + title + description + optional primary/secondary
buttons (`data-state="EMPTY"`). Home and Search already implement these exact
strings in their views. No empty page invents its own copy anymore.

## 2. Loading foundation

Skeleton family in `apps/client-h5/src/components/loading/`:

- `HomeSkeleton` — header/search/entries/list shape.
- `SearchResultSkeleton` — result-row shape (matches `PlaceListItem` height).
- `PlaceSkeleton` — detail-page shape.
- `MapLoadingOverlay` — overlay over the stable map frame.
- `EvidenceSkeleton` — evidence-section shape.

Rule: loading keeps the content structure stable (no full-screen spinner, no
layout shift). `PaSpinner`/`PaSkeleton` exist as the primitives; pages compose
the family components instead of spinning.

## 3. Error foundation

`src/errors.ts` maps any thrown value to one of six presentations
(`ERROR_PRESENTATIONS` in `@petaccess/design-tokens/src/copy.ts`):

| Kind | Title | Description | Retry |
|---|---|---|---|
| NETWORK_OFFLINE | 当前无网络连接 | 已加载内容仍可查看；需要联网的操作已暂停。 | 重新连接 |
| SERVICE_UNAVAILABLE | 服务暂时不可用 | 数据服务暂未响应，请稍后重试。 | 重试 |
| AUTH_EXPIRED | 登录已过期 | 请重新登录后再继续。 | 重新登录 |
| MAP_UNAVAILABLE | 地图暂不可用 | 地图服务未加载成功，请稍后重试或使用列表视图。 | 重试 |
| CONTENT_NOT_FOUND | 未找到该内容 | 它可能已被移除，或链接有误。 | — |
| UNKNOWN_ERROR | 出现了一点问题 | 操作未能完成，请重试。 | 重试 |

`presentError(e)` maps `ApiError` (status/code), `TypeError` (fetch network
failure) and offline `navigator.onLine === false` into these kinds; unknown
failures degrade to UNKNOWN_ERROR. `PaErrorState` renders icon + title +
description + retry (`data-state="ERROR"`, `role="alert"`); `AppBoundary` uses
the same mapping for uncaught render errors.

**Contract**: consumer build output and rendered pages never contain `500`,
`SQLAlchemy`, `FastAPI`, `Tauri`, `Rust` or stack-trace strings — verified by a
build-artifact grep in the engineering report and by the a11y/visual suites.

## 4. Offline foundation

`GlobalOfflineBanner` (hosted by ConsumerAppShell) shows
「当前离线，部分内容可能不是最新状态。」with a 重连 button
(`data-testid="global-offline-banner"`), driven by `useOnline()`.

Rules:
- Cached/loaded content stays visible but is **never presented as latest**.
- Mutating actions are disabled/explained by the pages (existing copy in
  ContributeView etc. retained).
- `PaOfflineState` exists for full-page offline contexts (`data-state="OFFLINE"`).

## 5. Toast / dialog

`useUi()` provides `toast(success|info|warning|error)`, `dismissToast`,
`confirm(...)` → Promise<boolean>. `ToastHost` renders the stack at
`--pa-z-toast` (role `alert` for error, `status` otherwise); `DialogHost` at
`--pa-z-modal`. No page-level `alert()` / console-only errors / random toast
libraries remain.

## 6. Verification

- e2e `empty-state.spec.ts` pins the Home empty title + the Search empty copy
  against route-intercepted empty responses.
- visual regression adds Home empty / Home fixture / Search empty / Search
  fixture / Offline / Error baselines (see V020_M2_SCREENSHOT_REVIEW.md).
