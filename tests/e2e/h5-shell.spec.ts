/**
 * UI-CORE-CLOSURE shell spec — deliberately **offline-safe**.
 *
 * The full journey spec (`h5-journey.spec.ts`) needs the real stack (API :8010 +
 * seeded PostGIS data). This file asserts only what the H5 bundle must render
 * with the API unreachable, so it stays runnable when ENV-01 blocks the
 * database. It is the regression net for the v0.6 surfaces:
 *
 *   map shell · pet profile · privacy controls · notification centre ·
 *   settings/methodology · coexistence boundary
 *
 * Every assertion is on structure the view renders unconditionally, never on
 * API-provided content.
 */
import { expect, test } from "@playwright/test";

test("decision home is search-first and states what is verified", async ({ page }) => {
  await page.goto("/");
  // Consumer UX Baseline v1 §9/§11: the home is a Decision Home, NOT the map.
  await expect(page.getByTestId("home-title")).toBeVisible();
  await expect(page.getByTestId("home-search")).toBeVisible();
  await expect(page.getByTestId("home-search-input")).toBeVisible();
  // the three query perspectives, with 看场所规则 as the default
  await expect(page.getByTestId("perspective-rules")).toBeVisible();
  await expect(page.getByTestId("perspective-rules")).toHaveAttribute("aria-pressed", "true");
  await expect(page.getByTestId("perspective-animal")).toBeVisible();
  await expect(page.getByTestId("perspective-coexist")).toBeVisible();
  // §9.2/§9.4: the map is reachable, but it is a link — not the landing surface
  await expect(page.getByTestId("go-map")).toBeVisible();
  await expect(page.getByTestId("map")).toHaveCount(0);
  // §12.2 + §9.9 wording is stated up front: 「规则待核实」and UNKNOWN ≠ ALLOWED
  await expect(page.getByTestId("home-semantics")).toContainText("规则待核实");
  await expect(page.getByTestId("home-semantics")).toContainText("不等于允许或禁止");
  // §12.6: contribution is a low-priority footer action
  await expect(page.getByTestId("contribute-link")).toBeVisible();
});

test("map is its own tab and renders the full interaction shell", async ({ page }) => {
  await page.goto("/#/map");
  // location state is always labelled, never implied by colour alone
  await expect(page.getByTestId("location-label")).toBeVisible();
  await expect(page.getByTestId("locate-btn")).toBeVisible();
  // map / list toggle exists and switches the primary surface
  await expect(page.getByTestId("view-map")).toBeVisible();
  await page.getByTestId("view-list").click();
  await expect(page.getByTestId("view-list")).toBeVisible();
  await page.getByTestId("view-map").click();
  // Without a reachable API the surface must be EITHER the provider-neutral
  // map renderer OR an explicit ERROR state — never a map with invented pins.
  await expect(page.getByTestId("map").or(page.getByText("加载失败"))).toBeVisible();
});

test("contribution tab asks for a place instead of guessing one", async ({ page }) => {
  // Consumer UX Baseline v1 §21–23: 贡献 is a tab, so it can be opened with no
  // place selected — and it must not invent one.
  await page.goto("/#/contribute");
  await expect(page.getByTestId("contribute-go-search")).toBeVisible();
  await expect(page.getByTestId("contribute-go-map")).toBeVisible();
  // the four entry points stay unavailable until a place is chosen
  await expect(page.getByTestId("entry-quick")).toHaveCount(0);
});

test("pet profile requires auth and offers the login path", async ({ page }) => {
  await page.goto("/#/pets");
  // signed out → PERMISSION_DENIED, and no data is ever submitted
  await expect(page.getByText("需要登录")).toBeVisible();
  // A link, not a button: it navigates to /onboarding, and it used to be a
  // `<button>` nested inside a `<RouterLink>` — two controls, two tab stops,
  // one target too small to hit. Querying by role keeps the test honest about
  // which it is.
  const login = page.getByRole("link", { name: "登录 / 注册" });
  await expect(login).toBeVisible();
  await expect(login).toHaveCount(1);
});

test("privacy controls render the data inventory", async ({ page }) => {
  await page.goto("/#/privacy");
  await expect(page.getByRole("heading", { name: /隐私/ })).toBeVisible();
});

test("notification centre states the channel limitation honestly", async ({ page }) => {
  await page.goto("/#/notifications");
  await expect(page.getByRole("heading", { name: "通知中心" })).toBeVisible();
  // never claims a message was delivered
  await expect(page.getByText(/Mock/)).toBeVisible();
});

test("settings page publishes the methodology and its limits", async ({ page }) => {
  await page.goto("/#/settings");
  await expect(page.getByRole("heading", { name: /设置与说明/ })).toBeVisible();
  await expect(page.getByTestId("methodology")).toBeVisible();
  await expect(page.getByTestId("evidence-strength")).toBeVisible();
  await expect(page.getByTestId("limits")).toBeVisible();
  // the rule layers are named, not implied
  await expect(page.getByTestId("methodology")).toContainText("法定要求");
  await expect(page.getByTestId("methodology")).toContainText("管理方规则");
});

test("coexistence boundary is framed as the user's own preference, not a rating", async ({
  page,
}) => {
  await page.goto("/#/boundary");
  await expect(page.getByRole("heading", { name: "共处边界" })).toBeVisible();
  await expect(page.getByText(/不是对场所的评分/)).toBeVisible();
});

test("place detail degrades to an explicit error state, never a guessed verdict", async ({
  page,
}) => {
  // no API → the page must show an ERROR state rather than inventing a status
  await page.goto("/#/place/00000000-0000-0000-0000-000000000000");
  await expect(page.getByText("加载失败").first()).toBeVisible();
});
