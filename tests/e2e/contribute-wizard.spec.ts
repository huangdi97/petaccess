/**
 * M7 Contribution wizard acceptance (A1/A2/A4, B2).
 *
 * Signs a real user in through the E2E API (register + login → pa_token in
 * localStorage), then drives the wizard: entry → reality presence form →
 * parent-flow submit (candidate REVIEW_PENDING) → 我的贡献 history row.
 */
import { expect, test, type APIRequestContext } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
const API = "http://127.0.0.1:8010/api/v1";
/** 云栖中心·测试商场 — seeded place with zones. */
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

async function signIn(request: APIRequestContext): Promise<string> {
  const email = `m7-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "M7 测试用户", email, password: "passw0rd123" },
  });
  expect(reg.ok(), `register failed: ${await reg.text()}`).toBeTruthy();
  const login = await request.post(`${API}/auth/login`, {
    data: { email, password: "passw0rd123" },
  });
  expect(login.ok()).toBeTruthy();
  return (await login.json()).access_token as string;
}

test("A1/A4 — 向导入口与现场记录表单渲染（已登录）", async ({ page, request }) => {
  const token = await signIn(request);
  // Deterministic token injection: addInitScript runs before every page load, so
  // a single full-page goto to the hash URL boots straight into ContributeView.
  // (The previous goto→reload pattern raced SPA boot under parallel workers and
  // intermittently landed on Home.)
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);
  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("consumer-app-shell")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("contribute-workspace")).toBeVisible({ timeout: 15000 });
  // Hardening (same pattern as B2, commit a8bab37): under 6 parallel workers
  // the lazy-loaded ContributeView chunk can exceed the default 5s expect
  // timeout on first load. Bounded 15s wait, then assert visibility.
  await expect(page.getByTestId("entry-reality-observed_presence")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("entry-quick")).toBeVisible();
  await page.getByTestId("entry-reality-observed_presence").click();
  await expect(page.getByTestId("reality-submit")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("reality-source-mode")).toBeVisible();
  await expect(page.getByTestId("reality-effort")).toBeVisible();
  await page.getByTestId("reality-source-mode").selectOption("on_site_past");
  await expect(page.getByTestId("reality-date")).toBeVisible();
});

test("A2 — 现场记录经父流提交，候选进入人工审核队列", async ({ page, request }) => {
  const token = await signIn(request);
  // Same deterministic token injection as A1: single full-page goto boots
  // straight into ContributeView without the goto→reload boot race.
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);
  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  // Hardening (same pattern as B2/A1, commit a8bab37): the entry is lazy-
  // loaded and can appear late under parallel workers; wait before clicking.
  await expect(page.getByTestId("entry-reality-observed_presence")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-reality-observed_presence").click();
  await expect(page.getByTestId("reality-source-mode")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("reality-source-mode").selectOption("on_site_past");
  await expect(page.getByTestId("reality-date")).toBeVisible();
  await page.getByTestId("reality-date").fill("2026-09-20");
  await page.getByTestId("reality-count").fill("2");
  const reportRequestPromise = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes(`/places/${MALL_ID}/reality/reports`),
  );
  await page.getByTestId("reality-submit").click();
  const reportBody = (await reportRequestPromise).postDataJSON() as {
    effort: { duration_bucket: string; animal_observed: boolean };
  };
  expect(reportBody.effort.duration_bucket).toBe("unknown");
  expect(reportBody.effort.animal_observed).toBe(true);
  // Bounded 15s: the parent-flow POST + candidate write can exceed the default
  // 5s expect under parallel workers (same pattern as B2).
  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("contribute-result")).toContainText(/已提交/);
});

test("A2.0 — 外部帖子只记录发布时间，不把发布时间伪装成事件时间", async ({ page, request }) => {
  const token = await signIn(request);
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);
  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-reality-observed_presence")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-reality-observed_presence").click();
  await page.getByTestId("reality-source-mode").selectOption("external_online_content");
  await page.getByTestId("reality-source-url").fill("https://example.com/public-post");
  await page.getByTestId("reality-source-platform").selectOption("web");
  await page.getByTestId("reality-published-date").fill("2026-09-20");

  const requestPromise = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes(`/places/${MALL_ID}/reality/reports`),
  );
  await page.getByTestId("reality-submit").click();
  const requestBody = (await requestPromise).postDataJSON() as {
    report: Record<string, unknown>;
    effort: unknown;
    external_content: Record<string, unknown> | null;
  };
  expect(requestBody.report.origin).toBe("external_online_content");
  expect(requestBody.report.time_evidence_state).toBe("publication_time_only");
  expect(requestBody.report.observed_at).toBeNull();
  expect(requestBody.report.claimed_event_at).toBeNull();
  expect(requestBody.report.fact_evidence_state).toBe("text_only_external");
  expect(requestBody.effort).toBeNull();
  expect(requestBody.external_content?.source_url).toBe("https://example.com/public-post");
  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });
});

test("A2.1 — Staff / Facility contribution uses canonical Reality domain values", async ({
  page,
  request,
}) => {
  const token = await signIn(request);
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);

  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-reality-staff_response")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-reality-staff_response").click();
  await page.getByTestId("reality-staff-role").selectOption("security");
  await page.locator("#reality-staff-action").selectOption("direct_to_allowed_zone");

  const staffRequestPromise = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes(`/places/${MALL_ID}/reality/reports`),
  );
  await page.getByTestId("reality-submit").click();
  const staffRequest = await staffRequestPromise;
  const staffBody = staffRequest.postDataJSON() as {
    report: Record<string, unknown>;
    candidates: { payload: Record<string, unknown> }[];
  };
  expect(staffBody.report.place_match_state).toBe("exact_place");
  expect(staffBody.report.place_match_evidence_types).toEqual(["user_confirmation"]);
  expect(staffBody.report.time_evidence_state).toBe("live_device_time");
  expect(staffBody.report.fact_evidence_state).toBe("first_hand_no_media");
  expect(staffBody.candidates[0]?.payload.response_action).toBe("direct_to_allowed_zone");
  expect(staffBody.candidates[0]?.payload.actor_role).toBe("security");
  expect(staffBody.candidates[0]?.payload.staff_awareness_state).toBe("awareness_unknown");
  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });

  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-reality-animal_facility")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-reality-animal_facility").click();
  await page.locator("#reality-facility-type").selectOption("pet_waiting_area");
  await page.locator("#reality-facility-status").selectOption("temporarily_unavailable");
  await page.getByTestId("reality-facility-access").selectOption("operator_provided");
  await page.getByTestId("reality-facility-capacity").fill("2");
  await page.getByTestId("reality-facility-more").locator("summary").click();
  await page.getByTestId("reality-facility-weather").selectOption({ label: "有" });
  await page.getByTestId("reality-facility-water").selectOption({ label: "有" });
  await page.getByTestId("reality-facility-supervision").selectOption({ label: "有工作人员看护" });

  const facilityRequestPromise = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes(`/places/${MALL_ID}/reality/reports`),
  );
  await page.getByTestId("reality-submit").click();
  const facilityRequest = await facilityRequestPromise;
  const facilityBody = facilityRequest.postDataJSON() as {
    candidates: { payload: Record<string, unknown> }[];
  };
  expect(facilityBody.candidates[0]?.payload.facility_type).toBe("pet_waiting_area");
  expect(facilityBody.candidates[0]?.payload.operational_state).toBe("temporarily_unavailable");
  expect(facilityBody.candidates[0]?.payload.purpose_state).toBe("purpose_unknown");
  expect(facilityBody.candidates[0]?.payload.access_mode).toBe("operator_provided");
  expect(facilityBody.candidates[0]?.payload.operator_provided).toBe(true);
  expect(facilityBody.candidates[0]?.payload.capacity).toBe(2);
  expect(facilityBody.candidates[0]?.payload.weather_protection).toBe(true);
  expect(facilityBody.candidates[0]?.payload.water_available).toBe(true);
  expect(facilityBody.candidates[0]?.payload.supervision_state).toBe("有工作人员看护");
  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });
});

test("A2.2 — 规则线索进入 RuleCandidate review，而不是 Observation/Rule", async ({
  page,
  request,
}) => {
  const token = await signIn(request);
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);
  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-rule")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-rule").click();
  await page.getByTestId("rule-known").selectOption("conditional");
  await page.getByTestId("rule-source-basis").selectOption("staff_statement");
  await page.getByTestId("rule-animal-scope").selectOption("ordinary_pet");

  const leadRequestPromise = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes(`/places/${MALL_ID}/rule-leads`),
  );
  await page.getByTestId("rule-submit").click();
  const leadRequest = await leadRequestPromise;
  const body = leadRequest.postDataJSON() as Record<string, unknown>;
  expect(body.animal_scope).toBe("ordinary_pet");
  expect(body.effect).toBe("conditional");
  expect(String(body.raw_text)).toContain("来源：工作人员口头说明");
  expect(body.proximity_verified).toBe(false);
  expect(body.distance_bucket).toBeNull();
  expect(body.accuracy_bucket).toBeNull();
  await expect(page.getByTestId("contribute-result")).toContainText("人工复核", {
    timeout: 15000,
  });
});

test("A2.2b — 规则牌可独立提交证据，不要求用户先解释准入结论", async ({ page, request }) => {
  const token = await signIn(request);
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);
  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await page.getByTestId("entry-rule").click();
  await page.getByTestId("rule-intent-signage").click();

  // Valid 1×1 PNG: the flow is tested as an evidence upload, not as an OCR-quality test.
  const png = Buffer.from(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl8WQAAAABJRU5ErkJggg==",
    "base64",
  );
  await page.getByTestId("rule-evidence-file").setInputFiles({
    name: "signage.png",
    mimeType: "image/png",
    buffer: png,
  });
  await expect(page.getByTestId("rule-upload-msg")).toBeVisible({ timeout: 15000 });

  const ruleLeadRequest = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes(`/places/${MALL_ID}/rule-leads`),
  );
  await page.getByTestId("rule-submit").click();
  const body = (await ruleLeadRequest).postDataJSON() as Record<string, unknown>;
  expect(body.media_id).toBeTruthy();
  expect(body.effect).toBeNull();
  expect(body.animal_scope).toBeNull();
  expect(String(body.raw_text)).toContain("规则牌 / 公告证据");
  await expect(page.getByTestId("contribute-result")).toContainText("不会自动生成", {
    timeout: 15000,
  });
});

test("A2.3 — 场所纠错只提交 review lead，不直接修改场所", async ({ page, request }) => {
  const token = await signIn(request);
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);
  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-quick")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-quick").click();
  await page.getByTestId("correction-detail").fill("地址楼层需要人工复核");

  const correctionRequestPromise = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes("/verifications"),
  );
  await page.getByTestId("quick-submit").click();
  const correctionRequest = await correctionRequestPromise;
  const body = correctionRequest.postDataJSON() as Record<string, unknown>;
  expect(body.event_type).toBe("place_correction");
  expect(body.result).toBe("uncertain");
  expect(body.proximity_verified).toBe(false);
  await expect(page.getByTestId("contribute-result")).toContainText("人工核验", {
    timeout: 15000,
  });
});

test("A2.4 — “这次没看到”记录 effort，而不是生成动物缺席 claim", async ({ page, request }) => {
  const token = await signIn(request);
  const eventsResponse = await request.get(`${API}/places/${MALL_ID}/reality/events`);
  expect(eventsResponse.ok()).toBeTruthy();
  const events = (await eventsResponse.json()) as {
    id: string;
    event_type: string;
    zone_id: string | null;
  }[];
  const target = events.find((event) => event.event_type === "observed_presence");
  expect(target).toBeTruthy();

  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);
  const targetQuery = encodeURIComponent(target!.id);
  const zoneQuery = target!.zone_id ? `&zone=${encodeURIComponent(target!.zone_id)}` : "";
  const effortUrl = `${BASE}/#/contribute/${MALL_ID}?mode=effort&target=${targetQuery}${zoneQuery}`;
  await page.goto(effortUrl, { waitUntil: "load" });
  await expect(page.getByTestId("effort-duration")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("effort-duration").selectOption("min_10_30");

  const reportRequestPromise = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes(`/places/${MALL_ID}/reality/reports`),
  );
  await page.getByTestId("effort-submit").click();
  const body = (await reportRequestPromise).postDataJSON() as {
    candidates: unknown[];
    effort: {
      duration_bucket: string;
      animal_observed: boolean;
      covered_zone_ids: string[];
    };
    confirmation: {
      confirmation_type: string;
      target_claim_id: string;
    };
  };
  expect(body.candidates).toEqual([]);
  expect(body.effort.animal_observed).toBe(false);
  expect(body.effort.duration_bucket).toBe("min_10_30");
  if (target!.zone_id) expect(body.effort.covered_zone_ids).toContain(target!.zone_id);
  expect(body.confirmation.confirmation_type).toBe("not_seen_now");
  expect(body.confirmation.target_claim_id).toBe(target!.id);
  await expect(page.getByTestId("contribute-result")).toContainText("不会生成", {
    timeout: 15000,
  });
});

test("A3 — 规则线索直接进入 RuleCandidate review，不走 Observation", async ({ page, request }) => {
  const token = await signIn(request);
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);
  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-rule")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-rule").click();
  await page.getByTestId("rule-known").selectOption("conditional");
  await page.getByTestId("rule-source-basis").selectOption("official_online");

  const leadRequest = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes(`/api/v1/places/${MALL_ID}/rule-leads`),
  );
  await page.getByTestId("rule-submit").click();
  const req = await leadRequest;
  const body = req.postDataJSON() as Record<string, unknown>;
  expect(body.effect).toBe("conditional");
  expect(body).not.toHaveProperty("observed_action");
  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("contribute-result")).toContainText("不会改变准入结论");
});

test("A3.1 — 场所纠错允许只知道当前值错误", async ({ page, request }) => {
  const token = await signIn(request);
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), token);
  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-quick")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-quick").click();
  await page.getByTestId("correction-unknown").check();

  const verificationRequest = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().endsWith("/api/v1/verifications"),
  );
  await page.getByTestId("quick-submit").click();
  const req = await verificationRequest;
  const body = req.postDataJSON() as Record<string, unknown>;
  expect(body.event_type).toBe("place_correction");
  expect(String(body.note)).toContain("不知道正确值");
  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });
});

test("A2.2 — Rule lead 与场所纠错都进入人工核验并出现在统一贡献历史", async ({ page, request }) => {
  const token = await signIn(request);
  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);

  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-rule")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-rule").click();
  await page.getByTestId("rule-known").selectOption("conditional");
  await page.getByTestId("rule-source-basis").selectOption("uncertain");
  await page.getByTestId("rule-submit").click();
  await expect(page.getByTestId("contribute-result")).toContainText("人工复核", {
    timeout: 15000,
  });

  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await page.getByTestId("entry-quick").click();
  await page.getByTestId("correction-detail").fill("该场所楼层信息需要核验");
  await page.getByTestId("quick-submit").click();
  await expect(page.getByTestId("contribute-result")).toContainText("人工核验", {
    timeout: 15000,
  });

  await page.goto(`${BASE}/#/mine`);
  const rows = page.getByTestId("contribution-row");
  await expect(rows.filter({ hasText: "新规则线索" })).toBeVisible({ timeout: 15000 });
  await expect(rows.filter({ hasText: "场所信息纠错" })).toBeVisible({ timeout: 15000 });
  await expect(rows.filter({ hasText: "REVIEW_PENDING" })).toHaveCount(0);
});

test("A2.2 — area-only 外部内容只保存线索，不冒充当前场所事实", async ({
  page,
  request,
}) => {
  const token = await signIn(request);
  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);
  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-reality-observed_presence")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-reality-observed_presence").click();

  await page.getByTestId("reality-source-mode").selectOption("external_online_content");
  await page.getByTestId("reality-source-url").fill("https://example.com/area-only-pet-post");
  await page.getByTestId("reality-place-match").selectOption("area_only");
  await page.getByTestId("reality-published-date").fill("2026-10-05");

  await expect(page.getByTestId("reality-imprecise-place-note")).toContainText(
    "不会把它挂成当前场所的事实",
  );

  const reportRequestPromise = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes(`/places/${MALL_ID}/reality/reports`),
  );
  await page.getByTestId("reality-submit").click();
  const reportRequest = await reportRequestPromise;
  const body = reportRequest.postDataJSON() as {
    report: { place_id: string | null; subject_place_id: string | null; place_match_state: string };
    candidates: unknown[];
  };
  expect(body.report.place_match_state).toBe("area_only");
  expect(body.report.place_id).toBeNull();
  expect(body.report.subject_place_id).toBeNull();
  expect(body.candidates).toEqual([]);

  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("contribute-result")).toContainText("没有生成当前场所的事实候选");
});

test("B2 — 我的贡献：提交后可见、空时走统一空态", async ({ page, request }) => {
  // Fresh user with no contributions → unified empty copy.
  const tokenA = await signIn(request);
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), tokenA);
  await page.goto(`${BASE}/#/mine`);
  await expect(page.getByTestId("contributions-empty")).toBeVisible();
  await expect(page.getByTestId("contributions-empty")).toContainText("还没有贡献记录");

  // The user who just submitted sees the row with a dictionary label.
  const tokenB = await signIn(request);
  // addInitScript runs before every navigation, so the token set here also
  // applies to the contribute goto below (no goto→reload boot race).
  await page.addInitScript((t) => localStorage.setItem("pa_token", t), tokenB);
  await page.goto(`${BASE}/#/contribute/${MALL_ID}`);
  await expect(page.getByTestId("entry-reality-observed_presence")).toBeVisible({
    timeout: 15000,
  });
  await page.getByTestId("entry-reality-observed_presence").click();
  await expect(page.getByTestId("reality-source-mode")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("reality-source-mode").selectOption("on_site_past");
  await expect(page.getByTestId("reality-date")).toBeVisible();
  await page.getByTestId("reality-date").fill("2026-09-20");
  await page.getByTestId("reality-submit").click();
  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });
  await page.goto(`${BASE}/#/mine`);
  // Hardening: the mine list fetch can exceed the default expect timeout when
  // the full suite runs under parallel workers. Bounded 15s wait, then assert.
  await expect(page.getByTestId("contribution-row").first()).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("contribution-row").first()).toContainText("现场出现记录");
  await expect(page.getByTestId("contribution-row").first()).toContainText("等待人工核验");
});
