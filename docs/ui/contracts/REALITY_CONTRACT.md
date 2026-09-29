# Reality Contract

> JSON：`docs/ui/contracts/json/reality.json`。
> 真正 Event Log。

## 1. 结构（每 event）

```text
Date Group
Time
Timeline marker
Location
Observed fact
Evidence / freshness
```

- 每 event = `.trace-row` 行（非 card，radius 0，无 shadow/无 panel）；
- 禁止 `NO_RECENT_RECORD ≠ NO_ANIMAL_PRESENCE` 等不变量原文。

## 2. 消费者文案示例

```text
18:42
一层公共区域

一只普通犬随同行人进入

地点已确认 · 时间已确认
2 个独立来源
```

## 3. 空态（无近期记录）

```text
暂无近期现场记录。
这并不代表现场没有动物。
```

绝不显示 `NO_RECENT_RECORD`。

## 4. 结构约束

- `.trace-row` != `.panel`；per-event panel count = 0；
- filter = 轻量 select/popover；
- QueryContext 可见（`query-context`）；
- 禁止事件卡化（Freeze §5）。

## 5. 语言

- observed_action / animal_scope 等经 mapper；
- 无 raw enum；无 UUID。