# Visual Regression Baseline

> 从「**没有截图基线**」到「47 张真实基线，5 个视口，比对模式全绿且可复现」。
> 复跑命令写在 §6。

## 1. 结果

| 项 | 值 |
|---|---|
| 基线总数 | **47**（消费者 33 + Admin 14） |
| 视口 | 5 个：`h5-390` / `h5-768` / `h5-1440` / `admin-1440` / `admin-768` |
| 比对模式结果 | **47 passed（0 failed）** |
| 生成后立刻再比对 | **47 passed** —— 基线可复现，不是"生成即通过" |
| 重复基线检查 | **0 组重复 MD5** —— 任何两张基线都不是同一张图 |
| 数据源 | 专用库 `petaccess_visual`，每次运行前重建并重新播种（§2） |
| 配置 | `playwright.visual.config.ts`（与功能 E2E 的 `playwright.config.ts` 分开） |
| 规格 | `tests/visual/consumer.spec.ts`（11 例 × 3 视口）、`tests/visual/admin.spec.ts`（7 例 × 2 视口） |
| 共用夹具 | `tests/visual/fixtures.ts` |

覆盖页面：

- **消费者（11）**：home / search-results / search-empty / map / map-sheet /
  place-unknown / place-restricted / rule-trace / contribute / mine / boundary
- **Admin（7）**：login / dashboard / rule-candidates / evidence / sources / regulations / audit

## 2. 确定性是怎么保证的

截图基线只在**确定**的前提下有意义。五件事：

| 手段 | 原因 |
|---|---|
| 专用库 `petaccess_visual`，每次运行前 DROP + 迁移 + 播种 | **见 §2.1**：跑实时开发库时，基线会随数据增长而失效 |
| `page.clock.install({time: 2026-09-15T04:00:00Z})` | 「3 天前核验」这类相对时间会随真实时间漂移 |
| `settle()` 等骨架屏消失 | H5 先渲染骨架再渲染内容；`networkidle` 在场所详情页（扇出 8 个请求）还没回来时就触发了 |
| `animations: disabled` / `caret: hide` / `scale: css` | 动画中间帧与光标闪烁不是设计的一部分 |
| 不 mock 数据源 | 空列表意味着数据为空，而不是夹具为空 |

`maxDiffPixelRatio: 0.02` —— 抗锯齿与字体栅格化在不同机器上有差异，阈值设 0 会让每次更新基线变成苦役。

### 2.1 为什么不能对着开发库截图（本轮发现并修掉）

最初的 47 张基线是对着开发库（`:8010`）截的。生成当天全绿，**第二天以比对模式重跑，Admin 8 张全红**：

| 基线 | 偏差 |
|---|---|
| `admin-rule-candidates` | 90644 px 不同（ratio 0.03） |
| `admin-sources` | 高度 839 → 843 |
| `admin-regulations` | 高度 3040 → 3334 |
| `admin-audit` | 高度 7471 → 7452；768 档 **130871 → 130890** |

原因不是渲染回归，是**数据在长**：审计日志、待审队列、现场记录都是单调增加的。
审计页基线本身就高 13 万像素，并且在 20s 内拍不完（超时而不是 diff）。
一张每次运行都会变的基线不能发现回归，只会制造噪声，而噪声会被忽略。

修法：视觉套件改用专用库，每次运行前由 `scripts/visual_db_reset.py` 重建并重新播种固定演示数据。
更新基线的那次运行与比对那次运行因此从**逐字节相同的初始状态**出发——这正是 diff 有意义的前提。

该脚本带硬护栏：库名固定为 `petaccess_visual`，且拒绝在保护名单内的库名上运行
（`run_demo_seed()` 会清空候选/争议/审计表，跑错库等于销毁治理数据）。
**开发库与试点数据从未被触碰。**

## 3. 三种「截图会骗人」的方式（都已加硬护栏）

### 3.1 错误态截图

预览服务器的 `VITE_API_PROXY` 指向了 `:8000`（默认值）而不是真实 API，
**11 个消费者页面全部渲染「加载失败」，而视觉用例"通过"了 20 个。**
`toHaveScreenshot` 只比像素，不比正确性：一张「加载失败」和下一张「加载失败」永远匹配。

→ `fixtures.ts::assertNotErrorState()`，在每次截图**前**检查 `[data-state="ERROR"|"NETWORK_ERROR"]`，
命中即抛错并打印页面上的原话。做成 `shot()` 的内建步骤而不是各用例自行调用——否则总有人忘。

### 3.2 空白页截图

平板视口原本用 `devices["iPad (gen 7)"]`，即 **WebKit**。本环境下 WebKit 加载不了应用：
`/@vite/client`、`/node_modules/.vite/deps/vue.js`、`/src/main.ts` **全部 404 + "Load request cancelled"**。
WebKit 仍然渲染 `index.html`，所以**运行不报错**——它截了一张空白文档，然后报 PASS。
17 张平板基线全是 **6.2 KB 空白页**，而同一页面在另外两个视口是 100–220 KB。

→ 两处修改：`fixtures.ts::assertRendered()` 检查 Vue 挂载点是否有子元素与文本；
平板视口改用 **Chromium** 768×1024（保留 iPad UA 与 `hasTouch`），理由写在配置里。

### 3.3 两张基线、一张图（本轮发现）

`map-sheet` 的名字与用例注释都说它拍的是"从列表打开的底部 sheet"。实际上它先点 `view-list`
再点列表行——而列表行是 `@click="open(p.id)"`，**直接跳转到场所详情页**。
于是 `map-sheet` 与 `place-unknown` 在三个视口上 **MD5 完全相同**：

```
009cc544a2c88078b29554750cf07f19  place-unknown-h5-1440-win32.png
009cc544a2c88078b29554750cf07f19  map-sheet-h5-1440-win32.png
```

两个基线名、一张图、底部 sheet **零覆盖**。真实入口是点地图上的 marker
（`MockMap` 的 `emit('select')`），多成员聚合点则是缩放而不是选中。

修 `map-sheet` 时又暴露出上半部分的成因：`.map-pin` 用 `translate(-50%, -100%)` 画在锚点**上方**，
而 `project()` 只把锚点夹在 8%~88%，没给 44px 的 pin 留空间——顶部一排 marker 被 `overflow: hidden`
裁掉一半，最高的那个中心点落在容器边缘，Playwright 报 `.map-mock intercepts pointer events`
（手指点 marker 正中会得到同样结果）。现在改用 CSS `clamp()` 按像素预留，
并且把 `.lbl` 放到 `.dot` 之前，让**针尖**而不是标签落在坐标上。

**建议新增的护栏（未做，见 §7）**：一条 `MD5 去重` 检查，任何两张基线相同即失败。

## 4. 视口矩阵

| 项目 | 引擎 | 视口 | 备注 |
|---|---|---|---|
| `h5-390` | Chromium（Pixel 5） | 393×851，DSF 2.75 | 手机 |
| `h5-768` | Chromium（tablet） | 768×1024，DSF 2，`hasTouch` | **不是 WebKit**，见 §3.2 |
| `h5-1440` | Chromium | 1440×900 | 桌面 |
| `admin-1440` | Chromium | 1440×900 | 桌面 |
| `admin-768` | Chromium（tablet） | 768×1024 | 同上 |

### 已知成本

`tests/visual` 目录 **3.6 MB**。改用固定种子库后，最重的审计页基线从 13 万像素高降到可控范围
（`admin-audit-admin-768` 2.1 MB → 43 KB）。`toHaveScreenshot.timeout` 仍保留 20s，
因为 768×1024 @2x 的长表格整页截图偶尔会接近默认 5s。

## 5. 与功能测试的关系

| | `playwright.config.ts` | `playwright.visual.config.ts` |
|---|---|---|
| 目的 | 断言**行为** | 断言**外观** |
| 用例 | `tests/e2e` | `tests/visual` |
| 手段 | `getByTestId` / `getByRole` / 文本 | `toHaveScreenshot` |
| 视口 | 默认 | 5 个 |
| API | 开发库 `:8010` | 专用库 `:8011`（每次重建） |

两者共用同一份种子数据与同一个 API 代码，但**互不替代**：功能全绿不代表像素没变，像素全绿不代表行为正确。

## 6. 复跑

视觉套件自带 API（`webServer` 会先跑 `scripts/visual_db_reset.py` 再起 uvicorn），
前端由 Playwright 启动，**不需要手动起任何服务**：

```bash
# 生成 / 更新基线
./node_modules/.bin/playwright test -c playwright.visual.config.ts --update-snapshots

# 比对（CI 与验收用这个）
./node_modules/.bin/playwright test -c playwright.visual.config.ts
```

⚠️ 手动起过前端服务时要先关掉：视觉配置里前端是 `reuseExistingServer: true`，
一个指向 `:8010` 的手动预览会被**复用**，套件就悄悄跑回实时数据库，§2.1 的问题立刻复现。

手动起服务时必须显式给 API 地址，否则前端代理到 `:8000`，页面渲染「加载失败」——见 §3.1。

## 7. 判定

**VISUAL_REGRESSION = PASS。**

47 张基线，5 个视口，生成后再次以比对模式复验 **47 passed**，0 组重复基线。

本轮修掉三条会静默失效的路径：错误态可成基线、空白页可成基线、**两张基线是同一张图**。
另修掉"基线对着会增长的实时库"这一根本问题——在那之前，"47 passed"只在生成它的那个下午成立。

仍缺一条护栏：**基线名与页面内容的一致性目前只有人工断言覆盖**（`place-unknown` 断言答案徽标为
`UNKNOWN`，`place-restricted` 断言为 `RESTRICTED`）。机器层面的命名一致性检查（文件名 ↔ 页面关键状态）尚未实现。
