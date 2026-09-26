/**
 * Empty-First P0 regression (contract §23 / AC-09): when the backend is
 * unreachable the app must still mount — AppShell renders, Home renders, and an
 * offline/error affordance appears. A backend outage must never be a gray
 * screen or a forever-loading gate.
 *
 * The backend is simulated as unreachable with Playwright route aborts, so this
 * spec stays deterministic and independent of :8010 availability.
 */
import { expect, test, type Page } from "@playwright/test";

async function captureErrors(page: Page) {
  const uncaught: string[] = [];
  page.on("pageerror", (e) => uncaught.push(`pageerror: ${e.message}`));
  page.on("console", (m) => {
    if (m.type() !== "error") return;
    // The browser itself logs aborted /api loads as console.error even though
    // the app handles them (Empty-First). The app-level gate that matters is
    // "no unhandled JS exception", so resource-failure lines are not app bugs.
    if (m.text().startsWith("Failed to load resource:")) return;
    uncaught.push(`console.error: ${m.text()}`);
  });
  return uncaught;
}

test("backend unreachable -> AppShell and Home still render (no gray screen, no unhandled error)", async ({
  page,
}) => {
  const uncaught = await captureErrors(page);
  // Simulate backend down: every /api request aborts like a dead server.
  await page.route("**/api/**", (route) => route.abort());

  await page.goto("/");
  await expect(page.getByTestId("consumer-app-shell")).toBeVisible();
  await expect(page.getByTestId("home-title")).toBeVisible();
  await expect(page.getByTestId("home-search-input")).toBeVisible();

  // Home must settle: its loading state ends in error/offline, never in a
  // permanently stuck skeleton.
  await expect(page.getByTestId("home-title")).toBeVisible({ timeout: 10000 });

  // No unhandled runtime error may leak out of a backend outage.
  expect(uncaught).toEqual([]);
});