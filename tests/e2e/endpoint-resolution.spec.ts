/**
 * Regression spec for REG-003 / FF-001: the packaged Tauri runtime must NOT
 * depend on a Vite dev/preview proxy. The endpoint resolver maps each runtime
 * (WEB / TAURI_DESKTOP / TAURI_ANDROID) to an explicit API base.
 *
 * Fail-before evidence: this spec imports apps/client-h5/src/config/endpoints,
 * which does not exist until the fix is implemented — the run fails with a
 * module-resolution error, then passes after implementation.
 */
import { expect, test } from "@playwright/test";
import { detectRuntimeKind, resolveApiEndpoint } from "../../apps/client-h5/src/config/endpoints";

test("runtime kind is detected from webview UA + tauri internals", () => {
  expect(detectRuntimeKind("Mozilla/5.0 (Windows NT 10.0; Win64; x64)", false)).toBe("WEB");
  expect(
    detectRuntimeKind("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", true),
  ).toBe("TAURI_DESKTOP");
  expect(
    detectRuntimeKind("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36", true),
  ).toBe("TAURI_ANDROID");
});

test("WEB resolves relative /api/v1 (dev server proxy owns it)", () => {
  expect(resolveApiEndpoint({}, "WEB")).toBe("/api/v1");
  expect(resolveApiEndpoint({ VITE_API_BASE: "http://127.0.0.1:8000/api/v1" }, "WEB")).toBe(
    "http://127.0.0.1:8000/api/v1",
  );
});

test("TAURI_DESKTOP resolves an absolute endpoint, never a relative proxy path", () => {
  expect(resolveApiEndpoint({}, "TAURI_DESKTOP")).toBe("http://127.0.0.1:8000/api/v1");
  expect(
    resolveApiEndpoint({ VITE_TAURI_API_BASE: "https://api.example.com/api/v1" }, "TAURI_DESKTOP"),
  ).toBe("https://api.example.com/api/v1");
});

test("TAURI_ANDROID resolves 10.0.2.2 (emulator host) ONLY as the dev default", () => {
  expect(resolveApiEndpoint({}, "TAURI_ANDROID")).toBe("http://10.0.2.2:8000/api/v1");
  expect(
    resolveApiEndpoint(
      { VITE_TAURI_ANDROID_API_BASE: "https://api.example.com/api/v1" },
      "TAURI_ANDROID",
    ),
  ).toBe("https://api.example.com/api/v1");
  // 10.0.2.2 must never leak into WEB or desktop resolution.
  expect(resolveApiEndpoint({}, "WEB")).not.toContain("10.0.2.2");
  expect(resolveApiEndpoint({}, "TAURI_DESKTOP")).not.toContain("10.0.2.2");
});
