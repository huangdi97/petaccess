/**
 * Runtime-aware API endpoint resolution (forensic fix REG-003 / FF-001).
 *
 * The H5 bundle used to default to the relative "/api/v1" path, which only
 * works while a Vite dev/preview proxy is serving the page. Tauri packaged
 * apps (Windows/Android) have no Vite server: relative fetches hit the
 * WebView's own asset origin and every API call fails silently at the data
 * layer (the Empty-First shell still renders, so the failure is invisible on
 * screenshots).
 *
 * Each runtime resolves to an explicit endpoint:
 *   WEB           -> VITE_API_BASE ?? "/api/v1"          (dev proxy owns /api)
 *   TAURI_DESKTOP -> VITE_TAURI_API_BASE ?? "http://127.0.0.1:8000/api/v1"
 *   TAURI_ANDROID -> VITE_TAURI_ANDROID_API_BASE ?? "http://10.0.2.2:8000/api/v1"
 *
 * PROVIDER: 10.0.2.2 is the Android emulator's alias for the host machine and
 * is ONLY the Android *dev* default. Production Android builds must pin
 * VITE_TAURI_ANDROID_API_BASE at build time; this module never leaks 10.0.2.2
 * into WEB or desktop resolution.
 */
export type PetAccessRuntimeKind = "WEB" | "TAURI_DESKTOP" | "TAURI_ANDROID";

export interface EndpointEnv {
  VITE_API_BASE?: string;
  VITE_TAURI_API_BASE?: string;
  VITE_TAURI_ANDROID_API_BASE?: string;
}

export function detectRuntimeKind(
  userAgent: string,
  hasTauriInternals: boolean,
): PetAccessRuntimeKind {
  if (!hasTauriInternals) return "WEB";
  return /android/i.test(userAgent) ? "TAURI_ANDROID" : "TAURI_DESKTOP";
}

export function resolveApiEndpoint(
  env: EndpointEnv,
  kind: PetAccessRuntimeKind,
): string {
  const strip = (v: string | undefined): string | undefined => v?.replace(/\/$/, "");
  switch (kind) {
    case "TAURI_ANDROID":
      return strip(env.VITE_TAURI_ANDROID_API_BASE) ?? "http://10.0.2.2:8000/api/v1";
    case "TAURI_DESKTOP":
      return strip(env.VITE_TAURI_API_BASE) ?? "http://127.0.0.1:8000/api/v1";
    case "WEB":
      return strip(env.VITE_API_BASE) ?? "/api/v1";
  }
}