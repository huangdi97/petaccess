/**
 * Packaged Android WebView route stress gate.
 *
 * Reuses one CDP websocket so the gate measures the real SPA/router rather
 * than repeatedly relaunching the process. It asserts canonical page identity
 * and zero horizontal overflow on every transition.
 */
const fs = require("node:fs");
const path = require("node:path");
const http = require("node:http");

const port = process.argv[2] ?? process.env.PETACCESS_ANDROID_CDP_PORT ?? "9235";
const cycles = Number(process.env.PETACCESS_ANDROID_STRESS_CYCLES ?? "20");
const evidenceRoot =
  process.env.PETACCESS_ANDROID_EVIDENCE_DIR ??
  path.resolve(__dirname, "..", "..", "artifacts", "android-preview-runtime");
const outFile = path.join(evidenceRoot, "runtime", "route_stress.json");
const PLACE_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

const routes = [
  { hash: "#/", page: "home", name: "home" },
  { hash: "#/search", page: "search", name: "search" },
  { hash: "#/map", page: "map", name: "map" },
  { hash: `#/place/${PLACE_ID}`, page: "place", name: "place" },
  { hash: `#/place/${PLACE_ID}/reality`, page: "reality", name: "reality" },
  { hash: `#/place/${PLACE_ID}/evidence`, page: "evidence", name: "evidence" },
];

function getJson(urlPath) {
  return new Promise((resolve, reject) => {
    http
      .get({ host: "127.0.0.1", port, path: urlPath, timeout: 5000 }, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => resolve(JSON.parse(data)));
      })
      .on("error", reject);
  });
}

async function main() {
  fs.mkdirSync(path.dirname(outFile), { recursive: true });
  const targets = await getJson("/json");
  const target = targets.find((item) => item.type === "page") ?? targets[0];
  if (!target?.webSocketDebuggerUrl) throw new Error("no debuggable WebView page");

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.id && pending.has(message.id)) {
      pending.get(message.id)(message);
      pending.delete(message.id);
    }
  };
  const send = (method, params = {}) =>
    new Promise((resolve) => {
      id += 1;
      pending.set(id, resolve);
      ws.send(JSON.stringify({ id, method, params }));
    });

  await new Promise((resolve) => (ws.onopen = resolve));

  async function evaluate(expression) {
    const response = await send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (response.result?.exceptionDetails) {
      throw new Error(response.result.exceptionDetails.text);
    }
    return response.result.result.value;
  }

  const transitions = [];
  let failure = null;
  const started = Date.now();

  outer: for (let cycle = 1; cycle <= cycles; cycle += 1) {
    for (const route of routes) {
      const t0 = Date.now();
      await evaluate(`location.hash = ${JSON.stringify(route.hash)}`);

      let snapshot = null;
      for (let attempt = 0; attempt < 40; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 100));
        snapshot = JSON.parse(
          await evaluate(`JSON.stringify((() => {
            const ui = document.querySelector("[data-ui-page]");
            const root = document.documentElement;
            const body = document.body;
            return {
              uiPage: ui?.getAttribute("data-ui-page") ?? null,
              uiState: ui?.getAttribute("data-ui-state") ?? null,
              shell: !!document.querySelector("[data-testid=consumer-app-shell]"),
              viewportWidth: window.innerWidth,
              scrollWidth: root?.scrollWidth ?? body?.scrollWidth ?? 0,
            };
          })())`),
        );
        if (snapshot.uiPage === route.page) break;
      }

      const overflow = snapshot.scrollWidth > snapshot.viewportWidth + 1;
      const ok = snapshot.shell && snapshot.uiPage === route.page && !overflow;
      transitions.push({
        cycle,
        route: route.name,
        elapsedMs: Date.now() - t0,
        ok,
        uiPage: snapshot.uiPage,
        uiState: snapshot.uiState,
        viewportWidth: snapshot.viewportWidth,
        scrollWidth: snapshot.scrollWidth,
        horizontalOverflow: overflow,
      });

      if (!ok) {
        failure = transitions[transitions.length - 1];
        break outer;
      }
    }
  }

  ws.close();

  const payload = {
    schemaVersion: 1,
    result: failure ? "FAIL" : "PASS",
    cycles,
    routesPerCycle: routes.length,
    transitions: transitions.length,
    expectedTransitions: cycles * routes.length,
    elapsedMs: Date.now() - started,
    failure,
  };
  fs.writeFileSync(outFile, JSON.stringify(payload, null, 2));
  console.log(JSON.stringify(payload));

  if (failure) process.exit(1);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
