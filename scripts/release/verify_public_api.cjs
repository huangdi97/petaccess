#!/usr/bin/env node
/**
 * Verify that a packaged-runtime API base is a live PetAccess API.
 *
 * Required env:
 *   PETACCESS_PUBLIC_API_BASE=https://host.example/api/v1
 *
 * Optional:
 *   PETACCESS_REQUIRE_REAL_MAP=1
 *
 * The real-map mode proves both the public render config and the private
 * server-side coordinate provider. No credential is printed or persisted.
 */
function fail(message) {
  console.error(`public-api-preflight: ${message}`);
  process.exit(1);
}

const raw = (process.env.PETACCESS_PUBLIC_API_BASE ?? "").trim();
if (!raw) fail("PETACCESS_PUBLIC_API_BASE is required");

let url;
try {
  url = new URL(raw);
} catch {
  fail("PETACCESS_PUBLIC_API_BASE must be an absolute URL");
}

if (url.protocol !== "https:") fail("PETACCESS_PUBLIC_API_BASE must use https");
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

const base = `${url.origin}${normalizedPath}`;
const timeoutMs = Number.parseInt(process.env.PETACCESS_API_PREFLIGHT_TIMEOUT_MS ?? "10000", 10);

async function requestJson(endpoint, init = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(endpoint, {
      ...init,
      headers: {
        Accept: "application/json",
        ...(init.headers ?? {}),
      },
      signal: controller.signal,
    });
    if (!response.ok) {
      throw new Error(`${endpoint} -> HTTP ${response.status}`);
    }
    return {
      payload: await response.json(),
      headers: response.headers,
    };
  } finally {
    clearTimeout(timer);
  }
}

async function main() {
  const tauriOrigin = "http://tauri.localhost";
  const pingResponse = await requestJson(base + "/ping", {
    headers: { Origin: tauriOrigin },
  });
  if (pingResponse.payload?.pong !== true) {
    throw new Error("/api/v1/ping did not return { pong: true }");
  }
  const allowOrigin = pingResponse.headers.get("access-control-allow-origin");
  if (allowOrigin !== tauriOrigin) {
    throw new Error(
      `PetAccess API CORS does not allow packaged Tauri origin: expected ${tauriOrigin}, got ${allowOrigin ?? "(missing)"}`,
    );
  }

  const healthResponse = await requestJson(url.origin + "/health");
  if (healthResponse.payload?.status !== "ok") {
    throw new Error("/health did not return status=ok");
  }

  let mapMode = "not-required";
  if (process.env.PETACCESS_REQUIRE_REAL_MAP === "1") {
    const { payload: mapConfig } = await requestJson(base + "/ai/map/config");
    if (
      mapConfig?.real_enabled !== true ||
      mapConfig?.provider !== "tencent" ||
      typeof mapConfig?.client_key !== "string" ||
      !mapConfig.client_key
    ) {
      throw new Error(
        "real map required but /ai/map/config is not a ready Tencent render provider",
      );
    }

    const { payload: translated } = await requestJson(base + "/ai/map/translate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        coordinates: [{ lat: 31.23, lng: 121.47 }],
      }),
    });
    if (
      translated?.provider !== "tencent" ||
      translated?.coordinate_system !== "GCJ-02" ||
      !Array.isArray(translated?.coordinates) ||
      translated.coordinates.length !== 1
    ) {
      throw new Error(
        "real-map coordinate probe did not return one Tencent GCJ-02 coordinate",
      );
    }
    mapMode = "tencent-verified";
  }

  console.log(`public-api-preflight: origin=${url.origin}`);
  console.log(`public-api-preflight: base_path=${normalizedPath}`);
  console.log(
    `public-api-preflight: health=ok ping=ok tauri_cors=ok real_map=${mapMode}`,
  );
}

main().catch((error) => {
  fail(error instanceof Error ? error.message : String(error));
});
