# docs/legal — 法律文本草案索引

> **状态：全部为工程侧草案（DRAFT）。**
> 每一份文件顶部均标注 `LEGAL_REVIEW_REQUIRED`。
> **未经过执业律师审阅前，不得对外发布，不得作为正式条款展示。**
> 本目录文件由 `WORKBUDDY_PRODUCTION_MASTER_GOAL.md` P7 要求生成，仅提供结构与事实基础，不构成法律意见。

| 文件 | 用途 | 状态 |
|---|---|---|
| `PRIVACY_POLICY_DRAFT.md` | 隐私政策 | `LEGAL_REVIEW_REQUIRED` |
| `USER_AGREEMENT_DRAFT.md` | 用户协议 | `LEGAL_REVIEW_REQUIRED` |
| `DATA_METHODOLOGY_DRAFT.md` | 数据与证据方法论（可对外公开） | `LEGAL_REVIEW_REQUIRED`（事实部分已核实） |
| `CORRECTION_APPEAL_POLICY_DRAFT.md` | 纠错与申诉政策 | `LEGAL_REVIEW_REQUIRED` |
| `OPERATOR_CLAIM_TERMS_DRAFT.md` | 管理方认领条款 | `LEGAL_REVIEW_REQUIRED` |
| `DISCLAIMER_DRAFT.md` | 免责声明 | `LEGAL_REVIEW_REQUIRED` |

## 事实基线（供律师参考，均有工程证据）

| 事实 | 证据 |
|---|---|
| 不默认长期保存位置轨迹 | ADR-012、`PRIVACY_DATA_INVENTORY.md` |
| 贡献位置采用距离分桶，不存精确坐标 | `PlaceView.vue` `distance_bucket`、`accuracy_bucket` |
| 不提供评分/排名/红黑榜 | ADR-014、`COPY_GUIDE.md`、机读禁用词守卫 |
| AI 不做规则裁决 | ADR-005、`publish_gate.py`、`publish_reviewed_r1.py` 人类签署门禁 |
| 采集未绕过登录/验证码 | `EVIDENCE_REPAIR_LOG_R1.md`（14 次尝试逐条留痕） |
| 来源按再分发许可分级 | `source_artifact.display_allowed/redistribution_allowed/storage_allowed` |
| 小区仅记录公共空间规则 | ADR-013 |
| 观察 ≠ 规则 | ADR-004、`PlaceView.vue` 免责文案 |

## 待主体确认的信息（草案中留空）

- 运营主体全称、注册地址、联系方式
- 个人信息保护负责人及联系方式
- 域名与备案号
- 数据存储地域
