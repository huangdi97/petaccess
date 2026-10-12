/**
 * Windows Tauri/WebView2 shell smoke.
 *
 * This is runtime-shell evidence only: the GitHub Windows runner does not
 * provision the real PostGIS-backed PetAccess API. The smoke therefore proves
 * that the packaged WebView2 runtime starts, routes mount, the app shell is
 * present, document geometry is sane, and screenshots can be captured. It
 * must never be cited as proof of data-layer correctness.
 */
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const CDP = process.env.PETACCESS_WINDOWS_CDP ?? "http://127.0.0.1:9222";
const ROOT = path.resolve(__dirname, "..", "..");
const OUT_DIR = path.join(ROOT, "artifacts", "windows-preview-runtime");
const RUNTIME_DIR = path.join(OUT_DIR, "runtime");
const SCREENSHOT_DIR = path.join(OUT_DIR, "screenshots");

const routes = [
  { hash: "#/", name: "home", expectedPage: "home" },
  { hash: "#/contribute", name: "contribute", expectedPage: "contribution" },
  { hash: "#/mine", name: "mine", expectedPage: "mine" },
  { hash: "#/settings", name: "settings", expectedPage: "settings" },
  { hash: "#/privacy", name: "privacy", expectedPage: "privacy" },
  { hash: "#/about", name: "about", expectedPage: "about" },
];

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
            reject(new Error(`invalid CDP JSON: ${error.message}`));
          }
        });
      },
    );
    request.on("timeout", () => request.destroy(new Error("CDP discovery timeout")));
    request.on("error", reject);
  });
}

async function connectTarget() {
  const targets = await getJson("/json");
  const target = targets.find((item) => item.type === "page") ?? targets[0];
  if (!target?.webSocketDebuggerUrl) throw new Error("no WebView2 page target");

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  const pending = new Map();
  let nextId = 0;

  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("WebView2 websocket open timeout")), 10000);
    ws.onopen = () => {
      clearTimeout(timer);
      resolve();
    };
    ws.onerror = () => {
      clearTimeout(timer);
      reject(new Error("WebView2 websocket failed to open"));
    };
  });

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
      reject(new Error("WebView2 websocket closed"));
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

  return { ws, send, target };
}

async function main() {
  fs.mkdirSync(RUNTIME_DIR, { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const { ws, send, target } = await connectTarget();
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

  async function waitForPage(expectedPage, timeoutMs = 15000) {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      const value = await run(
        `document.querySelector('[data-ui-page="${expectedPage}"]') !== null`,
      );
      if (value) return;
      await sleep(150);
    }
    throw new Error(`surface timeout: ${expectedPage}`);
  }

  async function snapshot() {
    return JSON.parse(
      await run(`JSON.stringify((() => {
        const root = document.documentElement;
        const body = document.body;
        const ui = document.querySelector("[data-ui-page]");
        return {
          url: location.href,
          title: document.title,
          shell: !!document.querySelector("[data-testid=consumer-app-shell]"),
          uiPage: ui?.getAttribute("data-ui-page") ?? null,
          uiState: ui?.getAttribute("data-ui-state") ?? null,
          viewport: { width: innerWidth, height: innerHeight },
          scrollWidth: root?.scrollWidth ?? body?.scrollWidth ?? 0,
          horizontalOverflow:
            (root?.scrollWidth ?? body?.scrollWidth ?? 0) > innerWidth + 1,
          text: body?.innerText.slice(0, 1000) ?? "",
        };
      })())`),
    );
  }

  async function capture(name) {
    const result = await send("Page.captureScreenshot", {
      format: "png",
      fromSurface: true,
      captureBeyondViewport: false,
    });
    if (!result.data) throw new Error("Page.captureScreenshot returned no data");
    const targetPath = path.join(SCREENSHOT_DIR, `${name}.png`);
    fs.writeFileSync(targetPath, Buffer.from(result.data, "base64"));
    return targetPath;
  }

  const rows = [];
  let failed = false;

  for (const route of routes) {
    let error = null;
    await run(`location.hash = ${JSON.stringify(route.hash)}`);
    try {
      await waitForPage(route.expectedPage);
      await sleep(500);
    } catch (caught) {
      error = caught.message;
    }

    const state = await snapshot();
    if (!state.shell) error ??= "Consumer shell missing";
    if (state.uiPage !== route.expectedPage) {
      error ??= `expected ${route.expectedPage}, got ${state.uiPage}`;
    }
    if (state.horizontalOverflow) {
      error ??= `horizontal overflow ${state.scrollWidth} > ${state.viewport.width}`;
    }

    let screenshot = null;
    try {
      screenshot = await capture(route.name);
    } catch (caught) {
      error ??= `screenshot failed: ${caught.message}`;
    }

    rows.push({ ...route, ok: error === null, error, state, screenshot });
    if (error) failed = true;
    console.log(`${route.name}: ${error ? "FAIL" : "PASS"}`);
  }

  const output = {
    generatedAt: new Date().toISOString(),
    evidenceScope: "tauri-webview2-shell-runtime-only",
    dataLayer: "not-proven-by-this-workflow",
    cdp: CDP,
    target: {
      id: target.id ?? null,
      type: target.type ?? null,
      url: target.url ?? null,
    },
    result: failed ? "FAIL" : "PASS",
    routes: rows,
  };
  fs.writeFileSync(
    path.join(RUNTIME_DIR, "windows_shell_smoke.json"),
    JSON.stringify(output, null, 2),
  );

  ws.close();

  if (failed) process.exit(1);
  console.log(`WINDOWS_WEBVIEW2_SHELL_SMOKE=PASS routes=${rows.length}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
