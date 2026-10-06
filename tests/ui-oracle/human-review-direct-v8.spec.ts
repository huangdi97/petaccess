/**
 * direct-v8 canonical HUMAN_REVIEW capture.
 *
 * This is deliberately stricter than the old local acceptance pack: a PNG is
 * written only after the DOM proves the frozen product archetype is actually
 * present. Machine validity is still NOT human visual acceptance.
 */
import { mkdirSync, statSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const API = "http://127.0.0.1:8012/api/v1";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";
const CAFE_ID = "8412b521-5e1c-505d-9dec-568acb860c76";
const BRANCH_ID = "3b5a341a-e550-5f0c-b35a-319ed43bd840";
const OUT = path.resolve("artifacts/ui-direct-v8/HUMAN_REVIEW");

type Scope = "desktop" | "mobile" | "both";
interface Shot {
  name: string;
  scope: Scope;
  route: string;
  auth?: boolean;
  clickTestid?: string;
  waitTestid?: string;
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
    h1: "搜索场所规则",
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
    h1: "搜索场所规则",
    requiredText: ["筛选只影响显示，不改变任何结论"],
    note: "Filter is a compact presentation control; it never changes Rule/Reality facts.",
  },
  {
    name: "02b_search_empty",
    scope: "both",
    route: "/#/search?q=不存在的场所zzz",
    page: "search",
    state: "empty",
    h1: "搜索场所规则",
    requiredTestids: ["search-empty", "search-empty-contribute"],
    requiredText: ["没有找到已收录场所"],
    note: "Search empty keeps context and one primary contribution/recovery action.",
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
    scope: "desktop",
    route: `/#/place/${MALL_ID}?view=rules`,
    page: "place",
    state: "ready",
    h1: "云栖中心·测试商场",
    requiredText: ["规则"],
    note: "Rule Groups with context/source/conditions, divider-led rather than card wall.",
  },
  {
    name: "05_place_space",
    scope: "desktop",
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
    scope: "desktop",
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
    scope: "desktop",
    route: "/#/map?lens=reality",
    page: "map",
    h1: "规则与现场地图",
    requiredTestids: ["map", "map-lens-reality"],
    requiredText: ["现场"],
    note: "Reality lens includes published presence/staff/facility facts; no pet-friendliness score.",
  },
  {
    name: "08_map_facility",
    scope: "desktop",
    route: "/#/map?lens=facility",
    page: "map",
    h1: "规则与现场地图",
    requiredTestids: ["map", "map-lens-facility"],
    requiredText: ["设施"],
    note: "Facility is its own factual lens; facility != entry policy.",
  },
  {
    name: "09_map_divergence",
    scope: "desktop",
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
    scope: "desktop",
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
    scope: "desktop",
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
    scope: "desktop",
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
    scope: "desktop",
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
    scope: "desktop",
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
    name: "16c_contribution_done",
    scope: "desktop",
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
    scope: "desktop",
    route: "/#/mine",
    auth: true,
    h1: "我的",
    requiredText: ["关注的变化", "我的贡献"],
    note: "Mine keeps rule-watch / reality-watch and contribution history separate.",
  },
  {
    name: "18_settings",
    scope: "desktop",
    route: "/#/settings",
    h1: "设置与说明",
    note: "Secondary reading workspace; no ModeBar/card-wall regression.",
  },
  {
    name: "19_privacy",
    scope: "desktop",
    route: "/#/privacy",
    auth: true,
    h1: "隐私与数据",
    requiredText: ["数据清单", "账号删除与数据导出"],
    note: "Privacy states unavailable server workflows honestly; no fake local submit action.",
  },
  {
    name: "20_notifications",
    scope: "desktop",
    route: "/#/notifications",
    auth: true,
    h1: "通知中心",
    requiredText: ["规则变化", "现场更新"],
    note: "Notifications separate Rule and Reality watches; no fake push-delivery claim.",
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
    scope: "desktop",
    route: "/#/boundary",
    auth: true,
    h1: "共处边界",
    requiredText: ["不改变场所规则"],
    note: "Boundary is private preference comparison and never a venue score.",
  },
  {
    name: "23_why",
    scope: "desktop",
    route: `/#/place/${MALL_ID}/why`,
    h1: "为什么是这个结果",
    requiredText: ["规则与现场关系", "不会用一次现场观察替代正式规则"],
    note: "Why explains consumer reasoning, not resolver/internal traces.",
  },
  {
    name: "24_about",
    scope: "desktop",
    route: "/#/about",
    h1: "关于 PetAccess",
    note: "Methodology is a reading workspace, not an engineering dashboard.",
  },
  {
    name: "25_onboarding",
    scope: "desktop",
    route: "/#/onboarding",
    h1: "开始使用",
    note: "Authentication stays quiet and task-oriented.",
  },
  {
    name: "26_not_found",
    scope: "desktop",
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
      page.getByText(value, { exact: false }).first(),
      `${shot.name}: ${value}`,
    ).toBeVisible({
      timeout: 15000,
    });
  }
  return page.evaluate(() => {
    const host = document.querySelector("[data-ui-page]");
    const h1 = document.querySelector("h1");
    return {
      route: location.hash,
      page: host?.getAttribute("data-ui-page") ?? null,
      state: host?.getAttribute("data-ui-state") ?? null,
      fixture: host?.getAttribute("data-ui-fixture") ?? null,
      h1: h1?.textContent?.trim() ?? null,
    };
  });
}

test("direct-v8 canonical human-review packet", async ({ page, request }, testInfo) => {
  const desktop = testInfo.project.name === "oracle-desktop";
  const targetScope: Scope = desktop ? "desktop" : "mobile";
  const viewport = desktop ? { width: 1440, height: 900 } : { width: 430, height: 932 };
  const out = path.join(OUT, targetScope);
  mkdirSync(out, { recursive: true });

  let token: string | null = null;
  const rows: Record<string, unknown>[] = [];

  for (const shot of SHOTS.filter((item) => item.scope === "both" || item.scope === targetScope)) {
    await page.setViewportSize(viewport);
    await page.clock.install({ time: new Date("2026-10-06T04:00:00Z") }).catch(() => {});

    if (shot.auth) {
      token ??= await signIn(request);
      await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);
    }

    // Every shot must start from a fresh Document, not just a new hash. Several
    // human-review states intentionally reuse the same Contribution URL; a
    // hash-only page.goto would preserve the previous component's step state
    // and make the next entry button disappear. The harmless outer query
    // forces a hard bootstrap while preserving the requested hash route.
    const captureRoute = shot.route.startsWith("/#")
      ? `/?human_review_shot=${encodeURIComponent(shot.name)}${shot.route.slice(1)}`
      : shot.route;
    await page.goto(captureRoute);
    await settle(page);

    if (shot.clickTestid) {
      await page.getByTestId(shot.clickTestid).click();
      if (shot.waitTestid) {
        await page.getByTestId(shot.waitTestid).waitFor({ state: "visible", timeout: 15000 });
      }
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
      route: shot.route,
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
