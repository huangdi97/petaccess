# HUMAN_REVIEW_QUICK_TABLE_R1.md

> GOV-01 速填表 · 一行一条，**按风险排序**。
> 「我的决定」列填：`APPROVE` / `APPROVE_WITH_NOTE` / `HOLD` / `REJECT`
> 详细依据见 `HUMAN_REVIEW_PACKET_R1.md` 对应编号。

**图例**：🔴 错归因 ｜ 🟠 弱证据 ｜ ⚠️ 存在冲突 ｜ ⚖️ 法定强制

| 编号 | Place | Rule 摘要 | Evidence | Conflict | AI建议 | 我的决定 |
|---|---|---|---|---|---|---|
| **G1-01** 🔴🟠 | Manner咖啡（凯德虹口商业中心店） | `mn-outdoor-media`：普通宠物 · 有条件允许 · outdoor_seating | search_snippet | 无 | REJECT |  |
| **G2-01** ⚖️ | 上海迪士尼乐园 | `dl-legal-dog`：犬（通用） · 禁止 · whole_park | primary_direct | 无 | HOLD |  |
| **G2-02** ⚠️ | 广场公园（黄浦段） | `gc-other-keep`：普通宠物 · 禁止 · other_areas | primary_direct | 有 | HOLD |  |
| **G2-03** 🟠⚠️ | 港汇恒隆广场 | `gh-outdoor-keep`：普通宠物 · 有条件允许 · outdoor | search_snippet | 有 | HOLD |  |
| **G3-01** ⚖️ | Manner咖啡（凯德虹口商业中心店） | `mn-sd-legal`：服务犬 · 允许 | primary_direct | 无 | APPROVE_WITH_NOTE |  |
| **G3-02** ⚖️ | 上海图书馆东馆 | `lib-sd-legal`：服务犬 · 允许 | primary_direct | 无 | APPROVE_WITH_NOTE |  |
| **G3-03** ⚠️⚖️ | 上海迪士尼乐园 | `dl-sd-legal`：服务犬 · 允许 | primary_direct | 有 | APPROVE_WITH_NOTE |  |
| **G3-04** ⚠️ | 上海迪士尼乐园 | `dl-sd-op`：服务犬 · 有条件允许 · whole_park | primary_direct | 有 | APPROVE |  |
| **G3-05** ⚠️ | 前滩太古里 | `qt-indoor-op`：普通宠物 · 禁止 · indoor | primary_direct | 有 | APPROVE |  |
| **G3-06** ⚠️ | 前滩太古里 | `qt-outdoor-op`：普通宠物 · 有条件允许 · outdoor_open | primary_direct | 有 | APPROVE |  |
| **G3-07** ⚖️ | 前滩太古里 | `qt-sd-legal`：服务犬 · 允许 | primary_direct | 无 | APPROVE_WITH_NOTE |  |
| **G3-08** ⚠️⚖️ | 和平饭店（费尔蒙） | `fp-sd-legal`：服务犬 · 允许 | primary_direct | 有 | APPROVE_WITH_NOTE |  |
| **G3-09** ⚠️ | 和平饭店（费尔蒙） | `fp-sd-op`：服务犬 · 有条件允许 · whole_hotel | primary_direct | 有 | APPROVE |  |
| **G3-10** ⚠️ | 广场公园（黄浦段） | `gc-h6-pilot`：普通宠物 · 有条件允许 · h6_pet_area | primary_direct | 有 | APPROVE |  |
| **G3-11** ⚠️ | 星巴克咖啡（徐汇西岸梦中心店） | `xm-indoor-new`：普通宠物 · 禁止 · indoor | secondary_reputable | 有 | APPROVE |  |
| **G3-12** ⚠️ | 星巴克咖啡（徐汇西岸梦中心店） | `xm-outdoor-media`：普通宠物 · 有条件允许 · outdoor_pet_area | secondary_reputable | 有 | APPROVE |  |
| **G3-13** ⚖️ | 星巴克咖啡（徐汇西岸梦中心店） | `xm-sd-legal`：服务犬 · 允许 | primary_direct | 无 | APPROVE_WITH_NOTE |  |
| **G3-14** ⚖️ | 星巴克臻选上海烘焙工坊 | `sb-sd-legal`：服务犬 · 允许 | primary_direct | 无 | APPROVE_WITH_NOTE |  |
| **G3-15** ⚠️ | 港汇恒隆广场 | `gh-indoor-new`：普通宠物 · 禁止 · indoor | secondary_reputable | 有 | APPROVE |  |
| **G3-16** ⚖️ | 港汇恒隆广场 | `gh-sd-legal`：服务犬 · 允许 | primary_direct | 无 | APPROVE_WITH_NOTE |  |
| **G4-01** ⚖️ | Manner咖啡（凯德虹口商业中心店） | `mn-legal-dog`：犬（通用） · 禁止 · indoor | primary_direct | 无 | APPROVE |  |
| **G4-02** ⚖️ | 上海图书馆东馆 | `lib-legal-dog`：犬（通用） · 禁止 · whole_building | primary_direct | 无 | APPROVE |  |
| **G4-03**  | 上海图书馆东馆 | `lib-pets-op`：普通宠物 · 禁止 · whole_building | primary_direct | 无 | APPROVE |  |
| **G4-04**  | 上海图书馆东馆 | `lib-sd-op`：服务犬 · 允许 · whole_building | primary_direct | 无 | APPROVE |  |
| **G4-05**  | 上海迪士尼乐园 | `dl-pet-ban`：普通宠物 · 禁止 · whole_park | primary_direct | 无 | APPROVE |  |
| **G4-06** ⚖️ | 前滩太古里 | `qt-indoor-legal`：犬（通用） · 禁止 · indoor | primary_direct | 无 | APPROVE |  |
| **G4-07**  | 前滩太古里 | `qt-sd-op`：服务犬 · 允许 | primary_direct | 无 | APPROVE |  |
| **G4-08** ⚖️ | 和平饭店（费尔蒙） | `fp-legal-dog`：犬（通用） · 禁止 · whole_hotel | primary_direct | 无 | APPROVE |  |
| **G4-09**  | 和平饭店（费尔蒙） | `fp-pets-op`：普通宠物 · 禁止 · whole_hotel | primary_direct | 无 | APPROVE |  |
| **G4-10**  | 大吉路公园 | `dj-pilot`：普通宠物 · 有条件允许 · whole_park | primary_direct | 无 | APPROVE |  |
| **G4-11** ⚖️ | 星巴克咖啡（徐汇西岸梦中心店） | `xm-legal-dog`：犬（通用） · 禁止 · indoor | primary_direct | 无 | APPROVE |  |
| **G4-12** ⚖️ | 星巴克臻选上海烘焙工坊 | `sb-legal-dog`：犬（通用） · 禁止 · whole_store | primary_direct | 无 | APPROVE |  |
| **G4-13** ⚖️ | 港汇恒隆广场 | `gh-legal-dog`：犬（通用） · 禁止 · indoor | primary_direct | 无 | APPROVE |  |

## 签署

| 字段 | 值 |
|---|---|
| reviewer（具名） |  |
| reviewer_role |  |
| reviewed_at |  |
| 是否接受 service_dog scope 泛化（ADR-020） | ☐ 是 ☐ 否 |
| 首批批准条数（≤ `--max-approve`） |  |
| 签名 |  |

