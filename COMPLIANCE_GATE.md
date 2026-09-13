# COMPLIANCE_GATE.md

> P7 · 中国大陆地图/平台/内容合规矩阵
> 生成：2026-09-13（GMT+8）
>
> **诚实声明**：本文件由工程侧整理，**不构成法律意见**。任何标注 `LEGAL_REVIEW_REQUIRED` 或 `PLATFORM_REVIEW_REQUIRED` 的条目，必须在正式公开上线前由具备资质的律师或对应平台完成确认。本文件不宣称「已合法合规」。

---

## 状态词表

| 标注 | 含义 |
|---|---|
| `VERIFIED` | 已有可复现的工程或文档证据支撑（不代表法律结论） |
| `NEEDS_PROVIDER_CONFIRMATION` | 需向服务商书面确认（地图/短信/支付等） |
| `LEGAL_REVIEW_REQUIRED` | 需执业律师出具意见 |
| `PLATFORM_REVIEW_REQUIRED` | 需平台（微信/应用商店）审核通过 |
| `NOT_APPLICABLE_YET` | 当前形态不触发 |

---

## 1. 地图 SDK 与地图数据

| # | 条目 | 现状 | 标注 |
|---|---|---|---|
| 1.1 | 使用腾讯位置服务（Tencent Map）作为首个 provider | 代码已具备 `TencentMapProvider` 适配器（`app/providers/tencent_map.py`）+ 13 项契约测试；**未接真实 Key**（B-04） | `NEEDS_PROVIDER_CONFIRMATION` |
| 1.2 | 地图数据展示的边界与审图号要求 | 未评估。腾讯地图 SDK 通常已内嵌合规底图；**自绘覆盖层（overlay）**是否触发额外审图要求需确认 | `NEEDS_PROVIDER_CONFIRMATION` |
| 1.3 | 是否自行绘制国界/行政区划 | **否**。产品仅展示 POI 点与场所内区域（Zone），不绘制行政边界 | `NOT_APPLICABLE_YET` |
| 1.4 | 坐标系 | 后端 `location_wkt` 使用 WGS84（如 `POINT(121.4893 31.1784)`）。中国大陆地图服务普遍要求 GCJ-02，**坐标系转换必须在地图 provider 层完成** | `VERIFIED`（风险已识别，转换未实现） |
| 1.5 | 地图数据的转售/再分发 | 产品不分发原始地图数据，仅展示 | `NOT_APPLICABLE_YET` |
| 1.6 | 外部 Place ID 作为主键 | ADR-003 规定平台自有 UUID，地图 ID 仅作 external ref | `VERIFIED` |

**需用户/服务商确认的具体问题**
1. 腾讯位置服务协议是否允许「将 POI 与自建规则数据叠加展示」？
2. 自绘 Zone 覆盖层是否需要单独审图？
3. WGS84→GCJ-02 转换的责任方与合规口径。

---

## 2. 微信小程序

| # | 条目 | 现状 | 标注 |
|---|---|---|---|
| 2.1 | 小程序 AppID | `apps/client/manifest.json` 的 `mp-weixin.appid` 为空（B-02） | `PLATFORM_REVIEW_REQUIRED` |
| 2.2 | 服务类目 | 未选择。产品含 UGC（用户贡献/纠错）与位置服务，**类目选择直接决定是否可过审** | `PLATFORM_REVIEW_REQUIRED` |
| 2.3 | `getLocation` 隐私接口 | manifest 已声明 `requiredPrivateInfos` 与用途说明；**接口审批未提交** | `PLATFORM_REVIEW_REQUIRED` |
| 2.4 | 用户隐私保护指引 | 需在微信后台单独填写并审核，与 §4 隐私政策草案**需一致** | `PLATFORM_REVIEW_REQUIRED` |
| 2.5 | UGC 内容安全（文本/图片） | 贡献流程为结构化表单（无自由评论区，符合 spec §7），但**上传图片仍需内容安全接口（如 `security.imgSecCheck`）**，当前未接入 | `PLATFORM_REVIEW_REQUIRED` |
| 2.6 | 是否涉及"点评/评价"类目 | 产品**不提供**评分/排名/评价（ADR-014、`COPY_GUIDE.md` §2），显著降低类目风险 | `VERIFIED`（设计层面） |

---

## 3. UGC / 内容合规

| # | 条目 | 现状 | 标注 |
|---|---|---|---|
| 3.1 | 用户贡献是否构成"发布信息" | 是（规则补充、现场照片、纠错）。需内容审核机制与投诉入口 | `LEGAL_REVIEW_REQUIRED` |
| 3.2 | 结构化优先、不做自由评论区 | spec §7 与实现一致；显著降低内容风险 | `VERIFIED` |
| 3.3 | 侵权风险（对场所的商业评价） | 产品只陈述「准入规则」与「来源」，不做质量评价。但**"明确限制"仍可能被场所方理解为负面标记**，需免责与申诉机制 | `LEGAL_REVIEW_REQUIRED` |
| 3.4 | 用户上传照片的肖像权/著作权 | 需在贡献条款中取得授权并声明审核权 | `LEGAL_REVIEW_REQUIRED` |
| 3.5 | 未成年人 | 平台不面向未成年人设计；贡献者需年满 18 周岁 | `LEGAL_REVIEW_REQUIRED` |

---

## 4. 隐私与个人信息

| # | 条目 | 现状 | 标注 |
|---|---|---|---|
| 4.1 | 个人信息清单 | 已有 `PRIVACY_DATA_INVENTORY.md` | `VERIFIED` |
| 4.2 | 位置信息 | 仅在用户主动操作时采集，且**不默认长期保存轨迹**（ADR-012）；贡献时采用距离分桶（`distance_bucket`）而非精确坐标 | `VERIFIED` |
| 4.3 | 账号与鉴权 | 邮箱+密码（bcrypt）+ JWT；无第三方登录（B-06） | `VERIFIED` |
| 4.4 | 删除/导出权 | 需实现账号删除与数据导出流程（当前未实现） | `LEGAL_REVIEW_REQUIRED` |
| 4.5 | 隐私政策文本 | 见 `docs/legal/PRIVACY_POLICY_DRAFT.md`（**草案，未经律师审阅**） | `LEGAL_REVIEW_REQUIRED` |
| 4.6 | 个人信息保护影响评估（PIPIA） | 未开展 | `LEGAL_REVIEW_REQUIRED` |
| 4.7 | 数据出境 | 若使用境外 AI provider 处理图片，可能构成数据出境，需单独评估 | `LEGAL_REVIEW_REQUIRED` |

---

## 5. 证据与来源的合法性

| # | 条目 | 现状 | 标注 |
|---|---|---|---|
| 5.1 | 采集是否绕过登录/验证码/访问控制 | **否**。`EVIDENCE_REPAIR_LOG_R1.md` 记录 14 次尝试，403/验证码即停并改走合法通道 | `VERIFIED` |
| 5.2 | 来源再分发许可 | 每条来源记录 `display_allowed` / `redistribution_allowed` / `storage_allowed`；`redistribution=false` 的新闻/官网仅内部核验用 | `VERIFIED` |
| 5.3 | lead-only 证据 | 社媒/搜索片段为 `display=false`+`storage=false`，且被 Pre-Publish Validation 硬拦截 | `VERIFIED` |
| 5.4 | 引用原文的合理使用边界 | 展示"规则陈述"而非原文全文，属事实性引用；边界需律师确认 | `LEGAL_REVIEW_REQUIRED` |
| 5.5 | 政府法规文本再分发 | `redistribution_allowed=true` | `VERIFIED` |

---

## 6. 主体资质与上线

| # | 条目 | 现状 | 标注 |
|---|---|---|---|
| 6.1 | 域名与 ICP 备案 | 无（B-07） | `LEGAL_REVIEW_REQUIRED` |
| 6.2 | 隐私政策主体名称 | 未确定 | `LEGAL_REVIEW_REQUIRED` |
| 6.3 | 应用商店（Android/iOS/HarmonyOS）上架主体 | 无账号（B-03） | `PLATFORM_REVIEW_REQUIRED` |
| 6.4 | 增值电信业务经营许可（ICP 许可证） | 需评估：含 UGC 的平台是否需 B25 类许可 | `LEGAL_REVIEW_REQUIRED` |
| 6.5 | 是否涉及"新闻信息服务" | 产品转载/引用新闻作为证据来源，**不从事新闻采编发布**；边界需确认 | `LEGAL_REVIEW_REQUIRED` |

---

## 7. 产品定位层面的风险缓释（已内建于设计）

| 风险 | 缓释措施 | 证据 |
|---|---|---|
| 被认定为对商户的评价平台 | 无评分、无排名、无"红黑榜"；机读禁用词守卫 | `COPY_GUIDE.md` §4、`tests/unit/test_design_tokens.py` |
| 遇宠率/社交攀比 | 明确不做遇宠率 | AGENTS.md 约束、`FORBIDDEN_COPY` 含"遇宠率" |
| 长期跟踪用户位置 | 默认不保存轨迹（ADR-012） | `PRIVACY_DATA_INVENTORY.md` |
| 小区住户隐私 | 小区只记录公共空间规则，不记录住户 | ADR-013 |
| AI 越权裁决规则 | AI 仅做 extraction/candidate；发布前六检 + 人类签署 | ADR-005、`publish_gate.py`、`publish_reviewed_r1.py` |

---

## 8. Gate 判定

```text
COMPLIANCE_GATE = PASS_WITH_EXTERNAL_LEGAL_REVIEW
```

| 子项 | 判定 |
|---|---|
| 地图 SDK 合规 | `NEEDS_PROVIDER_CONFIRMATION` |
| 微信小程序类目/隐私接口 | `PLATFORM_REVIEW_REQUIRED` |
| UGC 内容合规 | `LEGAL_REVIEW_REQUIRED` |
| 隐私合规 | `LEGAL_REVIEW_REQUIRED` |
| 来源采集合法性 | **PASS**（工程证据充分） |
| 证据再分发许可建模 | **PASS**（字段级建模 + 硬门） |
| 主体资质 | `LEGAL_REVIEW_REQUIRED` |

**用户需完成的最小动作（按优先级）**
1. 聘请执业律师审阅 `docs/legal/` 下 6 份草案，并出具意见；
2. 向腾讯位置服务书面确认 §1 的三个问题；
3. 注册微信小程序主体并完成类目与隐私接口审批；
4. 完成域名注册与 ICP 备案；
5. 确认隐私政策主体名称与联系方式。
