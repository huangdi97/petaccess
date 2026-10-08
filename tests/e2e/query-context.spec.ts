/**
 * Query-context acceptance.
 *
 * The global query editor is a real control, not display-only chrome:
 * changing to a declared service-dog role must produce a new
 * CoexistenceSnapshot request on every consumer surface that shows it.
 */
import { expect, test, type APIRequestContext, type Page, type Request } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
const API = "http://127.0.0.1:8010/api/v1";
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

function isGuideDogSnapshot(request: Request): boolean {
  if (request.method() !== "POST" || !request.url().includes("/coexistence")) return false;
  try {
    const body = request.postDataJSON() as Record<string, unknown>;
    return (
      body.animal === "dog" &&
      body.service_role === "working" &&
      body.declared_role === "guide_dog" &&
      body.action === "enter"
    );
  } catch {
    return false;
  }
}

async function chooseGuideDog(page: Page): Promise<Request> {
  await page.getByTestId("query-context-edit").click();
  await page.getByRole("button", { name: /服务犬通行/ }).click();
  const requestPromise = page.waitForRequest(isGuideDogSnapshot);
  await page.getByTestId("query-service-role").selectOption("guide_dog");
  const request = await requestPromise;
  await expect(page.getByTestId("query-context-summary")).toContainText("导盲犬");
  return request;
}

async function signedToken(request: APIRequestContext): Promise<string> {
  const email = `query-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
  const register = await request.post(`${API}/auth/register`, {
    data: { display_name: "Query Context 用户", email, password: "passw0rd123" },
  });
  expect(register.ok(), await register.text()).toBeTruthy();
  return ((await register.json()) as { access_token: string }).access_token;
}

for (const scenario of [
  { name: "Home", route: "/#/" },
  { name: "Search", route: "/#/search" },
  { name: "Map", route: "/#/map" },
  { name: "Place", route: `/#/place/${MALL_ID}` },
]) {
  test(`${scenario.name} refreshes CoexistenceSnapshot when query context changes`, async ({
    page,
  }) => {
    await page.goto(`${BASE}${scenario.route}`);
    await expect(page.getByTestId("query-context-summary")).toBeVisible({ timeout: 15000 });
    const request = await chooseGuideDog(page);
    expect((request.postDataJSON() as Record<string, unknown>).declared_role).toBe("guide_dog");
  });
}

test("query editor exposes only real query inputs", async ({ page }) => {
  await page.goto(`${BASE}/#/`);
  await page.getByTestId("query-context-edit").click();
  await expect(page.getByRole("button", { name: /普通携带/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /服务犬通行/ })).toBeVisible();
  await expect(page.getByRole("button", { name: /规则视角/ })).toHaveCount(0);
});

test("working service-dog pet persists as the truthful current query object", async ({
  page,
  request,
}) => {
  const token = await signedToken(request);
  const created = await request.post(`${API}/pets`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      display_name: "小白",
      species: "dog",
      breed_text: null,
      weight_kg: null,
      shoulder_height_cm: null,
      service_role: "working",
      registration_status: null,
      vaccination_status: null,
      avatar_url: null,
    },
  });
  expect(created.ok(), await created.text()).toBeTruthy();
  const pet = (await created.json()) as { id: string };

  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);
  await page.goto(`${BASE}/#/pets`);
  await page.getByTestId(`pet-use-${pet.id}`).click();

  await expect(page.getByTestId("query-context-summary")).toContainText("小白");
  await expect(page.getByTestId("query-context-summary")).toContainText("服务犬");
  expect(await page.evaluate(() => localStorage.getItem("pa_active_pet_id"))).toBe(pet.id);

  await page.reload();
  await expect(page.getByTestId("query-context-summary")).toContainText("小白");
  await expect(page.getByTestId("query-context-summary")).toContainText("服务犬");

  await page.getByTestId("query-context-edit").click();
  await expect(page.getByTestId("query-service-role")).toBeVisible();
  await expect(page.getByTestId("query-service-role")).toHaveValue("");
});


test("cold Evidence and Why deep links restore the persisted active pet before resolving", async ({
  page,
  request,
}) => {
  const token = await signedToken(request);
  const created = await request.post(`${API}/pets`, {
    headers: { Authorization: `Bearer ${token}` },
    data: {
      display_name: "深链服务犬",
      species: "dog",
      breed_text: null,
      weight_kg: null,
      shoulder_height_cm: null,
      service_role: "working",
      registration_status: null,
      vaccination_status: null,
      avatar_url: null,
    },
  });
  expect(created.ok(), await created.text()).toBeTruthy();
  const pet = (await created.json()) as { id: string };

  await page.addInitScript(
    ({ accessToken, activePetId }) => {
      localStorage.setItem("pa_token", accessToken);
      localStorage.setItem("pa_active_pet_id", activePetId);
    },
    { accessToken: token, activePetId: pet.id },
  );

  for (const route of [
    `/#/place/${MALL_ID}/evidence`,
    `/#/place/${MALL_ID}/why`,
  ]) {
    const snapshot = page.waitForRequest((req) => {
      if (req.method() !== "POST" || !req.url().includes("/coexistence")) return false;
      const body = req.postDataJSON() as Record<string, unknown>;
      return body.service_role === "working" && body.animal === "dog";
    });
    await page.goto(`${BASE}${route}`);
    const requestRow = await snapshot;
    const body = requestRow.postDataJSON() as Record<string, unknown>;
    expect(body.service_role).toBe("working");
    await expect(page.getByTestId("query-context-summary")).toContainText("深链服务犬");
  }
});
