# BLOCKERS.md

Template per GOAL §2: 缺什么 / 为什么 / 用户要做什么 / 拿到后执行什么 / 影响哪个 Gate。

## B-01 uni-app x 全端构建需要 HBuilderX
- Type: 工具链（GUI IDE，无法无人值守安装/驱动）
- Affected gate: G18 微信 / G19 Android / G20 iOS / G21 HarmonyOS（uni-app x 编译产物）
- Missing external input: HBuilderX（含 uni-app x 编译插件）；HarmonyOS 端另需 DevEco Studio
- Why code cannot complete it: uni-app x 官方构建链路绑定 HBuilderX GUI（无 npm CLI，
  `dcloudio/uni-preset-vue` 无 vite-uts 分支）；HBuilderX 下载入口对脚本访问受限
  （dcloud.io 403/404），且安装属于系统级变更，需用户亲自执行。
- Work already completed: 完整 uni-app x 源码工程（apps/client：manifest.json、pages.json、
  App.uvue、7 个页面 .uvue、平台 adapter）；全部业务逻辑在平台无关的
  @petaccess/client-core（与 H5 验证应用共享，已真跑）。
- Exact user action:
  1. 从 https://www.dcloud.io/hbuilderx.html 下载并安装 HBuilderX（4.8+）；
  2. HBuilderX → 工具 → 插件安装 → 安装「uni-app x 编译插件」；
  3. 文件 → 打开目录 → 选择 `apps/client`；
  4. 运行 → 运行到浏览器 → Chrome（H5）；或 运行到微信开发者工具 / 真机。
- Exact verification after resolution:
  `cd apps/client && HBuilderX 运行 H5` → 页面与 apps/client-h5 行为一致；
  微信端需 AppID（见 B-02）；Android/iOS/HarmonyOS 需对应签名/账号（B-03）。
- 影响：G18/G19/G20/G21 在 HBuilderX 就绪前标记 BLOCKED_EXTERNAL；
  H5 行为已由 apps/client-h5 + Playwright（G17）真实验证。

## B-02 微信小程序 AppID / 类目 / 隐私接口审批
- Type: 第三方账号凭证
- Affected gate: G18
- Missing external input: 微信小程序 AppID（manifest.json `mp-weixin.appid` 为空），
  类目审核、`getLocation` 隐私接口审批
- Why code cannot complete it: 需要注册微信小程序主体并过审，无法自动化。
- Work already completed: manifest.json 已含 `requiredPrivateInfos` 与位置用途说明；
  代码不依赖真实 AppID（urlCheck=false，mock provider）。
- Exact user action: 注册小程序 → AppID 填入 apps/client/manifest.json → 微信开发者工具导入 apps/client。
- Exact verification after resolution: 微信开发者工具编译预览通过。
- 影响：G18 BLOCKED_EXTERNAL。

## B-03 移动端签名与开发者账号（Android 上架 / iOS 证书 / HarmonyOS 签名）
- Type: 第三方账号与证书
- Affected gate: G19 / G20 / G21
- Missing external input: Android 签名 keystore 与应用市场账号；Apple Developer 账号与证书；
  华为开发者账号与发布证书（DevEco Studio）
- Why code cannot complete it: 证书/账号必须由主体持有者申请。
- Work already completed: uni-app x 源码工程就绪；平台差异集中在 platform adapter。
- Exact user action: 申请对应账号/证书后，在 HBuilderX 中按标准流程云打包/本地打包。
- Exact verification after resolution: 对应平台安装包真机安装启动。
- 影响：G19/G20/G21 BLOCKED_EXTERNAL。

## B-04 腾讯地图 Key
- Type: 第三方服务凭证
- Affected gate: G08（地图真实数据）
- Missing external input: TENCENT_MAP_KEY_CLIENT / TENCENT_MAP_KEY_SERVER（.env）
- Why code cannot complete it: Key 需腾讯位置服务账号申请。
- Work already completed: MapProvider 抽象 + Mock 实现（synthetic 场所/图钉/多边形渲染），
  拿到 Key 后只需在 provider factory 切换（factory.py / map adapter），业务逻辑零改动。
- Exact user action: 申请 Key → 填 .env → FEATURE_REAL_MAP=true → 重启 API。
- Exact verification after resolution: /ai/map/config 返回 tencent provider；前端地图渲染真实底图。
- 影响：G08 以 Mock 实现 PASS（viewport/search/zone 渲染与业务逻辑真跑），真实底图留待 Key。

## B-05 真实 AI Provider Key（vision/OCR）
- Type: 第三方服务凭证
- Affected gate: G09（真实识别）
- Missing external input: AI_API_KEY + 具体 provider 选型
- Why code cannot complete it: 无 Key 无法调用真实模型。
- Work already completed: VisionProvider/OCRProvider 接口 + Mock（确定性输出）；
  /ai/* 端点含"用户确认"契约（服务犬/体重永不由图片认定）。
- Exact user action: 选型（如通义/腾讯云）→ AI_API_KEY 填 .env → FEATURE_REAL_AI=true →
  在 app/providers/factory.py 落地对应 adapter（接口已冻结）。
- Exact verification after resolution: /ai/pet-vision 返回真实建议且要求用户确认。
- 影响：G09 以 Mock PASS，真实识别 BLOCKED_EXTERNAL。

## B-06 OAuth / 短信（登录方式扩展）
- Type: 第三方凭证
- Affected gate: 无（当前账密登录已覆盖 MVP 闭环）
- Missing external input: 微信开放平台/Apple/华为 OAuth 凭证；短信签名
- Work already completed: JWT 会话体系（注册/登录/REST），token Provider 注入。
- 影响：扩展登录方式时补充。

## B-07 生产域名 / 备案 / 法务合规确认
- Type: 主体资质与法律确认
- Affected gate: G22/G23 的上线部分（不影响本地 RC）
- Missing external input: 域名、ICP 备案、隐私政策主体、地图业务边界合规确认（design #43）
- Work already completed: 合规等待项均以 feature flag / Mock 隔离（design #43 第 10 条）。
- 影响：上线部署时补充。
