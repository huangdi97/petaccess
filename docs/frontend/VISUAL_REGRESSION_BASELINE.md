# Visual Regression Baseline

> 本轮从「**没有截图基线**」变成「47 张真实基线，比对模式全绿」。
> 复跑命令写在 §6，任何人可复现。

## 1. 结果

| 项 | 值 |
|---|---|
| 基线总数 | **47**（消费者 33 + Admin 14） |
| 视口 | 5 个：`h5-390` / `h5-768` / `h5-1440` / `admin-1440` / `admin-768` |
| 比对模式结果 | **47 passed（0 failed）** |
| 生成后再比对 | **47 passed** —— 基线可复现，不是"生成即通过" |
| 配置 | `playwright.visual.config.ts`（与功能 E2E 的 `playwright.config.ts` 分开） |
| 规格 | `tests/visual/consumer.spec.ts`（11 例 × 3 视口）、`tests/visual/admin.spec.ts`（7 例 × 2 视口） |
| 共用夹具 | `tests/visual/fixtures.ts` |

覆盖页面：

- **消费者（11）**：home / search-results / search-empty / map / map-sheet / place-unknown /
  place-conditional / rule-trace / contribute / mine / boundary
- **Admin（7）**：login / dashboard / rule-candidates / evidence / sources / regulations / audit

## 2. 确定性是怎么保证的

截图基线只在**确定**的前提下有意义。四件事：

| 手段 | 原因 |
|---|---|
| `page.clock.install({time: 2026-09-15T04:00:00Z})` | 「3 天前核验」这类相对时间会随真实时间漂移，不冻结的话每次 diff 都在说数据的谎 |
| `settle()` 等骨架屏消失 | H5 先渲染骨架再渲染内容；`networkidle` 在场所详情页（扇出 8 个请求）还没回来时就触发了，截到的是 loading 态 |
| `animations: disabled` / `caret: hide` / `scale: css` | 动画中间帧与光标闪烁不是设计的一部分 |
| 数据源固定为真实种子库（`:8010`） | 不 mock：空列表意味着数据为空，而不是夹具为空 |

`maxDiffPixelRatio: 0.02` —— 抗锯齿与字体栅格化在不同机器上有差异，阈值设 0 会让每次更新基线变成苦役。

## 3. 两个「截图会骗人」的坑（都已加硬护栏）

### 3.1 错误态截图

预览服务器的 `VITE_API_PROXY` 指向了 `:8000`（默认值）而不是 `:8010`（真实 API），
**11 个消费者页面全部渲染「加载失败」，而视觉用例"通过"了 20 个。**

`toHaveScreenshot` 只比像素，不比正确性：一张「加载失败」和下一张「加载失败」永远匹配。
唯一暴露它的用例，是因为它需要点击一个错误页上没有的按钮。

→ `fixtures.ts::assertNotErrorState()`，在每次截图**前**检查 `[data-state="ERROR"|"NETWORK_ERROR"]`，
命中即抛错并打印页面上的原话。做成 `shot()` 的内建步骤而不是各用例自行调用——否则总有人忘。

### 3.2 空白页截图

平板视口原本用 `devices["iPad (gen 7)"]`，即 **WebKit**。本环境下 WebKit 加载不了应用：
`/@vite/client`、`/node_modules/.vite/deps/vue.js`、`/src/main.ts` **全部 404 + "Load request cancelled"**。

WebKit 仍然渲染 `index.html`，所以**运行不报错**——它截了一张空白文档，然后报 PASS。
17 张平板基线全是 **6.2 KB 空白页**，而同一页面在另外两个视口是 100–220 KB。

→ 两处修改：

1. `fixtures.ts::assertRendered()`：检查 Vue 挂载点（`#app` / `#root`）是否有子元素与文本。
   检查的是挂载点而不是 `document.body.innerText`——有些真实页面本来就短（空搜索结果只有一个标题加一句话），
   而**从未启动**的页面是挂载点为空的。
2. 平板视口改用 **Chromium** 768×1024（保留 iPad UA 与 `hasTouch`），
   理由与证据都写在配置里的 `tablet` 常量上方。

> **一张空白基线比没有基线更糟**：它看起来像覆盖，实际什么都没编码。

## 4. 视口矩阵

| 项目 | 引擎 | 视口 | 备注 |
|---|---|---|---|
| `h5-390` | Chromium（Pixel 5） | 393×851，DSF 2.75 | 手机 |
| `h5-768` | Chromium（tablet） | 768×1024，DSF 2，`hasTouch` | **不是 WebKit**，见 §3.2 |
| `h5-1440` | Chromium | 1440×900 | 桌面 |
| `admin-1440` | Chromium | 1440×900 | 桌面 |
| `admin-768` | Chromium（tablet） | 768×1024 | 同上 |

### 已知成本

`tests/visual` 总计 **12 MB**。两张最重的基线是长页面的整页截图：

| 基线 | 大小 |
|---|---|
| `admin-audit-admin-768-win32.png` | 2.1 MB |
| `admin-evidence-admin-768-win32.png` | 1.0 MB |
| `admin-audit-admin-1440-win32.png` | 1.0 MB |

`playwright.visual.config.ts` 里 `toHaveScreenshot.timeout` 已从默认 5s 提到 20s——
768×1024 @2x 的审计日志整页截图会**超时而不是 diff**。

可选收敛手段（本轮未做，属 P2 仓储治理）：平板档 `deviceScaleFactor` 降到 1（约省 2 MB），
或对两个最长页面改为视口内截图。记录在案而不是假装不存在。

## 5. 与功能测试的关系

| | `playwright.config.ts` | `playwright.visual.config.ts` |
|---|---|---|
| 目的 | 断言**行为** | 断言**外观** |
| 用例 | `tests/e2e` | `tests/visual` |
| 手段 | `getByTestId` / `getByRole` / 文本 | `toHaveScreenshot` |
| 视口 | 默认 | 5 个 |

两者共用同一个 API 与同一份种子数据，但**互不替代**：功能全绿不代表像素没变，像素全绿不代表行为正确。

## 6. 复跑

前置：API / H5 预览 / Admin 各自可用（`webServer` 会尝试启动，`reuseExistingServer: true`）。

```bash
# 生成 / 更新基线
./node_modules/.bin/playwright test -c playwright.visual.config.ts --update-snapshots

# 比对（CI 与验收用这个）
./node_modules/.bin/playwright test -c playwright.visual.config.ts
```

想手动起服务时注意：**前端在配置加载时读 `VITE_API_PROXY`**，不设它就会代理到 `:8000`，
页面会渲染「加载失败」——见 §3.1。

```bash
VITE_API_PROXY=http://127.0.0.1:8010 pnpm --filter @petaccess/client-h5 exec vite preview --host 127.0.0.1 --port 5175
VITE_API_PROXY=http://127.0.0.1:8010 pnpm --filter @petaccess/admin exec vite --host 127.0.0.1 --port 5173
```

## 7. 判定

**VISUAL_REGRESSION = PASS。**

47 张基线，5 个视口，生成后再次以比对模式复验 **47 passed**。
本轮同时修掉了「错误态可成基线」与「空白页可成基线」两条会静默失效的路径——
这是基线数量之外更重要的一点：**基线只有在会失败的时候才有价值。**
