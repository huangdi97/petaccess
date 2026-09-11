# 跨端构建与平台差异说明（Phase 12 / GOAL §17）

## 架构

```text
@petaccess/client-core      ← 全部业务逻辑（API facade、会话、模式、答案合成）
        ↑ 共享                    ↑ 共享
apps/client (uni-app x)    apps/client-h5 (Vite+Vue3)
HBuilderX 构建 → 5 端       本地真跑 + Playwright E2E（G07/G17）
```

平台差异集中在两处，业务页面零 `if (platform)`：

1. `apps/client/platform/adapter.ts` — storage 与 API 基址（uni 全局对象 + 条件编译）。
2. `packages/client-core/src/platform/map.ts` — MapAdapter 接口；H5 端 MockMap 组件、
   uni-app x 端 `<map>` 组件、真实腾讯 JS SDK 均为该接口的实现（ADR-008）。

## 各端状态

| 端 | 状态 | 说明 |
|---|---|---|
| Web/H5 | **真跑** | apps/client-h5 已构建并经浏览器端到端验证（G07）；uni-app x H5 构建见 B-01 |
| 微信小程序 | 源码就绪 | manifest.json `mp-weixin` 段已配（含隐私接口声明）；构建需 AppID（B-02） |
| Android | 源码就绪 | HBuilderX 云/本地打包；签名与账号 B-03 |
| iOS | 源码就绪 | HBuilderX + Apple 证书（B-03） |
| HarmonyOS | 源码就绪 | uni-app x → DevEco Studio 流程（B-01/B-03） |

## 每端清单（GOAL §17）

- **permission**
  - 微信：`scope.userLocation` 用途说明已写入 manifest.json。
  - Android：`ACCESS_FINE_LOCATION` 由 uni-app x 构建清单生成，用途=附近查询/现场核验。
  - iOS：`NSLocationWhenInUseUsageDescription` 文案：位置仅用于附近查询与现场核验，不建立连续轨迹。
  - HarmonyOS：`ohos.permission.LOCATION`，同样文案。
- **privacy copy**：统一文案在 H5 Onboarding/Mine 与 uni-app x onboarding/mine 页：
  「位置仅用于附近查询与现场核验，不建立连续轨迹；小区只展示公共空间规则；
  服务犬身份仅由用户声明」。服务端永不存原始 GPS（ADR-012，仅分桶结果）。
- **map config**：mock provider 默认（`/ai/map/config`）；腾讯 Key 见 BLOCKERS B-04。
- **media config**：上传 ≤10MB 图片（服务端校验）；OCR 仅入审核队列。
- **build notes**：
  - H5 验证：`cd apps/client-h5 && pnpm build && pnpm preview`（API 地址经
    `VITE_API_BASE` 注入，dev 模式走 5174 代理）。
  - uni-app x 全端：HBuilderX 打开 `apps/client`（B-01 步骤）。
