# HUMAN_REVIEW_QUICK_TABLE_R2.md

> GOV-01 速填表 · 一行一条。取代 R1 速填表。
> 「我的决定」列填：`APPROVE` / `APPROVE_WITH_NOTE` / `HOLD` / `REJECT`

**图例**：🔴 建议拒绝 ｜ 🟠 建议挂起 ｜ ⚖️ 法定强制 ｜ 🦮 导盲犬精确 scope

| 编号 | Place | Rule | 来源原话 | 精确 scope | 归一化 | Evidence | AI建议 | 我的决定 |
|---|---|---|---|---|---|---|---|---|
| **R2-01** 🔴 | Manner咖啡（凯德虹口商业中心店） | `mn-outdoor-media`：有条件允许 | ordinary_pet | ordinary_pet | `exact` | search_snippet | RECOMMEND_REJECT |  |
| **R2-02** 🔴 | 港汇恒隆广场 | `gh-outdoor-keep`：有条件允许 | ordinary_pet | ordinary_pet | `exact` | search_snippet | RECOMMEND_REJECT |  |
| **R2-03** 🟠 | 上海图书馆东馆 | `lib-sd-op`：允许 | 导盲犬、军警犬例外 | — | `legal_interpretation_required` | primary_direct | RECOMMEND_HOLD |  |
| **R2-04** 🟠 | 和平饭店（费尔蒙） | `fp-sd-op`：有条件允许 | — | — | `legal_interpretation_required` | primary_direct | RECOMMEND_HOLD |  |
| **R2-05** ⚖️ | Manner咖啡（凯德虹口商业中心店） | `mn-legal-dog`：禁止 | dog | dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-06** ⚖️🦮 | Manner咖啡（凯德虹口商业中心店） | `mn-sd-legal`：允许 | 导盲犬 | guide_dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-07** ⚖️ | 上海图书馆东馆 | `lib-legal-dog`：禁止 | dog | dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-08**  | 上海图书馆东馆 | `lib-pets-op`：禁止 | ordinary_pet | ordinary_pet | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-09** ⚖️🦮 | 上海图书馆东馆 | `lib-sd-legal`：允许 | 导盲犬 | guide_dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-10** ⚖️ | 上海迪士尼乐园 | `dl-legal-dog`：禁止 | dog | dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-11**  | 上海迪士尼乐园 | `dl-pet-ban`：禁止 | ordinary_pet | ordinary_pet | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-12** ⚖️🦮 | 上海迪士尼乐园 | `dl-sd-legal`：允许 | 导盲犬 | guide_dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-13** 🦮 | 上海迪士尼乐园 | `dl-sd-op`：有条件允许 | 导盲犬 | guide_dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-14** ⚖️ | 前滩太古里 | `qt-indoor-legal`：禁止 | dog | dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-15**  | 前滩太古里 | `qt-indoor-op`：禁止 | ordinary_pet | ordinary_pet | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-16**  | 前滩太古里 | `qt-outdoor-op`：有条件允许 | ordinary_pet | ordinary_pet | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-17** ⚖️🦮 | 前滩太古里 | `qt-sd-legal`：允许 | 导盲犬 | guide_dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-18** 🦮 | 前滩太古里 | `qt-sd-op`：允许 | 除导盲犬外 | guide_dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-19** ⚖️ | 和平饭店（费尔蒙） | `fp-legal-dog`：禁止 | dog | dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-20**  | 和平饭店（费尔蒙） | `fp-pets-op`：禁止 | ordinary_pet | ordinary_pet | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-21** ⚖️🦮 | 和平饭店（费尔蒙） | `fp-sd-legal`：允许 | 导盲犬 | guide_dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-22**  | 大吉路公园 | `dj-pilot`：有条件允许 | ordinary_pet | ordinary_pet | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-23**  | 广场公园（黄浦段） | `gc-h6-pilot`：有条件允许 | ordinary_pet | ordinary_pet | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-24**  | 广场公园（黄浦段） | `gc-other-keep`：禁止 | ordinary_pet | ordinary_pet | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-25**  | 星巴克咖啡（徐汇西岸梦中心店） | `xm-indoor-new`：禁止 | ordinary_pet | ordinary_pet | `exact` | secondary_reputable | RECOMMEND_APPROVE |  |
| **R2-26** ⚖️ | 星巴克咖啡（徐汇西岸梦中心店） | `xm-legal-dog`：禁止 | dog | dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-27**  | 星巴克咖啡（徐汇西岸梦中心店） | `xm-outdoor-media`：有条件允许 | ordinary_pet | ordinary_pet | `exact` | secondary_reputable | RECOMMEND_APPROVE |  |
| **R2-28** ⚖️🦮 | 星巴克咖啡（徐汇西岸梦中心店） | `xm-sd-legal`：允许 | 导盲犬 | guide_dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-29** ⚖️ | 星巴克臻选上海烘焙工坊 | `sb-legal-dog`：禁止 | dog | dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-30** ⚖️🦮 | 星巴克臻选上海烘焙工坊 | `sb-sd-legal`：允许 | 导盲犬 | guide_dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-31**  | 港汇恒隆广场 | `gh-indoor-new`：禁止 | ordinary_pet | ordinary_pet | `exact` | secondary_reputable | RECOMMEND_APPROVE |  |
| **R2-32** ⚖️ | 港汇恒隆广场 | `gh-legal-dog`：禁止 | dog | dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |
| **R2-33** ⚖️🦮 | 港汇恒隆广场 | `gh-sd-legal`：允许 | 导盲犬 | guide_dog | `exact` | primary_direct | RECOMMEND_APPROVE |  |

## 签署

| 字段 | 值 |
|---|---|
| reviewer（具名） |  |
| reviewer_role |  |
| reviewed_at |  |
| 是否确认 ADR-025 源忠实 scope（不再泛化为 service_dog） | ☐ 是 ☐ 否 |
| 首批批准条数（≤ `--max-approve`） |  |
| 签名 |  |

