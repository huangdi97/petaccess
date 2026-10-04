import { expect, test, type Page, type APIRequestContext } from "@playwright/test";
import { mkdir } from "node:fs/promises";
import path from "node:path";

const API = "http://127.0.0.1:8012/api/v1";
const OUT = path.resolve("artifacts/ui-direct-secondary");
const PLACE_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

async function signIn(request: APIRequestContext): Promise<string> {
  const email = `secondary-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "Secondary Review", email, password: "passw0rd123" },
  });
  expect(reg.ok(), await reg.text()).toBeTruthy();
  const login = await request.post(`${API}/auth/login`, {
    data: { email, password: "passw0rd123" },
  });
  expect(login.ok(), await login.text()).toBeTruthy();
  return (await login.json()).access_token as string;
}

async function setToken(page: Page, token: string | null) {
  await page.goto("/");
  await page.evaluate((value) => {
    if (value) localStorage.setItem("pa_token", value);
    else localStorage.removeItem("pa_token");
  }, token);
}

async function capture(page: Page, name: string, route: string) {
  await page.goto(route);
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.locator("h1").first().waitFor({ state: "visible", timeout: 15000 });
  await page.waitForTimeout(350);

  const metrics = await page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
    text: document.body.innerText,
  }));
  expect(metrics.scrollWidth).toBeLessThanOrEqual(metrics.clientWidth + 1);
  expect(metrics.text).not.toMatch(
    /[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}/i,
  );
  expect(metrics.text).not.toContain("supersession");
  expect(metrics.text).not.toContain("ADR-");
  expect(metrics.text).not.toContain("lead-only");
  expect(metrics.text).not.toContain("UNKNOWN");
  expect(metrics.text).not.toContain("template layer");
  expect(metrics.text).not.toContain("operator specificity");
  expect(metrics.text).not.toContain("jurisdiction layer");

  await page.screenshot({
    path: path.join(OUT, `${name}.png`),
    fullPage: true,
    animations: "disabled",
  });
}

test("secondary consumer pages inherit the final visual language", async ({
  page,
  request,
}, testInfo) => {
  await mkdir(OUT, { recursive: true });
  const mobile = testInfo.project.name === "oracle-mobile";
  const suffix = mobile ? "mobile" : "desktop";

  await setToken(page, null);
  await capture(page, `onboarding-${suffix}`, "/#/onboarding");

  const token = await signIn(request);
  await setToken(page, token);

  const routes = mobile
    ? [
        ["mine", "/#/mine"],
        ["settings", "/#/settings"],
        ["privacy", "/#/privacy"],
        ["notifications", "/#/notifications"],
        ["pets", "/#/pets"],
        ["pet-new", "/#/pet/new"],
        ["boundary", "/#/boundary"],
        ["about", "/#/about"],
        ["why", `/#/place/${PLACE_ID}/why`],
        ["not-found", "/#/this-route-does-not-exist"],
      ]
    : [
        ["mine", "/#/mine"],
        ["settings", "/#/settings"],
        ["privacy", "/#/privacy"],
        ["notifications", "/#/notifications"],
        ["pets", "/#/pets"],
        ["pet-new", "/#/pet/new"],
        ["boundary", "/#/boundary"],
        ["about", "/#/about"],
        ["why", `/#/place/${PLACE_ID}/why`],
      ];

  for (const [name, route] of routes) {
    await capture(page, `${name}-${suffix}`, route);
  }
});
