# UX_FLOW.md

> 宠物准入与公共空间共处规则平台 · 用户流程
> 对应 `UI_UX_IMPLEMENTATION_SPEC.md` §12 与 `WORKBUDDY_PRODUCTION_MASTER_GOAL.md` §4
> 基准 commit `716b163` · 生成时间 2026-09-14（GMT+8）

本文描述**已实现**的流程，并在每一步标注真实状态分支。未实现的分支显式标注 `NOT_IMPLEMENTED`，不做示意性描述。

---

## 0. 贯穿所有流程的四条规则

1. **证据先于结论**：任何"允许/限制"结论都必须能展开到来源、日期与核验时间。
2. **UNKNOWN 是一等结论**：信息不足时输出"尚未核验"，并说明"未收录 ≠ 不存在规则"。
3. **AI 只给建议**：AI 识别结果一律标注"AI 建议"，需用户确认后才写入（`PetNewView`）。
4. **离线不排队**：离线时不接受提交，避免产生未经确认的记录（`useOnline.ts`）。

---

## 1. 流程 A — 带宠查询（"我的宠物能不能去？"）

```text
进入 App
  └─ 会话恢复（session.restore）
       ├─ 未登录 → 可浏览；提交类操作触发 PERMISSION_DENIED 态
       └─ 已登录 → 载入 PetProfile / BoundaryProfile
  └─ 地图首页（HomeView）
       ├─ LOADING      → SkeletonList（3 行卡片骨架）
       ├─ OFFLINE      → 顶部离线横幅 + 暂停提交
       ├─ ERROR        → StateMessage(ERROR) + [重试]
       ├─ EMPTY        → StateMessage(EMPTY)「暂无收录内容」
       └─ SUCCESS      → Mock 地图 + 附近场所列表
            └─ 点击场所 → Place Detail
                 ├─ LOADING → SkeletonList（4 行）
                 ├─ ERROR   → StateMessage(ERROR) + [重试]
                 └─ SUCCESS → 「当前答案」区
                      结论 = 由 session.mode + activePet + 场所规则共同决定
                      ├─ MATCH       → 明确允许
                      ├─ CONDITIONAL → 有条件（列出 obligations）
                      ├─ RESTRICTED  → 明确限制
                      ├─ UNKNOWN     → 尚未核验（列出 unknownInputs，不猜测）
                      └─ CONFLICT    → 来源存在不一致
                          └─ [为什么是这个结果] → MatchExplainView
```

**关键设计**：`watch([session.mode, session.activePet])` 会在用户切换宠物或模式时**立即重算**，无需刷新页面。这保证"换一只宠物"这一动作不会留下过期的旧结论。

---

## 2. 流程 B — 空间边界查询（"能到哪里、做到什么程度？"）

```text
Place Detail
  └─ §1 当前答案（普通宠物 / 我的 PetProfile / 我的 BoundaryProfile 三视角）
  └─ §2 分区域规则
       ├─ 有分区 → 逐 zone 显示 StatusBadge + obligations
       ├─ 无分区但有全场规则 → 显示「全场 · scope · action」
       └─ 均无 → 「暂无已收录规则（信息不足 ≠ 允许）」
  └─ [为什么是这个结果] → MatchExplainView
       ├─ effective-effect   最终生效结论
       ├─ 附加条件            obligations
       ├─ 推导过程            可展开的判定链
       ├─ 被抑制的规则        被更高层级压制者（含抑制原因）
       ├─ 未解冲突            「需人工复核」
       └─ 边界比对            逐项 符合 / 冲突 / 未知（永不汇总为总分）
```

**红线**：边界比对**逐项判定、不汇总**。没有任何"总分/匹配度百分比"，因为把多维偏好压成一个数会让用户无法知道是哪一项导致了结论。

---

## 3. 流程 C — 直接看规则（"这个地方现在怎么规定？"）

```text
搜索（SearchView）
  ├─ OFFLINE → 顶部横幅 + 输入框可编辑但提交被拒（提示"搜索需要联网"）
  ├─ LOADING → SkeletonList
  ├─ ERROR   → StateMessage(ERROR) + [重试]
  ├─ EMPTY   → StateMessage(EMPTY)「没有匹配的场所。未收录不代表该场所没有规则。」
  └─ SUCCESS → 结果卡片（名称 + 类型 + 地址 + 未核验状态徽标）
       └─ 点击 → Place Detail
            └─ §3 规则来源与核验
                 ├─ 逐条显示 issuer + SourceBadge（官方法规/政府来源/管理方确认/现场核验/用户现场报告/需要复核/来源不一致）
                 ├─ 最近核验时间
                 └─ 快捷核验：[仍有效] [已变化] [不确定]
                      └─ 未登录 → 提示"需要登录后才能核验"
```

---

## 4. 流程 D — 现场贡献（ContributeView）

四种入口，**不提供自由评论区**（自由文本会产生无法结构化的断言）：

| 入口 | 交互 | 结果 |
|---|---|---|
| 快速确认 | "页面显示普通宠物仅户外，目前仍然如此吗？" → 仍然如此 / 已变化 / 不确定 | 写入 VerificationEvent |
| 拍规则牌 | 相机 / 上传 → 证据说明 → OCR 预览 → **用户确认场所** | 进入证据链，不直接成规则 |
| 我知道规则 | 结构化表单 | 生成 RuleCandidate（REVIEW_PENDING） |
| 我有现场经历 | Observation form | 生成 ObservationClaim（≠ 规则） |

**硬约束**：以上四种均**不产生已发布规则**。AI 只做抽取，最终裁决由具名人类评审员完成（ADR-005）。

---

## 5. 流程 E — 共处边界设置（BoundaryView）

```text
进入 /boundary
  ├─ LOADING → SkeletonList（4 行）
  ├─ ERROR   → StateMessage(ERROR) + [重试]
  ├─ OFFLINE → 顶部横幅；[保存边界] 置灰
  └─ SUCCESS → 逐属性选择
       每个属性三选一：可接受 / 希望没有 / 必须禁止（硬性）/ 希望提供（视属性而定）
       再次点击已选项 = 清除该属性 → 保持「未知」
       └─ [保存边界]
            ├─ 未登录 → 提示"（需登录后保存）"
            └─ 成功   → "已保存 N 项边界（未设置项保持未知）"
```

**关键设计**：不设置任何属性 = 该属性保持 UNKNOWN，**不会**被默认成"可接受"。这与 UNKNOWN ≠ allowed 一致。

---

## 6. 流程 F — 纠错 / 异议

```text
Place Detail → [对此处规则提出异议]
  ├─ 未登录 → "提交失败（需登录）"
  └─ 成功   → "异议已提交，进入人工复核流程"
```

异议进入 Admin 的 Disputes 队列，不直接改动规则。管理方认领走 Admin 的 Claims 流程。

---

## 7. 状态分支总表

| 状态 | 触发 | 呈现 | 是否可恢复 |
|---|---|---|---|
| LOADING | 请求进行中 | SkeletonList / `.skeleton` | — |
| EMPTY | 请求成功但无数据 | StateMessage(EMPTY) + "未收录 ≠ 不存在规则" | — |
| ERROR | 请求失败 | StateMessage(ERROR) + [重试] | ✅ 可重试 |
| OFFLINE | `navigator.onLine === false` | 顶部横幅 + 提交类按钮置灰 | ✅ 恢复网络后自动消失 |
| PARTIAL | 部分字段缺失 | StateMessage(PARTIAL) | — |
| STALE | 证据超时效 / 规则复核逾期 | StatusBadge(STALE) | — |
| CONFLICT | 来源结论冲突 | StatusBadge(CONFLICT) + 指向 MatchExplainView 未解冲突区 | 需人工复核 |
| PERMISSION_DENIED | 未登录执行提交类操作 | StateMessage(PERMISSION_DENIED) 或内联提示 | ✅ 登录后重试 |
| SUCCESS | 正常 | 内容 | — |

---

## 8. 未实现流程（诚实记录）

| # | 流程 | 状态 |
|---|---|---|
| 1 | 定位授权（location permission）流程 | `NOT_IMPLEMENTED`（当前使用合成演示坐标） |
| 2 | 关注/收藏列表页（Mine 有入口但无独立列表页） | `PARTIAL` |
| 3 | 通知中心 / 推送落地页 | `NOT_IMPLEMENTED` |
| 4 | 隐私设置页 / 账号删除 / 数据导出 | `NOT_IMPLEMENTED` |
| 5 | 关于与数据方法页 | `NOT_IMPLEMENTED` |
| 6 | 管理方认领（Operator 侧自助） | `PARTIAL`（仅 Admin 侧） |
| 7 | 上传贡献状态跟踪页 | `PARTIAL` |
