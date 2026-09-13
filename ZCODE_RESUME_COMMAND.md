# ZCODE_RESUME_COMMAND.md

你现在是在 WorkBuddy 之后继续接管同一个现有项目，不是从头开始。

先完整读取：
- `ZCODE_RESUME_AFTER_WORKBUDDY_v0.5.md`
- 当前 `PROJECT_STATE_V05.md`
- 当前 `ACCEPTANCE_MATRIX_v0.5.md`
- `WORKBUDDY_TAKEOVER_REPORT.md`（如果存在）
- `FINAL_RELEASE_REPORT.md`
- `DECISIONS.md`
- `BLOCKERS.md`

然后立即执行：

```bash
git status
git diff --stat
git diff
git diff --cached
git log --oneline -20
git rev-parse HEAD
```

禁止 reset/clean/覆盖 WorkBuddy 的未提交改动。

创建 `ZCODE_RESUME_TAKEOVER_REPORT.md`，重跑当前 baseline，识别 WorkBuddy 已完成、半完成和未开始的 Gate。

然后从第一个 `PARTIAL / FAIL / NOT_RUN` Gate 继续，不重做已经 PASS 的内容。

继续执行 `ZCODE_RESUME_AFTER_WORKBUDDY_v0.5.md` 中的全部要求，直到所有本地可完成 Gate PASS，并生成 `V05_FINAL_REPORT.md`。

不要只写计划，不要问我是否继续，现在直接开始执行。
