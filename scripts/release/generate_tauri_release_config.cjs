#!/usr/bin/env node
/**
 * Generate the strict Tauri overlay used only by signed Release builds.
 *
 * The canonical tauri.conf.json intentionally supports local development
 * (127.0.0.1 / 10.0.2.2). Shipping that CSP and the packaged-runtime endpoint
 * defaults into a signed release would silently produce a build that points at
 * a developer machine. Release therefore fails closed unless an explicit
 * HTTPS PetAccess API base is supplied by CI.
 *
 * Usage:
 *   PETACCESS_PUBLIC_API_BASE=https://api.example.com/api/v1 \
 *     node scripts/release/generate_tauri_release_config.cjs <output.json>
 */
const fs = require("node:fs");
const path = require("node:path");

function fail(message) {
  console.error(`release-runtime-config: ${message}`);
  process.exit(1);
}

const output = process.argv[2];
if (!output) fail("output path is required");

const raw = (process.env.PETACCESS_PUBLIC_API_BASE ?? "").trim();
if (!raw) {
  fail(
    "PETACCESS_PUBLIC_API_BASE is required for signed Release builds; refusing packaged dev defaults",
  );
}

let url;
try {
  url = new URL(raw);
} catch {
  fail("PETACCESS_PUBLIC_API_BASE must be an absolute URL");
}

if (url.protocol !== "https:") {
  fail("PETACCESS_PUBLIC_API_BASE must use https");
}
if (url.username || url.password) {
  fail("PETACCESS_PUBLIC_API_BASE must not contain embedded credentials");
}
if (url.search || url.hash) {
  fail("PETACCESS_PUBLIC_API_BASE must not contain query parameters or fragments");
}

const normalizedPath = url.pathname.replace(/\/+$/, "");
if (!normalizedPath.endsWith("/api/v1")) {
  fail("PETACCESS_PUBLIC_API_BASE must end with /api/v1");
}

const apiBase = `${url.origin}${normalizedPath}`;
const apiOrigin = url.origin;
const csp = [
  "default-src 'self'",
  `connect-src 'self' ipc: http://ipc.localhost ${apiOrigin} https://apis.map.qq.com https://map.qq.com https://mapapi.qq.com https://*.map.qq.com https://*.map.gtimg.com`,
  `img-src 'self' asset: http://asset.localhost data: blob: ${apiOrigin} https://map.qq.com https://mapapi.qq.com https://*.map.qq.com https://*.map.gtimg.com`,
  "style-src 'self' 'unsafe-inline'",
  "font-src 'self' data:",
  "script-src 'self' https://map.qq.com https://mapapi.qq.com",
  "worker-src 'self' blob:",
].join("; ");

const config = {
  app: {
    security: {
      csp,
    },
  },
};

fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
fs.writeFileSync(output, JSON.stringify(config, null, 2) + "\n", "utf8");

console.log(`release-runtime-config: api_base=${apiBase}`);
console.log(`release-runtime-config: api_origin=${apiOrigin}`);
console.log(`release-runtime-config: output=${output}`);
