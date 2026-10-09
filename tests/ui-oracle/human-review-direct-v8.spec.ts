/**
 * direct-v8 canonical HUMAN_REVIEW capture.
 *
 * This is deliberately stricter than the old local acceptance pack: a PNG is
 * written only after the DOM proves the frozen product archetype is actually
 * present. Machine validity is still NOT human visual acceptance.
 */
import { execFileSync } from "node:child_process";
import { mkdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const API = "http://127.0.0.1:8012/api/v1";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";
const CAFE_ID = "8412b521-5e1c-505d-9dec-568acb860c76";
const BRANCH_ID = "3b5a341a-e550-5f0c-b35a-319ed43bd840";
const OUT = path.resolve("artifacts/ui-direct-v8/HUMAN_REVIEW");

function currentHead(): string {
  // GITHUB_SHA in pull_request runs may refer to a synthetic merge commit.
  // The capture workflow checks out the exact PR head, so repository HEAD is
  // the only reliable identifier for the bytes actually used to take shots.
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  } catch {
    return process.env.GITHUB_SHA ?? "unknown";
  }
}

type Scope = "desktop" | "mobile" | "both";
interface Shot {
  name: string;
  scope: Scope;
  route: string;
  auth?: boolean;
  clickTestid?: string;
  waitTestid?: string;
  selectTestid?: { id: string; value: string };
  openDetailsTestid?: string;
  prepareOperatorPolicy?: boolean;
  submitReality?: boolean;
  page?: string;
  state?: string;
  h1?: string;
  requiredTestids?: string[];
  requiredText?: string[];
  note: string;
}

const SHOTS: Shot[] = [
  {
    name: "01_home",
    scope: "both",
    route: "/#/",
    page: "home",
    state: "ready",
    h1: "去之前，先看看这里的规则和现场。",
    requiredTestids: ["entry-presence", "entry-indoor", "entry-dining", "entry-rules"],
    requiredText: ["近期值得先看", "规则与现场速览"],
    note: "Home = Query Launcher + four task lenses + recommendation + coexistence digest.",
  },
  {
    name: "02_search",
    scope: "both",
    route: "/#/search",
    page: "search",
    h1: "搜索场所的规则与现场",
    requiredTestids: ["search-input", "search-count"],
    requiredText: ["筛选"],
    note: "Search = List–Detail on desktop / compact list on mobile; Rule+Reality+Evidence stay together.",
  },
  {
    name: "02a_search_filter",
    scope: "both",
    route: "/#/search",
    clickTestid: "filter-toggle",
    page: "search",
    state: "filter",
    h1: "搜索场所的规则与现场",
    requiredText: ["筛选只影响显示，不改变任何结论"],
    note: "Filter is a compact presentation control; it never changes Rule/Reality facts.",
  },
  {
    name: "02b_search_empty",
    scope: "both",
    route: "/#/search?q=不存在的场所zzz",
    page: "search",
    state: "empty",
    h1: "搜索场所的规则与现场",
    requiredTestids: ["search-empty", "search-empty-map"],
    requiredText: ["没有找到已收录场所"],
    note: "Search empty keeps context and one implemented recovery action; it does not route into a contribution flow that requires an existing place.",
  },
  {
    name: "03_place_overview",
    scope: "both",
    route: `/#/place/${MALL_ID}`,
    page: "place",
    state: "ready",
    h1: "云栖中心·测试商场",
    requiredTestids: ["section-answer", "overview-reality", "overview-evidence"],
    requiredText: ["规则", "现场概览", "工作人员处理", "动物设施", "证据与来源"],
    note: "Place first screen = Coexistence Passport, not a generic detail page.",
  },
  {
    name: "03a_place_unknown",
    scope: "both",
    route: `/#/place/${BRANCH_ID}`,
    page: "place",
    state: "unknown",
    h1: "星河咖啡·栖霞分店",
    requiredText: ["信息不足"],
    note: "Unknown is a first-class answer; no fabricated allow/prohibit verdict.",
  },
  {
    name: "04_place_rules",
    scope: "both",
    route: `/#/place/${MALL_ID}?view=rules`,
    page: "place",
    state: "ready",
    h1: "云栖中心·测试商场",
    requiredText: ["规则"],
    note: "Rule Groups with context/source/conditions, divider-led rather than card wall.",
  },
  {
    name: "05_place_space",
    scope: "both",
    route: `/#/place/${MALL_ID}?view=space`,
    page: "place",
    state: "ready",
    h1: "云栖中心·测试商场",
    requiredTestids: ["animal-facilities"],
    requiredText: ["动物设施", "使用方式", "最近核验", "不等于允许动物进入"],
    note: "Space dossier exposes verified facility use/safety facts without converting them to policy.",
  },
  {
    name: "06_map_rule",
    scope: "both",
    route: "/#/map?lens=rule",
    page: "map",
    h1: "规则与现场地图",
    requiredTestids: [
      "map",
      "map-lens-rule",
      "map-lens-reality",
      "map-lens-facility",
      "map-lens-divergence",
    ],
    requiredText: ["规则", "现场", "设施", "不一致"],
    note: "Spatial Workspace: four first-class lenses share one place/snapshot model.",
  },
  {
    name: "07_map_reality",
    scope: "both",
    route: "/#/map?lens=reality",
    page: "map",
    h1: "规则与现场地图",
    requiredTestids: ["map", "map-lens-reality"],
    requiredText: ["现场"],
    note: "Reality lens includes published presence/staff/facility facts; no pet-friendliness score.",
  },
  {
    name: "08_map_facility",
    scope: "both",
    route: "/#/map?lens=facility",
    page: "map",
    h1: "规则与现场地图",
    requiredTestids: ["map", "map-lens-facility"],
    requiredText: ["设施"],
    note: "Facility is its own factual lens; facility != entry policy.",
  },
  {
    name: "09_map_divergence",
    scope: "both",
    route: "/#/map?lens=divergence",
    page: "map",
    h1: "规则与现场地图",
    requiredTestids: ["map", "map-lens-divergence"],
    requiredText: ["不一致"],
    note: "Divergence is descriptive only and never rewrites Rule or Reality.",
  },
  {
    name: "10_map_mobile_selected",
    scope: "mobile",
    route: `/#/map?lens=reality&place=${MALL_ID}`,
    page: "map",
    h1: "规则与现场地图",
    requiredTestids: ["map-mobile-sheet", "sheet-open-detail"],
    requiredText: ["现场概览", "查看场所"],
    note: "Real overlay bottom sheet stays above the bottom nav and uses the same CoexistenceSnapshot.",
  },
  {
    name: "11_reality",
    scope: "both",
    route: `/#/place/${MALL_ID}/reality`,
    page: "reality",
    state: "ready",
    h1: "现场记录",
    requiredTestids: ["trace-summary", "trace-observations", "reality-filter"],
    requiredText: ["现场记录", "工作人员处理", "设施", "不等于正式准入规则"],
    note: "Reality = published v0.9 event log: presence/staff/facility, human-verified and time-basis explicit.",
  },
  {
    name: "11a_reality_empty",
    scope: "desktop",
    route: `/#/place/${CAFE_ID}/reality`,
    page: "reality",
    state: "empty",
    h1: "现场记录",
    requiredTestids: ["trace-observations", "reality-go-enter"],
    requiredText: ["暂无近期现场记录", "并不代表现场没有动物"],
    note: "No published Reality event is explicitly not 'no animal presence'.",
  },
  {
    name: "12_evidence",
    scope: "both",
    route: `/#/place/${MALL_ID}/evidence`,
    page: "evidence",
    state: "ready",
    h1: "证据与来源",
    requiredTestids: ["evidence-head", "evidence-items", "evidence-sources"],
    requiredText: ["证据来源链", "观察时间", "提交时间", "核验时间", "规则依据", "现场来源"],
    note: "Evidence = provenance record with Observed / Submitted / Reviewed kept distinct.",
  },
  {
    name: "12a_evidence_dispute",
    scope: "both",
    route: `/#/place/${MALL_ID}/evidence`,
    auth: true,
    clickTestid: "reality-dispute-open",
    waitTestid: "reality-dispute-note",
    page: "evidence",
    state: "ready",
    h1: "证据与来源",
    requiredTestids: ["reality-dispute-reason", "reality-dispute-note", "reality-dispute-submit"],
    requiredText: ["问题类型", "需要核验什么", "不会删除记录", "不会自动改变规则"],
    note: "Correction/dispute is a governed transaction on one published Reality fact, never a direct edit.",
  },
  {
    name: "13_contribution_choose",
    scope: "both",
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    page: "contribution",
    state: "choose-type",
    h1: "你刚刚知道了什么？",
    requiredTestids: [
      "entry-rule",
      "entry-reality-observed_presence",
      "entry-reality-staff_response",
      "entry-reality-animal_facility",
      "entry-quick",
    ],
    requiredText: ["提交内容会进入人工核验"],
    note: "Contribution entry has five consumer intents and no admin/schema language.",
  },
  {
    name: "14_contribution_rule",
    scope: "both",
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-rule",
    waitTestid: "rule-submit",
    page: "contribution",
    state: "step-1",
    h1: "现场贡献",
    requiredTestids: ["rule-submit"],
    requiredText: ["补充规则信息", "不会自动生成或发布规则"],
    note: "Rule lead is governed evidence/review, never Observation and never auto-published Rule.",
  },
  {
    name: "15_contribution_correction",
    scope: "both",
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-quick",
    waitTestid: "quick-submit",
    page: "contribution",
    state: "step-1",
    h1: "现场贡献",
    requiredTestids: ["quick-options", "correction-unknown", "quick-submit"],
    requiredText: ["哪里需要纠正", "不知道正确值"],
    note: "Place correction is a structured, review-pending lead; uncertainty is a valid answer.",
  },
  {
    name: "16_contribution_reality",
    scope: "both",
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-reality-observed_presence",
    waitTestid: "reality-submit",
    page: "contribution",
    state: "step-2",
    h1: "现场贡献",
    requiredTestids: ["reality-source-mode", "reality-submit"],
    requiredText: ["这条信息来自哪里", "什么时候", "在哪里", "你看到了什么"],
    note: "Reality contribution is a structured transaction, not a generic comment form.",
  },
  {
    name: "16a_contribution_staff",
    scope: "both",
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-reality-staff_response",
    waitTestid: "reality-submit",
    page: "contribution",
    state: "step-2",
    h1: "现场贡献",
    requiredTestids: ["reality-staff-role", "reality-staff-awareness", "reality-submit"],
    requiredText: ["是哪类工作人员", "不收集工作人员姓名"],
    note: "Staff response captures role/action/awareness without identity and never becomes OperatorPolicy.",
  },
  {
    name: "16b_contribution_facility",
    scope: "both",
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-reality-animal_facility",
    waitTestid: "reality-submit",
    page: "contribution",
    state: "step-2",
    h1: "现场贡献",
    requiredTestids: [
      "reality-facility-purpose",
      "reality-facility-access",
      "reality-facility-more",
    ],
    requiredText: ["你怎么确认它是动物相关设施", "补充设施使用与安全信息"],
    note: "Facility contribution asks purpose certainty first and keeps optional safety/use attributes behind progressive disclosure.",
  },
  {
    name: "16d_contribution_external",
    scope: "both",
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-reality-observed_presence",
    waitTestid: "reality-source-mode",
    selectTestid: { id: "reality-source-mode", value: "external_online_content" },
    page: "contribution",
    state: "step-2",
    h1: "现场贡献",
    requiredTestids: [
      "reality-source-url",
      "reality-place-match",
      "reality-published-date",
      "reality-external-event-date",
    ],
    requiredText: [
      "公开内容链接",
      "内容能定位到哪里",
      "内容发布时间",
      "不会把发布时间当成现场发生时间",
    ],
    note: "External content keeps source time, event time and place-match precision separate before review.",
  },
  {
    name: "16e_contribution_facility_details",
    scope: "both",
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-reality-animal_facility",
    waitTestid: "reality-facility-more",
    openDetailsTestid: "reality-facility-more",
    page: "contribution",
    state: "step-2",
    h1: "现场贡献",
    requiredTestids: [
      "reality-facility-weather",
      "reality-facility-shade",
      "reality-facility-ventilation",
      "reality-facility-water",
      "reality-facility-supervision",
      "reality-facility-security",
    ],
    requiredText: ["遮雨", "遮阳", "通风", "饮水", "看护情况", "安全 / 锁闭情况"],
    note: "Facility safety/use facts are progressive disclosure and never a safety score or entry-policy inference.",
  },
  {
    name: "16c_contribution_done",
    scope: "both",
    route: `/#/contribute/${MALL_ID}`,
    auth: true,
    clickTestid: "entry-reality-observed_presence",
    waitTestid: "reality-submit",
    submitReality: true,
    page: "contribution",
    state: "done",
    h1: "现场贡献",
    requiredTestids: ["contribute-result", "done-mine", "done-place"],
    requiredText: ["已提交待核验", "审核完成前"],
    note: "Successful contribution remains review-pending and never claims the Rule changed.",
  },
  {
    name: "17_mine",
    scope: "both",
    route: "/#/mine",
    auth: true,
    h1: "我的",
    requiredText: ["关注的变化", "我的贡献"],
    note: "Mine keeps rule-watch / reality-watch and contribution history separate.",
  },
  {
    name: "18_settings",
    scope: "both",
    route: "/#/settings",
    h1: "设置与说明",
    note: "Secondary reading workspace; no ModeBar/card-wall regression.",
  },
  {
    name: "19_privacy",
    scope: "both",
    route: "/#/privacy",
    auth: true,
    h1: "隐私与数据",
    requiredText: ["数据清单", "账号删除与数据导出"],
    note: "Privacy states unavailable server workflows honestly; no fake local submit action.",
  },
  {
    name: "20_notifications",
    scope: "both",
    route: "/#/notifications",
    auth: true,
    h1: "通知中心",
    requiredText: ["规则变化", "现场更新"],
    note: "Notifications separate Rule and Reality watches; no fake push-delivery claim.",
  },
  {
    name: "20a_operator_claim",
    scope: "both",
    route: `/#/place/${MALL_ID}/operator-claim`,
    auth: true,
    h1: "场所方认领",
    requiredTestids: [
      "operator-name",
      "operator-org-type",
      "operator-verification-method",
      "operator-claim-submit",
    ],
    requiredText: ["人工核验", "不会自动改变任何准入规则"],
    note: "Operator claim is a governed identity transaction; submission itself never changes Rule or Reality.",
  },
  {
    name: "20b_operator_policy_approved",
    scope: "both",
    route: "/#/place/__OPERATOR_POLICY_PLACE__/operator-claim",
    auth: true,
    prepareOperatorPolicy: true,
    h1: "场所方认领",
    requiredTestids: [
      "operator-claim-result",
      "operator-policy",
      "operator-policy-zone",
      "operator-policy-animal",
      "operator-policy-action",
      "operator-policy-effect",
      "operator-policy-submit",
    ],
    requiredText: [
      "场所方身份已核验",
      "维护管理方规则",
      "场所管理方正式政策",
      "工作人员的一次处理自动变成政策",
      "法律或监管规则",
    ],
    note: "Approved operator governance is human-reviewed too: identity approval unlocks structured operator policy without leaking internal rule-layer enums.",
  },
  {
    name: "21_pets",
    scope: "both",
    route: "/#/pets",
    auth: true,
    h1: "宠物档案",
    note: "Pet profiles remain an optional query-context input, not a social profile surface.",
  },
  {
    name: "21a_pet_new",
    scope: "both",
    route: "/#/pet/new",
    auth: true,
    h1: "新建宠物档案",
    requiredTestids: ["pet-name", "pet-species", "pet-service-role", "pet-save"],
    requiredText: ["只填写规则判断真正需要的信息", "平台不会通过照片或品种推断"],
    note: "Pet input is minimal query context; missing attributes stay unknown and service-dog role is user-declared.",
  },
  {
    name: "22_boundary",
    scope: "both",
    route: "/#/boundary",
    auth: true,
    h1: "共处边界",
    requiredText: ["不改变场所规则"],
    note: "Boundary is private preference comparison and never a venue score.",
  },
  {
    name: "23_why",
    scope: "both",
    route: `/#/place/${MALL_ID}/why`,
    h1: "为什么是这个结果",
    requiredText: ["规则与现场关系", "不会用一次现场观察替代正式规则"],
    note: "Why explains consumer reasoning, not resolver/internal traces.",
  },
  {
    name: "24_about",
    scope: "both",
    route: "/#/about",
    h1: "关于 PetAccess",
    note: "Methodology is a reading workspace, not an engineering dashboard.",
  },
  {
    name: "25_onboarding",
    scope: "both",
    route: "/#/onboarding",
    h1: "开始使用",
    note: "Authentication stays quiet and task-oriented.",
  },
  {
    name: "26_not_found",
    scope: "both",
    route: "/#/this-route-does-not-exist",
    h1: "这个页面不存在",
    note: "404 uses the same consumer shell and recovery affordances.",
  },
];

async function signIn(request: APIRequestContext): Promise<string> {
  const suffix = `${Date.now()}-${Math.floor(Math.random() * 1e6)}`;
  const email = `direct-v8-human-${suffix}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "Direct V8 人审探针", email, password: "passw0rd123" },
  });
  expect(reg.ok(), await reg.text()).toBeTruthy();
  const login = await request.post(`${API}/auth/login`, {
    data: { email, password: "passw0rd123" },
  });
  expect(login.ok(), await login.text()).toBeTruthy();
  return (await login.json()).access_token as string;
}

async function signInAdmin(request: APIRequestContext): Promise<string> {
  const login = await request.post(`${API}/auth/login`, {
    data: { email: "admin@demo-petaccess.com", password: "admin12345" },
  });
  expect(login.ok(), `admin login failed: ${await login.text()}`).toBeTruthy();
  return (await login.json()).access_token as string;
}

async function prepareApprovedOperatorPolicy(
  request: APIRequestContext,
  userToken: string,
  projectName: string,
): Promise<string> {
  const adminToken = await signInAdmin(request);
  const suffix = `${projectName}-${Date.now()}-${Math.floor(Math.random() * 1e6)}`;

  const place = await request.post(`${API}/places`, {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: {
      canonical_name: `人审管理方场所·${suffix}`,
      place_type: "mall",
      canonical_address: "人审专用测试地址",
      lifecycle_status: "active",
      location_wkt: "POINT(121.4737 31.2304)",
    },
  });
  expect(
    place.ok(),
    `create operator-policy fixture place failed: ${await place.text()}`,
  ).toBeTruthy();
  const placeId = (await place.json()).id as string;

  const claim = await request.post(`${API}/operator-claims/self-serve`, {
    headers: { Authorization: `Bearer ${userToken}` },
    data: {
      place_id: placeId,
      operator_name: `人审测试管理方·${suffix}`,
      org_type: "company",
      work_email: "ops-human-review@example.com",
      website: null,
      verification_method: "work_email",
      verification_note: "仅用于 direct-v8 人工视觉验收 fixture",
    },
  });
  expect(claim.ok(), `create operator claim failed: ${await claim.text()}`).toBeTruthy();
  const claimId = (await claim.json()).id as string;

  const review = await request.post(`${API}/operator-claims/${claimId}/review`, {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: { approve: true, rejection_reason: null },
  });
  expect(review.ok(), `approve operator claim failed: ${await review.text()}`).toBeTruthy();

  return placeId;
}

async function settle(page: Page): Promise<void> {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page
    .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
      timeout: 15000,
    })
    .catch(() => {});
  await page.addStyleTag({
    content: "* { transition: none !important; animation: none !important; }",
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.waitForTimeout(200);
}

async function assertShot(page: Page, shot: Shot): Promise<Record<string, unknown>> {
  if (shot.page) {
    const host = page.locator(`[data-ui-page="${shot.page}"]`);
    await expect(host, `${shot.name}: data-ui-page`).toBeVisible({ timeout: 15000 });
    if (shot.state) await expect(host).toHaveAttribute("data-ui-state", shot.state);
  }
  if (shot.h1) await expect(page.locator("h1").first()).toContainText(shot.h1);
  for (const id of shot.requiredTestids ?? []) {
    await expect(page.getByTestId(id).first(), `${shot.name}: ${id}`).toBeVisible({
      timeout: 15000,
    });
  }
  for (const value of shot.requiredText ?? []) {
    await expect(
      page.getByText(value, { exact: false }).filter({ visible: true }).first(),
      `${shot.name}: ${value}`,
    ).toBeVisible({
      timeout: 15000,
    });
  }

  if (shot.page === "map") {
    const mock = page.locator('[data-ui="mock-map"]');
    if (await mock.isVisible().catch(() => false)) {
      await expect(
        page.getByTestId("map-real-provider-fallback"),
        `${shot.name}: simplified basemap disclosure`,
      ).toContainText("简化空间底图");
      await expect(page.getByTestId("map-real-provider-fallback")).toContainText("已收录坐标");
    }
  }

  return page.evaluate(() => {
    const host = document.querySelector("[data-ui-page]");
    const h1 = document.querySelector("h1");
    const mapRenderer = document.querySelector('[data-ui="real-map"]')
      ? "real"
      : document.querySelector('[data-ui="mock-map"]')
        ? "simplified"
        : null;
    return {
      route: location.hash,
      page: host?.getAttribute("data-ui-page") ?? null,
      state: host?.getAttribute("data-ui-state") ?? null,
      fixture: host?.getAttribute("data-ui-fixture") ?? null,
      h1: h1?.textContent?.trim() ?? null,
      mapRenderer,
    };
  });
}

test("direct-v8 canonical human-review packet", async ({ page, request }, testInfo) => {
  const projectName = testInfo.project.name;
  const desktop = projectName === "oracle-desktop";
  const tablet = projectName === "oracle-tablet";
  const targetScope: Scope = desktop || tablet ? "desktop" : "mobile";
  const captureScope = tablet ? "tablet" : targetScope;
  const viewport = desktop
    ? { width: 1440, height: 900 }
    : tablet
      ? { width: 800, height: 1080 }
      : { width: 430, height: 932 };
  const out = path.join(OUT, captureScope);
  mkdirSync(out, { recursive: true });

  let token: string | null = null;
  let operatorPolicyPlaceId: string | null = null;
  const rows: Record<string, unknown>[] = [];

  for (const shot of SHOTS.filter((item) => item.scope === "both" || item.scope === targetScope)) {
    await page.setViewportSize(viewport);
    await page.clock.install({ time: new Date("2026-10-06T04:00:00Z") }).catch(() => {});

    if (shot.auth) {
      token ??= await signIn(request);
      await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);
    }

    if (shot.prepareOperatorPolicy) {
      if (!token) throw new Error("approved operator policy fixture requires signed-in user");
      operatorPolicyPlaceId ??= await prepareApprovedOperatorPolicy(
        request,
        token,
        testInfo.project.name,
      );
    }

    const resolvedRoute = operatorPolicyPlaceId
      ? shot.route.replace("__OPERATOR_POLICY_PLACE__", operatorPolicyPlaceId)
      : shot.route;

    // Every shot must start from a fresh Document, not just a new hash. Several
    // human-review states intentionally reuse the same Contribution URL; a
    // hash-only page.goto would preserve the previous component's step state
    // and make the next entry button disappear. The harmless outer query
    // forces a hard bootstrap while preserving the requested hash route.
    const captureRoute = resolvedRoute.startsWith("/#")
      ? `/?human_review_shot=${encodeURIComponent(shot.name)}${resolvedRoute.slice(1)}`
      : resolvedRoute;
    await page.goto(captureRoute);
    await settle(page);

    if (shot.clickTestid) {
      await page.getByTestId(shot.clickTestid).first().click();
      if (shot.waitTestid) {
        await page.getByTestId(shot.waitTestid).waitFor({ state: "visible", timeout: 15000 });
      }
      await settle(page);
    }

    if (shot.selectTestid) {
      await page.getByTestId(shot.selectTestid.id).selectOption(shot.selectTestid.value);
      await settle(page);
    }

    if (shot.openDetailsTestid) {
      const details = page.getByTestId(shot.openDetailsTestid);
      await details.locator("summary").click();
      await expect(details).toHaveAttribute("open", "");
      await settle(page);
    }

    if (shot.submitReality) {
      const date = page.getByTestId("reality-date");
      if (await date.isVisible().catch(() => false)) await date.fill("2026-10-05");
      await page.getByTestId("reality-submit").click();
      await page.getByTestId("contribute-result").waitFor({ state: "visible", timeout: 15000 });
      await settle(page);
    }

    const actual = await assertShot(page, shot);
    const file = path.join(out, `${shot.name}.png`);
    await page.screenshot({ path: file });
    rows.push({
      name: shot.name,
      viewport: `${viewport.width}x${viewport.height}`,
      route: resolvedRoute,
      note: shot.note,
      actual,
      bytes: statSync(file).size,
    });
  }

  writeFileSync(
    path.join(out, "manifest.json"),
    JSON.stringify(
      {
        project: testInfo.project.name,
        sourceHead: currentHead(),
        sourceBranch: process.env.GITHUB_HEAD_REF || process.env.GITHUB_REF_NAME || "local",
        machineValidatedOnly: true,
        humanVisualAcceptance: "PENDING",
        generatedAt: new Date().toISOString(),
        shots: rows,
      },
      null,
      2,
    ),
    "utf8",
  );
});
