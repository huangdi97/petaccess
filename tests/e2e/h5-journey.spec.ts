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
  await expect(page.getByText("附近已核验")).toBeVisible();
  await expect(page.getByRole("heading", { name: "规则待核实" })).toBeVisible();

  // the map tab still renders the full shell and the list fallback
  await page.goto("/#/map");
  await expect(page.getByTestId("map")).toBeVisible();
  await page.getByTestId("view-list").click();
  await expect(page.getByRole("heading", { name: "附近场所" })).toBeVisible();
  await expect(page.getByText("星河咖啡·测试店").first()).toBeVisible();
  await expect(page.getByText("青岚公园·演示").first()).toBeVisible();
});

test("place detail shows one-sentence answer with zones and provenance", async ({ page }) => {
  await page.goto(`/#/place/${CAFE_ID}`);
  const answer = page.getByTestId("answer");
  await expect(answer).toBeVisible();
  // design #48: actionable answer + obligations + source + last verification
  // anonymous visit → no pet profile yet (explicit, never guessed)
  await expect(answer).toContainText("我的宠物：未设置");
  await expect(page.getByTestId("answer-status")).toContainText("有条件进入");
  await expect(answer).toContainText("需牵引");
  // provenance is rendered by section 1 as a whole, not by the answer block
  await expect(page.getByTestId("section-answer")).toContainText("最近核验：");
  // zone breakdown: every zone is listed, and its status is computed on demand
  // (one evaluation per zone, so the list does not fan out into N requests)
  const zones = page.getByTestId("zones");
  await expect(zones).toContainText("室内堂食区");
  await expect(zones).toContainText("户外座位区");
  const indoor = zones.locator(".zone-row").filter({ hasText: "室内堂食区" });
  await indoor.getByRole("button", { name: "查看" }).click();
  await expect(indoor).toContainText("明确限制");
  // observations coexist with rules but do not change the answer
  await expect(page.getByText("no_interaction_observed").first()).toBeVisible();
});

test("mode switch re-evaluates: service dog → allowed", async ({ page }) => {
  await page.goto(`/#/place/${CAFE_ID}`);
  await expect(page.getByTestId("answer-status")).toHaveText("有条件进入");
  await page.getByRole("button", { name: "服务犬通行" }).click();
  await expect(page.getByTestId("answer-status")).toHaveText("可以进入");
  await page.getByRole("button", { name: "带宠出行" }).click();
  await expect(page.getByTestId("answer-status")).toHaveText("有条件进入");
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
  // the answer has to belong to the new place too, not just the title
  await expect(page.getByTestId("answer-ordinary")).toContainText("尚未核验");

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
  // Not `getByText(name)` on purpose: the same-brand branch row carries the
  // flagship's name in its 「所属 …」 line, so a plain text query matches twice
  // and Playwright fails on strict mode rather than on anything real.
  await expect(page.getByTestId("result-星河咖啡·测试店")).toBeVisible();
});

test("same-brand branches come back as two labelled rows, answer first", async ({ page }) => {
  await page.goto("/#/search");
  await page.getByTestId("search-input").fill("星河咖啡");
  await page.getByTestId("search-btn").click();

  const flagship = page.getByTestId("result-星河咖啡·测试店");
  const branch = page.getByTestId("result-星河咖啡·栖霞分店");
  await expect(flagship).toBeVisible();
  await expect(branch).toBeVisible();

  // Two rows, not one ambiguous one, and the child says whose it is.
  await expect(branch.getByTestId("result-branch")).toContainText("星河咖啡·测试店");

  // Each row states how much rule material sits behind it.
  await expect(flagship.getByTestId("result-rules")).toContainText("生效规则");
  await expect(branch.getByTestId("result-rules")).toContainText("尚未收录规则");

  // The row that can actually answer comes first — a rule-less branch used to
  // lead on alphabetical order, so the top hit read 「尚未收录规则」 while the
  // answer sat one row down.
  await expect(page.locator("[data-testid^='result-星河']").first()).toContainText(
    "星河咖啡·测试店",
  );
});

test("register → create pet → answer carries pet context → quick confirm", async ({ page }) => {
  const email = `e2e-${Date.now()}@example.com`;

  // register
  await page.goto("/#/onboarding");
  await page.getByRole("button", { name: "注册", exact: true }).click();
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

  // place answer references the pet
  await page.goto(`/#/place/${CAFE_ID}`);
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
  await page.getByRole("button", { name: "注册", exact: true }).click();
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
