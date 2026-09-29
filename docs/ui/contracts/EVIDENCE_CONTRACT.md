# Evidence Contract

> JSON：`docs/ui/contracts/json/evidence.json`。
> Evidence = Provenance Record。

## 1. 顶部信息

```text
Place name
Zone
Observed time
```

无 place display name 时：`场所信息暂不可用`。禁止 UUID。

## 2. Provenance 链（5 步，consumer-friendly）

```text
原始证据
↓
地点匹配
↓
时间确认
↓
来源确认
↓
人工核验
```

每步必须消费者语言可读（非 raw status）。

## 3. 三时间分离

- Observed（观察时间）
- Submitted（提交时间）
- Reviewed（核验时间）

分开呈现，不得合并/丢失。

## 4. 结构

- `evidence-provenance` 恰好 5 个 `.surface-row`（5 步）；
- `evidence-items` / `evidence-sources` 存在；
- 永久免责行：`现场事实不代表正式准入规则。`（`evidence-disclaimer`）；
- QueryContext 可见。

## 5. 语言 / 密度

- UUID / raw enum / ALL_CAPS 可见 = 0；
- provenance 步连续（无 `<dl>` 平铺、无卡墙）。