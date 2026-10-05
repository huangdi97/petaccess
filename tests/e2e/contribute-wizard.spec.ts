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
  await expect(page.getByTestId("reality-date")).toBeVisible();
  await expect(page.getByTestId("reality-effort")).toBeVisible();
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
  await expect(page.getByTestId("reality-date")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("reality-date").fill("2026-09-20");
  await page.getByTestId("reality-count").fill("2");
  await page.getByTestId("reality-submit").click();
  // Bounded 15s: the parent-flow POST + candidate write can exceed the default
  // 5s expect under parallel workers (same pattern as B2).
  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId("contribute-result")).toContainText(/已提交/);
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
  await page.locator("#reality-staff-action").selectOption("direct_to_allowed_zone");

  const staffRequestPromise = page.waitForRequest(
    (r) => r.method() === "POST" && r.url().includes(`/places/${MALL_ID}/reality/reports`),
  );
  await page.getByTestId("reality-submit").click();
  const staffRequest = await staffRequestPromise;
  const staffBody = staffRequest.postDataJSON() as {
    candidates: { payload: Record<string, unknown> }[];
  };
  expect(staffBody.candidates[0]?.payload.response_action).toBe("direct_to_allowed_zone");
  expect(staffBody.candidates[0]?.payload.actor_role).toBe("unknown_staff");
  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });

  await page.goto(`${BASE}/#/contribute/${MALL_ID}`, { waitUntil: "load" });
  await expect(page.getByTestId("entry-reality-animal_facility")).toBeVisible({ timeout: 15000 });
  await page.getByTestId("entry-reality-animal_facility").click();
  await page.locator("#reality-facility-type").selectOption("pet_waiting_area");
  await page.locator("#reality-facility-status").selectOption("temporarily_unavailable");

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
  expect(facilityBody.candidates[0]?.payload).not.toHaveProperty("operator_provided");
  await expect(page.getByTestId("contribute-result")).toBeVisible({ timeout: 15000 });
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
  await expect(page.getByTestId("reality-date")).toBeVisible({ timeout: 15000 });
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
