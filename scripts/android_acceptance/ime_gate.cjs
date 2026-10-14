/**
 * Android packaged-WebView IME/input acceptance.
 *
 * Proves two real input flows on the running Tauri Preview package:
 *   1. public Search input
 *   2. authenticated Pet New name input
 *
 * The gate uses an actual adb tap + Android input text, not DOM value
 * assignment. While the IME is active, the focused control must remain inside
 * the visual viewport. The first Android Back must dismiss the IME without
 * changing the Consumer route.
 */
const childProcess = require("node:child_process");
const fs = require("node:fs");
const http = require("node:http");
const path = require("node:path");

const CDP = process.env.PETACCESS_ANDROID_CDP ?? "http://127.0.0.1:9223";
const SERIAL = (process.env.PETACCESS_ANDROID_SERIAL ?? "").trim();
const AUTH_TOKEN = (process.env.PETACCESS_ANDROID_AUTH_TOKEN ?? "").trim();
const ROOT = path.resolve(__dirname, "..", "..");
const EVIDENCE_ROOT =
  process.env.PETACCESS_ANDROID_EVIDENCE_DIR ?? path.join(ROOT, "artifacts", "android_acceptance");
const RUNTIME_DIR = path.join(EVIDENCE_ROOT, "runtime");
const SCREENSHOT_DIR = path.join(EVIDENCE_ROOT, "screenshots", "ime");
const OUT = path.join(RUNTIME_DIR, "ime_gate.json");

if (!SERIAL) throw new Error("PETACCESS_ANDROID_SERIAL is required");
if (!AUTH_TOKEN) throw new Error("PETACCESS_ANDROID_AUTH_TOKEN is required");

function adbBinary() {
  if (process.env.ADB_PATH) return process.env.ADB_PATH;
  const sdk = process.env.ANDROID_SDK_ROOT || process.env.ANDROID_HOME;
  if (sdk) {
    const candidate = path.join(
      sdk,
      "platform-tools",
      process.platform === "win32" ? "adb.exe" : "adb",
    );
    if (fs.existsSync(candidate)) return candidate;
  }
  return process.platform === "win32" ? "adb.exe" : "adb";
}

function adb(args, options = {}) {
  return childProcess.execFileSync(adbBinary(), ["-s", SERIAL, ...args], {
    stdio: options.binary ? ["ignore", "pipe", "pipe"] : ["ignore", "pipe", "pipe"],
    encoding: options.binary ? null : "utf8",
    timeout: 30000,
  });
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
            reject(new Error(`invalid CDP JSON: ${error.message}`));
          }
        });
      },
    );
    request.on("timeout", () => request.destroy(new Error("CDP HTTP timeout")));
    request.on("error", reject);
  });
}

async function connectPage() {
  const targets = await getJson("/json");
  const target =
    targets.find(
      (item) =>
        item.type === "page" &&
        typeof item.webSocketDebuggerUrl === "string" &&
        item.webSocketDebuggerUrl.length > 0,
    ) ?? targets.find((item) => typeof item.webSocketDebuggerUrl === "string");

  if (!target?.webSocketDebuggerUrl) throw new Error("no debuggable WebView page target");

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("CDP websocket open timeout")), 5000);
    ws.onopen = () => {
      clearTimeout(timer);
      resolve();
    };
    ws.onerror = () => {
      clearTimeout(timer);
      reject(new Error("CDP websocket failed to open"));
    };
  });

  let nextId = 0;
  const pending = new Map();

  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (!message.id || !pending.has(message.id)) return;
    const item = pending.get(message.id);
    clearTimeout(item.timer);
    pending.delete(message.id);
    if (message.error) {
      item.reject(new Error(`${message.error.message} (${message.error.code})`));
    } else {
      item.resolve(message.result ?? {});
    }
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

  await send("Runtime.enable");
  await send("Page.enable");
  return { ws, send, run, target };
}

async function main() {
  fs.mkdirSync(RUNTIME_DIR, { recursive: true });
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const { ws, run, target } = await connectPage();
  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const waitFor = async (expression, timeoutMs = 15000) => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      if (await run(expression)) return;
      await sleep(150);
    }
    throw new Error(`timeout waiting for: ${expression}`);
  };

  const geometry = async (selector) =>
    JSON.parse(
      await run(`JSON.stringify((() => {
        const el = document.querySelector(${JSON.stringify(selector)});
        const root = document.documentElement;
        if (!el) return { present: false };
        const rect = el.getBoundingClientRect();
        const vv = window.visualViewport;
        const top = vv?.offsetTop ?? 0;
        const height = vv?.height ?? window.innerHeight;
        const tabbar = document.querySelector("[data-testid=mobile-tabbar]");
        const tabbarStyle = tabbar ? getComputedStyle(tabbar) : null;
        const tabbarRect = tabbar?.getBoundingClientRect() ?? null;
        const tabbarVisible = Boolean(
          tabbar &&
            tabbarStyle &&
            tabbarStyle.display !== "none" &&
            tabbarStyle.visibility !== "hidden" &&
            Number.parseFloat(tabbarStyle.opacity || "1") > 0.05 &&
            (tabbarRect?.height ?? 0) > 1
        );
        return {
          present: true,
          testId: el.getAttribute("data-testid"),
          active: document.activeElement === el,
          value: "value" in el ? String(el.value) : null,
          devicePixelRatio: window.devicePixelRatio,
          rect: {
            left: rect.left,
            top: rect.top,
            right: rect.right,
            bottom: rect.bottom,
            width: rect.width,
            height: rect.height,
          },
          viewport: {
            innerWidth: window.innerWidth,
            innerHeight: window.innerHeight,
            visualTop: top,
            visualHeight: height,
            visualBottom: top + height,
          },
          documentScrollWidth: root.scrollWidth,
          horizontalOverflow: root.scrollWidth > window.innerWidth + 1,
          visibleInVisualViewport:
            rect.top >= top - 1 && rect.bottom <= top + height - 8,
          imeState: root.dataset.ime ?? null,
          tabbarVisible,
          tabbarRect: tabbarRect
            ? {
                top: tabbarRect.top,
                bottom: tabbarRect.bottom,
                height: tabbarRect.height,
              }
            : null,
          hash: location.hash,
        };
      })())`),
    );

  const captureDevice = (name) => {
    const png = adb(["exec-out", "screencap", "-p"], { binary: true });
    const file = path.join(SCREENSHOT_DIR, name);
    fs.writeFileSync(file, png);
    if (png.length < 1024 || png.subarray(0, 8).toString("hex") !== "89504e470d0a1a0a") {
      throw new Error(`invalid device screenshot: ${file}`);
    }
    return file;
  };

  const cases = [
    {
      id: "search",
      hash: "#/search",
      page: "search",
      selector: '[data-testid="search-input"]',
      text: "ImeSearch42",
      authenticated: false,
    },
    {
      id: "pet-new",
      hash: "#/pet/new",
      page: "pet-new",
      selector: '[data-testid="pet-name"]',
      text: "ImePet42",
      authenticated: true,
    },
  ];

  const rows = [];
  let failed = false;

  for (const testCase of cases) {
    let error = null;
    if (testCase.authenticated) {
      await run(`localStorage.setItem("pa_token", ${JSON.stringify(AUTH_TOKEN)}); true`);
    }

    await run(`location.hash = ${JSON.stringify(testCase.hash)}`);
    try {
      await waitFor(
        `Boolean(document.querySelector('[data-ui-page="${testCase.page}"]') && document.querySelector(${JSON.stringify(testCase.selector)}))`,
      );
      await sleep(600);
    } catch (routeError) {
      error = routeError.message;
    }

    const before = await geometry(testCase.selector);
    if (!before.present) error ??= "input missing";
    if (before.horizontalOverflow) error ??= "horizontal overflow before IME";
    if (before.imeState !== "hidden") {
      error ??= `unexpected pre-IME state: ${JSON.stringify(before.imeState)}`;
    }
    if (!before.tabbarVisible) error ??= "mobile tabbar missing before IME";

    if (!error) {
      const x = Math.round((before.rect.left + before.rect.width / 2) * before.devicePixelRatio);
      const y = Math.round((before.rect.top + before.rect.height / 2) * before.devicePixelRatio);
      adb(["shell", "input", "tap", String(x), String(y)]);
      await sleep(900);
      adb(["shell", "input", "text", testCase.text]);
      await sleep(700);
    }

    const withIme = await geometry(testCase.selector);
    if (!withIme.active) error ??= "input did not retain focus after adb tap";
    if (!String(withIme.value ?? "").includes(testCase.text)) {
      error ??= `adb text did not reach input: ${JSON.stringify(withIme.value)}`;
    }
    if (withIme.horizontalOverflow) error ??= "horizontal overflow with IME";
    if (!withIme.visibleInVisualViewport) {
      error ??= `focused input covered by visual viewport: ${JSON.stringify(withIme)}`;
    }
    if (withIme.imeState !== "visible") {
      error ??= `IME runtime state did not become visible: ${JSON.stringify(withIme)}`;
    }
    if (withIme.tabbarVisible) {
      error ??= `mobile tabbar remained visible above IME: ${JSON.stringify(withIme.tabbarRect)}`;
    }

    let screenshot = null;
    try {
      screenshot = captureDevice(`ime__${testCase.id}.png`);
    } catch (shotError) {
      error ??= shotError.message;
    }

    // With the software keyboard visible, Android Back must dismiss IME first.
    // It must not navigate the Consumer route or exit the Activity.
    const hashBeforeBack = withIme.hash;
    adb(["shell", "input", "keyevent", "KEYCODE_BACK"]);
    await waitFor(`document.documentElement.dataset.ime !== "visible"`, 5000).catch(() => {});
    await sleep(250);
    const afterBack = await geometry(testCase.selector);
    if (afterBack.hash !== hashBeforeBack) {
      error ??= `Back changed route while IME was active: ${hashBeforeBack} -> ${afterBack.hash}`;
    }
    if (afterBack.imeState !== "hidden") {
      error ??= `IME runtime state did not return hidden: ${JSON.stringify(afterBack)}`;
    }
    if (!afterBack.tabbarVisible) {
      error ??= "mobile tabbar did not return after IME dismissal";
    }

    const row = {
      id: testCase.id,
      ok: error === null,
      error,
      before,
      withIme,
      afterBack,
      screenshot,
    };
    rows.push(row);
    if (!row.ok) failed = true;
    console.log(
      `IME ${testCase.id}: ${row.ok ? "PASS" : "FAIL"} | active=${withIme.active} | visible=${withIme.visibleInVisualViewport} | route=${withIme.hash}`,
    );
  }

  const payload = {
    generatedAt: new Date().toISOString(),
    target: { id: target.id ?? null, url: target.url ?? null },
    result: failed ? "FAIL" : "PASS",
    cases: rows,
  };
  fs.writeFileSync(OUT, JSON.stringify(payload, null, 2));
  ws.close();

  if (failed) {
    console.error(`ANDROID IME GATE FAIL — see ${OUT}`);
    process.exit(1);
  }
  console.log(`ANDROID IME GATE PASS — ${rows.length}/${rows.length}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
