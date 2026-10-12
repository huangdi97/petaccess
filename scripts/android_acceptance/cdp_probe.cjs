/**
 * Android FAST semantic probe through the debug Tauri WebView CDP socket.
 *
 * Usage:
 *   node cdp_probe.cjs <adb-forward-port> <action>
 *
 * Actions:
 *   home / search / map / place / reality / evidence / snapshot / offline / recovery / nav
 *
 * The probe reports the canonical Consumer page/state/fixture plus horizontal
 * overflow. It never treats a screenshot alone as proof that the expected
 * product surface actually rendered.
 */
const http = require("node:http");

const port = process.argv[2] ?? "9223";
const action = process.argv[3] ?? "home";
const PLACE_ID = "5a9084d0-d2c7-5bb3-9914-fa7a11c53d9e";

function getJson(path) {
  return new Promise((resolve, reject) => {
    http
      .get({ host: "127.0.0.1", port, path, timeout: 5000 }, (res) => {
        let data = "";
        res.on("data", (chunk) => (data += chunk));
        res.on("end", () => resolve(JSON.parse(data)));
      })
      .on("error", reject);
  });
}

async function main() {
  const targets = await getJson("/json");
  const page = targets.find((target) => target.type === "page") ?? targets[0];
  if (!page?.webSocketDebuggerUrl) throw new Error("no debuggable WebView page");

  const ws = new WebSocket(page.webSocketDebuggerUrl);
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

  const run = async (expression) => {
    const response = await send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (response.result?.exceptionDetails) {
      throw new Error(response.result.exceptionDetails.text);
    }
    return response.result.result.value;
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  async function go(hash, delay = 1800) {
    await run(`location.hash = ${JSON.stringify(hash)}`);
    await sleep(delay);
  }

  async function snapshot() {
    return JSON.parse(
      await run(`JSON.stringify((() => {
        const surface = document.querySelector("[data-ui-page]");
        const root = document.documentElement;
        const body = document.body;
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
          uiPage: surface?.getAttribute("data-ui-page") ?? null,
          uiState: surface?.getAttribute("data-ui-state") ?? null,
          uiFixture: surface?.getAttribute("data-ui-fixture") ?? null,
          offlineBanner: !!document.querySelector("[data-testid=global-offline-banner]"),
          errorState: !!document.querySelector("[data-state=ERROR]"),
          results: document.querySelectorAll("[data-testid^=result-]").length,
          viewportWidth: window.innerWidth,
          scrollWidth: root?.scrollWidth ?? body?.scrollWidth ?? 0,
          horizontalOverflow:
            (root?.scrollWidth ?? body?.scrollWidth ?? 0) > window.innerWidth + 1,
          safeAreaTop,
          contentTop,
          safeAreaOverlap: safeAreaTop > 0.5 && contentTop + 0.5 < safeAreaTop,
          textSample: body?.innerText.slice(0, 500) ?? "",
        };
      })())`),
    );
  }

  async function logRoute(label, hash, expectedPage, delay = 1800) {
    await go(hash, delay);
    const value = await snapshot();
    if (!value.shell) throw new Error(`${label}: Consumer shell missing`);
    if (value.uiPage !== expectedPage) {
      throw new Error(`${label}: expected data-ui-page=${expectedPage}, got ${value.uiPage}`);
    }
    if (value.horizontalOverflow) {
      throw new Error(
        `${label}: horizontal overflow ${value.scrollWidth} > ${value.viewportWidth}`,
      );
    }
    if (value.safeAreaOverlap) {
      throw new Error(
        `${label}: content starts at ${value.contentTop}px inside a ${value.safeAreaTop}px top safe area`,
      );
    }
    console.log(`${label} ${JSON.stringify(value)}`);
  }

  if (action === "home") {
    await logRoute("HOME", "#/", "home");
  } else if (action === "search") {
    await go("#/search");
    await run(`(() => {
      const input = document.querySelector("[data-testid=search-input]");
      if (!input) throw new Error("search input missing");
      input.value = "咖啡";
      input.dispatchEvent(new Event("input", { bubbles: true }));
      document.querySelector("[data-testid=search-btn]")?.click();
    })()`);
    await sleep(2500);
    const value = await snapshot();
    if (value.uiPage !== "search" || value.horizontalOverflow || value.safeAreaOverlap) {
      throw new Error(`SEARCH invalid state: ${JSON.stringify(value)}`);
    }
    console.log(`SEARCH ${JSON.stringify(value)}`);
  } else if (action === "map") {
    await logRoute("MAP", "#/map", "map", 2200);
  } else if (action === "place") {
    await logRoute("PLACE", `#/place/${PLACE_ID}`, "place", 2600);
  } else if (action === "reality") {
    await logRoute("REALITY", `#/place/${PLACE_ID}/reality`, "reality", 2600);
  } else if (action === "evidence") {
    await logRoute("EVIDENCE", `#/place/${PLACE_ID}/evidence`, "evidence", 2600);
  } else if (action === "snapshot") {
    const value = await snapshot();
    if (!value.shell || value.horizontalOverflow || value.safeAreaOverlap) {
      throw new Error(`SNAPSHOT invalid state: ${JSON.stringify(value)}`);
    }
    console.log(`SNAPSHOT ${JSON.stringify(value)}`);
  } else if (action === "offline") {
    await run(`window.dispatchEvent(new Event("offline"))`);
    await sleep(600);
    console.log(`OFFLINE ${JSON.stringify(await snapshot())}`);
  } else if (action === "recovery") {
    await run(`window.dispatchEvent(new Event("online"))`);
    await sleep(600);
    console.log(`RECOVERY ${JSON.stringify(await snapshot())}`);
  } else if (action === "nav") {
    await logRoute("NAV_MAP", "#/map", "map");
    await logRoute("NAV_HOME", "#/", "home");
  } else {
    throw new Error(`unknown action: ${action}`);
  }

  ws.close();
}

main().catch((error) => {
  console.error("FAIL", error.message);
  process.exit(1);
});
