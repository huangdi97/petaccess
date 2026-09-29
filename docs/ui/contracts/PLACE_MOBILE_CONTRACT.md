# Place Mobile Contract

> 目标 viewport：430 × 932。JSON：`docs/ui/contracts/json/place.mobile.json`。
> 单列，无右侧 inspector。

## 1. 首屏顺序（严格）

```text
Place Identity
Current Query
Primary Decision
Key Conditions
Recent Reality teaser
```

然后：Zones → Rules → Staff/Facilities → Evidence → More/History。

## 2. 首屏必须可见（430×932）

- place name；
- primary decision；
- 至少一项 supporting fact；
- 不被大量来源/历史/meta 占满。

## 3. 禁止超长 schema dump

默认折叠：历史版本、完整 provenance、内部规则版本、详细边界原始字段。
折叠用 disclosure toggle（aria-expanded），不缩字号、不堆 metadata。

## 4. 密度

第一 viewport 可见文本行目标 ≤ ~30；若 40+ → WARN/FAIL。
不要机械删重要信息；优先 progressive disclosure。
最大语义间隔 ≤ 180px。

## 5. 语言

- UUID / snake_case / internal enum / engineering invariant visible = 0；
- zone 显示 `一层公共区域` 等消费者文案。