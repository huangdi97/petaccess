# REALITY_AUDIT_PLAN.md

## 目标
验证模型能否表达真实世界，而不是先铺全国数据。

## 第一阶段
使用 adversarial synthetic fixtures。

## 第二阶段
30–50 个真实地点人工样本：
- 20 餐饮/咖啡
- 5 商场
- 5 公园
- 5 酒店/景区/其他
- 属地法规

不得伪造真实商家规则。

## 每个 Place 输出
- expressible yes/no
- unsupported conditions
- unknown fields
- source quality
- freshness
- resolver result
- boundary result
- schema gaps

## 产物
- REALITY_AUDIT_REPORT.md
- SCHEMA_GAPS.md
- CSV/JSON import template
- provenance manifest
