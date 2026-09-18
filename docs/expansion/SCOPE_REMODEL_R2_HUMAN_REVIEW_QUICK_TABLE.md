# SCOPE-REMODEL-R2 — Human Review Quick Table

| # | Place | Candidate ID | 原文术语 | normalized subject | normalization type | Layer | effect | Evidence | Source | Freshness | Monitor | 未建模残差 | 法律适用 | 例外依赖 | AI 建议 | final_decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 上海迪士尼乐园 | `7b595de9…` | 「动物（导盲犬除外）」 | dog | compound_term_split | OPERATOR_POLICY | prohibited | original/operator_official | 上海迪士尼度假区官网《上海迪士尼乐园 | 90d | url_hash | **YES** | — | w01-305fa08c1e | APPROVE_AS_SPLIT | **null** |
| 2 | 上海迪士尼乐园 | `4580ab21…` | 「动物（导盲犬除外）」 | cat | compound_term_split | OPERATOR_POLICY | prohibited | original/operator_official | 上海迪士尼度假区官网《上海迪士尼乐园 | 90d | url_hash | **YES** | — | — | APPROVE_AS_SPLIT | **null** |
| 3 | 上海迪士尼乐园 | `4ca5e55a…` | 「动物（导盲犬除外）」 | other | compound_term_split | OPERATOR_POLICY | prohibited | original/operator_official | 上海迪士尼度假区官网《上海迪士尼乐园 | 90d | url_hash | **YES** | — | — | APPROVE_AS_SPLIT | **null** |
| 4 | 上海动物园 | `a4e2ba26…` | 「动物」 | dog | compound_term_split | OPERATOR_POLICY | prohibited | original/operator_official | 上海动物园官网《温馨提示》 | 90d | url_hash | **YES** | UNRESOLVED | — | APPROVE_WITH_LEGAL_CAVEAT | **null** |
| 5 | 上海动物园 | `27893d75…` | 「动物」 | cat | compound_term_split | OPERATOR_POLICY | prohibited | original/operator_official | 上海动物园官网《温馨提示》 | 90d | url_hash | **YES** | — | — | APPROVE_AS_SPLIT | **null** |
| 6 | 上海动物园 | `2a3de3ab…` | 「动物」 | other | compound_term_split | OPERATOR_POLICY | prohibited | original/operator_official | 上海动物园官网《温馨提示》 | 90d | url_hash | **YES** | — | — | APPROVE_AS_SPLIT | **null** |

- 完整 Candidate ID 见 `docs/expansion/review_decisions_scope_remodel_r2.json`。
- 「未建模残差 = YES」：本行只覆盖当前词表可表达的部分；词表外动物 = UNKNOWN，不是 ALLOWED。
- AI 建议列**不是决定**；所有 `final_decision` 仍为 `null`。

