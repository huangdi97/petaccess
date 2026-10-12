import type { Router } from "vue-router";

export type AndroidBackAction = "back" | "home" | "exit";

/**
 * Decide Android Back from Consumer navigation state, not WebView history.
 *
 * Android WebView can report canGoBack=true even on a fresh hash-router Home
 * because the WebView itself may retain an internal navigation entry. That is
 * not a meaningful PetAccess destination. Vue Router's history.state.back is
 * the product-level source of truth.
 */
export function decideAndroidBackAction(
  routePath: string,
  routerBackTarget: unknown,
): AndroidBackAction {
  if (typeof routerBackTarget === "string" && routerBackTarget.length > 0) {
    return "back";
  }
  return routePath === "/" ? "exit" : "home";
}

/**
 * Install the native Android Back contract for the packaged Tauri runtime.
 *
 * Product behavior:
 * - a real Vue Router back target exists -> return to it;
 * - a deep-linked non-home route has no Consumer history -> return Home;
 * - Home with no Consumer history -> finish the Android Activity.
 *
 * Tauri's canGoBack payload is retained for diagnostics, but deliberately does
 * not decide product navigation because WebView history and Consumer history
 * are not equivalent for a hash-routed app.
 */
export async function installAndroidBackHandler(router: Router): Promise<void> {
  const [{ onBackButtonPress }, { invoke }] = await Promise.all([
    import("@tauri-apps/api/app"),
    import("@tauri-apps/api/core"),
  ]);

  await onBackButtonPress(({ canGoBack }) => {
    const state = window.history.state as { back?: unknown } | null;
    const routePath = router.currentRoute.value.path;
    const action = decideAndroidBackAction(routePath, state?.back);

    console.info(
      `PETACCESS_ANDROID_BACK action=${action} route=${routePath} webviewCanGoBack=${canGoBack}`,
    );

    if (action === "back") {
      router.back();
      return;
    }

    if (action === "home") {
      void router.replace("/");
      return;
    }

    void invoke("exit_app").catch((error) => {
      console.error("PETACCESS_ANDROID_BACK exit_app failed", error);
    });
  });
}
