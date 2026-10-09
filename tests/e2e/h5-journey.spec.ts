/**
 * G17 Playwright E2E: H5 core journey against the real stack
 * (API on :8010, H5 on :5175, seeded demo data).
 */
import { expect, test } from "@playwright/test";

const CAFE_ID = "8412b521-5e1c-505d-9dec-568acb860c76"; // deterministic seed UUID
const BRANCH_ID = "3b5a341a-e550-5f0c-b35a-319ed43bd840"; // 星河咖啡·栖霞分店, 0 rules → UNKNOWN

test("health and decision home render nearby places", async ({ page }) => {
  await page.goto("/");
  // Consumer UX Baseline v1 §9/§11: the landing surface is the Decision Home
  // (search-first). The map moved to its own tab.
  await expect(page.getByTestId("home-title")).toBeVisible();
  await expect(page.getByTestId("home-search-input")).toBeVisible();
  await expect(page.getByText("附近已有依据")).toBeVisible();
  await expect(page.getByRole("heading", { name: "附近待补充" })).toBeVisible();

  // the map tab still renders the full shell; desktop is List+Map split so the
  // result pane is already visible without any 地图/列表 mode toggle (§32).
  await page.goto("/#/map");
  await expect(page.getByTestId("map")).toBeVisible();
  await expect(page.getByRole("heading", { name: "附近场所" })).toBeVisible();
  await expect(page.getByText("星河咖啡·测试店").first()).toBeVisible();
  await expect(page.getByText("青岚公园·演示").first()).toBeVisible();
});

test("place detail shows one-sentence answer with zones and provenance", async ({ page }) => {
  // v0.2.5 §15: unknown places render the minimal Unknown Overview, so the
  // full dossier (answer/zones/evidence) is asserted on the ready mall fixture.
  const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";
  await page.goto(`/#/place/${MALL_ID}`);
  const answer = page.getByTestId("answer");
  await expect(answer).toBeVisible();
  // Mall verdict for a plain dog is conditional (carrier rule); the answer
  // references the query context line, never a flattened zone verdict.
  await expect(page.getByTestId("answer-status")).toContainText("有条件");
  await expect(page.getByTestId("overview-reality")).toBeVisible();
  const basics = page.getByTestId("overview-basics");
  await expect(basics).toBeVisible();
  await expect(basics).toContainText("商场");
  await expect(basics).toContainText("空间记录");
  // space summary shows the mall's first zones by consumer name
  const zones = page.getByTestId("overview-zones");
  await expect(zones).toContainText("一层");
  // rules view (v0.2.4 §23) carries the conditions & provenance
  await page.goto(`/#/place/${MALL_ID}?view=rules`);
  await expect(page.getByTestId("place-rules-view")).toBeVisible();
  await expect(page.getByTestId("place-rules-view")).toContainText("需宠物包");
  // evidence summary on the overview
  await page.goto(`/#/place/${MALL_ID}`);
  await expect(page.getByTestId("overview-evidence")).toBeVisible();
});

test("mode switch re-evaluates: service dog → allowed", async ({ page }) => {
  await page.goto(`/#/place/${CAFE_ID}`);
  // plain dog at place level: no place-scoped ordinary-pet rule → UNKNOWN
  // (v0.2.5 §15 renders the minimal Unknown Overview, not a dossier).
  await expect(page.getByTestId("place-unknown")).toBeVisible();
  await expect(page.getByTestId("place-unknown")).toContainText("信息不足");
  // Query Context primitive: open the editor and switch to service-dog mode.
  await page.getByTestId("query-context-edit").click();
  await page.getByRole("button", { name: "服务犬通行" }).click();
  // service-dog mode asks as a working (assistance) dog → place-level allowed
  await expect(page.getByTestId("inspector-verdict")).toHaveText("可以进入");
  await page.getByTestId("query-context-edit").click();
  await page.getByRole("button", { name: "普通携带" }).click();
  await expect(page.getByTestId("place-unknown")).toBeVisible();
  await expect(page.getByTestId("place-unknown")).toContainText("信息不足");
});

/**
 * Regression: switching between two places must re-render the second one.
 *
 * Vue Router reuses `PlaceView` across `/place/:id` changes, and the component
 * used to read `route.params.id` once at setup — so a param change left the
 * previous place on screen. The URL said one place, the page showed another:
 * for a rule-lookup product, another place's rules under this place's name.
 *
 * A hash-only navigation is exactly what an in-app link and a back/forward step
 * produce, so it exercises the path that `page.goto` on a fresh URL never would
 * (a full load always remounts and hid the bug).
 */
test("switching between two places re-renders the second one", async ({ page }) => {
  await page.goto(`/#/place/${CAFE_ID}`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("星河咖啡·测试店");

  await page.goto(`/#/place/${BRANCH_ID}`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("星河咖啡·栖霞分店");
  // the unknown overview has to belong to the new place too, not just the title
  await expect(page.getByTestId("place-unknown")).toBeVisible();
  await expect(page.getByTestId("place-unknown")).toContainText("信息不足");

  // Same mechanism from the user's side: history back and forward.
  await page.goBack();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("星河咖啡·测试店");
  await page.goForward();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("星河咖啡·栖霞分店");
});
test("search finds place by fuzzy name", async ({ page }) => {
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("星河");
  await page.getByTestId("search-btn").click();
  await expect(page.getByTestId(`result-${CAFE_ID}`)).toBeVisible();
});

test("same-brand branches come back as two labelled rows, answer first", async ({ page }) => {
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("星河咖啡");
  await page.getByTestId("search-btn").click();

  const flagship = page.getByTestId(`result-${CAFE_ID}`);
  const branch = page.getByTestId(`result-${BRANCH_ID}`);
  await expect(flagship).toBeVisible();
  await expect(branch).toBeVisible();

  // v0.2.4 §11：rows no longer carry a separate 所属-brand meta line; each row
  // is its own place with its own name (the parent-name line was removed).
  await expect(branch.getByTestId("result-branch")).toHaveCount(0);

  // Canonical search is Reality-first by default while Rule status remains
  // visible in the same row. Internal rule/source tallies stay out of the list.
  await expect(flagship.getByTestId("row-lens-headline")).toHaveCount(1);
  await expect(branch.getByTestId("row-lens-headline")).toHaveCount(1);
  await expect(page.getByTestId("result-rules")).toHaveCount(0);
  // The branch with stronger governed context remains the first ranked row.
  await expect(page.locator("ul.result-list > li").first()).toContainText("星河咖啡·测试店");
});

test("register → create pet → answer carries pet context → quick confirm", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;

  // register
  await page.goto("/#/onboarding");
  await page.getByRole("tab", { name: "注册", exact: true }).click();
  await page.locator("input").nth(0).fill("E2E 用户");
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill("passw0rd123");
  await page.getByRole("button", { name: "注册并开始" }).click();
  await expect(page).toHaveURL(/#\/$/);

  // create pet 豆豆
  await page.goto("/#/pet/new");
  await page.getByTestId("pet-name").fill("豆豆");
  await page.getByTestId("pet-weight").fill("9.5");
  await page.getByTestId("pet-save").click();
  await expect(page).toHaveURL(/#\/$/);

  // place answer references the pet (ready fixture: the cafe is UNKNOWN and
  // v0.2.5 §15 shows its minimal Unknown Overview without an answer block).
  await page.goto(`/#/place/5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e`);
  await expect(page.getByTestId("answer")).toContainText("我的宠物：豆豆");

  // quick confirm requires auth → succeeds and records
  await page.getByRole("button", { name: "仍然如此" }).first().click();
  await expect(page.getByTestId("quick-msg")).toContainText("已记录");
});

/**
 * v0.5 journey: coexistence boundary -> explainable match.
 *
 * Verifies the two new H5 surfaces reach real API data and that the boundary
 * result stays per-item (no total score) with missing data reported as UNKNOWN
 * rather than coerced into a verdict.
 */
test("v0.5: set coexistence boundary and boundary-match explains per item", async ({ page }) => {
  const email = `e2e-bnd-${Date.now()}@example.com`;

  // register (a boundary profile is user-scoped)
  await page.goto("/#/onboarding");
  await page.getByRole("tab", { name: "注册", exact: true }).click();
  await page.locator("input").nth(0).fill("边界 E2E");
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill("passw0rd123");
  await page.getByRole("button", { name: "注册并开始" }).click();
  await expect(page).toHaveURL(/#\/$/);

  // set one stance: indoor_access -> require_prohibited
  await page.goto("/#/boundary");
  await expect(page.getByRole("heading", { name: "共处边界" })).toBeVisible();
  await page.getByTestId("stance-indoor_access-require_prohibited").click();
  await page.getByTestId("boundary-save").click();
  await expect(page.getByTestId("boundary-msg")).toContainText("已保存");

  // reload: the saved stance is restored (server-persisted, not local state)
  await page.goto("/#/boundary");
  await expect(page.getByTestId("stance-indoor_access-require_prohibited")).toHaveClass(/active/);

  // the explainable-match page shows the per-item comparison
  await page.goto(`/#/place/${CAFE_ID}/why`);
  await expect(page.getByTestId("effective-effect")).toBeVisible();
  await expect(page.getByTestId("boundary-section")).toBeVisible();
  await expect(page.getByTestId("boundary-item").first()).toBeVisible();
  // per-item verdict vocabulary only -- never a numeric score
  await expect(page.getByTestId("boundary-section")).toContainText("无总分");
});

test("v0.5: explainable match shows derivation steps", async ({ page }) => {
  await page.goto(`/#/place/${CAFE_ID}/why`);
  const rules = page.getByTestId("effective-rules");
  await expect(rules).toBeVisible();
  await expect(rules).toContainText("推导过程");
  // compliance state is one of the closed vocabulary
  await expect(rules).toContainText(/各层一致|存在潜在冲突|需人工复核|信息不足/);
});
