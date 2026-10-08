/**
 * M4 Map + Place Passport acceptance (A1/A2/A4, B1/B2/B3/B5).
 *
 * Runs on the self-contained E2E stack (petaccess_e2e seeded with the
 * deterministic fixtures — 星河咖啡·测试店 family, CAFE_ID has published rules).
 * The e2e default viewport (1280x720) is desktop, so the map renders in
 * split-view and the PlacePreview pane is present.
 */
import { expect, test } from "@playwright/test";

const BASE = "http://127.0.0.1:5175";
/** Deterministic seed UUID with published rules (h5-journey.spec.ts). */
const CAFE_ID = "8412b521-5e1c-505d-9dec-568acb860c76";
/** Ready fixture (place-ready-v1) — unknown places render the §15 Unknown Overview. */
const MALL_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

test("A4 — /#/map?place= 深链预选；页面选择后 back/forward 同步", async ({ page }) => {
  // Entry 1: deep link opens the desktop pane with the right place.
  await page.goto(`${BASE}/#/map?place=${CAFE_ID}`);
  await expect(page.getByTestId("place-preview")).toBeVisible();
  await expect(page.getByTestId("preview-open")).toHaveAttribute("href", `#/place/${CAFE_ID}`);

  // Entry 2: an unknown place id leaves the pane in its empty hint state.
  await page.goto(`${BASE}/#/map?place=00000000-0000-0000-0000-000000000000`);
  await expect(page.getByTestId("preview-empty")).toBeVisible();

  // Back restores the deep-linked selection; forward re-applies the empty one.
  await page.goBack();
  await expect(page.getByTestId("preview-open")).toHaveAttribute("href", `#/place/${CAFE_ID}`);
  await page.goForward();
  await expect(page.getByTestId("preview-empty")).toBeVisible();
});

test("A4.1 — a Place-to-Map link resolves an exact place outside nearby results", async ({
  page,
}) => {
  // Simulate a user opening a place outside the default camera's nearby
  // result set. The exact place may still be resolved through search by ID.
  await page.route("**/api/v1/places/nearby?*", async (route) => {
    await route.fulfill({
      json: { items: [], total: 0, limit: 30, offset: 0 },
    });
  });

  await page.goto(`${BASE}/#/map?place=${MALL_ID}`);
  await expect(page.getByTestId("map")).toBeVisible();
  await expect(page.getByTestId("place-preview")).toContainText("云栖中心", {
    timeout: 15000,
  });
  await expect(page.getByTestId(`place-${MALL_ID}`)).toBeVisible();
  await expect(page.getByTestId("preview-open")).toHaveAttribute("href", `#/place/${MALL_ID}`);
});

test("A4.2 — Search inspector opens the exact selected place on Map", async ({ page }) => {
  await page.goto(`${BASE}/#/search?q=云栖`);
  const mapLink = page.getByTestId("inspector-map-location");
  await expect(mapLink).toBeVisible({ timeout: 15000 });
  await expect(mapLink).toHaveAttribute("href", `#/map?place=${MALL_ID}`);
  await mapLink.click();
  await expect(page).toHaveURL(/#\/map\?place=/);
  await expect(page.getByTestId("place-preview")).toContainText("云栖中心", {
    timeout: 15000,
  });
});

test("A1 — desktop 地图 split-view + 四 Lens + 详情面板", async ({ page }) => {
  await page.goto(`${BASE}/#/map`);
  await expect(page.getByTestId("map")).toBeVisible();
  for (const lens of ["rule", "reality", "facility", "divergence"]) {
    await expect(page.getByTestId(`map-lens-${lens}`)).toBeVisible();
  }
  // Desktop auto-selects the first hit so the pane is populated, not empty.
  await expect(page.getByTestId("place-preview")).toBeVisible();
  await expect(page.getByTestId("preview-open")).toBeVisible();
});

test("A1.0.1 — fallback marker 不靠颜色单独表达语义", async ({ page }) => {
  await page.goto(`${BASE}/#/map`);
  const marker = page.locator(".dot[data-ui='map-marker']").first();
  await expect(marker).toBeVisible({ timeout: 15000 });
  await expect(marker.locator(".dot__glyph")).not.toHaveText("");
  const pin = marker.locator("xpath=..");
  // Labels are intentionally pointer-transparent so neighboring markers
  // remain clickable. Test the actual glyph's hit target, and keyboard
  // focus as a separate non-color-only path.
  await marker.hover();
  await expect(pin.locator(".lbl")).toBeVisible();
  await pin.focus();
  await expect(pin.locator(".lbl")).not.toHaveText("");
});

test("A1.0.2 — nearby venue cluster is neutral and requires per-place inspection", async ({
  page,
}) => {
  await page.goto(`${BASE}/#/map`);
  const group = page
    .locator(".map-pin")
    .filter({ has: page.locator(".map-cluster") })
    .first();
  await expect(group).toBeVisible({ timeout: 15000 });
  await expect(group).toHaveAttribute("aria-label", /准入结论需分别查看/);
  await expect(group.locator(".map-cluster")).toHaveClass("map-cluster");
});

test("A1.1 — Map 内搜索保持 Spatial Workspace 并选择真实场所", async ({ page }) => {
  await page.goto(`${BASE}/#/map`);
  await expect(page.getByTestId("map-search-input")).toBeVisible();
  await page.getByTestId("map-search-input").fill("云栖中心");
  await page.getByTestId("map-search-submit").click();

  await expect(page).toHaveURL(/#\/map/);
  await expect(page.getByTestId(`place-${MALL_ID}`)).toBeVisible({ timeout: 15000 });
  await expect(page.getByTestId(`place-${MALL_ID}`)).toHaveAttribute("data-selected", "true");
  await expect(page.getByTestId("place-preview")).toContainText("云栖中心");
});

test("A1.2 — mobile map searches without leaving the spatial canvas", async ({ page }) => {
  await page.setViewportSize({ width: 430, height: 932 });
  await page.goto(`${BASE}/#/map`);

  const input = page.getByTestId("map-mobile-search-input");
  await expect(input).toBeVisible();
  await expect(page.getByTestId("map-mobile-locate")).toBeVisible();

  await input.fill("云栖中心");
  await page.getByTestId("map-mobile-search-submit").click();

  await expect(page.getByTestId("map")).toBeVisible();
  await expect(page.getByTestId("map-mobile-sheet")).toContainText("云栖中心", {
    timeout: 15000,
  });
});

test("A1.3 — missing coordinates never create fictional map pins, even in dev", async ({
  page,
}) => {
  await page.route("**/api/v1/places/nearby**", async (route) => {
    const response = await route.fetch();
    const payload = await response.json();
    await route.fulfill({
      status: response.status(),
      contentType: "application/json",
      body: JSON.stringify({
        ...payload,
        items: payload.items.map((place: Record<string, unknown>) => ({
          ...place,
          latitude: null,
          longitude: null,
        })),
      }),
    });
  });
  await page.goto(`${BASE}/#/map`);

  await expect(page.getByTestId("map-surface")).toBeVisible();
  await expect(page.locator(".map-pin")).toHaveCount(0);
  await expect(page.getByTestId("coverage-hint")).toContainText("缺少可用位置坐标");
  await expect(page.getByTestId("coverage-hint")).toContainText("当前查询没有可显示的位置点");
});

test("A1.4 — missing-coordinate named search preserves desktop List + Map", async ({ page }) => {
  await page.route("**/api/v1/places?*", async (route) => {
    const response = await route.fetch();
    const payload = await response.json();
    await route.fulfill({
      status: response.status(),
      contentType: "application/json",
      body: JSON.stringify({
        ...payload,
        items: payload.items.map((place: Record<string, unknown>) => ({
          ...place,
          latitude: null,
          longitude: null,
        })),
      }),
    });
  });
  await page.goto(`${BASE}/#/map`);
  await page.getByTestId("map-search-input").fill("云栖中心");
  await page.getByTestId("map-search-submit").click();

  await expect(page.getByTestId("map")).toBeVisible();
  await expect(page.getByTestId(`place-${MALL_ID}`)).toBeVisible();
  await expect(page.getByTestId("map-search-feedback")).toContainText("缺少可用位置坐标");
  await expect(page.getByTestId("place-preview")).toContainText("云栖中心");
});

test("A1.5 — dragging the fallback map requests places at the new center", async ({ page }) => {
  await page.goto(`${BASE}/#/map`);
  const surface = page.getByTestId("map-surface");
  await expect(surface).toBeVisible();
  const box = await surface.boundingBox();
  expect(box).not.toBeNull();
  if (!box) return;

  const lngChanged = page.waitForRequest((request) => {
    if (!request.url().includes("/api/v1/places/nearby?")) return false;
    const lng = Number(new URL(request.url()).searchParams.get("lng"));
    return Number.isFinite(lng) && Math.abs(lng - 121.47) > 0.001;
  });

  const x = box.x + box.width * 0.4;
  const y = box.y + box.height * 0.24;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + 140, y + 35, { steps: 5 });
  await page.mouse.up();
  await lngChanged;

  await expect(page.getByTestId("map")).toBeVisible();
  await expect(page.getByTestId("map-provider-fallback")).toContainText("示意底图");
});

test("A2 — map 错误统一呈现，不泄漏内部字样", async ({ page }) => {
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ error: { message: "Internal Server Error: psycopg2 at SQLAlchemy" } }),
    }),
  );
  await page.goto(`${BASE}/#/map`);
  await expect(page.locator('[data-state="ERROR"]').first()).toBeVisible();
  const text = await page.evaluate(() => document.body.innerText);
  for (const needle of ["SQLAlchemy", "FastAPI", "psycopg2", "Internal Server Error"]) {
    expect(text, `map must not leak ${needle}`).not.toContain(needle);
  }
});

test("A2 — map 空态使用统一文案（地图暂无已发布场所 + 返回首页）", async ({ page }) => {
  await page.route("**/api/v1/places/nearby**", (route) =>
    route.fulfill({ json: { items: [], total: 0, limit: 20, offset: 0 } }),
  );
  await page.goto(`${BASE}/#/map`);
  await expect(page.getByTestId("map-empty")).toBeVisible();
  await expect(page.getByTestId("map-empty")).toContainText("地图暂无已发布场所");
  await expect(
    page.getByTestId("map-empty").getByRole("button", { name: "返回首页" }),
  ).toBeVisible();
});

test("B1/B2 — Place Dossier 概览 + 规则/现场 view 关键段齐备", async ({ page }) => {
  // §15: unknown places (cafe) show the minimal Unknown Overview, so the
  // dossier overview blocks are asserted on the ready mall fixture; the cafe
  // still serves the rules/reality views (they render regardless of state).
  await page.goto(`${BASE}/#/place/${MALL_ID}`);
  // Rule dimension: answer section with verdict + overview evidence summary.
  await expect(page.getByTestId("section-answer")).toBeVisible();
  await expect(page.getByTestId("overview-evidence")).toBeVisible();
  // Reality dimension visible on the overview too (recent reality block).
  await expect(page.getByTestId("overview-reality")).toBeVisible();
  // Rules view carries the source rows.
  await page.goto(`${BASE}/#/place/${MALL_ID}?view=rules`);
  await expect(page.getByTestId("place-rules-view")).toBeVisible();
  await expect(page.getByTestId("rule-source").first()).toBeVisible();
  // Reality view hosts the shared published v0.9 event log.
  await page.goto(`${BASE}/#/place/${MALL_ID}?view=reality`);
  await expect(page.getByTestId("place-reality-view")).toBeVisible();
  await expect(
    page.getByTestId("place-reality-view").locator("[data-ui='reality-event-log']"),
  ).toBeVisible();
});

test("B2.1 — Space view 展示已核验设施属性且不暗示准入或安全保证", async ({ page }) => {
  await page.goto(`${BASE}/#/place/${MALL_ID}?view=space`);
  await expect(page.getByTestId("animal-facilities")).toBeVisible();
  await expect(page.getByTestId("animal-facility-record").first()).toBeVisible();
  await expect(page.getByTestId("animal-facilities")).toContainText("使用方式");
  await expect(page.getByTestId("animal-facilities")).toContainText("最近核验");
  await expect(page.getByTestId("animal-facilities")).toContainText("不等于允许动物进入");
  await expect(page.getByTestId("animal-facilities")).toContainText("不构成安全");
});

test("B2.2 — 仅有发布时间的设施线索不冒充当前空间设施事实", async ({ page }) => {
  await page.route("**/api/v1/places/*/reality/events**", (route) =>
    route.fulfill({
      json: [
        {
          id: "publication-only-facility",
          event_type: "animal_facility",
          time_evidence_state: "publication_time_only",
          facility_type: "water_bowl",
          facility_purpose_state: "purpose_signage_supported",
          facility_state: "active",
          source_id: null,
        },
      ],
    }),
  );
  await page.goto(`${BASE}/#/place/${MALL_ID}?view=space`);
  await expect(page.getByTestId("animal-facilities")).toBeVisible();
  await expect(page.getByTestId("animal-facility-record")).toHaveCount(0);
  await expect(page.getByTestId("animal-facility-summary-row").first()).toBeVisible();
});

test("B2.3 — Reality keeps the selected zone isolated from other areas", async ({
  page,
  request,
}) => {
  const response = await request.get(`http://127.0.0.1:8010/api/v1/places/${MALL_ID}/zones`);
  expect(response.ok(), await response.text()).toBeTruthy();
  const zones = (await response.json()) as { id: string }[];
  expect(zones.length).toBeGreaterThanOrEqual(2);
  const [first, second] = zones;
  expect(first).toBeDefined();
  expect(second).toBeDefined();

  const makeEvent = (id: string, zoneId: string) => ({
    id,
    place_id: MALL_ID,
    zone_id: zoneId,
    event_type: "observed_presence",
    event_at: "2026-09-24T18:42:00Z",
    time_basis: "observed",
    time_evidence_state: "observed_time_verified",
    verification_status: "verified",
    animal_scope: "dog",
    observed_action: "present",
  });
  await page.route(`**/api/v1/places/${MALL_ID}/reality/events**`, (route) =>
    route.fulfill({
      json: [
        makeEvent("11111111-1111-4111-8111-111111111111", first!.id),
        makeEvent("22222222-2222-4222-8222-222222222222", second!.id),
      ],
    }),
  );
  await page.goto(`${BASE}/#/place/${MALL_ID}/reality?zone=${first!.id}`);

  await expect(page.getByTestId("reality-zone-scope")).toBeVisible();
  await expect(page.locator('[data-ui="reality-event"]')).toHaveCount(1);
  await page.getByRole("link", { name: "查看全部区域" }).click();
  await expect(page.locator('[data-ui="reality-event"]')).toHaveCount(2);
});

test("B2.5 — adding Reality from an empty scoped timeline retains the verified zone", async ({
  page,
  request,
}) => {
  const response = await request.get(`http://127.0.0.1:8010/api/v1/places/${MALL_ID}/zones`);
  expect(response.ok(), await response.text()).toBeTruthy();
  const zones = (await response.json()) as { id: string }[];
  const zoneId = zones[0]?.id;
  expect(zoneId).toBeDefined();

  await page.route(`**/api/v1/places/${MALL_ID}/reality/events**`, (route) =>
    route.fulfill({ json: [] }),
  );
  await page.goto(`${BASE}/#/place/${MALL_ID}/reality?zone=${zoneId}`);
  const contribute = page.getByTestId("reality-go-enter");
  await expect(contribute).toBeVisible();
  await expect(contribute).toHaveAttribute("href", `#/contribute/${MALL_ID}?zone=${zoneId}`);
});

test("B3 — Place Evidence view 证据来源链渲染，无原始枚举", async ({ page }) => {
  await page.goto(`${BASE}/#/place/${CAFE_ID}?view=evidence`);
  await expect(page.getByTestId("place-evidence-view")).toBeVisible();
  await expect(page.getByTestId("evidence-provenance")).toBeVisible();
  const text = await page.evaluate(() => document.body.innerText);
  for (const raw of ["VERIFIED", "PENDING", "DISPUTED", "HISTORICAL"]) {
    expect(text, `raw evidence enum ${raw} must not reach the page`).not.toContain(raw);
  }
});

test("B4.3 — Place identity renders and map CTA reflects coordinate availability", async ({
  page,
}) => {
  await page.goto(`${BASE}/#/place/${MALL_ID}`);
  await expect(page.locator('[data-ui="place-identity"] [data-ui="place-type-glyph"]')).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByTestId("place-map-link")).toContainText("地图定位");

  await page.route(`**/api/v1/places/${MALL_ID}/summary`, async (route) => {
    const response = await route.fetch();
    const payload = await response.json();
    await route.fulfill({
      status: response.status(),
      contentType: "application/json",
      body: JSON.stringify({ ...payload, latitude: null, longitude: null }),
    });
  });
  await page.reload();
  await expect(page.getByTestId("place-map-link")).toContainText("地图列表查看", {
    timeout: 15000,
  });
});

test("B5 — Search DecisionInspector 查看完整场所 → Place Passport", async ({ page }) => {
  // Search the ready mall fixture: the cafe deep-link lands on the §15 Unknown
  // Overview, which has no dossier answer block.
  await page.goto(`${BASE}/#/search?q=云栖`);
  await expect(page.getByTestId("decision-inspector")).toBeVisible();
  await page.getByTestId("inspector-open").click();
  await expect(page.getByTestId("section-answer")).toBeVisible();
});

test("B2.4 — unknown zone links cannot claim another area's Reality or contribution scope", async ({
  page,
}) => {
  const missingZone = "00000000-0000-0000-0000-000000000000";
  await page.goto(`${BASE}/#/place/${MALL_ID}/reality?zone=${missingZone}`);

  await expect(page.getByTestId("reality-zone-scope")).toContainText("所选区域未收录");
  await expect(page.getByText("所选区域无法确认")).toBeVisible();
  await expect(page.getByTestId("reality-go-enter")).toHaveCount(0);
  await expect(page.getByTestId("reality-workspace")).toHaveAttribute("data-ui-state", "empty");
  await page.getByRole("link", { name: "查看全部区域 →" }).click();
  await expect(page).toHaveURL(new RegExp(`#/place/${MALL_ID}/reality$`));
});
