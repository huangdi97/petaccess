import type { Router } from "vue-router";

/**
 * Install the native Android Back contract for the packaged Tauri runtime.
 *
 * Product behavior:
 * - browser/router history exists -> go to the previous Consumer surface;
 * - a deep-linked non-home route has no prior history -> return Home;
 * - Home with no prior history -> close the Android activity.
 *
 * The Tauri modules are loaded only by the Android packaged runtime. Web/H5
 * never imports the native bridge at startup.
 */
export async function installAndroidBackHandler(router: Router): Promise<void> {
  const [{ onBackButtonPress }, { getCurrentWindow }] = await Promise.all([
    import("@tauri-apps/api/app"),
    import("@tauri-apps/api/window"),
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

    void getCurrentWindow().close();
  });
}
