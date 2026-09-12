# AI_PROVIDER_SELECTION.md

> 状态：**未选型**（v0.5 决策记录）。按 NEXT_GOAL §A3：未选型时不得假装文本
> provider 能做 vision/OCR。

## 候选与评估维度

| 维度 | 腾讯云 OCR/图像 | 阿里云通义 | 火山方舟 | 自部署开源 (PaddleOCR) |
|---|---|---|---|---|
| 中文门牌/告示 OCR | 强（通用+表格） | 强 | 中 | 中（需 GPU/运维） |
| 宠物物种/品种分类 | 需自建分类 | 多模态可 | 多模态可 | 需训练 |
| 合规（境内数据处理） | 境内 | 境内 | 境内 | 自托管 |
| 成本模型 | 按次 | 按 token | 按 token | 固定运维 |
| 平台一致性（地图已是腾讯系） | 高 | 中 | 中 | 无 |

## 决策

1. **OCR 首选腾讯云 OCR**（与地图同一账号体系、境内合规、中文告示强），
   待采购后以 `OCR_PROVIDER=tencent` + `AI_API_KEY` 启用，live smoke 按 B-05。
2. **Vision（物种建议）暂缓选型**：分类准确率需用自有样本集评测后再定；
   在此之前仅 Mock。禁止用纯文本 LLM 冒充 vision。
3. **NLQueryProvider（自然语言→QueryContext 草稿）**：等 OCR/Vision 落地后
   同一供应商优先；接口已冻结（`parse_query`），不阻塞。

## 无论选谁，硬约束不变（design #21 / NEXT_GOAL §A3）

- AI 输出一律为 **建议/候选**：物种/品种建议需用户确认；
- 永不自动认定服务犬身份；永不从图像写 confirmed 体重/肩高；
- OCR/URL/用户上传产出只能进入 **RuleCandidate → Review → Publish**；
- AI 不做最终准入/法律判断；secret 不进日志（guard 层统一脱敏）。

## 已落地（不依赖 Key 的部分）

- `app/providers/base.py`：VisionProvider / OCRProvider / NaturalLanguageQueryProvider 接口。
- `app/providers/ai_guard.py`：统一调用守卫（超时/重试/错误归一化/遥测/secret 脱敏）。
- `tests/contract/test_ai_guard.py`：守卫行为 fixture 契约测试。
- `/ai/*` 端点全部经 guard 调用。
