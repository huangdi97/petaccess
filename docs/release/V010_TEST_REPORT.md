# V010 TEST REPORT 鈥?2026-09-24

> 鐘舵€佹爣璁?(Status Legend): **CURRENT VERIFIED** 鏈細璇?2026-09-24)瀹為檯鎵ц骞舵牳楠?| **HISTORICAL** 姝ゅ墠浼氳瘽鎵ц銆佹湰杞湭閲嶈窇 | **NOT RERUN** 鏈噸璺?鍘熷洜宸叉敞鏄? | **BLOCKED** 鏃犳硶鎵ц(鍘熷洜宸叉敞鏄?

## 鐘舵€佹€昏〃 (Status Table)

| 娴嬭瘯 | 缁撴灉 | 鏍囪 |
|---|---|---|
| Backend pytest | 916 passed / 2 skipped | CURRENT VERIFIED |
| Gate unit tests | 21 passed | CURRENT VERIFIED |
| Playwright E2E锛坔5-shell + h5-journey锛?| 18 passed | CURRENT VERIFIED |
| Playwright E2E锛坋mpty-state.spec.ts锛?| 3 passed | CURRENT VERIFIED |
| Visual suite | 47 passed锛?7 families 脳 viewports锛宑ompare-mode锛?| CURRENT VERIFIED |
| mypy | 93 files, 0 errors | CURRENT VERIFIED |
| ruff check / format --check | PASS锛?92 files锛?| CURRENT VERIFIED |
| client-h5 build (vue-tsc + vite) | PASS | CURRENT VERIFIED |
| admin build (vue-tsc + vite) | PASS | CURRENT VERIFIED |
| CI 瀹為檯杩愯 | BLOCKED锛堟棤 git remote锛屾湭鎺堟潈锛?| BLOCKED |
| DEPENDENCY_SCAN锛坧ip-audit锛?| 缁撴灉寰?orchestrator 濉綍 | NOT RERUN |
| Desktop 绐楀彛鐩存帴鎴浘 | 鏈崟鑾凤紙headless Win32 title lookup 涓嶅彲闈狅紱娓叉煋缁忚繘绋嬫爲/Playwright 纭锛?| NOT RERUN锛堝眬闄愶級 |

## 1. 鍚庣

- pytest锛?16 passed / 2 skipped锛圱EST db `petaccess_test` + celery worker on redis /1锛夆€斺€?PASS銆?- Gate unit tests锛?1 passed銆?
## 2. 鍓嶇 E2E

- h5-shell + h5-journey锛?8 passed銆?- empty-state.spec.ts锛? passed锛堝悎璁?21锛夈€?
## 3. Visual

- 47 passed锛坧rojects锛歨5-390 / h5-768 / h5-1440 + admin-768 / admin-1440锛夈€?- 17 baseline families锛涗负涓€娆℃湁鎰忕殑鏂囨鍙樻洿閲嶆柊鐢熸垚杩囦竴娆″熀绾匡紱compare-mode PASS銆?
## 4. 闈欐€佷笌鏋勫缓

- mypy锛?3 files, 0 errors锛堝巻鍙?97 鍙ｅ緞涓烘洿骞胯寖鍥村惈 worker锛涙湰杞互 93 files 涓哄噯锛夈€?- ruff check + ruff format --check锛歅ASS锛?92 files锛夈€?- vue-tsc + vite build锛歝lient-h5銆乤dmin 鍧?PASS銆?
## 5. 鏈墽琛岄」锛堝瀹炴爣璁帮級

- **CI 瀹為檯杩愯**锛欱LOCKED 鈥斺€?鏃?git remote 涓旀湭鑾疯繍琛屾巿鏉冦€?- **DEPENDENCY_SCAN**锛歂OT RERUN 鈥斺€?facts 浠呰褰?"pip-audit 宸茶繍琛?锛岀粨鏋滄暟瀛楀緟 orchestrator 濉綍銆?- **Desktop 绐楀彛鐩存帴鎴浘**锛歂OT RERUN 鈥斺€?headless 鐜涓嶅彲闈狅紱娓叉煋宸查€氳繃 WebView2 杩涚▼鏍?+ bundled copy + Playwright 鍚?bundle 娓叉煋纭銆?
## 6. 缁撹

**缁撹: FULL_REGRESSION = PASS**锛堝凡鎵ц椤瑰叏缁匡紱CI / DEPENDENCY_SCAN / 绐楀彛鎴浘鎸変笂琛ㄥ瀹炴爣璁帮級銆?