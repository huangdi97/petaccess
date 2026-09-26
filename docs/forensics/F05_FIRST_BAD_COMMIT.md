# F05 FIRST BAD COMMIT

**NOT_APPLICABLE — bisect 未进入。**

判定依据（合同 §14：仅当 A PASS 且 C FAIL 才进入 bisect；GOOD=c84b4cf / BAD=HEAD）：

三矩阵（F03）= **A PASS / B PASS / C PASS**——v0.1.0 官方（A）与 v0.1.0 重建（B）与当前 HEAD（C）在统一工具链下 boot/render 全部通过。没有 "PASS→FAIL" 断点，因此不存在 FIRST_BAD_COMMIT。

附加反证（为何不可能是代码回归/坏提交引入）：
- F04：v0.1.0→HEAD 依赖零漂移（package.json/Cargo/pyproject/锁文件逐字节相同）；Android 栈 tracked 变更 = 0；BOOT_CRITICAL 5 个文件（App.vue/ConsumerAppShell.vue/main.ts/router.ts/styles.css）在 C 对象实测渲染正常。
- 后端全量 945 passed / 2 skipped（0 fail，pre-fix 基线）。

F05 状态：NOT_APPLICABLE（原因：无 FAIL 断点可定位）。