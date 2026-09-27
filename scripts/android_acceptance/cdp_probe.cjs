/**
 * Android FAST 验证 - 通过 CDP 连接 Android WebView（debug APK）。
 * 用法: node android_cdp_probe.mjs <adb-port> <expr-or-action>
 * actions: home / search / map / offline / recovery / nav-home / nav-map / nav-contribute / nav-mine
 */
const http = require("node:http");

const port = process.argv[2] ?? "9223";
const action = process.argv[3] ?? "home";

function getJson(path) {
  return new Promise((resolve, reject) => {
    http
      .get({ host: "127.0.0.1", port, path, timeout: 5000 }, (res) => {
        let data = "";
        res.on("data", (c) => (data += c));
        res.on("end", () => resolve(JSON.parse(data)));
      })
      .on("error", reject);
  });
}

async function main() {
  const targets = await getJson("/json");
  const page = targets.find((t) => t.type === "page") ?? targets[0];
  const ws = new WebSocket(page.webSocketDebuggerUrl);
  let id = 0;
  const pending = new Map();
  ws.onmessage = (ev) => {
    const msg = JSON.parse(ev.data);
    if (msg.id && pending.has(msg.id)) {
      pending.get(msg.id)(msg);
      pending.delete(msg.id);
    }
  };
  const send = (method, params = {}) =>
    new Promise((resolve) => {
      id += 1;
      pending.set(id, resolve);
      ws.send(JSON.stringify({ id, method, params }));
    });
  await new Promise((res) => (ws.onopen = res));

  const expr = `JSON.stringify({
    url: location.href,
    title: document.title,
    shell: !!document.querySelector('[data-testid=consumer-app-shell]'),
    offlineBanner: !!document.querySelector('[data-testid=global-offline-banner]'),
    homeTitle: !!document.querySelector('[data-testid=home-title]'),
    searchInput: !!document.querySelector('[data-testid=search-input]'),
    mapShell: !!document.querySelector('[data-testid=map]'),
    errorState: !!document.querySelector('[data-state=ERROR]'),
    results: document.querySelectorAll('[data-testid^=result-]').length,
  })`;

  const run = async (expression) => {
    const r = await send("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (r.result?.exceptionDetails) {
      return { error: r.result.exceptionDetails.text };
    }
    return JSON.parse(r.result.result.value);
  };

  const log = (label, v) => console.log(`${label} ${JSON.stringify(v)}`);

  if (action === "home") {
    await send("Runtime.evaluate", { expression: `location.hash = "#/"` });
    await new Promise((r) => setTimeout(r, 1200));
    log("HOME", await run(expr));
  } else if (action === "search") {
    await send("Runtime.evaluate", { expression: `location.hash = "#/search"` });
    await new Promise((r) => setTimeout(r, 1500));
    await send("Runtime.evaluate", {
      expression: `document.querySelector('[data-testid=search-input]').value = "咖啡"`,
    });
    await send("Runtime.evaluate", {
      expression: `document.querySelector('[data-testid=search-btn]').click()`,
    });
    await new Promise((r) => setTimeout(r, 2500));
    log("SEARCH", await run(expr));
  } else if (action === "offline") {
    await send("Runtime.evaluate", {
      expression: `window.dispatchEvent(new Event("offline"))`,
    });
    await new Promise((r) => setTimeout(r, 600));
    log("OFFLINE", await run(expr));
  } else if (action === "recovery") {
    await send("Runtime.evaluate", {
      expression: `window.dispatchEvent(new Event("online"))`,
    });
    await new Promise((r) => setTimeout(r, 600));
    log("RECOVERY", await run(expr));
  } else if (action === "nav") {
    await send("Runtime.evaluate", { expression: `location.hash = "#/map"` });
    await new Promise((r) => setTimeout(r, 1200));
    const m = await run(expr);
    await send("Runtime.evaluate", { expression: `location.hash = "#/"` });
    await new Promise((r) => setTimeout(r, 1200));
    const h = await run(expr);
    log("NAV_MAP", m);
    log("NAV_HOME", h);
  }
  ws.close();
}

main().catch((e) => {
  console.error("FAIL", e.message);
  process.exit(1);
});