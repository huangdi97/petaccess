# HUMAN_REVIEW_QUICK_TABLE_R2_FINAL.md

> GOV-01 最终速填表 · 一行一条（取代 R2 / R1 速填表）。
> 「我的决定」列填：`APPROVE` / `APPROVE_WITH_NOTE` / `HOLD` / `REJECT`

**图例**：🔴 建议拒绝 ｜ 🟠 建议挂起 ｜ ⚖️ 法定强制 ｜ 🦮 导盲犬精确 scope ｜
🐕‍🦺 军警犬拆分

| 编号 | Place | Rule | 来源原话 | 精确 scope | 归一化 | Evidence | AI建议 | 我的决定 |
|---|---|---|---|---|---|---|---|---|
| **FINAL-01** 🔴 | Manner咖啡（凯德虹口商业中心店） | `mn-outdoor-media`：有条件允许 | ordinary_pet | `ordinary_pet` | `exact` | search_snippet | RECOMMEND_REJECT |  |
| **FINAL-02** 🔴 | 和平饭店（费尔蒙） | `fp-sd-op`：允许 | service_dog | `—` | `legal_interpretation_required` | primary_direct | RECOMMEND_REJECT |  |
| **FINAL-03** 🔴 | 港汇恒隆广场 | `gh-outdoor-keep`：有条件允许 | ordinary_pet | `ordinary_pet` | `exact` | search_snippet | RECOMMEND_REJECT |  |
| **FINAL-04** ⚖️ | Manner咖啡（凯德虹口商业中心店） | `mn-legal-dog`：禁止 | dog | `dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-05** ⚖️🦮 | Manner咖啡（凯德虹口商业中心店） | `mn-sd-legal`：允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-06** ⚖️ | 上海图书馆东馆 | `lib-legal-dog`：禁止 | dog | `dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-07**  | 上海图书馆东馆 | `lib-pets-op`：禁止 | ordinary_pet | `ordinary_pet` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-08** ⚖️🦮 | 上海图书馆东馆 | `lib-sd-legal`：允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-09** 🦮 | 上海图书馆东馆 | `lib-sd-op-guide`：允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-10** 🐕‍🦺 | 上海图书馆东馆 | `lib-sd-op-military`：允许 | 军警犬 | `military_working_dog` | `compound_term_split` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-11** 🐕‍🦺 | 上海图书馆东馆 | `lib-sd-op-police`：允许 | 军警犬 | `police_dog` | `compound_term_split` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-12** ⚖️ | 上海迪士尼乐园 | `dl-legal-dog`：禁止 | dog | `dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-13**  | 上海迪士尼乐园 | `dl-pet-ban`：禁止 | ordinary_pet | `ordinary_pet` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-14** ⚖️🦮 | 上海迪士尼乐园 | `dl-sd-legal`：允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-15** 🦮 | 上海迪士尼乐园 | `dl-sd-op`：有条件允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-16** ⚖️ | 前滩太古里 | `qt-indoor-legal`：禁止 | dog | `dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-17**  | 前滩太古里 | `qt-indoor-op`：禁止 | ordinary_pet | `ordinary_pet` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-18**  | 前滩太古里 | `qt-outdoor-op`：有条件允许 | ordinary_pet | `ordinary_pet` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-19** ⚖️🦮 | 前滩太古里 | `qt-sd-legal`：允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-20** 🦮 | 前滩太古里 | `qt-sd-op`：允许 | 除导盲犬外 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-21** ⚖️ | 和平饭店（费尔蒙） | `fp-legal-dog`：禁止 | dog | `dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-22**  | 和平饭店（费尔蒙） | `fp-pets-op`：禁止 | ordinary_pet | `ordinary_pet` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-23** ⚖️🦮 | 和平饭店（费尔蒙） | `fp-sd-legal`：允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-24** 🦮 | 和平饭店（费尔蒙） | `fp-sd-op-firstparty`：允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-25**  | 大吉路公园 | `dj-pilot`：有条件允许 | ordinary_pet | `ordinary_pet` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-26**  | 广场公园（黄浦段） | `gc-h6-pilot`：有条件允许 | ordinary_pet | `ordinary_pet` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-27**  | 广场公园（黄浦段） | `gc-other-keep`：禁止 | ordinary_pet | `ordinary_pet` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-28**  | 星巴克咖啡（徐汇西岸梦中心店） | `xm-indoor-new`：禁止 | ordinary_pet | `ordinary_pet` | `exact` | secondary_reputable | RECOMMEND_APPROVE |  |
| **FINAL-29** ⚖️ | 星巴克咖啡（徐汇西岸梦中心店） | `xm-legal-dog`：禁止 | dog | `dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-30**  | 星巴克咖啡（徐汇西岸梦中心店） | `xm-outdoor-media`：有条件允许 | ordinary_pet | `ordinary_pet` | `exact` | secondary_reputable | RECOMMEND_APPROVE |  |
| **FINAL-31** ⚖️🦮 | 星巴克咖啡（徐汇西岸梦中心店） | `xm-sd-legal`：允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-32** ⚖️ | 星巴克臻选上海烘焙工坊 | `sb-legal-dog`：禁止 | dog | `dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-33** ⚖️🦮 | 星巴克臻选上海烘焙工坊 | `sb-sd-legal`：允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-34**  | 港汇恒隆广场 | `gh-indoor-new`：禁止 | ordinary_pet | `ordinary_pet` | `exact` | secondary_reputable | RECOMMEND_APPROVE |  |
| **FINAL-35** ⚖️ | 港汇恒隆广场 | `gh-legal-dog`：禁止 | dog | `dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **FINAL-36** ⚖️🦮 | 港汇恒隆广场 | `gh-sd-legal`：允许 | 导盲犬 | `guide_dog` | `exact` | primary_direct | RECOMMEND_APPROVE |  |

## 签署

| 字段 | 值 |
|---|---|
| reviewer（具名） |  |
| reviewer_role |  |
| reviewed_at |  |
| 确认 ADR-025 源忠实 scope（不再泛化为 service_dog） | ☐ 是 ☐ 否 |
| 确认 ADR-028 复合词「军警犬」拆分不扩张到其他 working dog | ☐ 是 ☐ 否 |
| 首批批准条数（≤ `--max-approve`） |  |
| 签名 |  |

