# BLIND_UI_PHASE_D_REALITY_EVIDENCE_CONTRIBUTION.md — Phase D：Reality / Evidence / Contribution 收口

> 阶段产物：`artifacts/blind-ui-recovery/reports/phase-d-*`、`compare-reality.json`、`compare-evidence.json`、`compare-contribution.json`

## 目标（契约 §C.14）

- Reality：真正 event log（Date Group → Time → Timeline marker → Location → Observed fact → Evidence/freshness），每 event 非 card；禁止工程不变量原文。
- Evidence：顶部 Place name / Zone / Observed time（无 display name 时「场所信息暂不可用」）；无 UUID；provenance 链消费者可读（原始证据→地点匹配→时间确认→来源确认→人工核验）；Observed/Submitted/Reviewed 三时间分离。
- Contribution：第一屏「你刚刚知道了什么？」，5 个消费者选项，选中后 3–4 个 focused step，Final「已提交待核验」；Playwright 测试覆盖 needs-place guard、real flow entry、intermediate step、submit/done、mobile（不能只凭 guard 页存在判 PASS）。

## 改动

- `RealityTraceView.vue`：`data-ui="reality-timeline"` / `reality-event` / `reality-empty`；空态加 primary「刷新」+ secondary「查看场所准入」；事件行改 consumer labels（`犬 · 进入（工作人员：未观察到干预）`）。
- `EvidenceView.vue`：`data-ui="evidence-shell"` / `evidence-times` / `observed-time` / `submitted-time` / `reviewed-time`；场所名改「场所信息暂不可用」；raw enum → labels；来源 fallback 改「其他来源 / 核验状态未知」；空态加「刷新」。
- `EvidenceProvenance.vue`：根加 `data-ui="evidence-provenance"`。
- `ContributeEntry.vue`：根加 `data-ui="contribution-flow"`。
- 后端 `reality_reports.py`：note 改自然语言「暂无记录不代表现场没有动物。」（纯展示文案，不改语义；相关后端 tests 无该字符串断言，30 个 reality 测试全过）。
- 契约：reality 拆 ready（星河咖啡，有 observation 行）/ empty（云栖中心，空态）；evidence 加 records 页（星河咖啡）；contribution entry 页 `auth: true`（真实登录流）；规则支持 `pages[]` 页级限定。

## 机器 Gate（Oracle，stage=phase-d / final）

| 契约 | PASS | WARN | FAIL |
|---|---|---|---|
| reality（ready+empty） | 14 | 0 | 0 |
| evidence（ready+records） | 16 | 0 | 0 |
| contribution（needs-place+entry，auth） | 14 | 0 | 0 |

- Reality ready 页实测 2 条 trace-row（`data-ui=reality-event`），行文本为中文消费者文案，无 invariant 命中。
- Evidence records 页 provenance 恰好 5 步、时间行 ≥3（surfaceRows=6）。
- Contribution entry 页 5 个选项 +「你刚刚知道了什么？」可见（认证态，非 guard）。

## 回归

- 后端 pytest：`-k reality` 30/30 PASS；全量 836 passed / 2 skipped / 4 环境性失败（celery worker 未运行、OCR、SDK adb 路径硬编码——均不引用 reality_reports，详见 FINAL REPORT）。
- e2e contribute-wizard：串行 3/3 PASS（并行 2-worker 下存在已知懒加载超时 flake，仓库此前 a8bab37 有同类硬化）。

## 证据

`artifacts/blind-ui-recovery/probes/phase-d-reality.json`、`phase-d-evidence.json`、`phase-d-contribution.json`；截图 `screens/final/reality-reality-ready.png`、`evidence-evidence-records.png`、`contribution-contribute-entry.png`。
