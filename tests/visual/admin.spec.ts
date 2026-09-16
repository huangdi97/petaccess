/**
 * Admin console — real render against the real API.
 *
 * Two things here are easy to get wrong and both were, in an earlier pass:
 * the console uses **history routes** (no `#`), and the login form's submit
 * control is a bare `<button>` inside a `<form>`, so `button[type="submit"]`
 * matches nothing and the suite silently screenshots the login screen seven
 * times. There is also no `/review` or `/publish` page — the review queue is
 * `/rule-candidates`, and publishing is an action on a candidate rather than a
 * destination.
 *
 * Signing in is done through the real form so the baseline covers whatever the
 * console actually does with a credential.
 */
import { expect } from "@playwright/test";

import { freezeClock, settle, shot, test } from "./fixtures";

const EMAIL = "admin@demo-petaccess.com";
const PASSWORD = "admin12345";

test.beforeEach(async ({ page }) => {
  await freezeClock(page);
  await page.goto("/login");
  await settle(page);
  await page.fill('input[type="email"]', EMAIL);
  await page.fill('input[type="password"]', PASSWORD);
  await page.click("form button");
  await page.waitForTimeout(2000);
  // A silent login failure turns every baseline below into a picture of the
  // login page, so fail loudly instead.
  expect(page.url()).not.toContain("/login");
});

test("login", async ({ page }) => {
  await page.goto("/login");
  await settle(page);
  await shot(page, "admin-login");
});

test("dashboard", async ({ page }) => {
  await page.goto("/dashboard");
  await settle(page);
  await shot(page, "admin-dashboard");
});

test("review queue — rule candidates", async ({ page }) => {
  await page.goto("/rule-candidates");
  await settle(page);
  await shot(page, "admin-rule-candidates");
});

test("evidence", async ({ page }) => {
  await page.goto("/evidence");
  await settle(page);
  await shot(page, "admin-evidence");
});

test("sources", async ({ page }) => {
  await page.goto("/sources");
  await settle(page);
  await shot(page, "admin-sources");
});

test("regulations", async ({ page }) => {
  await page.goto("/regulations");
  await settle(page);
  await shot(page, "admin-regulations");
});

test("audit log", async ({ page }) => {
  await page.goto("/audit");
  await settle(page);
  await shot(page, "admin-audit");
});
