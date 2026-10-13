/**
 * Full packaged-Android Consumer journey over the debug Tauri WebView.
 *
 * Android System WebView exposes a page-level DevTools target, not a full
 * desktop-Chromium browser context. Attaching through Playwright's
 * chromium.connectOverCDP() can therefore fail during browser bootstrap on
 * Browser.setDownloadBehavior even when the WebView itself is healthy.
 *
 * This journey talks directly to the WebView page target via CDP. It covers
 * every Router page in its public/default state, plus the governed Place
 * rules/space views, with semantic identity and screenshot evidence.
 */
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const CDP = process.env.PETACCESS_ANDROID_CDP ?? "http://127.0.0.1:9223";
const ROOT = path.resolve(__dirname, "..", "..");
const EVIDENCE_ROOT =
  process.env.PETACCESS_ANDROID_EVIDENCE_DIR ?? path.join(ROOT, "artifacts", "android_acceptance");
const RUNTIME_DIR = path.join(EVIDENCE_ROOT, "runtime");
const SCREENSHOT_DIR = path.join(EVIDENCE_ROOT, "screenshots");
// Keep the established filename because coverage/report tooling already consumes it.
const OUT = path.join(RUNTIME_DIR, "cdp_journey_playwright.json");
const PLACE_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";
const AUTH_TOKEN = (process.env.PETACCESS_ANDROID_AUTH_TOKEN ?? "").trim();
const REQUIRE_REAL_MAP = process.env.PETACCESS_REQUIRE_REAL_MAP === "1";

const routes = [
  { hash: "#/", tag: "R01", name: "home", expectedPage: "home" },
  { hash: "#/search", tag: "R02", name: "search", expectedPage: "search" },
  { hash: "#/map", tag: "R03", name: "map", expectedPage: "map" },
  { hash: `#/place/${PLACE_ID}`, tag: "R04", name: "place-overview", expectedPage: "place" },
  {
    hash: `#/place/${PLACE_ID}?view=rules`,
    tag: "R05",
    name: "place-rules",
    expectedPage: "place",
  },
  {
    hash: `#/place/${PLACE_ID}?view=space`,
    tag: "R06",
    name: "place-space",
    expectedPage: "place",
  },
  {
    hash: `#/place/${PLACE_ID}/reality`,
    tag: "R07",
    name: "reality",
    expectedPage: "reality",
  },
  {
    hash: `#/place/${PLACE_ID}/evidence`,
    tag: "R08",
    name: "evidence",
    expectedPage: "evidence",
  },
  {
    hash: "#/contribute",
    tag: "R09",
    name: "contribute-entry",
    expectedPage: "contribution",
  },
  { hash: "#/mine", tag: "R10", name: "mine", expectedPage: "mine" },
  { hash: "#/settings", tag: "R11", name: "settings", expectedPage: "settings" },
  { hash: "#/privacy", tag: "R12", name: "privacy", expectedPage: "privacy" },
  { hash: "#/about", tag: "R13", name: "about", expectedPage: "about" },
  { hash: "#/onboarding", tag: "R14", name: "onboarding", expectedPage: "onboarding" },
  { hash: "#/pet/new", tag: "R15", name: "pet-new", expectedPage: "pet-new" },
  { hash: "#/pets", tag: "R16", name: "pets", expectedPage: "pets" },
  { hash: "#/notifications", tag: "R17", name: "notifications", expectedPage: "notifications" },
  { hash: "#/boundary", tag: "R18", name: "boundary", expectedPage: "boundary" },
  {
    hash: `#/place/${PLACE_ID}/why`,
    tag: "R19",
    name: "match-explain",
    expectedPage: "match-explain",
  },
  {
    hash: `#/place/${PLACE_ID}/operator-claim`,
    tag: "R20",
    name: "operator-claim",
    expectedPage: "operator-claim",
  },
  {
    hash: "#/__petaccess_runtime_missing__",
    tag: "R21",
    name: "not-found",
    expectedPage: "not-found",
  },
];

const authenticatedRoutes = [
  {
    hash: `#/contribute/${PLACE_ID}`,
    tag: "A01",
    name: "auth-contribute",
    expectedPage: "contribution",
    expectedState: "choose-type",
    authenticated: true,
  },
  {
    hash: "#/mine",
    tag: "A02",
    name: "auth-mine",
    expectedPage: "mine",
    expectedState: "signed-in",
    authenticated: true,
  },
  {
    hash: "#/privacy",
    tag: "A03",
    name: "auth-privacy",
    expectedPage: "privacy",
    expectedState: "signed-in",
    authenticated: true,
  },
  {
    hash: "#/pets",
    tag: "A04",
    name: "auth-pets",
    expectedPage: "pets",
    expectedState: "ready",
    authenticated: true,
  },
  {
    hash: "#/notifications",
    tag: "A05",
    name: "auth-notifications",
    expectedPage: "notifications",
    expectedState: "ready",
    authenticated: true,
  },
  {
    hash: "#/boundary",
    tag: "A06",
    name: "auth-boundary",
    expectedPage: "boundary",
    expectedState: "ready",
    authenticated: true,
  },
  {
    hash: "#/pet/new",
    tag: "A07",
    name: "auth-pet-new",
    expectedPage: "pet-new",
    expectedState: "ready",
    authenticated: true,
  },
];

function safeName(value) {
  return value.replace(/[^a-z0-9_-]+/gi, "_");
}

function getJson(endpointPath) {
  const base = new URL(CDP);
  return new Promise((resolve, reject) => {
    const request = http.get(
      {
        host: base.hostname,
        port: base.port || 80,
        path: endpointPath,
        timeout: 5000,
      },
      (response) => {
        let data = "";
        response.on("data", (chunk) => (data += chunk));
        response.on("end", () => {
          try {
            resolve(JSON.parse(data));
          } catch (error) {
            reject(new Error(`invalid CDP JSON from ${endpointPath}: ${error.message}`));
          }
        });
      },
    );
    request.on("timeout", () => request.destroy(new Error(`CDP HTTP timeout: ${endpointPath}`)));
    request.on("error", reject);
  });
}

async function connectPageTarget() {
  const maxAttempts = 20;
  let lastError = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    let ws = null;
    try {
      const targets = await getJson("/json");
      const target =
        targets.find(
          (item) =>
            item.type === "page" &&
            typeof item.webSocketDebuggerUrl === "string" &&
            item.webSocketDebuggerUrl.length > 0,
        ) ??
        targets.find(
          (item) =>
            typeof item.webSocketDebuggerUrl === "string" && item.webSocketDebuggerUrl.length > 0,
        );

      if (!target?.webSocketDebuggerUrl) {
        throw new Error("no debuggable WebView page target");
      }

      ws = new WebSocket(target.webSocketDebuggerUrl);
      await new Promise((resolve, reject) => {
        const timer = setTimeout(() => reject(new Error("CDP websocket open timeout")), 3000);
        ws.onopen = () => {
          clearTimeout(timer);
          resolve();
        };
        ws.onerror = () => {
          clearTimeout(timer);
          reject(new Error("CDP websocket failed to open"));
        };
      });

      const pending = new Map();
      let nextId = 0;

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        if (!message.id || !pending.has(message.id)) return;
        const { resolve, reject, timer } = pending.get(message.id);
        clearTimeout(timer);
        pending.delete(message.id);
        if (message.error) {
          reject(new Error(`${message.error.message} (${message.error.code})`));
          return;
        }
        resolve(message.result ?? {});
      };

      ws.onclose = () => {
        for (const { reject, timer } of pending.values()) {
          clearTimeout(timer);
          reject(new Error("CDP websocket closed"));
        }
        pending.clear();
      };

      const send = (method, params = {}) =>
        new Promise((resolve, reject) => {
          nextId += 1;
          const id = nextId;
          const timer = setTimeout(() => {
            pending.delete(id);
            reject(new Error(`CDP command timeout: ${method}`));
          }, 15000);
          pending.set(id, { resolve, reject, timer });
          ws.send(JSON.stringify({ id, method, params }));
        });

      // A socket can open while the freshly recreated WebView is still being
      // replaced. Prove this target is alive before handing it to the journey.
      await send("Runtime.enable");
      await send("Runtime.evaluate", {
        expression: "document.readyState",
        returnByValue: true,
      });

      console.log(
        `CDP target ready attempt=${attempt} id=${target.id ?? "-"} url=${target.url ?? "-"}`,
      );
      return { ws, send, target };
    } catch (error) {
      lastError = error;
      try {
        ws?.close();
      } catch {
        // best-effort cleanup between retries
      }
      if (attempt < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 500));
      }
    }
  }

  throw new Error(
    `CDP page target did not stabilize after ${maxAttempts} attempts: ${lastError?.message ?? lastError}`,
  );
}

async function main() {
  fs.mkdirSync(RUNTIME_DIR, { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const { ws, send, target } = await connectPageTarget();
  await send("Runtime.enable");
  await send("Page.enable");

  const run = async (expression) => {
    const response = await send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (response.exceptionDetails) {
      throw new Error(response.exceptionDetails.text || "Runtime.evaluate exception");
    }
    return response.result?.value;
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const waitForSurface = async (expectedPage, timeoutMs = 15000) => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const ready = await run(`(() => {
        const el = document.querySelector('[data-ui-page="${expectedPage}"]');
        if (!el) return false;
        const style = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        return (
          style.visibility !== "hidden" &&
          style.display !== "none" &&
          rect.width > 0 &&
          rect.height > 0
        );
      })()`);
      if (ready) return;
      await sleep(150);
    }
    throw new Error(`surface timeout: data-ui-page=${expectedPage}`);
  };

  const snapshot = async () =>
    JSON.parse(
      await run(`JSON.stringify((() => {
        const root = document.documentElement;
        const body = document.body;
        const ui = document.querySelector("[data-ui-page]");
        const insetProbe = document.createElement("div");
        insetProbe.style.cssText =
          "position:fixed;visibility:hidden;pointer-events:none;padding-top:env(safe-area-inset-top,0px)";
        body?.appendChild(insetProbe);
        const safeAreaTop = Number.parseFloat(getComputedStyle(insetProbe).paddingTop) || 0;
        insetProbe.remove();
        const shellMain = document.querySelector(".consumer-app-shell__main");
        const contentTop = shellMain?.getBoundingClientRect().top ?? 0;
        return {
          url: location.href,
          title: document.title,
          shell: !!document.querySelector("[data-testid=consumer-app-shell]"),
          uiPage: ui?.getAttribute("data-ui-page") ?? null,
          uiState: ui?.getAttribute("data-ui-state") ?? null,
          uiFixture: ui?.getAttribute("data-ui-fixture") ?? null,
          viewport: {
            width: window.innerWidth,
            height: window.innerHeight,
          },
          document: {
            scrollWidth: root?.scrollWidth ?? body?.scrollWidth ?? 0,
            scrollHeight: root?.scrollHeight ?? body?.scrollHeight ?? 0,
          },
          horizontalOverflow:
            (root?.scrollWidth ?? body?.scrollWidth ?? 0) > window.innerWidth + 1,
          safeAreaTop,
          contentTop,
          safeAreaOverlap: safeAreaTop > 0.5 && contentTop + 0.5 < safeAreaTop,
          mapProviderSurface: document.querySelector(".tencent-map")
            ? "tencent"
            : document.querySelector(
                  "[data-testid=map-provider-fallback], [data-testid=map-real-provider-fallback]",
                )
              ? "fallback"
              : null,
          mapFallbackCopy:
            document.querySelector("[data-testid=map-real-provider-fallback]")?.textContent?.trim() ??
            null,
          text: body?.innerText.slice(0, 1600) ?? "",
        };
      })())`),
    );

  const captureScreenshot = async (shotPath) => {
    let result;
    try {
      result = await send("Page.captureScreenshot", {
        format: "png",
        fromSurface: true,
        captureBeyondViewport: false,
      });
    } catch {
      result = await send("Page.captureScreenshot", { format: "png" });
    }
    if (!result.data) throw new Error("Page.captureScreenshot returned no data");
    fs.writeFileSync(shotPath, Buffer.from(result.data, "base64"));
  };

  const rows = [];
  let failed = false;
  let authInjected = false;
  const routeCases = AUTH_TOKEN ? [...routes, ...authenticatedRoutes] : routes;

  for (const route of routeCases) {
    if (route.authenticated && !authInjected) {
      await run(`localStorage.setItem("pa_token", ${JSON.stringify(AUTH_TOKEN)}); true`);
      authInjected = true;
    }
    const startedAt = Date.now();
    await run(`location.hash = ${JSON.stringify(route.hash)}`);

    let routeError = null;
    try {
      await waitForSurface(route.expectedPage);
      await sleep(800);
    } catch (error) {
      routeError = error.message;
    }

    const state = await snapshot();

    if (!state.shell) routeError ??= "Consumer shell missing";
    if (state.uiPage !== route.expectedPage) {
      routeError ??= `expected ${route.expectedPage}, got ${state.uiPage}`;
    }
    if (route.expectedState && state.uiState !== route.expectedState) {
      routeError ??= `expected state ${route.expectedState}, got ${state.uiState}`;
    }
    if (state.horizontalOverflow) {
      routeError ??= `horizontal overflow ${state.document.scrollWidth} > ${state.viewport.width}`;
    }
    if (state.safeAreaOverlap) {
      routeError ??= `top safe-area overlap: contentTop=${state.contentTop}, safeAreaTop=${state.safeAreaTop}`;
    }
    if (route.name === "map" && REQUIRE_REAL_MAP && state.mapProviderSurface !== "tencent") {
      routeError ??= `real map required but packaged surface is ${state.mapProviderSurface ?? "unknown"}`;
    }

    const shot = path.join(SCREENSHOT_DIR, `phoneM__${safeName(route.name)}__${route.tag}.png`);
    try {
      await captureScreenshot(shot);
    } catch (error) {
      routeError ??= `screenshot failed: ${error.message}`;
    }

    const row = {
      ...route,
      elapsedMs: Date.now() - startedAt,
      ok: routeError === null,
      error: routeError,
      snapshot: state,
      screenshot: shot,
    };
    rows.push(row);
    if (!row.ok) failed = true;

    console.log(
      `  ${route.tag} ${route.name}: ${row.ok ? "PASS" : "FAIL"} | ${state.uiPage}/${state.uiState ?? "-"} | overflow=${state.horizontalOverflow} | safeTop=${state.safeAreaTop}/${state.contentTop}`,
    );
  }

  fs.writeFileSync(
    OUT,
    JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        cdp: CDP,
        target: {
          id: target.id ?? null,
          type: target.type ?? null,
          url: target.url ?? null,
        },
        engine: "webview-page-cdp",
        result: failed ? "FAIL" : "PASS",
        authenticatedSweepRequested: Boolean(AUTH_TOKEN),
        authenticatedCases: rows.filter((row) => row.authenticated).length,
        requireRealMap: REQUIRE_REAL_MAP,
        mapProviderSurface:
          rows.find((row) => row.name === "map")?.snapshot?.mapProviderSurface ?? null,
        routes: rows,
      },
      null,
      2,
    ),
  );

  ws.close();

  if (failed) {
    console.error(`CDP JOURNEY FAIL — see ${OUT}`);
    process.exit(1);
  }
  console.log(
    `CDP JOURNEY PASS — ${rows.length}/${rows.length} cases (public=${routes.length}, authenticated=${rows.filter((row) => row.authenticated).length})`,
  );
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
