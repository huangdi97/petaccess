# V010_TECH_DEBT_REGISTER.md

# v0.1.0 Phase A �?閹垛偓閺堫垰鈧櫣娅ョ拋鏉垮斀

> 閺夈儲绨?docs/audit/V010_REPOSITORY_BASELINE.md(2026-09-23 閸欘亣顕伴惄妯煎�?
> 閻樿埖鈧?OPEN(瀵板懍鎱?/ IN_PROGRESS / DONE / WONTFIX(鐠佹澘缍嶉崢鐔锋�?
> 濮ｅ繘銆嶉崥?ID / severity / file / problem / risk / fix / verification / status

Severity:CRITICAL(閸欐垵绔烽梼璇差�? / HIGH(閸欐垵绔烽崜宥呯箑娣? / MEDIUM(鎼存柧鎱? / LOW(閸欘垳绱?

---

## 閸氬海顏?services/api)

| ID | Sev | File | Problem | Risk | Fix | Verification | Status |
|---|---|---|---|---|---|---|---|
| TD-001 | HIGH | app/api/v1/v05.py(3103 �? | God module,鏉╂粏绉?300 鐞涘瞼鈥栨稉濠囨�?HTTP/domain/鐟欏嫬鍨崝鐘烘祰濞ｉ攱�?| 閸ョ偛缍婇棃銏犮亣閵嗕焦妫ゅ▔鏇炲礋閸忓啫瀵插ù瀣�?gate �?FAIL | 閹稿浜寸拹锝嗗閸?鐠侯垳鏁遍挅鍕�?+ service/domain 閹峰棗鍤?_load_layered_rules 缁涘銇囬崙鑺ユ殶閹峰棗�?| 閺傚洣娆?<300 �?ruff/mypy/pytest 閸忋劎璞?gate FAIL閳墾ASS | OPEN |
| TD-002 | HIGH | app/rulespec/v05_resolver.py:resolve(467 �?McCabe 109) | 閸楁洖鍤遍弫鏉款槻閺夊倸瀹虫潻鍥彯,閺嶇绺?AI 閸掋倕鐣鹃柧鎹愮�?| 閸掋倕鐣鹃柅鏄忕帆閺冪姵纭剁€光剝鐓?濞村鐦?娴犺缍嶉弨鐟板З妤傛﹢顥撻梽?| 閹峰棗鍨庢稉铏圭摜閻ｃ儵�?鐏忓繐鍤遍弫?娣囨繃瀵旂悰灞艰礋娑撳秴褰?behavior-preserving) | resolve 閹峰棗鍨庨崥搴″礋閸戣姤鏆?�?0 �?golden fixtures 閸ョ偛缍?| OPEN |
| TD-003 | HIGH | app/db/seed.py(1494 �?run_demo_seed 1378 �? | 缁夊秴鐡欓弫鐗堝�?God function;�?demo 閸︾儤澧?| v0.1.0 release 缁備焦顒?demo seed �?release path;seed �?release 閺佺増宓佺捄顖氱窞闂団偓闂呮梻顬?| �?seed 閺佺増宓佹稉?fixture/JSON;release 鐠侯垰绶炴稉宥呭鏉?seed;閺嶅洩顔?dev/test-only | release 閺嬪嫬缂撴稉宥呮�?seed 閺佺増宓?閺傚洦銆傞梾鏃傤瀲婢圭増�?| OPEN |
| TD-004 | HIGH | app/services/evidence_service.py(649 �?7 �?type:ignore) | 鐠囦焦宓侀崺鐔哥壋韫囧啩绗熼崝锛勮閸ㄥ鈧啴鈧?+ 閺傚洣娆㈢搾鍛�?| 鐠囦焦宓侀崚銈呯暰閺冪姷琚崹瀣墡妤?缂傛牞鐦ч張鐔兼晩鐠囶垰褰夋潻鎰攽閺冨爼鏁婄�?| 鐞涖儳琚崹瀣侀崹瀣Х�?ignore;閹峰棗鍨庨張宥呭閼卞矁�?| type:ignore�?;mypy 閸忋劎璞?| OPEN |
| TD-005 | MEDIUM | app/core/idempotency.py(2 �?silent catch) | 楠炲倻鐡戦柨顔界閻炲棗銇戠拹銉潶闂堟瑩绮崥鍛婃�?| 楠炲倻鐡戞潏鍦櫕婢惰鲸鏅ユ稉鏃€妫ょ憴鍌涚�?鏉╂繂寮界憴鍕�?�?6 | 閺勬儳绱?domain error + 缂佹挻鐎崠鏍ㄦ）韫?婢惰精瑙﹂崣顖炲櫢鐠?| silent catch�?;楠炲倻鐡戦崶鐐茬秺濞村�?| OPEN |
| TD-006 | MEDIUM | app/core/security.py(1 �?silent catch) | 鐎瑰鍙忔潏鍦櫕闁挎瑨顕ょ悮顐︽饯�?| 鐎瑰鍙忔径杈Е娑撳秴褰茬憴鍌涚�?| 閺勬儳绱￠弮銉ョ�?+ fail 鐠囶厺绠?鐎瑰鍙忛崶鐐茬秺濞村�?| 濞村鐦憰鍡欐磰鐎瑰鍙忔径杈Е鐠侯垰�?| OPEN |
| TD-007 | MEDIUM | app/worker/tasks.py(5 婢跺嫬顔旈幑鏇″箯) | 闂冪喎鍨禒璇插鐎硅姤宕熼�?闁插秷鐦拠顓濈疅閼村棗�?| 娴犺濮熸径杈Е閻樿埖鈧椒绗夐崣顖欎繆 | 缁墽鈥樺鍌氱�?+ Celery 闁插秷鐦粵鏍殣閺勬儳绱￠�?| 娴犺濮熸径杈Е濞村鐦憰鍡欐�?| OPEN |
| TD-008 | MEDIUM | app/db/safety.py(651 �?7 �?print) | 鐎瑰鍙忛弫蹇斿妳濡€虫健�?print 閼板矂娼紒鎾寸€崠鏍ㄦ）�?閺傚洣娆㈢搾鍛�?| 閺冦儱绻旀稉宥呭讲濡偓缁鳖潿鈧焦妫ょ痪褍鍩?gate 鐡掑懏鐖?| �?logging;閹峰棗鍨庡Ο鈥虫健;娣囨繄鏆€鐎瑰鍙忔稉宥呭綁闁插繑鏁為柌?| logging 閺囨寧宕?閺傚洣娆?<300 | OPEN |
| TD-009 | MEDIUM | app 閸忋劌鐓?49 �?Any 娴ｈ法鏁?�?import) | 缁鐎风痪顏勭伐鏉╂繂�?coexistence_snapshot 13閵嗕工ccess_answer 11 閺堚偓闂嗗棔�?| 閸掋倕鐣鹃柧鎹愮熅閺冪姷琚崹瀣╃箽閹?| 闁劖鏋冩禒鎯八?typed model;unjustified Any �?0 | mypy strict 閹殿偅寮?Any 瑜版帡娴?| OPEN |
| TD-010 | MEDIUM | app 24 娑擃亝鏋冩禒?>300 �?�?enums.py 848閵嗕沟odels/v05.py 499) | 閹靛綊鍣虹憴鍕佺搾鍛�?| 缂佸瓨濮㈤幋鎰拱妤傛ǜ鈧線姣﹀ù瀣�?| 閹稿浜寸拹锝嗗閸?閸忓牆顦╅悶?gate 韫囧懘娓堕惃鍕付鐏忓繘�? | gate FAIL閳墾ASS | OPEN |
| TD-011 | MEDIUM | services/api/tests 4 閺傚洣娆㈡稉搴㈢�?tests/ 閻ゆ垳鎶€闁插秴顦查懕宀冪煑 | 濞村鐦崣宀€娲拌ぐ?閼卞矁鐭楁稉宥嗙�?| 濞村鐦鍌溞╅妴浣烘樊閹躲倖璐╂稊?| 閸氬牆鑻熼崚鐗堢�?tests/ 閹存牗妲戠涵顔跨珶閻?閸掔娀娅庨柌宥咁槻 | 濞村鐦崗銊╁�?PASS;閺冪娀鍣告径宥嗙ゴ鐠囨洖鎮?| OPEN |
| TD-012 | LOW | app/config.py 閸愬懎绁?dev JWT/DB/S3 姒涙顓婚崐?| 閻㈢喍楠囬悳顖氼暔缂傜儤妯夊�?fail-fast | 閻㈢喍楠囩拠顖滄�?dev 閸戭厽宓?| 閻㈢喍楠囧Ο鈥崇础(AAPP_ENV=production)鐎佃鏅遍幇鐔煎帳缂冾喖宸遍崚鑸垫▔瀵繑褰佹笟?缂傚搫銇戦崡鍐叉儙閸斻劌銇戠�?| 閻㈢喍楠囧Ο鈥崇础閸氼垰濮╁ù瀣�?| OPEN |
| TD-013 | LOW | migrations/versions/e9f2c1d4a5b6_*.py | UTF-8 BOM | 宸ュ叿閾捐В鏋愬け�?| 鍘婚�?BOM锛圡1 宸插�? 鍐呭涓嶅彉�?| ast 鍙В�? alembic �?drift | DONE (M1) |
| TD-014 | LOW | scripts/(89 娑擃亙绔村▎鈩冣�?鏉╂劗娣懘姘拱) | 婢堆囧櫤妤傛ê顦查弶鍌氬娑撯偓濞嗏剝鈧嗗壖閺堫剚绮搁悾娆庣波鎼?| 鐎孤ゎ吀閸ｎ亪鐓堕妴浣烘樊閹躲倛绀嬮幏?| 瑜版帗銆傞懛?scripts/archive 閹存牗妲戠涵顔界垼鐠侀绔村▎鈩冣�?娑撳秴寮稉?production gate | gate 閹烘帡娅庨懘姘拱閻╊喖�?閺傚洦銆傜拠瀛樻�?| OPEN |
| TD-028 | LOW | services/api/app �?FastAPI/Celery/中间�?装饰器注册入口（api/v1/*、main.py、worker/*�?| 文本语料�?dead-code 扫描无法�?@router.get / @app.get / @celery_app.task 装饰器看出注册引用，误报�?dead-code | 非真实死代码：装饰器即运行期引用（FastAPI 聚合、Celery 字符串任务名、中间件注入�?| 按符号逐条�?gate_exemptions.json 注册（rule=dead-code, symbol=<name>），引用�?TD；不允许整路径豁�?| gate PASS; dead-code 无未豁免 FAIL | DONE (M1 v0.2.0) |
| TD-029 | LOW | models/enums.py StaffAwarenessState/FacilityPurposeState; providers/factory.py get_map_provider | 文档化领域枚举与规划中的 Map adapter 工厂尚未接线，文本扫描报 dead-code | 删除会丢失文档化领域词汇（addendum PHASE 9/10 �?Map 计划�?| 按符号逐条注册（rule=dead-code），接线随对�?phase 落地 | gate PASS; 接线后移除豁�?| DONE (M1 v0.2.0) |
---

## 閸撳秶顏?apps/, packages/)

| ID | Sev | File | Problem | Risk | Fix | Verification | Status |
|---|---|---|---|---|---|---|---|
| TD-015 | HIGH | client-h5 PlaceView.vue(723)/ContributeView.vue(700)/HomeView.vue(427) | God Component,鏉╂粏绉?200 鐞涘瞼瀛╃�?| 娑撳秴褰茬紒瀛樺Б;Empty-First(Phase H)閺€鐟板З妤傛﹢顥撻梽?| 閹稿灏崸妤佸缂佸嫪�?+ composable 閹剁晫顬囨稉姘闁槒�?| 缂佸嫪娆?�?00;vue-tsc/build PASS;鐟欏棜顫庨崺铏瑰殠閸ョ偛�?| OPEN |
| TD-016 | MEDIUM | admin 6 娑擃亣顫嬮崶?250�?00 �?SpatialExtrasView 397閵嗕副rganizationsView 389 �? | 缂佸嫪娆㈢憴鍕佺搾鍛�?| 缂佸瓨濮㈤幋鎰拱妤?| �?composable/鐎涙劗绮嶆禒?| 缂佸嫪娆?�?00(admin �?release 娑撹楠囬崫?閸欘垰娆㈤崥搴濈稻闂団偓閺€璺哄�? | OPEN |
| TD-017 | MEDIUM | packages/client-core/src/api/client.ts(728 鐞涘本澧滈崘? | 閹靛鍟?API client 娑撳海鏁撻幋?schema.d.ts 楠炶泛鐡?| API contract 濠曞倻些(Phase G) | 缂佺喍绔撮崚鎵晸閹?client 閹存牗妲戠涵?adapter;閺嶇顕?OpenAPI SSOT | contract 濞村鐦?濠曞倻些濡偓濞?| OPEN |
| TD-018 | MEDIUM | apps/client(uni-app)28 婢跺嫮鈥栫紓鏍�?hex �?| 閸烆垯绔村〒鍝ヮ瀲娴?design-tokens 閻ㄥ嫬顓归幋椋庮�?| 鐟欏棜顫庢稉宥勭閼?Phase J 鐟曚焦鐪?0 绾剛绱惍浣藉�?| 瀵洖鍙?tokens 缁涘鐜弰鐘茬�?閺囨寧宕叉稉?CSS 閸欐﹢鍣?| uni-app 绾剛绱惍浣藉閳? | OPEN |
| TD-019 | MEDIUM | 閸忋劌澧犵粩顖涙�?errorCaptured/errorHandler;admin 閺冪姷顬囩痪?缂冩垹绮堕柨娆掝�?UI | 閺冪姷绮烘稉鈧柨娆掝嚖鏉堝湱鏅?| 瀵倸鐖堕弮鍓佹鐏?鐟佹悂鏁婄拠?Phase L 鐟曚焦鐪板В蹇涖€?error/offline 閻樿埖鈧?| 瀵ゅ搫鍙忕仦�?error boundary + 缂冩垹绮堕柨娆掝嚖缂佸嫪�?閹恒儱鍙?admin | 濞夈劌鍙嗛柨娆掝�?�?閺勫墽銇氶崣瀣偨妞ょ敻娼惂钘夌潌 | OPEN |
| TD-020 | MEDIUM | 閺冪姷瀚�?EmptyState 缂佸嫪娆?"閺嗗倹妫?閺傚洦顢嶉弫锝堟�?�?2 閺傚洣娆?| Empty 鐠囶厺绠熸稉宥囩埠娑撯偓;Phase K P0 | 缁岃櫣濮搁幀浣筋嚖鐎佃偐鏁ら�?| �?EmptyState 缂佸嫪娆?design-tokens PAGE_STATES 瀹告彃鐣炬稊澶庮嚔娑?,缂佺喍绔撮弬鍥�?| Empty 閻晠妯�?0 place/rule/reality)�?PASS | OPEN |
| TD-021 | LOW | import.meta.env 2 婢跺嫰鍣告径宥夌帛鐠併倕鈧?`/api/v1`;�?env 鐏忎浇顥婂Ο鈥虫健 | 闁板秶鐤嗛弫锝堟�?| 楠炲啿褰撮柅鍌炲�?Desktop/Android)�?base URL 濞ｈ渹璐?| 瀵ゆ椽娉︽稉?env 濡€虫�?platform adapter) | 閸楁洜鍋ｉ柊宥囩�?Tauri/Capacitor 闁倿鍘ゅù瀣�?| OPEN |

| TD-030 | LOW | client-h5 consumer components >200 lines (DecisionInspector/MapResultPane/PlaceOverviewPane/PlaceRulesPane/RealityEventLog/MapSelectedSheet/MockMap/DesktopRail/EvidenceProvenance/PlaceResultRow/ContributeRealityForm/ContributeSignageForm/RealityPanel/ContributeView/RealityTraceView) | frozen v5 consumer UI; RC round forbids UI refactor (visual baseline freeze) | split after release; keep visual determinism | gate exemptions.json + visual suite PASS | OPEN |
---

## 闁板秶鐤?/ CI / 閸欐垵绔?
| ID | Sev | File | Problem | Risk | Fix | Verification | Status |
|---|---|---|---|---|---|---|---|
| TD-022 | CRITICAL | .github/workflows | �?CI | 鍙戝竷绠＄嚎缂哄�?| Phase AC: pr-ci + release-ci 钀藉湴 | YAML 鍚堟�? 杩滅▼鎵ц寰?remote+鎺堟�?| DONE (M1/M10, 杩滅▼鎵ц�?BLOCKED) |
| TD-023 | HIGH | docs/governance/FIRST_REAL_PUBLISH_BATCH_01A_CLOSURE.md | 閻ゆ垳鎶�?secret 濡€崇础閸涙垝鑵?閸婂吋婀拠璇插�? | 閼汇儱鎯堥惇鐔风杽閸戭厽宓侀崚娆愮�?| 娴滃搫浼愰弽绋跨杽閸愬懎�?閼汇儱鎯?secret 缁斿宓嗘潪顔藉床楠炲爼鍣搁崘娆掝嚉閺傚洣娆?濞撳懐鎮?git history 閼汇儱鍑￠幓鎰�?| gitleaks/detect-secrets 閸忋劋绮?0 閸涙垝鑵?| OPEN |
| TD-024 | HIGH | 鍏ㄤ�?secret 鎵�?| 鏃犺嚜鍔ㄩ槻�?| 娉勬紡鏃犳劅�?| scan_secrets.py + CI 鎺ュ�?| 0 findings | DONE (M1) |
| TD-025 | LOW | packages/design-tokens version 0.6.0-beta.1 | SSOT 婕傜Щ | VERSION_DRIFT>0 | 缁熶�?0.1.0 + check_version_drift.py gate | VERSION_DRIFT = 0 | DONE (M9) |
| TD-026 | LOW | README.md(73 �?pytest 209 鏉╁洦婀? | 閺傚洦銆傛潻鍥ㄦ�?閺堫亝褰侀�?v0.9/Reality/閺傜増鐏﹂弸?| 鐠囶垰顕辩拠鏄忊�?| Phase AB 闁插秴鍟?README(�?0.1.0 Early Preview 鐎规矮缍? | README 閸愬懎顔愭稉搴ｅ箛閻樻湹绔撮�?| OPEN |
| TD-027 | LOW | docs/adr �?ADR-030/031 閻欘剛鐝涢弬鍥︽�?ADR-001~029 閸愬懎绁?DECISIONS.md | ADR 缂傛牕褰挎潻鐐电敾閹囨浆閺傚洦銆傜紒瀛樺Б | 閸愬磭鐡ラ梾鎹愭嫹濠?| 閸欘垱澹掗柌蹇擃嚤閸戣櫣瀚�?ADR 閺傚洣娆?闂堢偛褰傜敮?blocker) | docs/adr 缂傛牕褰挎潻鐐电�?| OPEN |

---

## 濮瑰洦鈧?
| Severity | 閺佷即鍣?| 鐠囧瓨妲?|
|---|---|---|
| CRITICAL | 1 | TD-022 �?CI(閸欐垵绔烽梼璇差�? |
| HIGH | 8 | TD-001/002/003/004/015/023/024 + 閸╄櫣鍤庢稉顓☆潐濡ょТ閺嶅洭銆?|
| MEDIUM | 13 | TD-005~011�?16~020 �?|
| LOW | 5（TD-013/025 �?DONE; �?TD-012/014/021/026/027�?|

婢跺嫮鐤嗘い鍝勭�?鐎靛綊缍?master goal Phase 妞ゅ搫绨?:
1. Phase B �?gate �?TD-001/002/003/008/010/015/016 鏉╂稑鍙嗛懛顏勫З FAIL 閸掓銆?閸忓牐顔€閻滄壆濮搁弰鐐偓褍�?
2. Phase C/D 閸氬海顏柌宥嗙�?�?TD-001/002/004/005/006/007/008/009/011/012
3. Phase I/J/K/L 閸撳秶顏?�?TD-015/016/018/019/020/021
4. Phase AC CI �?TD-022;Phase F/Z 鐎瑰鍙?�?TD-023/024
5. Phase AE �?TD-025;Phase AB �?TD-026/027

> �?濮ｅ繘銆嶆穱顔碱槻闁棄绻€妞ょ粯婀佹宀冪槈(verification �?,娑撳秴鍘戠拋?閺€鐟扮暚閸?PASS"�?