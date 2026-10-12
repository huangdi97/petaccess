import { expect, test, type APIRequestContext } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
const API = "http://127.0.0.1:8010/api/v1";

async function signIn(request: APIRequestContext): Promise<string> {
  const email = `boundary-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "边界测试用户", email, password: "passw0rd123" },
  });
  expect(reg.ok(), `register failed: ${await reg.text()}`).toBeTruthy();

  const login = await request.post(`${API}/auth/login`, {
    data: { email, password: "passw0rd123" },
  });
  expect(login.ok(), `login failed: ${await login.text()}`).toBeTruthy();
  return (await login.json()).access_token as string;
}

test("boundary preferences stay honest and overflow-free on phone widths", async ({
  page,
  request,
}) => {
  const token = await signIn(request);
  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);

  for (const width of [320, 360, 390, 430]) {
    await page.setViewportSize({ width, height: width === 320 ? 568 : 844 });
    await page.goto(`${BASE}/#/boundary`, { waitUntil: "load" });

    const surface = page.locator('[data-ui-page="boundary"]');
    await expect(surface).toBeVisible({ timeout: 15000 });
    await expect(surface).toHaveAttribute("data-ui-state", "ready");

    const rows = page.getByTestId("boundary-attr");
    await expect(rows).toHaveCount(10);

    // A new profile must remain explicitly unset. UI polish must never turn an
    // unanswered preference into an inferred preference.
    const unsetChoices = page.locator('[data-testid^="stance-"][data-testid$="-unset"]');
    await expect(unsetChoices).toHaveCount(10);
    for (const choice of await unsetChoices.all()) {
      await expect(choice).toBeChecked();
    }

    await expect(page.getByTestId("boundary-selected-count")).toHaveText("已设置 0 / 10");

    const layout = await page.evaluate(() => {
      const root = document.documentElement;
      const choices = Array.from(document.querySelectorAll<HTMLElement>(".boundary-choices")).map(
        (element) => {
          const rect = element.getBoundingClientRect();
          return { left: rect.left, right: rect.right, width: rect.width };
        },
      );
      return {
        viewportWidth: window.innerWidth,
        scrollWidth: root.scrollWidth,
        choices,
      };
    });

    expect(layout.scrollWidth, `boundary page overflow at ${width}px`).toBeLessThanOrEqual(
      layout.viewportWidth + 1,
    );
    for (const choice of layout.choices) {
      expect(
        choice.left,
        `segmented control starts outside viewport at ${width}px`,
      ).toBeGreaterThanOrEqual(-1);
      expect(
        choice.right,
        `segmented control ends outside viewport at ${width}px`,
      ).toBeLessThanOrEqual(layout.viewportWidth + 1);
    }
  }
});

test("choosing and clearing a boundary stance preserves explicit unset semantics", async ({
  page,
  request,
}) => {
  const token = await signIn(request);
  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);
  await page.goto(`${BASE}/#/boundary`, { waitUntil: "load" });

  const avoid = page.getByTestId("stance-off_leash-avoid");
  const unset = page.getByTestId("stance-off_leash-unset");

  await expect(unset).toBeChecked({ timeout: 15000 });
  await avoid.check();
  await expect(avoid).toBeChecked();
  await expect(page.getByTestId("boundary-selected-count")).toHaveText("已设置 1 / 10");

  await unset.check();
  await expect(unset).toBeChecked();
  await expect(page.getByTestId("boundary-selected-count")).toHaveText("已设置 0 / 10");
});
