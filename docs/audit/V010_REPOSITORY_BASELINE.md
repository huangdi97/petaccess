# V010_REPOSITORY_BASELINE.md

# v0.1.0 Phase A 鈥?鍏ㄤ粨鍙瀹¤ 路 浠撳簱鍩虹嚎

> 鐢熸垚鏃ユ湡:2026-09-23(鍩轰簬浠撳簱瀹為檯鍙鐩樼偣,闈炲巻鍙叉姤鍛婂鍒?
> 鐘舵€佹爣璁?CURRENT VERIFIED(鏈瀹炴祴) / HISTORICAL(鍘嗗彶璁板綍,鏈噸璺? / NOT RERUN(鏈疆鏈噸璺? / BLOCKED(澶栭儴鏉′欢缂哄け)

---

## 1. 鍩虹嚎鏍搁獙缁撴灉

| 椤圭洰 | 澹扮О鍊?| 瀹炴祴鍊?| 鐘舵€?|
|---|---|---|---|
| Git HEAD | `6079847` | `d4e7e66` (master, M10) | CURRENT VERIFIED |
| Worktree | 鈥?| clean (0 changed) | CURRENT VERIFIED |
| MIGRATION_HEAD | `e9f2c1d4a5b6` | alembic head `e9f2c1d4a5b6`(鍗?head,閾惧畬鏁?鍒濆 revision `864ffcfc7ccb`) | CURRENT VERIFIED |
| pytest | 889 passed / 2 skipped | 鏈噸璺?Phase B/X 閲嶈窇) | NOT RERUN |
| ruff / format | PASS | 鏈噸璺?Phase B 閲嶈窇) | NOT RERUN |
| mypy | 97 files / 0 errors | 鏈噸璺?Phase B 閲嶈窇) | NOT RERUN |
| H5 / Admin vue-tsc + build | PASS | 鏈噸璺?Phase B 閲嶈窇) | NOT RERUN |
| Playwright | 18 passed | 鏈噸璺?| NOT RERUN |
| Visual | 17 baselines PASS | 鏈噸璺?| NOT RERUN |
| Reality DB migration/persistence | PASS | alembic head 宸插疄娴?drill 鏈噸璺?| PARTIAL |
| Security Critical/High = 0 | PASS | 鏈噸璺?Phase Z 閲嶈窇) | NOT RERUN |
| Backup/Restore | PASS | 鏈噸璺?| NOT RERUN |
| Observability | basic endpoints PASS | 鏈噸璺?| NOT RERUN |

鍏抽敭宸紓璁板綍:
- `e9f2c1d4a5b6` 鏄?**alembic revision**,涓嶆槸 git commit;git 涓笉瀛樺湪鍚屽悕 commit(鍒濇煡璇垽,宸叉緞娓?銆?- 鍘嗗彶璐ㄩ噺鏁板瓧鍏ㄩ儴鎸?NOT RERUN 瀵瑰緟,Phase B(宸ョ▼ gate)璧烽€愰」閲嶉獙銆?
---

## 2. 浠撳簱缁撴瀯

```
E:\AI\瀹犵墿绠＄悊
鈹溾攢 apps/
鈹? 鈹溾攢 client/        uni-app x 瀹㈡埛绔?.uvue,7 椤?+ tabBar,14 鏂囦欢)
鈹? 鈹溾攢 client-h5/     Vue 3 H5 娑堣垂鑰呯(86 鏂囦欢;src: 25 .vue + 6 .ts)
鈹? 鈹斺攢 admin/         Vue 3 绠＄悊绔?102 鏂囦欢;src: 29 .vue + 6 .ts)
鈹溾攢 services/
鈹? 鈹溾攢 api/           FastAPI 鍚庣(290 鏂囦欢;app 93 .py + migrations 24 versions + 鐙珛 tests 4)
鈹? 鈹斺攢 worker/        Celery worker(浠?pyproject.toml,鏃?.py)
鈹溾攢 packages/
鈹? 鈹溾攢 api-client/    OpenAPI 鐢熸垚 TS client(schema.d.ts 7042 琛岀敓鎴愪唬鐮?+ index.ts)
鈹? 鈹溾攢 client-core/   鎵嬪啓 API client(728 琛?+ platform adapter
鈹? 鈹溾攢 design-tokens/ 璇箟 tokens(index.ts 291 琛?+ tokens.css)
鈹? 鈹斺攢 rule-spec/     JSON schema + fixtures(鏃?src)
鈹溾攢 tests/            unit(43) / integration(23) / contract(4) / isolation(2) / e2e(1) / fixtures / visual
鈹溾攢 scripts/          89 涓?.py 杩愮淮/涓€娆℃€ц剼鏈?鈹溾攢 docs/             16 涓瓙鐩綍(adr 2, engineering 16, governance 47, reality_audit 26, ...) + audit(鏂板缓)
鈹溾攢 infra/            docker/initdb/01-extensions.sql
鈹溾攢 schemas/          petaccessjson-0.1.example.json 绛?鈹溾攢 .github/          涓嶅瓨鍦?鍏ㄤ粨 0 CI 閰嶇疆)
鈹斺攢 鏍? pyproject.toml, package.json(pnpm workspace), docker-compose.yml(db/redis/minio),
      AGENTS.md, DECISIONS.md, GOAL.md, 浜у搧姣嶇増 md
```

鍚庣鍒嗗眰(app/):`api/v1`(17) / `core`(10) / `db`(5) / `models`(11) / `providers`(7) / `rulespec`(13) / `schemas`(8) / `services`(13) / `worker`(3) / `tools`(2)銆傚垎灞傝竟鐣屾竻鏅?绗﹀悎 UI鈫扐pp鈫扗omain鈫扨orts 鏂瑰悜銆?
---

## 3. 鏂囦欢鏁伴噺缁熻

| 绫诲埆 | 鏁伴噺 |
|---|---|
| backend app .py | 93 |
| tests .py(鏍?tests/) | 75(鍙?services/api/tests 4 涓枒浼奸噸澶嶈亴璐? |
| alembic migration versions | 24 |
| scripts .py | 89 |
| client-h5 .vue / .ts | 25 / 6 |
| admin .vue / .ts | 29 / 6 |
| uni-app .uvue / .ts | 9 / 1 |
| 鎵嬪啓 TS 澶ф枃浠?| client.ts 728 琛?>300) |
| 鐢熸垚 TS | schema.d.ts 7042 琛?璞佸厤) |

---

## 4. 琛屾暟 / 澶嶆潅搴﹁秴鏍?宸ョ▼瑙勮寖闂ㄧ鐜扮姸)

### 4.1 Python app(>250 / >300 琛?
- >300 琛?**24 涓?*;>250 琛?**27 涓?*
- 鏈€涓ラ噸:`api/v1/v05.py` **3103**銆乣db/seed.py` **1494**銆乣models/enums.py` **848**銆乣rulespec/v05_resolver.py` **747**銆乣api/v1/reality.py` **718**銆乣tools/reality_audit.py` **705**銆乣db/safety.py` **651**銆乣services/evidence_service.py` **649**
- migrations >250:4 涓?璞佸厤椤?浣?864ffcfc7ccb 杈?832 琛?

### 4.2 tests(>300 琛?
- **21 涓?*;鏈€澶?`unit/test_animal_scope.py` 752

### 4.3 鍓嶇 .vue/.uvue
- >150:**20 涓?*;>200:**16 涓?*
- 鏈€涓ラ噸:`client-h5/views/PlaceView.vue` 723銆乣ContributeView.vue` 700銆乣HomeView.vue` 427銆乤dmin `SpatialExtrasView.vue` 397銆乣OrganizationsView.vue` 389
- uni-app .uvue 鍏ㄩ儴 鈮?37,鍚堣

### 4.4 鍑芥暟涓庡鏉傚害
- 鍑芥暟浣?>60 琛?**168 涓?*(top: `db/seed.py:run_demo_seed` 1378銆乣v05_resolver.py:resolve` 467)
- McCabe 澶嶆潅搴?>10:**160 涓?*(top: `v05_resolver.py:resolve` **109**銆乣access_answer.py:build_access_answer` 36)
- 闆嗕腑鍦ㄦ牳蹇冨垽瀹氶摼璺?v05 绯诲垪 / access_answer / publish_gate)

---

## 5. 绫诲瀷绾緥

| 椤?| 鏁伴噺 | 鍒嗗竷 |
|---|---|---|
| `# noqa` | 194(scripts/tests 涓轰富;app 鍐?7) | worker/tasks.py 4, celery_app 2, seed 1 |
| `cast(` | 3 | core/idempotency銆乷bservability銆乺atelimit 鍚?1 |
| `# type: ignore` | 13(app 鍐?11) | **evidence_service.py 7**銆乤nswerability 2銆乨isputes 2 |
| `Any`(app 闈?import) | 49 娆′娇鐢?/ 65 鍚?import | coexistence_snapshot 13銆乤ccess_answer 11銆乻afety 8銆乻torage 7銆乼encent_map 6 |
| 鍓嶇 `any` | 4 | admin/RealityClaimsView.vue 脳3 + 鐢熸垚浠ｇ爜 1 |
| 鍓嶇 ts-ignore 瀹舵棌 | 0 | 鈥?|

缁撹:鍓嶇绾緥濂?鍚庣鏍稿績鍩熷瓨鍦ㄩ泦涓被鍨嬮€冮€?璇佹嵁/绛旀鍒ゅ畾),杩濆弽寮虹被鍨嬭鍒欍€?
---

## 6. TODO / 姝讳唬鐮?/ 鏃ュ織

| 椤?| 缁撴灉 |
|---|---|
| 瑁?TODO/FIXME/HACK/XXX(Python) | **0** |
| 瑁?TODO/FIXME/HACK/XXX(鍓嶇 src) | **0** |
| `console.log(` 鍓嶇 src | **0** |
| `print(` backend app | **10**(`db/safety.py` 7 鈥斺€?瀹夊叏鏁忔劅妯″潡鐢?print 鑰岄潪缁撴瀯鍖栨棩蹇? |
| 姝昏矾鐢?姝荤粍浠?| 鏈彂鐜版槑鏄炬璺敱;uni-app 涓?client-h5 瀛樺湪鍔熻兘閲嶅瀹炵幇(StatusBadge/ModeBar 涓ゅ) |
| i18n | 鏃?v0.1.0 涓嶈姹? |

---

## 7. 閰嶇疆 / Env / Secret

| 椤?| 缁撴灉 |
|---|---|
| 闆嗕腑 Settings | 鏈?`app/core/config.py` `class Settings(BaseSettings)`(pydantic-settings v2,env_file 鏍?.env) |
| 鏁ｈ惤 env 璇诲彇 | `os.getenv` 9 澶?app 1 + tests 1 + scripts 7);`import.meta.env` 2 澶勯噸澶嶉粯璁ゅ€?`/api/v1` |
| .env.example | 37 琛?鍏?dev 鍗犱綅鍊?**鏃犵湡瀹?secret**;.env 29 閿笌 example 瀹屽叏涓€鑷?|
| 鍙枒榛樿鍊?| config.py 鍐呭祵 dev JWT_SECRET / DB / S3 鏄庢枃榛樿(鐢熶骇闇€ fail-fast 瑕嗙洊) |
| Secret 鎵弿 | **鏃犱换浣曟壂鎻忛厤缃?*(gitleaks/detect-secrets 鍧囨棤);鍏ㄤ粨 1 涓枒浼?secret 鍛戒腑鏂囦欢:`docs/governance/FIRST_REAL_PUBLISH_BATCH_01A_CLOSURE.md`(**闇€浜哄伐鏍稿疄**) |
| docker-compose | db(postgis)/redis/minio,鍏ㄩ儴 `${VAR:-default}` 鎻掑€?鏃犵‖缂栫爜鍑嵁 |
| .gitignore | 瀹屾暣(鍚?.env銆佸瘑閽ュ悗缂€ *.p12/*.jks/*.pem/*.key銆乤gent 杈撳嚭鐩綍) |

---

## 8. CI / 鍙戝竷鍩哄缓

| 椤?| 鐜扮姸 |
|---|---|
| GitHub workflows | **涓嶅瓨鍦?*(鏃?.github) |
| 浠讳綍 CI 杞戒綋 | **0**(浠呮湰鍦?scripts/dev.sh test.sh lint.sh typecheck.sh + qa_all.ps1) |
| Secret 鎵弿 CI | 鏃?|
| Tauri / Android 宸ョ▼ | **涓嶅瓨鍦?*(鏃?src-tauri / Cargo.toml / tauri.conf.json / AndroidManifest)鈥斺€擯hase Q鈥揢 寰呭缓 |
| GitHub remote / release | 鏃?remote銆佹棤 tag(v0.5-quality-freeze 涓哄巻鍙叉湰鍦?tag) |
| docs/release | 6 涓枃妗?鏈€鏂?V09_FINAL_REPORT;`docs/audit` 鍘熶负绌?鏈 Phase A 濉厖) |

---

## 9. Version SSOT(Phase AE 棰勬)

| 浣嶇疆 | version |
|---|---|
| package.json(鏍? + apps/admin + client-h5 + client + packages/client-core + api-client | 0.1.0(6 澶勪竴鑷? |
| pyproject.toml(鏍? + services/api + services/worker | 0.1.0(3 澶勪竴鑷? |
| **packages/design-tokens/package.json** | **0.6.0-beta.1(鍞竴婕傜Щ)** |
| 鍙戝竷杞鏂囨。 | 宸插埌 v0.9-R1(浠ｇ爜鐗堟湰鍙锋湭闅忚疆娆℃帹杩? |

鐜扮姸:婕傜Щ鐐?1 澶?design-tokens);v0.1.0 鐩爣瑕佹眰 VERSION_DRIFT = 0,Phase AE 鏀跺彛銆?
---

## 10. Phase A 鍏ㄦ竻鍗曟牳瀵?鐩爣椤?鈫?鍙戠幇)

| 妫€鏌ラ」 | 缁撴灉 |
|---|---|
| 鏂囦欢鎬绘暟 / production source / tests / generated | 鉁?瑙?搂3 |
| >250 / >300 琛屼汉宸ユ簮鐮?| 鉁?24 涓?>300(app),21 涓?tests >300 |
| UI component >200 琛?| 鉁?16 涓?|
| function >60 琛?| 鉁?168 涓?|
| complexity >10 / >15 | 鉁?160 涓?>10(app 鍐?63 涓?>15 绾у€欓€? |
| deep nesting | 鏈崟鍒楁壂鎻?闅忓鏉傚害椤硅鐩?,Phase B gate 琛?|
| high parameter count | 鏈崟鍒楁壂鎻?闇€ Phase D 鎶芥煡) |
| circular dependency | 鏈彂鐜?app 渚濊禆鏂瑰悜鍗曞悜);Phase C 鐢ㄥ伐鍏烽獙璇?|
| duplicate domain model | services/api/tests 4 鏂囦欢涓庢牴 tests 鐤戜技閲嶅鑱岃矗(鏈‘璁ら噸澶嶉€昏緫) |
| any / cast / ignore / noqa | 鉁?搂5 |
| TODO/FIXME/HACK/TEMP | 鉁?0(鍓嶇涓庡悗绔? |
| dead route / dead component | 鏈彂鐜版璺敱;uni-app 涓?H5 鍙屽疄鐜版槸鏈€澶ч噸澶嶉潰 |
| dead env / dead dependency | 鏈彂鐜版槑鏄炬 env;渚濊禆姝婚」鏈崟鍒楁壂鎻?Phase B 琛? |
| duplicated config | 鍓嶇 env 榛樿鍊?2 澶勯噸澶?搂7);鍚庣 config 闆嗕腑鑹ソ |
| scattered process.env / os.getenv | 鉁?灏戦噺(9 + 2),鍙帶 |
| hardcoded colors | 鉁?28 澶勫叏鍦?uni-app(.uvue);client-h5/admin 鐨?.vue 涓?0(鍏ㄨ蛋 tokens) |
| hardcoded spacing | 鏈彂鐜?璁捐 tokens 宸茶鐩?client-h5/admin) |
| raw magic status | 鏈郴缁熸壂鎻?闇€ Phase D 鎶界偣);tokens 宸叉彁渚?STATUS_SEMANTICS |
| silent catch / broad exception | 鉁?17 瀹芥崟鑾?+ 18 鍙枒 silent catch(app 10) |
| logging privacy issues | 鏈彂鐜版晱鎰熸鏂囨棩蹇?db/safety.py 鐢?print 鏄粨鏋勬€ч棶棰?|
| N+1 / unbounded query | 鏈郴缁熸壂鎻?Phase D 闇€閫愭煡璇㈠璁? |
| synchronous heavy media | 鏈彂鐜?濯掍綋璧?storage provider,鏃犲悓姝ラ噸濯掍綋) |
| missing idempotency | 宸叉湁 core/idempotency.py;鍏跺唴閮?2 澶?silent catch 闇€淇?|
| unsafe transaction | 鏈彂鐜版槑鏄捐秺鐣?commit;Phase D 瀹¤ |
| API/client drift | schema.d.ts 涓虹敓鎴愪唬鐮?SSOT=OpenAPI);鎵嬪啓 client.ts 728 琛屼笌鐢熸垚 client 骞跺瓨,闇€ Phase G 鏍稿婕傜Щ |

---

## 11. 缁撹

- **鍋ュ悍闈?*:缁撴瀯鍒嗗眰娓呮櫚銆侀厤缃泦涓€侀浂瑁?TODO銆侀浂鍓嶇绫诲瀷閫冮€搞€乼okens 瑕嗙洊鍒颁綅銆乤lembic 鍗?head銆?env 鏃犵湡瀹?secret銆?- **涓昏椋庨櫓闈?*(鎸夊奖鍝嶆帓搴?:
  1. **鏃?CI / 鏃?secret 鎵弿 / 鏃?GitHub remote** 鈥斺€?鍙戝竷绠＄嚎瀹屽叏缂哄け(Phase AC 鍓嶄笉鍙彂甯?銆?  2. **瑙勬ā澶辨帶闆嗕腑鍦ㄦ牳蹇冨垽瀹氶摼璺?* 鈥斺€?v05.py 3103 琛屻€乺esolve() McCabe 109銆乻eed.py 1494 琛?鐩存帴杩濆弽 300 琛?60 琛?澶嶆潅搴﹂棬绂?Phase B/C/D 鏀跺彛)銆?  3. **閿欒鍚炲櫖浣嶄簬骞傜瓑/瀹夊叏杈圭晫** 鈥斺€?idempotency / security / worker 鐨?silent catch(Phase D 蹇呬慨)銆?  4. **绫诲瀷閫冮€搁泦涓湪璇佹嵁/绛旀鍒ゅ畾鍩?* 鈥斺€?evidence_service 7 澶?type:ignore銆?9 澶?Any 浣跨敤(Phase C/D 鏀跺彛)銆?  5. **uni-app 瀹㈡埛绔父绂讳簬璁捐浣撶郴** 鈥斺€?28 澶勭‖缂栫爜鑹层€佹棤 env/绂荤嚎/閿欒澶勭悊(Phase I/J 鏀跺彛)銆?- 涓嬩竴姝?Phase B(宸ョ▼瑙勮寖鑷姩 gate 钀藉湴) 鈫?Phase C(鏋舵瀯瀹¤) 鈫?Phase D(鍚庣 review),閫愰」浠?NOT RERUN 杞?CURRENT VERIFIED銆?