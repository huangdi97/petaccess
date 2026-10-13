import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
const API = "http://127.0.0.1:8010/api/v1";
const PLACE_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

async function signIn(request: APIRequestContext): Promise<string> {
  const email = `a11y-${Date.now()}-${Math.floor(Math.random() * 1e6)}@example.com`;
  const password = "passw0rd123";
  const register = await request.post(`${API}/auth/register`, {
    data: { display_name: "A11y Test", email, password },
  });
  expect(register.ok(), await register.text()).toBeTruthy();
  const login = await request.post(`${API}/auth/login`, { data: { email, password } });
  expect(login.ok(), await login.text()).toBeTruthy();
  return (await login.json()).access_token as string;
}

async function auditCurrentSurface(page: Page, label: string): Promise<void> {
  await expect(page.getByTestId("consumer-app-shell")).toBeVisible({ timeout: 15000 });
  await expect(page.locator("[data-ui-page]").first()).toBeVisible({ timeout: 15000 });

  const report = await page.evaluate(() => {
    const isVisible = (element: Element): boolean => {
      if (!(element instanceof HTMLElement)) return false;
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      return (
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        rect.width > 0 &&
        rect.height > 0
      );
    };

    const labelledByText = (element: Element): string => {
      const ids = element.getAttribute("aria-labelledby")?.trim().split(/\s+/).filter(Boolean) ?? [];
      return ids
        .map((id) => document.getElementById(id)?.textContent?.trim() ?? "")
        .filter(Boolean)
        .join(" ");
    };

    const explicitLabel = (element: Element): string => {
      const id = element.id;
      if (!id) return "";
      const escaped = CSS.escape(id);
      return document.querySelector(`label[for="${escaped}"]`)?.textContent?.trim() ?? "";
    };

    const implicitLabel = (element: Element): string =>
      element.closest("label")?.textContent?.trim() ?? "";

    const accessibleName = (element: Element): string =>
      element.getAttribute("aria-label")?.trim() ||
      labelledByText(element) ||
      explicitLabel(element) ||
      implicitLabel(element) ||
      element.getAttribute("title")?.trim() ||
      element.textContent?.trim() ||
      "";

    const interactive = Array.from(
      document.querySelectorAll(
        'button, a[href], input, select, textarea, [role="button"], [role="link"]',
      ),
    ).filter(isVisible);

    const missingNames = interactive
      .filter((element) => {
        if (element instanceof HTMLInputElement && element.type === "hidden") return false;
        return accessibleName(element).length === 0;
      })
      .map((element) => ({
        tag: element.tagName.toLowerCase(),
        testid: element.getAttribute("data-testid"),
        id: element.id || null,
        role: element.getAttribute("role"),
      }));

    const formControls = Array.from(
      document.querySelectorAll("input:not([type=hidden]), select, textarea"),
    ).filter(isVisible);

    const missingFormLabels = formControls
      .filter((element) => {
        const name =
          element.getAttribute("aria-label")?.trim() ||
          labelledByText(element) ||
          explicitLabel(element) ||
          implicitLabel(element);
        return !name;
      })
      .map((element) => ({
        tag: element.tagName.toLowerCase(),
        type: element.getAttribute("type"),
        testid: element.getAttribute("data-testid"),
        id: element.id || null,
        placeholder: element.getAttribute("placeholder"),
      }));

    const ids = Array.from(document.querySelectorAll("[id]"))
      .map((element) => element.id)
      .filter(Boolean);
    const duplicates = [...new Set(ids.filter((id, index) => ids.indexOf(id) !== index))];

    const missingImageAlt = Array.from(document.querySelectorAll("img"))
      .filter(isVisible)
      .filter(
        (image) =>
          !image.hasAttribute("alt") &&
          image.getAttribute("aria-hidden") !== "true" &&
          image.getAttribute("role") !== "presentation",
      )
      .map((image) => image.getAttribute("src")?.slice(0, 120) ?? "(no src)");

    return {
      lang: document.documentElement.lang,
      h1Count: Array.from(document.querySelectorAll("h1")).filter(isVisible).length,
      missingNames,
      missingFormLabels,
      duplicates,
      missingImageAlt,
    };
  });

  expect(report.lang, `${label}: html lang`).toBe("zh-CN");
  expect(report.h1Count, `${label}: visible h1`).toBeGreaterThanOrEqual(1);
  expect(report.duplicates, `${label}: duplicate element ids`).toEqual([]);
  expect(report.missingNames, `${label}: unnamed interactive controls`).toEqual([]);
  expect(report.missingFormLabels, `${label}: unlabeled form controls`).toEqual([]);
  expect(report.missingImageAlt, `${label}: images missing alt semantics`).toEqual([]);
}

test("consumer accessibility contract — public core surfaces", async ({ page }) => {
  const routes = [
    ["/", "home"],
    ["/search", "search"],
    ["/map", "map"],
    [`/place/${PLACE_ID}`, "place"],
    [`/place/${PLACE_ID}/reality`, "reality"],
    [`/place/${PLACE_ID}/evidence`, "evidence"],
    ["/settings", "settings"],
    ["/about", "about"],
  ] as const;

  for (const [route, label] of routes) {
    await page.goto(`${BASE}/#${route}`, { waitUntil: "load" });
    await auditCurrentSurface(page, label);
  }
});

test("consumer accessibility contract — authenticated task surfaces", async ({ page, request }) => {
  const token = await signIn(request);
  await page.addInitScript((value) => localStorage.setItem("pa_token", value), token);

  const routes = [
    [`/contribute/${PLACE_ID}`, "contribution"],
    ["/mine", "mine"],
    ["/privacy", "privacy"],
    ["/boundary", "boundary"],
  ] as const;

  for (const [route, label] of routes) {
    await page.goto(`${BASE}/#${route}`, { waitUntil: "load" });
    await auditCurrentSurface(page, label);
  }
});
