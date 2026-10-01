# UI Human Closure V5 Manifest — 人审候选包清单（27 张）

> 实现基准：`IMPLEMENTATION_BASE` = v5 代码与测试完成后的实现 commit（分支历史内可查；
> 本文不自我引用最终 HEAD，最终 HEAD 以 Git 查询为准）。
> 产物：`artifacts/ui-human-closure-v5/HUMAN_REVIEW/`（HUMAN_REVIEW_INDEX.html +
> `<name>.png` + `<name>.json` metadata）。

## 1. 说明

- 每张截图在保存前先通过 **Capture State Integrity（O6）**：route/page/state/fixture/h1/
  entityId/selectedId/count 全部从真实 DOM 读取，与 shot `expect` 一致（`valid: true`）才写入。
- metadata **只证明真实状态，不宣称视觉通过**；Agent 不代替用户做视觉签字。
- 视口：desktop 1440×900、mobile 430×932；viewport capture；motion frozen +
  reduced-motion；固定时钟（2026-09-15T04:00:00Z）。
- 关键 responsive（768×1024 / 1280×800 / 360×800）只做 machine gate（ui-reconstruction
  180/180），不进人审包。

## 2. 清单（27 张，全部 VALID）

### Search（4）
| 文件名 | 视口 | route | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| search_desktop_ready | 1440×900 | `/#/search` | ready-selected | list-detail；toolbar 结果N|筛选 |
| search_desktop_empty | 1440×900 | `/#/search` | empty | 单 primary「提交场所线索」 |
| search_mobile_ready | 430×932 | `/#/search` | ready | 单列 rows |
| search_mobile_filter | 430×932 | `/#/search` | filter | 筛选 sheet |

### Place（5）
| 文件名 | 视口 | route | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| place_desktop_overview | 1440×900 | mall | ready | Overview 五块；main 820 |
| place_desktop_rules | 1440×900 | mall `?view=rules` | ready | Rule Groups 带回文章节 |
| place_desktop_unknown | 1440×900 | branch | unknown | Unknown Overview 最小化 |
| place_mobile_overview | 430×932 | mall | ready | Space/Evidence summary row |
| place_mobile_rules | 430×932 | mall `?view=rules` | ready | rule groups divider |

### Home（2）
| 文件名 | 视口 | route | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| home_desktop | 1440×900 | `/#/` | ready | 附近已有依据 / 附近待补充 |
| home_mobile | 430×932 | `/#/` | ready | 单列 rows |

### Map（4）
| 文件名 | 视口 | route | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| map_desktop | 1440×900 | `/#/map` | ready | List+Map |
| map_mobile_ready | 430×932 | `/#/map` | ready | 填满视口；segmented |
| map_mobile_selected_half | 430×932 | `/#/map?place=8412b521…` | ready | half 态 sheet |
| map_mobile_selected_expanded | 430×932 | 同上（点击 handle） | ready | expanded 态 |

### Reality（3）
| 文件名 | 视口 | route | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| reality_desktop_ready | 1440×900 | cafe `/reality` | ready | timeline 首屏 |
| reality_mobile_ready | 430×932 | cafe `/reality` | ready | mobile timeline |
| reality_desktop_empty | 1440×900 | mall `/reality` | empty | inline empty |

### Evidence（3）
| 文件名 | 视口 | route | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| evidence_desktop_ready | 1440×900 | cafe `/evidence` | ready | record identity + provenance |
| evidence_mobile_ready | 430×932 | cafe `/evidence` | ready | mobile 版本 |
| evidence_desktop_empty | 1440×900 | mall `/evidence` | empty | inline empty |

### Contribution（6）
| 文件名 | 视口 | route | 状态 | 备注 |
| --- | --- | --- | --- | --- |
| contribution_desktop_choose | 1440×900 | `/#/contribute/mall`（已登录） | choose-type | 5 option rows |
| contribution_desktop_step1 | 1440×900 | 同上（entry-quick） | step-1 | Step Shell + option rows |
| contribution_desktop_step2 | 1440×900 | 同上（entry-reality） | step-2 | reality cluster 表单 |
| contribution_desktop_done | 1440×900 | 同上（提交 reality） | done | 已提交待核验 copy |
| contribution_mobile_choose | 430×932 | 同上（已登录） | choose-type | 5 option rows |
| contribution_mobile_step1 | 430×932 | 同上（entry-quick） | step-1 | mobile step shell |

## 3. 验证

- `node --experimental-strip-types` 读取全部 27 个 metadata JSON：`valid=27 invalid=0`。
- `pnpm exec playwright test -c playwright.ui-oracle.config.ts tests/ui-oracle/human-review-v5.spec.ts`
  → 2 passed（oracle-desktop + oracle-mobile 各跑对应视口的 shot）。
- O6 actual 与 expected 逐字段一致；mismatches 全为空数组。

## 4. 状态

人审候选包已就绪，等待用户人工视觉签字；`UI_HUMAN_VISUAL_ACCEPTANCE = PENDING`。
