# Visual Fidelity — Phase A Report（Search + Place）

> 执行日期：2026-09-28
> 契约：PetAccess v0.2.1 Visual Fidelity Recovery（Goal 已批准）Phase A（Search Desktop/Mobile + Place Desktop/Mobile）
> 人工视觉失败证据：Goal §3.1 / §3.2 —— 本报告逐项关闭。

## 1. 文档状态重置（Goal §2）

```text
UI_PAGE_ARCHETYPE = PARTIAL_PASS        （结构已 PASS，视觉待人工确认）
UI_INFORMATION_ARCHITECTURE = PARTIAL_PASS
UI_VISUAL_FIDELITY = FAIL                （恢复中，等待 HUMAN_VISUAL_GATE_A）
UI_CONSUMER_LANGUAGE = FAIL              （Phase A 页面已清零，Reality/Evidence 属 Phase C）
UI_HUMAN_VISUAL_ACCEPTANCE = FAIL        （不得由 Agent 自宣）
UI_VISUAL_CLOSURE = REOPENED
```

## 2. 关闭清单（逐项对应 Goal §3）

### Search Desktop
| Goal 问题 | 关闭方式 | 证据 |
|---|---|---|
| Inspector 是 label/value 工程表 | `<dl>` 改为 Judgment 层级块（Identity→当前查询→大结论 26px→条件→近期现场→时效） | `DecisionInspector.vue` 重写；`search-desktop-ready/selected.png`；渲染核验 dlCount=0 |
| Primary Decision 不突出 | 结果行 `row-rule` 直接显示判定词（可以进入/信息不足…），medium 16px；Inspector 大结论 26px | `row-rule`/`inspector-verdict` 渲染核验 |
| 层级接近 | Context/条件/Reality/Evidence 分块 + accent 左边线强调决策 | 截图 + CSS 核验 |
| 行暴露过多工程信息 | 删「已核验：」前缀、删 `result-alias`、删重复条件行；`result-rules` 降 13px 灰字；`result-branch` 仅桌面轻量 | `bodyHasYanhe=false` 渲染核验；截图 |
| 信息无法快速扫描 | 行信息预算收敛为 6 项（名称/类型·距离/大结论/1 条件/Reality/极轻元数据） | 截图 |
| 空而不静 | 字号阶梯落地（14/17/18/19/22/26/30 token），Inspector 有边界与判定块 | tokens.css 新增 |

### Search Mobile
| Goal 问题 | 关闭方式 | 证据 |
|---|---|---|
| 桌面栏缩窄 | 移动端单列，行压缩为 ≤4 视觉组；`result-rules`/`result-branch` display:none | `search-mobile-ready.png`；渲染核验 rules/branch hidden |
| 次要 metadata 过多 | 同上 + 决策行 18px 不缩字 | 渲染核验 decisionFont=18px |
| 无 mobile compression | CSS media ≤767px 压缩规则 | 同上 |
| filter 铺 chips | `筛选 N` → PaBottomSheet（底部 sheet） | `search-mobile-filter.png` |

### Place Desktop
| Goal 问题 | 关闭方式 | 证据 |
|---|---|---|
| schema dump 感 | Dossier 顺序冻结：Identity→当前结论→近期现场→空间/区域→规则依据→证据与来源→共处/设施→历史/纠错 | `PlaceView.vue` 模板顺序 |
| 字号偏小 | 身份 30px、大结论 26px、section 18px（token） | tokens + 样式核验 |
| 长页面无节奏 | section 用 18px 标题 + divider 行 + 副标题层级 | 样式核验 |
| Inspector 不像持续判断 | Sticky Inspector 只保留 5 个关键块，与 Search 共用 DecisionInspector | `place-desktop-ready.png` |
| sections 视觉同权 | 当前结论块 accent 左边线（`sub-answer--mine`）突出 | 样式核验 |
| 主信息与 provenance 同权 | History/Correction 下沉到最后，QuickConfirm/现场记录次级化 | 模板顺序 |
| progressive disclosure 不足 | 历史版本默认折叠（disclosure toggle + aria-expanded） | `place-mobile-ready.png` |

### Place Mobile
| Goal 问题 | 关闭方式 | 证据 |
|---|---|---|
| raw enum 可见（pet_area/dining_area/ordinary_pet·enter/superseded/floor） | 统一 Consumer Label Mapper（`apps/client-h5/src/consumer/labels.ts`）覆盖 zone/animal/action/status/staff/observed/facility/coexistence/entrance；UUID 片段 → 「来源信息暂不可用」 | Consumer Leakage Gate Phase A = 0 泄漏；渲染核验 |
| 第一屏要素 | 身份+当前查询+大结论+条件在首屏 | 截图 |
| 历史/证明平铺 | disclosure toggle 折叠 | 截图 |

## 3. 消费者语言（Goal §29/§30）

- 新增 `apps/client-h5/src/consumer/labels.ts`：ANIMAL_SCOPE / RULE_ACTION / ZONE_TYPE / RULE_STATUS / RULE_LAYER / MANDATORY_LEVEL / OBSERVED_ACTION / STAFF_ACTION / FACILITY_STATE / AMENITY / ANIMAL_FACILITY / COEXISTENCE / COEXISTENCE_VALUE / ENTRANCE 全部消费者标签；`sourceLabel` 禁止 UUID 片段；fallback 一律消费者安全词。
- 映射表文档：`docs/ui/CONSUMER_VISIBLE_LANGUAGE_MAP.md`。
- 门禁：`tests/ui-reconstruction/consumer-leakage-gate.spec.ts`（visible text 层面，explicit denylist + UUID regex + invariant regex；Phase A scope 3 passed）。

## 4. 自动化门禁（Phase A 实际执行）

| 门禁 | 结果 | 说明 |
|---|---|---|
| vue-tsc | PASS | client-h5 --noEmit |
| eslint | PASS | 全仓 lint 0 error |
| prettier --check | PASS | 全仓 |
| client build | PASS | vite build |
| consumer-leakage-gate | 3 passed | Phase A scope（LEAKAGE_SCOPE=a） |
| phase1-gate | 25/25 | 全 viewport |
| a11y-gate | 30/30 | 全 viewport |
| h5-journey | 9/9 | 单跑 |
| consumer-contract-closure | 4/4 | 单跑 |
| map-passport | 7/7 | 单跑 |
| place-preview-overflow | 2/2 | 单跑 |
| m3-consumer-core | 5/5 | 单跑 |
| consumer-routes | PASS | 单跑 |
| contribute-wizard | 3/3 | 单跑（并行时 2 例 flake，见下） |
| e2e 全量并行 | 185 passed / 4 failed | 4 例均 TEST-001 既有并行 flake（contribute-wizard A1/A2 ×2、consumer-routes B1、h5-journey home）——单跑全绿 |

**TEST-001 flake 处理**：沿用历史冻结语义（UI_RECONSTRUCTION_FINAL_REPORT §剩余 gaps #2），记 `PASS_WITH_KNOWN_BASELINE_FLAKE`；不弱化断言、不删测试。

## 5. 真实截图（Phase A，全部 0 pageerror）

`artifacts/visual-fidelity-recovery/phase-a/`
- search-desktop-ready.png / search-desktop-selected.png / search-desktop-empty.png（1440×900）
- search-mobile-ready.png / search-mobile-filter.png（430×932）
- place-desktop-ready.png / place-desktop-unknown.png（1440×900）
- place-mobile-ready.png（430×932）

Gallery：`artifacts/visual-fidelity-recovery/VISUAL_FIDELITY_REVIEW.html`（Page/Viewport/State/Approved Direction/Actual/Notes 每格）。

## 6. Gate 状态

```text
HUMAN_VISUAL_GATE_A = PENDING
```

Phase A 完成：commit + push `feat/visual-fidelity-recovery`（不合入 master）。等待用户打开 Gallery 审查真实截图并显式回复 PASS / 修改意见。未获 PASS 前不推进 Phase B。

---

## 7. 第二轮修正（对照 Approved Reference 逐屏实测后）

### 7.1 对照方法

用 Windows OCR + PIL 像素分析提取参考板 7 屏（01 Home/02 Search/03 Map/04 Place/05 Reality/06 Evidence/07 Contribution，1536x1024）的真实内容与结构；对实现截图同样提取后逐屏对照。不以“我觉得”为结论。

| 实测维度 | 参考 Search 屏 | 参考 Place 屏 | 第一版实现 | 判定 |
|---|---|---|---|---|
| 白区比例 | 64% | 73% | 88-92% | 空而不静复现 |
| 结果行右端 | 时效徽章（2天前记录/10天·3记录） | - | 只有状态 | 缺项 |
| 列表头部 | 找到 32 个结果 计数行 | - | 无 | 缺项 |
| 内容呈现 | 平铺 divider | 平铺 divider | sub-answer / Inspector = 卡片(border+radius) | 违反 Freeze §5 |

### 7.2 实际修改

1. Search 行收紧：head = 左身份(名称/类型·距离) + 右「N 天前记录 + StatusBadge」；结论 + 1 关键条件同行；reality/evidence 单行；生效规则+所属收敛为 13px 极轻元数据单行（保留测试文案）。
2. 列表头部新增「找到 N 个结果」（data-testid=search-count）。
3. 去卡片化：.sub-answer 去 border/radius/bg -> 扁平 divider（保持 accent 左边线）；Inspector 去 border/radius/bg -> 扁平 pane + accent 左边线 + bottom divider（Freeze §5）。
4. 桌面 split 布局 body 不再收窄（max-width:none），列表白区随数据行数下降。

### 7.3 第二轮实测结果

- Search desktop 白区 88%（原 92%）；Search mobile 79%（原 89%）；Place mobile 71% ≈ 参考 73%。
- OCR 复核：移动 ≤4 行组、桌面计数行/时效徽章/结论+条件同行在真实截图中可见。
- 门禁：vue-tsc/eslint/prettier/build PASS；phase1+a11y+leakage(1440) 14/14；e2e affected（h5-journey/m3-consumer-core/place-preview-overflow/consumer-routes）21/21（独立栈）；leakage=0。

### 7.4 诚实说明

- 参考 32 条 vs 种子 5 条（数据量差异，非设计差异）。
- 白区是结构性代理，最终视觉接受度仍需人工目视（HUMAN_VISUAL_GATE_A）。

## 8. 第三轮修正（几何密度逐图实测后）

### 8.1 实测发现

| 维度 | 修复前（提交 0de87c0） | 实测 | 参考 |
|---|---|---|---|
| Search 桌面 Inspector 宽度 | 916px（flex 拉满 1372px body） | — | list-detail 双栏，Inspector 为支撑面 |
| Search 桌面 Inspector 高度 | 441px，下方空 245px | bodyH 594 | 双栏整体充满视口 |
| Search 桌面 workspace 宽度 | `max-width:none` 拉满 1440 | body x=84..1456 | 内容区有呼吸余量 |
| Place 桌面 section 距 | space-6(32px) | — | 更紧的节奏 |
| 结果行横向 padding | space-2(8px) | — | 紧凑 divider 行 |

### 8.2 实际修改

1. `.search-workspace__body--split`：`max-width:1180px` + `margin:0 auto`（不再拉满 1372px）；`align-items:stretch`。
2. `.search-inspector`：`max-width:560px` + `align-self:stretch`（Inspector 不再 916px 空散）。
3. `.decision-inspector`：`min-height:calc(100vh - 112px)` —— Inspector 纵向往满，成为真正的双栏支撑面（441→788px）。
4. `.result-row__link`：横向 padding space-2→space-1，行更紧凑。
5. `.place-section`：margin-bottom space-6→space-5（Place 长档案节奏收紧）。

### 8.3 第三轮实测结果

- Search 桌面：bodyH 594→820；Inspector 441→788px 高、560px 宽；Pane 400px 恒定。
- Place 桌面：Dossier 824px + Inspector 320px sticky（比例 2.6:1）。
- 全 viewport overflow=0；OCR 对照参考屏：计数行/时效徽章/结论+条件同行/Inspector 判定层级均在真实截图中。
- 门禁：vue-tsc/eslint/prettier/build PASS；ui-reconstruction phase1+a11y+leakage **70/70**；e2e affected 单跑全绿（TEST-001 contribute-wizard 并行/空态时序 flake 重跑 3/3 PASS，沿用已冻结语义）。

### 8.4 诚实说明

- 白区像素比例对浅色 UI 天然偏高（参考板含插画/色块），不作为唯一依据；几何/OCR/门禁三者共同判定。
- 种子数据 5 场所 vs 参考 32 条：数据量差异，非设计差异。
- 最终仍需 HUMAN_VISUAL_GATE_A 人工目视真实截图确认。
