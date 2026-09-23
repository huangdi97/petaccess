# FINAL_UAT_PREP — v0.9 Public Beta（2026-09-23）

> 母版 Phase 32（UAT）。真实 UAT 需要 7 类真实角色签署；本机无真人 → 主体 BLOCKED_HUMAN。
> 本文件为 UAT 就绪准备材料：角色清单、旅程、验收口径已备好；邀请角色后可直接执行。

## 0. 判定

```
UAT = BLOCKED_HUMAN（需要真实角色：携宠用户 / 不希望遇宠用户 / 普通用户 /
      导盲犬·服务犬相关用户 / 贡献者 / Reviewer / 场所管理方）
```

## 1. 就绪材料

- 数据：30 real Places（上海中心城区，真实坐标）已就绪；
- 功能：Rule（42）+ Reality（0，待贡献）+ Staff/Facility 语义层 + Evidence 全链路已实现；
- 工具：Playwright E2E 18 例、Visual 17 基线、a11y 机器可判定 0 缺陷；
- 账号：dev 登录/注册可用（mock auth；真实 OAuth 见 B-06）。

## 2. 角色与旅程（可直接执行）

| 角色 | 必测旅程 |
|---|---|
| 携宠用户 | 搜索 → 看 Rule → 看 Reality → Staff → Facility → Evidence → 贡献（现场看到） |
| 不希望遇宠用户 | 设置边界 → 边界匹配逐项解释（BOUNDARY_MATCH） |
| 普通用户 | 搜索一个地方 → 看完五个面；理解"未收录 ≠ 无规则" |
| 导盲犬/服务犬用户 | service-dog 模式 → 模式切换重评（E2E 已断言非扁平化答案） |
| 贡献者 | 现场看到 / 过去看到 / 帖子看到 三路径提交 → 查看 pending → 核验通过后 credit |
| Reviewer | Reality 候选队列 → 逐条核验 → 发布 → 撤回 → 审计 |
| 场所管理方 | Operator Claim / 更正 / 争议流程 |

## 3. 用户不需理解的概念（验收口径）

用户界面不得暴露：RuleLayer / holder_scope / proviso / source_scope_exact / normalization_type。
贡献表单按"记录什么"交互（动物出现 / 工作人员处理 / 动物相关设施），来源按"怎么知道"选择。

## 4. 结论

UAT 材料与口径已就绪；执行需真实角色 → BLOCKED_HUMAN。真实 UAT 完成后生成 FINAL_UAT_REPORT.md。
