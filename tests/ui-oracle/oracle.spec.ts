/**
 * UI Oracle — oracle.spec.ts
 *
 * Drives the deterministic visual stack (petaccess_visual seed, API :8011,
 * H5 preview :5175) and, for every contract JSON in docs/ui/contracts/json/,
 * visits each page at the contract viewport, measures elements / structure /
 * density in-page (probe.ts), scans visible text (language), screenshots each
 * state, and writes raw probe JSON to artifacts/blind-ui-recovery/probes/.
 *
 * Screenshots are evidence artifacts; the PASS/WARN/FAIL verdict lives in
 * compare.ts. Stage = UI_ORACLE_STAGE (baseline | phase-a | ... | final).
 * Projects = oracle-desktop / oracle-mobile; each test overrides the viewport
 * from its contract and filters by project.
 */
import { mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";

import { expect, test } from "@playwright/test";

import type { ContractSchema, PageDef } from "../../tools/ui-oracle/contracts.ts";
import { pageEval } from "../../tools/ui-oracle/page-eval.ts";
import {
  checkCollapsed,
  countFirstViewportTextLines,
  firstEl,
  leftRelativeToPane,
  measureBudget,
  measureComposition,
  measureDensity,
  measureElement,
  measureHierarchy,
  measureState,
  measureStructure,
  pxValue,
  resolveSelector,
  scanLanguage,
  scanRefs,
  visibleLinesIn,
  widestChildRatio,
} from "../../tools/ui-oracle/probe.ts";

const STAGE = process.env.UI_ORACLE_STAGE ?? "baseline";
const CONTRACTS_DIR = "docs/ui/contracts/json";
const OUT_DIR = path.resolve("artifacts/blind-ui-recovery/probes");
const SCREEN_DIR = path.resolve("artifacts/blind-ui-recovery/screens", STAGE);

function loadContractRows(): Array<{ id: string; viewport: { width: number; height: number } }> {
  return readdirSync(CONTRACTS_DIR)
    .filter((f) => f.endsWith(".json"))
    .map((f) => {
      const raw = JSON.parse(readFileSync(path.join(CONTRACTS_DIR, f), "utf8")) as ContractSchema;
      return { id: raw.id, viewport: raw.viewport };
    });
}

const CONTRACTS = loadContractRows();

/** In-page helpers are injected as `const` bindings by pageEval, so the
 * serialized probe wrappers below reference them by name lexically. */
const ELEMENT_HELPERS: Record<string, (...args: never[]) => unknown> = {
  measureElement: measureElement as unknown as (...args: never[]) => unknown,
  resolveSelector: resolveSelector as unknown as (...args: never[]) => unknown,
  leftRelativeToPane: leftRelativeToPane as unknown as (...args: never[]) => unknown,
};

const STRUCTURE_HELPERS: Record<string, (...args: never[]) => unknown> = {
  measureStructure: measureStructure as unknown as (...args: never[]) => unknown,
  checkCollapsed: checkCollapsed as unknown as (...args: never[]) => unknown,
};

const DENSITY_HELPERS: Record<string, (...args: never[]) => unknown> = {
  measureDensity: measureDensity as unknown as (...args: never[]) => unknown,
};

const HIERARCHY_HELPERS: Record<string, (...args: never[]) => unknown> = {
  measureHierarchy: measureHierarchy as unknown as (...args: never[]) => unknown,
  firstEl: firstEl as unknown as (...args: never[]) => unknown,
  pxValue: pxValue as unknown as (...args: never[]) => unknown,
};

const BUDGET_HELPERS: Record<string, (...args: never[]) => unknown> = {
  measureBudget: measureBudget as unknown as (...args: never[]) => unknown,
  visibleLinesIn: visibleLinesIn as unknown as (...args: never[]) => unknown,
  countFirstViewportTextLines: countFirstViewportTextLines as unknown as (
    ...args: never[]
  ) => unknown,
  pxValue: pxValue as unknown as (...args: never[]) => unknown,
};

const COMPOSITION_HELPERS: Record<string, (...args: never[]) => unknown> = {
  measureComposition: measureComposition as unknown as (...args: never[]) => unknown,
  widestChildRatio: widestChildRatio as unknown as (...args: never[]) => unknown,
};

const STATE_HELPERS: Record<string, (...args: never[]) => unknown> = {
  measureState: measureState as unknown as (...args: never[]) => unknown,
};
export interface ElementMeasurementShape {
  x: number | null;
  y: number | null;
  width: number | null;
  height: number | null;
  fontSize: string | null;
  fontWeight: string | null;
  lineHeight: string | null;
  padding: string | null;
  margin: string | null;
  borderRadius: string | null;
  boxShadow: string | null;
  backgroundColor: string | null;
  position: string | null;
  overflow: string | null;
  gap: string | null;
  borderBottomWidth: string | null;
  gridTemplateColumns: string | null;
  ariaLabel: string;
  count: number;
  maxChildWidth: number | null;
  contentHeightInViewport: number | null;
  leftRelative: number | null;
  sectionGapAvg: number | null;
  scrollWidth: number | null;
  clientWidth: number | null;
  rows: Array<{ height: number | null; borderRadius: string | null }>;
}

async function settle(page: import("@playwright/test").Page): Promise<void> {
  await page.waitForLoadState("networkidle").catch(() => {});
  await page
    .waitForFunction(() => document.querySelectorAll('[class*="skeleton"]').length === 0, {
      timeout: 12000,
    })
    .catch(() => {});
  await page.waitForTimeout(250);
}

async function freezeMotion(page: import("@playwright/test").Page): Promise<void> {
  await page.addStyleTag({
    content: "* { transition: none !important; animation: none !important; }",
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
}

async function visibleCountOf(
  page: import("@playwright/test").Page,
  selector: string,
): Promise<number> {
  return page.evaluate((sel) => {
    const nodes = Array.from(document.querySelectorAll(sel));
    return nodes.filter((n) => {
      const r = n.getBoundingClientRect();
      const cs = getComputedStyle(n);
      return cs.display !== "none" && cs.visibility !== "hidden" && r.width > 0 && r.height > 0;
    }).length;
  }, selector);
}

async function probeElement(
  page: import("@playwright/test").Page,
  rule: { ui?: string; fallbacks?: string[] },
): Promise<unknown> {
  const flat = (await pageEval(page, {
    fn: (a: unknown) => {
      const arg = a as { ui?: string; fallbacks?: string[] };
      return measureElement(document.body, arg.ui, arg.fallbacks);
    },
    helpers: ELEMENT_HELPERS,
    arg: { ui: rule.ui ?? undefined, fallbacks: rule.fallbacks ?? [] },
  })) as unknown as ElementMeasurementShape;

  return {
    bbox: { x: flat.x, y: flat.y, width: flat.width, height: flat.height },
    computed: {
      fontSize: flat.fontSize,
      fontWeight: flat.fontWeight,
      lineHeight: flat.lineHeight,
      padding: flat.padding,
      margin: flat.margin,
      borderRadius: flat.borderRadius,
      boxShadow: flat.boxShadow,
      backgroundColor: flat.backgroundColor,
      position: flat.position,
      overflow: flat.overflow,
      gap: flat.gap,
      borderBottomWidth: flat.borderBottomWidth,
      gridTemplateColumns: flat.gridTemplateColumns,
    },
    ariaLabel: flat.ariaLabel,
    count: flat.count,
    maxChildWidth: flat.maxChildWidth,
    contentHeightInViewport: flat.contentHeightInViewport,
    leftRelative: flat.leftRelative,
    sectionGapAvg: flat.sectionGapAvg,
    scrollWidth: flat.scrollWidth,
    clientWidth: flat.clientWidth,
    rows: flat.rows,
  };
}

interface StructureRuleArg {
  selector: string;
  fallbackSelector?: string;
  forbiddenClass?: string[];
  forbiddenText?: string[];
  mustContainText?: string;
  mustContainTexts?: string[];
  containsArrows?: boolean;
  surfaceRowCount?: { min?: number; max?: number };
  disclosureDefault?: "collapsed";
  xConsistent?: boolean;
}

interface StructureMeasurementShape {
  count: number;
  sampleClasses: string[];
  sampleText: string;
  surfaceRows: number;
  forbiddenTextHits: string[];
  missingRequiredTexts: string[];
  hasArrows: boolean;
  collapsed: boolean;
  xSpread: number | null;
  visibleInViewport: number;
}

async function probeStructure(
  page: import("@playwright/test").Page,
  rule: StructureRuleArg,
): Promise<unknown> {
  const raw = (await pageEval(page, {
    fn: (a: unknown) => measureStructure(document.body, a as StructureRuleArg),
    helpers: STRUCTURE_HELPERS,
    arg: rule,
  })) as unknown as StructureMeasurementShape;
  return {
    count: raw.count,
    sampleClasses: raw.sampleClasses,
    sampleText: raw.sampleText,
    surfaceRows: raw.surfaceRows,
    hasArrows: raw.hasArrows,
    collapsed: raw.collapsed,
    visibleInViewport: raw.visibleInViewport,
    details: {
      forbiddenTextHits: raw.forbiddenTextHits,
      missingRequiredTexts: raw.missingRequiredTexts,
    },
    xSpread: raw.xSpread,
  };
}

interface DensityRuleArg {
  selector: string;
  fallbackSelector?: string;
}

async function probeDensity(
  page: import("@playwright/test").Page,
  rule: DensityRuleArg | null,
): Promise<unknown> {
  return pageEval(page, {
    fn: (a: unknown) => measureDensity(document.body, a as DensityRuleArg | null),
    helpers: DENSITY_HELPERS,
    arg: rule,
  });
}

export interface HierarchyArgShape {
  a: string;
  b: string;
}

async function probeHierarchy(
  page: import("@playwright/test").Page,
  rule: HierarchyArgShape,
): Promise<unknown> {
  return pageEval(page, {
    fn: (a: unknown) => measureHierarchy(document.body, a as HierarchyArgShape),
    helpers: HIERARCHY_HELPERS,
    arg: rule,
  });
}

export interface BudgetArgShape {
  metric: "rowTextLines" | "firstViewportBlocks" | "firstViewportTextLines";
  selector?: string;
}

async function probeBudget(
  page: import("@playwright/test").Page,
  rule: BudgetArgShape,
): Promise<unknown> {
  return pageEval(page, {
    fn: (a: unknown) => measureBudget(document.body, a as BudgetArgShape),
    helpers: BUDGET_HELPERS,
    arg: rule,
  });
}

export interface CompositionArgShape {
  metric:
    | "contentOccupancy"
    | "inspectorOccupancy"
    | "largestVerticalGap"
    | "primaryStatusRepeatCount"
    | "semanticBlockCount";
  selector?: string;
  container?: string;
  text?: string;
}

async function probeComposition(
  page: import("@playwright/test").Page,
  rule: CompositionArgShape,
): Promise<unknown> {
  return pageEval(page, {
    fn: (a: unknown) => measureComposition(document.body, a as CompositionArgShape),
    helpers: COMPOSITION_HELPERS,
    arg: rule,
  });
}

async function probeState(page: import("@playwright/test").Page): Promise<unknown> {
  return pageEval(page, {
    fn: () => measureState(document.body, null),
    helpers: STATE_HELPERS,
  });
}

async function probeLanguage(page: import("@playwright/test").Page) {
  const text = await page.evaluate(() => document.body.innerText);
  const base = scanLanguage(text);
  return { ...base, refHits: scanRefs(text) };
}

async function runInteractions(
  page: import("@playwright/test").Page,
  pageDef: PageDef,
): Promise<void> {
  for (const interaction of pageDef.interactions ?? []) {
    for (const sel of interaction.clickSelectors ?? []) {
      const loc = page.locator(sel).first();
      if (await loc.count()) {
        await loc.click().catch(() => {});
      }
    }
    if (interaction.waitForSelector) {
      await page.waitForSelector(interaction.waitForSelector, { timeout: 3000 }).catch(() => {});
    }
  }
}

/** Sign a fresh user in through the oracle stack API (same flow as the
 * contribute-wizard e2e): register + login, then put the token into the page's
 * localStorage so the app session restore finds it. */
async function signIn(request: import("@playwright/test").APIRequestContext): Promise<string> {
  const API = "http://127.0.0.1:8012/api/v1";
  const email = `oracle-${Date.now()}-${Math.floor(Math.random() * 1e5)}@example.com`;
  const reg = await request.post(`${API}/auth/register`, {
    data: { display_name: "Oracle 探针", email, password: "passw0rd123" },
  });
  expect(reg.ok(), `register failed: ${await reg.text()}`).toBeTruthy();
  const login = await request.post(`${API}/auth/login`, {
    data: { email, password: "passw0rd123" },
  });
  expect(login.ok()).toBeTruthy();
  return (await login.json()).access_token as string;
}

async function runContract(
  page: import("@playwright/test").Page,
  request: import("@playwright/test").APIRequestContext,
  contract: ContractSchema,
): Promise<void> {
  const pagesRow: unknown[] = [];
  for (const pageDef of contract.pages) {
    await page.setViewportSize(contract.viewport);
    if (pageDef.auth) {
      // Authenticated page: seed pa_token on the app origin before visiting so
      // the entry flow (not the login guard) is what gets measured.
      const token = await signIn(request);
      await page.goto("/");
      await page.evaluate((t) => localStorage.setItem("pa_token", t), token);
    }
    await page.goto(pageDef.route);
    await freezeMotion(page);
    await settle(page);
    await expect(page.getByTestId("consumer-app-shell").first()).toBeVisible({ timeout: 15000 });

    // Interactions (e.g. mobile filter bottom sheet) run FIRST so every probe
    // below measures the DOM state the screenshot will actually show — sheet
    // radius/geometry only exists while the sheet is open (O6 honesty).
    await runInteractions(page, pageDef);

    const elements: Record<string, unknown> = {};
    for (const rule of contract.elements ?? []) {
      elements[rule.id] = await probeElement(page, rule);
    }
    const structure: Record<string, unknown> = {};
    for (const rule of contract.structure ?? []) {
      structure[rule.id] = await probeStructure(page, rule);
    }
    const density: Record<string, unknown> = {};
    for (const rule of contract.density ?? []) {
      density[rule.id] = await probeDensity(
        page,
        rule.selector ? { selector: rule.selector, fallbackSelector: rule.selector } : null,
      );
    }
    const hierarchy: Record<string, unknown> = {};
    for (const rule of contract.hierarchy ?? []) {
      hierarchy[rule.id] = await probeHierarchy(page, rule);
    }
    const budget: Record<string, unknown> = {};
    for (const rule of contract.budget ?? []) {
      budget[rule.id] = await probeBudget(page, rule);
    }
    const composition: Record<string, unknown> = {};
    for (const rule of contract.composition ?? []) {
      composition[rule.id] = await probeComposition(page, rule);
    }
    const language = await probeLanguage(page);
    for (const rule of contract.structure ?? []) {
      if (rule.minVisibleAfterClick !== undefined) {
        const v = await visibleCountOf(page, rule.selector);
        (structure[rule.id] as { visibleCountAfterClick?: number }).visibleCountAfterClick = v;
      }
    }
    const state = await probeState(page);

    const shotName = `${contract.id}-${pageDef.id}.png`;
    await page.screenshot({ path: path.join(SCREEN_DIR, shotName), fullPage: false });

    pagesRow.push({
      pageId: pageDef.id,
      route: pageDef.route,
      elements,
      structure,
      density,
      hierarchy,
      budget,
      composition,
      state,
      language,
      screenshot: shotName,
    });
  }

  mkdirSync(OUT_DIR, { recursive: true });
  writeFileSync(
    path.join(OUT_DIR, `${STAGE}-${contract.id}.json`),
    JSON.stringify(
      {
        contractId: contract.id,
        viewport: contract.viewport,
        stage: STAGE,
        generatedAt: new Date().toISOString(),
        pages: pagesRow,
      },
      null,
      2,
    ),
  );
}

for (const contractRow of CONTRACTS) {
  test(`oracle ${contractRow.id} @ ${contractRow.viewport.width}x${contractRow.viewport.height}`, async ({
    page,
    request,
  }, testInfo) => {
    const project = testInfo.project.name;
    test.skip(
      project === "oracle-tablet",
      "canonical contract rows own desktop/mobile viewports; tablet has dedicated responsive and Human Review evidence",
    );
    const wantDesktop = contractRow.viewport.width >= 1000;
    const isDesktopProject = project === "oracle-desktop";
    test.skip(
      wantDesktop !== isDesktopProject,
      `contract ${contractRow.id} belongs to ${wantDesktop ? "desktop" : "mobile"} project`,
    );

    const raw = JSON.parse(
      readFileSync(path.join(CONTRACTS_DIR, `${contractRow.id}.json`), "utf8"),
    ) as ContractSchema;
    await runContract(page, request, raw);
  });
}
