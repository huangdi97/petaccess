# Home Contract

> JSON：`docs/ui/contracts/json/home.json`。
> Home 不是 Dashboard。

## 1. 结构（自上而下）

```text
Location
Current Query
Primary Search
Recent
Nearby
Secondary Lens
```

## 2. 删除项

- perspective pill trio（`perspective-*` 按钮行 — `class="pill"` 三枚）→ 删除；
- feature cards → 删除；
- category chips → 删除；
- capability catalogue → 删除；
- Hero photo → 无。

## 3. Secondary Lens

轻量 link rows：

```text
现场情况 →
室内区域 →
餐饮区域 →
完整规则 →
```

（`present list` 用 arrow-link 行，不是 pill wall。）

## 4. 首屏密度

- 932px 移动首屏：Page identity + Current context + primary search 可见；
- 桌面 900px：任务启动结构完整（Location → Query → Search → Recent/Nearby）。

## 5. 语言

- 无 UUID / snake_case / ALL_CAPS 泄漏；
- recent list 的 `recent-<uuid>` testid 只存在于属性，不可见文本无 UUID。