# V020 RC Visual Baseline Manifest — Canonical Consumer Baseline Promotion

> 实现基准：`IMPLEMENTATION_BASE` = 本轮启动时 fetch 后的 v5 实现 commit（`70d670c…`，分支历史内可查；
> 本文不自我引用最终 HEAD，最终 HEAD 以 Git 查询为准）。

## 1. 结论

```text
CANONICAL_VISUAL_BASELINE_PROMOTION = PASS
VISUAL_BASELINE_PROMOTED = YES
VISUAL_BASELINE_DETERMINISM = PASS
```

- 只提升已人工冻结（PASS_FOR_RC）的 **Consumer** UI baseline：Home / Search / Map / Place /
  Reality / Evidence / Contribution + 受全局 tokens/shell 直接影响的 Consumer 截图。
- **Admin baseline 零改动**（`git status -- tests/visual/admin.spec.ts-snapshots/` 为空）。
- 与 v5 无关页面（mine / boundary / rule-trace / contribute 未产生 diff 的视图）未更新。

## 2. 方法（dry-run → expected diff → 只更新 Consumer）

1. 重新构建 `@petaccess/client-h5`（vue-tsc + vite build，PASS）。
2. 以当前 v5 code 跑 `playwright.visual.config.ts`（compare 模式）获得 dry-run 差异：
   - **EXPECTED_DIFF**：24 个 Consumer 用例失败，全部为 v5 冻结 UI 与旧 baseline 的像素差异
     （home/search/map/place/reality/offline/error/sheet），以及 3 类陈旧选择器断言
     （`answer-ordinary` / `trace-facts` 为 v0.2.4 之前的 testid，v5 已移除）。
   - **UNEXPECTED_DIFF**：0（Admin 14/14 直接 PASS，与 v5 无关页面无 diff）。
3. 将 Consumer spec 断言对齐冻结 v5 DOM（`place-unknown` 面板 / `section-answer` +
   `data-status` / `trace-observations`）——这是测试代码对齐已冻结 UI，**不是 UI 变更**。
4. 仅对 Consumer projects（h5-390 / h5-768 / h5-1440）执行 `--update-snapshots`：45/45 PASS。
5. 全量 compare 连续两轮：59/59 PASS ×2 → `VISUAL_BASELINE_DETERMINISM = PASS`。

## 3. 更新清单（24 张 PNG，全部 Consumer）

| file | old sha256 | new sha256 | reason | source human-review page |
| --- | --- | --- | --- | --- |
| `error-h5-390-win32.png` | bfdcee9320f4157d3987778be9d2c1b0db90a0645d43970e9fd6fd451b429127 | ef71b365a35884117b742dac84d57916acfc54e301a44a7e17c68847e0521d52 | 冻结 v5 UI 与旧 baseline 的预期差异（Error 统一错误态） | — |
| `home-empty-h5-390-win32.png` | 00b276f8db2fa91453a51a137f04ddd5eb01fe675c2efa7abff98c23566473d9 | 63888ba952f5904b311844b85fc57745f251d87abb91e1a36b2dfc51e50a7d64 | 冻结 v5 UI 与旧 baseline 的预期差异（Home 空态） | home_mobile |
| `home-fixture-h5-1440-win32.png` | e868b6f05115f55a9f888f761d6e657990bc57490ae2237052fff9d14069998c | 93eda56d406518702c8024e94c855fb9c952daec87408be697e2e982bc1e8ed9 | 冻结 v5 UI 与旧 baseline 的预期差异（Home 数据态） | home_desktop/home_mobile |
| `home-fixture-h5-390-win32.png` | 23ec0fa85b7873639657e4a921f4515596ed92ce0134dd1656c69c854cea8b15 | b02c32ac233073d92f68bdf5dc44273da427703aa6fbce6f3537cbe54d2c414b | 冻结 v5 UI 与旧 baseline 的预期差异（Home 数据态） | home_desktop/home_mobile |
| `home-fixture-h5-768-win32.png` | e73535411c525cc01f3a2a99f8fb01187d051961487ac8c8c1c2003806395613 | a3f435147b70fa42dd48c8d33ea05545fde069c2803fabe92f5a433ba838af48 | 冻结 v5 UI 与旧 baseline 的预期差异（Home 数据态） | home_desktop/home_mobile |
| `map-h5-1440-win32.png` | 226e5f659727786e8299e305a99381d82e9d9610c474442154222d28fedc761c | a3dfad9d505e78deb849f270e6969c552e7853434dc7f3d06216f9f9507790e2 | 冻结 v5 UI 与旧 baseline 的预期差异（Map） | map_desktop/map_mobile_ready |
| `map-h5-768-win32.png` | c4fe5cdaaa3d3c1eed378e1b8e5499bf80bbafd5a606bd8f8077edccf523cf8d | 180f4af43b9967e9979393247b6f697315742eea662dcd4955eef0575dc0a428 | 冻结 v5 UI 与旧 baseline 的预期差异（Map） | map_desktop/map_mobile_ready |
| `map-sheet-h5-390-win32.png` | 9279f1ccf9510466beee0ba7bf831a45fc3d07f883d71e2dc6a0117dacfb73b2 | da893669faa5fa037eb52b3f092f8765666729f7ea0d50ef3e6bdb5f3a5cb279 | 冻结 v5 UI 与旧 baseline 的预期差异（Map） | map_desktop/map_mobile_ready |
| `map-split-h5-1440-win32.png` | 226e5f659727786e8299e305a99381d82e9d9610c474442154222d28fedc761c | a3dfad9d505e78deb849f270e6969c552e7853434dc7f3d06216f9f9507790e2 | 冻结 v5 UI 与旧 baseline 的预期差异（Map） | map_desktop/map_mobile_ready |
| `map-split-h5-768-win32.png` | c4fe5cdaaa3d3c1eed378e1b8e5499bf80bbafd5a606bd8f8077edccf523cf8d | 180f4af43b9967e9979393247b6f697315742eea662dcd4955eef0575dc0a428 | 冻结 v5 UI 与旧 baseline 的预期差异（Map） | map_desktop/map_mobile_ready |
| `offline-h5-390-win32.png` | 993e09853985733915c09a89e62356d0544e41f6e706e7a089ebf0e3539fec05 | 9936e27401e6241a38f1eb0e6a98eac36eb6a00a88e3a913a0383ac57f3e5efd | 冻结 v5 UI 与旧 baseline 的预期差异（Offline 全局离线横幅） | — |
| `place-conditional-h5-1440-win32.png` | 7633a6717f196ba1d9b3d956945ead457d2c6603b4789a730f273be5c3a1619c | 64b4d83900426fdb9e673ac05c76f45b2e67a908e65948f9cd6bd286f1a98f78 | 冻结 v5 UI 与旧 baseline 的预期差异（Place 有条件结论） | place_desktop_overview/place_mobile_overview |
| `place-conditional-h5-390-win32.png` | c6e5468f941eacf28b9312eb46366d37cdfc5fa5e5ed4238cfc465aa74f59963 | 2c7c834409b774ec8cfa00809fd782b503577e8443a3a50ce61651bbc0d20d7f | 冻结 v5 UI 与旧 baseline 的预期差异（Place 有条件结论） | place_desktop_overview/place_mobile_overview |
| `place-conditional-h5-768-win32.png` | d9342ac9e7c324b82740f05b08e3d7f80660882ec038dab95b62603ea40d566e | f3db505105c162e996300aef8e82e1b12ad5b747bbda2230d1f9a04fb4b762a1 | 冻结 v5 UI 与旧 baseline 的预期差异（Place 有条件结论） | place_desktop_overview/place_mobile_overview |
| `place-unknown-h5-1440-win32.png` | de9cf7b832ab5d68eaf40fe52c9c56ddded372d349ece91834ffb44ae2ea25c0 | e7570fdafe727b52865af5bddb6244468e4266bbad1976ceac72687df2587224 | 冻结 v5 UI 与旧 baseline 的预期差异（Place 信息不足） | place_desktop_unknown |
| `place-unknown-h5-390-win32.png` | b6296e5ac3e955ce6ce885bc9d4bf03204c65bf3f3258bb097b297ab3d25a92e | 463361546b0a164c7590d7b7bb642a27f73e04d4e91650606d611d03bb30722c | 冻结 v5 UI 与旧 baseline 的预期差异（Place 信息不足） | place_desktop_unknown |
| `place-unknown-h5-768-win32.png` | faf3739bb749f54c281a394cad1acbf598d9977e9d360dfc1810511791ec9405 | 34ac99f9cb3dfbc120a6ab1b8cfb83f94fea2360ad0d7a822a346c410329d7da | 冻结 v5 UI 与旧 baseline 的预期差异（Place 信息不足） | place_desktop_unknown |
| `reality-trace-h5-1440-win32.png` | 079fdfb56706d7d9dcc1c461d7e7125d06885ae067d448008f1b647605a716d9 | dd74d36e74cdc672b5841740e8b5bd4cc6d16ab0e87f7d25dbfdc8d9866f12c1 | 冻结 v5 UI 与旧 baseline 的预期差异（Reality 现场轨迹） | reality_* |
| `reality-trace-h5-390-win32.png` | ea81c917bfc969678d53643eb6e31898f61670d09bd2bc87fed0ca77cc105b60 | 689680bd3ce5415cf52e0ae41e990a9bc711e34d169601caf8b1314d953bc331 | 冻结 v5 UI 与旧 baseline 的预期差异（Reality 现场轨迹） | reality_* |
| `reality-trace-h5-768-win32.png` | 1e0b576f7d6c64ee4d77ea8d70369574e950b691efbb9c160a682f2ec54dda98 | cf47ad2dcec87b8c5569c1529b7ccb36d72cc699d6939719b6ae11724b854b32 | 冻结 v5 UI 与旧 baseline 的预期差异（Reality 现场轨迹） | reality_* |
| `search-empty-h5-390-win32.png` | 6d59035c8d7fd21fda93ec9ba2032ff863f85f9dd3cb7fd6ed074dbe7868e9c2 | d313b65491833c1b06b9ae5660181d956a70b3820e27f4a75d1d9f39ff967b50 | 冻结 v5 UI 与旧 baseline 的预期差异（Search 空态） | search_desktop_empty |
| `search-empty-h5-768-win32.png` | 2bee33ff3ce0ee43025b5f1e261d67d75f92f48cd5196b9b0b372153a129924a | a3c82e9d5802b1b8000f9c754698c4e73ed4f7e88e3da3f24907a68d6873d1ed | 冻结 v5 UI 与旧 baseline 的预期差异（Search 空态） | search_desktop_empty |
| `search-fixture-h5-390-win32.png` | e8105ebf7674a13e2d3d5f3c6a3850c14e11e9c0bf315c62a9250ab9abd75369 | dc59f297ffecef428575dd5f2cd780f44cd5316e2841b5ad1990e23f459f4761 | 冻结 v5 UI 与旧 baseline 的预期差异（Search 数据态） | search_desktop_ready/search_mobile_ready |
| `search-fixture-h5-768-win32.png` | 00b7172da1c325a719dc0f6a2f828bd1c4dda8700e43fe94c5ac9788c2ff0174 | 93db88f02c530c71ecfee27e5e0145d789c2c3e0ea0c9771452935df6040e9ac | 冻结 v5 UI 与旧 baseline 的预期差异（Search 数据态） | search_desktop_ready/search_mobile_ready |


## 4. 确定性 / 稳定性说明

- 视觉套件使用固定视觉数据库 `petaccess_visual`（每次运行前 drop + reseed demo 数据）、
  冻结时钟（2026-09-15T04:00:00Z）、motion frozen + reduced-motion。
- 两次全量 compare 运行结果完全一致（59/59），无 time/animation/random/font drift。
- 更新的 PNG 全部来自真实 DOM capture（fixtures 断言页面状态后才截图，杜绝错误状态 baseline）。
