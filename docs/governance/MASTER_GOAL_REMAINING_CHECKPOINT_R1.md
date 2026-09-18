# Master Goal 剩余闭环 · 检查点 R1（BATCH-03 真实发布后）

> 按授权：真实发布与验证完成后**不自动启动 Wave02**，继续剩余闭环，到新的 Human Checkpoint 停止。
> 本文件是「现状盘点 + 需要你决定的事」，所有数字都来自刚跑过的查询，不是回顾。

## 1. ADR-031 holder_scope 收口 —— 确认完成（补上了缺失的一半）

- ADR-031 状态 `accepted`，`ADR030_HOLDER_SCOPE_CLOSURE_R1.md` 原有收口只覆盖了 **LEGAL 层**
  11 个基底（JPROV-001）。
- 本轮在**OPERATOR_POLICY 层**补了实测（迪士尼 dog 基底 + 运营方自己的导盲犬 but 书），
  已追加为该文件的 §12。结论：holder 未知 ⇒ `conditional` + `missing_inputs=['holder_scope']`；
  holder 满足 ⇒ 例外进入 `applied_exceptions` 但 **effect 仍是 conditional**（but 书自带条件）；
  generic `service_dog` / 警犬 / 军犬 全部 `prohibited`，但书不外溢。
- **残留（需另行授权）**：
  1. 渐进式提问 UI 未做（后端契约已提供 `holder_scopes` / `missing_inputs`）；
  2. **法条级区分仍缺失**：`access_rule` 没有法条引用列，provision 只能用
     （法律文件, layer, effect, scope）近似。要精确需增列 + 回填 + 人工审阅，
     **会触碰已发布的历史行** —— 这是新的人审项目，不是收尾动作。

## 2. 剩余 Scope Remodel 候选 —— 只剩 1 条，卡在法律适用性

| 候选 | 场所 / scope | 状态 |
|---|---|---|
| `a4e2ba26…` | 上海动物园 / dog | **HOLD**（`HIGHER_LEVEL_GUIDE_DOG_LEGAL_APPLICABILITY_UNRESOLVED`） |

其余 6 条（迪士尼 dog/cat/other + carve-out、动物园 cat/other）**全部已发布**。
这一条只能由你裁决：要么认定动物园的 OPERATOR_POLICY 犬类禁令对导盲犬不适用并给出依据，
要么维持 HOLD。

## 3. B4 世纪公园 —— 闸门 PASS，但一手来源仍未拿到

候选 `4e217d58-1060-4945-9fa1-b9b7e17d7e64`（世纪公园 / ordinary_pet / `宠物`）：

- `evidence_class = original`、`source_type = government_service`、
  发布者 `上海市文化和旅游事业发展中心`《又一新地标！…》—— 明确写着**转述世纪公园官方口径**。
- canonical pre-publish 闸门现在是 **PASS**（它不拦 `original` + 政府发布者），
  在 Wave01 登记表里的计划动作是 `CREATE_ACCESS_RULE`。
- 也就是说：**它不是被闸门挡住，而是没满足 B4 自己定的「一手来源」标准**。
  发不发是人审决定，不是闸门决定。前面几轮的一手来源检索仍是 `STILL_MISSING`。

## 4. B5 Place Geo —— 已完成

`place` 20/20 全部有坐标（`location IS NULL` = 0）。
遗留：CHARLIE'S 粉红汉堡（马当路店）、omitofee 上海首店 两条是**地址级**精度，
待运营方确认门牌号，属运营确认项，不是代码问题。

## 5. 剩余 APPROVED 清理 —— 发现一个陈旧的危险登记表（重要）

对 Wave01 登记表重跑当前闸门（只读）：

```
PREPUBLISH_APPROVED_EVALUATED = 15   PASS = 14   BLOCKED = 1
ACCESS_RULE_CREATE_COUNT = 1   NOOP_COUNT = 11   BLOCKED_COUNT = 1
```

计划明细里的三行值得警惕：

| 规则 | 计划动作 | 说明 |
|---|---|---|
| `w01-3a04d4d1aa`（迪士尼 / other，旧基底） | **SUPERSEDE_ACCESS_RULE** | 会用旧的 `other` 语义**顶替**刚发布的 SCOPE-R2 规则 `0d2f70f8…` |
| `w01-6f2bfd39d7`（动物园 / other，旧基底） | **SUPERSEDE_ACCESS_RULE** | 同上，会顶替 `352f6e0f…` |
| `w01-4e217d5810`（世纪公园 / ordinary_pet） | CREATE_ACCESS_RULE | 见 §3 |
| `w01-305fa08c1e`（迪士尼导盲犬，冻结） | BLOCKED | 遗留条件键 `type`；已被 `69e0916a…`（已发布）取代，永久不可执行 |

**这张 Wave01 登记表是在 SCOPE-REMODEL-R2 之前生成的，现在它已经过期**：
直接执行其中的两行 SUPERSEDE，等于把新发布的、语义正确的 `other` 规则用旧候选覆盖回去 —— 是一次回退。
我的建议是**不执行**它，而是把该登记表在文档层标记为「已被 SCOPE-REMODEL-R2 取代」（不改动任何已签署行、不动数据库）。

## 6. Wave02 —— 未启动

按授权未启动。等上面 2/3/5 的决策落定后再议。

---

## 需要你决定的事（4 项）

1. **动物园 dog（HOLD）**：维持 HOLD，还是给出法律依据后放行？
2. **世纪公园**：① 接受政府来源 + 在 provenance 上标注「转述官方口径」并发布；
   ② 继续找一手来源（前面几轮未找到）；③ 搁置。
3. **Wave01 剩余 APPROVED**：① 按我的建议标记「已被 SCOPE-REMODEL-R2 取代」并关闭该登记表（不动 DB）；
   ② 只发世纪公园一条；③ 其他方案。
4. **法条级引用列**：要不要开这个新项目（会触碰已发布历史行）？
