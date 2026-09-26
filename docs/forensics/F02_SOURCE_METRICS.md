# F02 SOURCE METRICS（本轮实测，2026-09-26）

## 1. Engineering Gate（M1 scanner）——重跑结果

`uv run python scripts/check_engineering_quality.py`：

```
engineering quality gate summary
  FAIL   0
  review 60
  warn   34
RESULT: PASS (0 FAIL / 60 REVIEW / 34 WARN)
```

与 M1 基线（0 FAIL）一致。所有非零项已登记至 `FORENSIC_FINDINGS_REGISTER.md`。

## 2. 文件规模数据（自 ALL_FILES.csv，1039 条）

- 人工维护文本文件按扩展名分：`.py/.ts/.tsx/.vue/.js/.rs/.ps1/.yml/.toml` 总数 1039（tracked 982 + gen/android 56 + .env 1）
- 全仓 >300 行人工源码（含后端与前端的当前代码，见 findings register）：见 register 逐项
- lint 门禁（CI 命令等价）：`ruff check`、`ruff format --check` 结果待修复后终查（本轮先提供 pytest 基线）

## 3. 后端全量回归（本轮实测，pre-fix 基线）

```
uv sync --dev --all-packages --frozen      → OK
scripts/isolated_db.py --role TEST --reset → OK
celery -A app.worker.celery_app worker --pool=solo -Q petaccess_test → OK（pid 记录）
uv run pytest -q                            → 945 passed, 2 skipped, 1 warning in 48.43s
PYTEST_EXIT = 0
```

历史基线为 938 passed / 2 skipped；本轮实测 **945 passed / 2 skipped，0 failed**（测试集比历史更多，无回归失败）。

## 4. 前端/脚本门禁（待修复后终查项）

- `pnpm lint:fe` / `pnpm format:check:fe` / `pnpm --filter @petaccess/client-h5 build` / `pnpm --filter @petaccess/admin build`：本轮已执行于 C 构建链（HEAD clean build 成功，见 F03/F11 证据）
- mypy（CI: `uv run mypy services/api/app`）与 ruff：与 pytest 同一 venv，将在修复后二次审计一并终查（§85）

## 5. 度量结论

SOURCE_METRICS = PASS_WITH_TRACKED_DEBT（0 FAIL；60 review + 34 warn 全数入 register，逐项带 tracking ID）。