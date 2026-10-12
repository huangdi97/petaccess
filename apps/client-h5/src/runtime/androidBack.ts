import type { Router } from "vue-router";

/**
 * Install the native Android Back contract for the packaged Tauri runtime.
 *
 * Product behavior:
 * - browser/router history exists -> go to the previous Consumer surface;
 * - a deep-linked non-home route has no prior history -> return Home;
 * - Home with no prior history -> finish the Android Activity.
 *
 * Tauri 2.11 exposes Android Back events in JS but does not yet expose the
 * 2.12 app.exit() helper. The final Home exit therefore goes through the small
 * Rust command backed by AppHandle::exit(0), whose Android behavior is to
 * finish the Activity rather than kill the process.
 */
export async function installAndroidBackHandler(router: Router): Promise<void> {
  const [{ onBackButtonPress }, { invoke }] = await Promise.all([
    import("@tauri-apps/api/app"),
    import("@tauri-apps/api/core"),
  ]);

  await onBackButtonPress(({ canGoBack }) => {
    const state = window.history.state as { back?: unknown } | null;
    const routerHasBackTarget = typeof state?.back === "string" && state.back.length > 0;

    if (canGoBack || routerHasBackTarget) {
      router.back();
      return;
    }

    if (router.currentRoute.value.path !== "/") {
      void router.replace("/");
      return;
    }

    void invoke("exit_app");
  });
}
