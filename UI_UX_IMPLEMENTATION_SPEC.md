# UI_UX_IMPLEMENTATION_SPEC.md
# v0.6 Beta UI / UX 生产级规范

## 1. 产品视觉定位

关键词：
- 中性
- 清晰
- 城市工具
- 信息可信
- 证据可追溯
- 克制
- 非“萌宠社区”

避免：
- 大面积粉色
- 大量爪印/卡通
- “雷店”
- “红榜/黑榜”
- “文明养宠评分”
- “卫生评分”
- 过度社交化

---

## 2. 核心页面

### 2.1 地图首页

顶部：
- 城市/当前位置
- 搜索框
- 当前模式：
  - 带宠查询
  - 空间边界

次级：
- filters
- 当前 Pet Profile / BoundaryProfile 摘要

主体：
- 地图
- neutral markers
- cluster
- selected place bottom sheet

底部：
- 地图
- 搜索/发现
- 贡献
- 我的

### 2.2 搜索

支持：
- place name
- category
- nearby

过滤：
- 明确允许
- 有条件
- 明确限制
- 已核验
- 最近核验
- 有独立宠物区
- 仅户外
- 推车/包
- service dog information
- 规则冲突

不要默认把 Unknown 过滤掉。

### 2.3 Place Card

显示：
- name
- type
- result badge
- 1–2 条最关键条件
- source badge
- last verified

不显示：
- 星级
- 综合分
- 好/坏店

### 2.4 Place Detail

Section 1：当前答案
- 普通宠物
- 我的 PetProfile
- 我的 BoundaryProfile

Section 2：哪里可以/不可以
- zones
- floors
- map overlay

Section 3：条件
- leash
- muzzle
- stroller
- carrier
- weight
- time

Section 4：共处边界
- dining indoor/outdoor
- seat
- table
- food area
- tableware
- pet zone

Section 5：怎么进入
- entrance
- elevator
- path

Section 6：设施
- water
- bags
- toilet
- stroller rental
- activity area

Section 7：来源
- government/operator/onsite/reporter
- date
- evidence summary
- freshness
- conflict/stale

Section 8：现场记录
必须标注：
> 现场记录 ≠ 场所正式政策

Section 9：历史
- versions
- superseded

Section 10：
- 纠错/补充
- 管理方认领

---

## 3. Status 语义

统一：

### ALLOWED
中文：
“明确允许”

### CONDITIONAL
“有条件”

### RESTRICTED
“明确限制”

### UNKNOWN
“尚未核验 / 暂无明确规则”

### CONFLICT
“来源存在不一致”

### STALE
“需要复核”

必须同时：
- icon
- text
- color

不能 color-only。

---

## 4. Source Badge

前台：

- 官方法规
- 政府来源
- 管理方确认
- 现场核验
- 用户现场报告
- 需要复核
- 来源不一致

后台可保留更细 EvidenceStrength。

---

## 5. Boundary Profile UX

不要问：
“你讨厌宠物吗？”

问：

### 室内堂食
- 接受普通宠物进入
- 不接受
- 不在意

### 顾客座椅
- 接受
- 不接受
- 不在意

### 食品自助区
- 接受
- 不接受
- 不在意

### 户外区域
同上。

### 独立携宠区
- 偏好有
- 不在意

结果逐条解释：
- 符合
- 冲突
- 未知

---

## 6. Pet Profile UX

字段：
- 名称 optional
- species
- breed optional
- weight
- shoulder height
- count
- carrier/stroller
- service role separately

AI photo recognition：
- “AI 建议”
- 用户确认
- 不能自动写 confirmed

---

## 7. Contribution UX

入口：

### 快速确认
“页面显示普通宠物仅户外，目前仍然如此吗？”
- 仍然如此
- 已变化
- 不确定

### 拍规则牌
- camera
- upload
- evidence notice
- OCR preview
- user confirms place

### 我知道规则
结构化表单

### 我有现场经历
Observation form

不提供自由评论区。

---

## 8. Neutral Copy

推荐：
- “明确限制”
- “有条件进入”
- “尚未核验”
- “最近现场记录”
- “管理方规则”
- “普通宠物”

禁止：
- “雷”
- “恶心”
- “脏”
- “没素质”
- “反宠”
- “爱宠人士”
- “文明指数”

---

## 9. Design Tokens

建立 token：

```text
color.bg.*
color.text.*
color.border.*
color.status.allowed
color.status.conditional
color.status.restricted
color.status.unknown
color.status.conflict
color.status.stale

spacing.1...
radius.sm/md/lg
font.size.*
font.weight.*
elevation.*
motion.*
```

---

## 10. Accessibility

- contrast
- keyboard
- focus
- screen reader labels where supported
- min touch 44px
- font scaling
- reduced motion
- no color-only state

---

## 11. UI QA

Playwright screenshot coverage：
- home map
- list
- detail allowed
- detail conditional
- detail unknown
- boundary
- contribution
- evidence review
- admin candidate

目标：
- 关键页面无 layout shift
- 不溢出
- 中文断行合理
- dark/light 若实现则一致

---

## 12. 输出

必须生成：
- DESIGN_SYSTEM.md
- UI_STATE_MATRIX.md
- COPY_GUIDE.md
- UX_FLOW.md
- FRONTEND_QA_REPORT.md

实现完成后：
`UI_FRONTEND_PRODUCTION_GATE = PASS`
