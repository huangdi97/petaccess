import type { Router } from "vue-router";

export type AndroidBackAction = "back" | "home" | "exit";

interface AndroidBackListener {
  unregister(): Promise<void>;
}

export function decideAndroidBackAction(
  routePath: string,
  consumerBackTarget: string | null,
): AndroidBackAction {
  if (consumerBackTarget) return "back";
  return routePath === "/" ? "exit" : "home";
}

export function shouldInterceptAndroidBack(
  routePath: string,
  consumerBackTarget: string | null,
): boolean {
  return decideAndroidBackAction(routePath, consumerBackTarget) !== "exit";
}

export class ConsumerRouteStack {
  private entries: string[];

  constructor(initialPath: string) {
    this.entries = initialPath ? [initialPath] : ["/"];
  }

  record(path: string): void {
    if (!path) return;
    const current = this.entries[this.entries.length - 1];
    if (current === path) return;

    // Query/hash changes are local state of the same Consumer surface (for
    // example Place ?view=rules -> ?view=evidence). Browser history may keep
    // those entries, but Android hardware Back should not make the user unwind
    // every local tab/filter change before leaving the page.
    const currentRoutePath = current?.split(/[?#]/, 1)[0] ?? "";
    const nextRoutePath = path.split(/[?#]/, 1)[0] ?? "";
    if (currentRoutePath && currentRoutePath === nextRoutePath) {
      this.entries[this.entries.length - 1] = path;
      return;
    }

    this.entries.push(path);
    if (this.entries.length > 64) this.entries.splice(0, this.entries.length - 64);
  }

  previous(currentPath: string): string | null {
    while (this.entries.length && this.entries[this.entries.length - 1] !== currentPath) {
      this.entries.pop();
    }
    if (this.entries.length <= 1) return null;
    return this.entries[this.entries.length - 2] ?? null;
  }

  consumeBack(currentPath: string): string | null {
    const target = this.previous(currentPath);
    if (!target) return null;
    this.entries.pop();
    return target;
  }

  reset(path = "/"): void {
    this.entries = [path];
  }
}

/**
 * Install PetAccess Android hardware-back contract.
 *
 * Android 16 predictive-back must remain system-owned at the task root.
 * Tauri onBackButtonPress takes over the default system behavior while a
 * listener is registered, so PetAccess registers it only when the Consumer
 * has an in-app Back action to perform. At a fresh Home root the listener is
 * removed and Android itself owns back-to-home.
 *
 * Non-root navigation is governed by the Consumer route stack, not WebView
 * incidental hash/history implementation.
 */
export async function installAndroidBackHandler(router: Router): Promise<void> {
  const [{ onBackButtonPress }, { invoke }] = await Promise.all([
    import("@tauri-apps/api/app"),
    import("@tauri-apps/api/core"),
  ]);

  const stack = new ConsumerRouteStack(router.currentRoute.value.fullPath);
  let listener: AndroidBackListener | null = null;
  let syncChain: Promise<void> = Promise.resolve();

  const setState = (state: "system-root" | "intercepting" | "failed"): void => {
    document.documentElement.dataset.androidBack = state;
  };

  const handleBack = ({ canGoBack }: { canGoBack: boolean }): void => {
    const current = router.currentRoute.value.fullPath;
    const callbackCount =
      Number(document.documentElement.dataset.androidBackCallbackCount ?? "0") + 1;
    document.documentElement.dataset.androidBackCallbackCount = String(callbackCount);
    document.documentElement.dataset.androidBackLastRoute = current;
    document.documentElement.dataset.androidBackLastAt = String(Date.now());
    const routePath = router.currentRoute.value.path;
    const target = stack.previous(current);
    const action = decideAndroidBackAction(routePath, target);

    console.info(
      `PETACCESS_ANDROID_BACK source=consumer-stack action=${action} route=${routePath} target=${target ?? "-"} webviewCanGoBack=${canGoBack}`,
    );

    if (action === "back") {
      const consumed = stack.consumeBack(current);
      document.documentElement.dataset.androidBackLastAction = "back";
      document.documentElement.dataset.androidBackLastTarget = consumed ?? "";
      if (consumed) {
        void router
          .replace(consumed)
          .then(() => {
            document.documentElement.dataset.androidBackLastResult =
              router.currentRoute.value.fullPath;
          })
          .catch((error) => {
            document.documentElement.dataset.androidBackLastResult = "router-error";
            console.error("PETACCESS_ANDROID_BACK router.replace failed", error);
          });
      }
      return;
    }

    if (action === "home") {
      document.documentElement.dataset.androidBackLastAction = "home";
      document.documentElement.dataset.androidBackLastTarget = "/";
      stack.reset("/");
      void router
        .replace("/")
        .then(() => {
          document.documentElement.dataset.androidBackLastResult =
            router.currentRoute.value.fullPath;
        })
        .catch((error) => {
          document.documentElement.dataset.androidBackLastResult = "router-error";
          console.error("PETACCESS_ANDROID_BACK router.replace home failed", error);
        });
      return;
    }

    // Race fallback only. Normal root state has no registered listener.
    const staleListener = listener;
    listener = null;
    setState("system-root");
    void staleListener
      ?.unregister()
      .catch((error) => {
        console.error("PETACCESS_ANDROID_BACK root listener unregister failed", error);
      })
      .finally(() => {
        window.setTimeout(() => {
          void invoke("exit_app").catch((error) => {
            console.error("PETACCESS_ANDROID_BACK exit_app fallback failed", error);
          });
        }, 0);
      });
  };

  const syncRegistration = async (): Promise<void> => {
    const current = router.currentRoute.value.fullPath;
    const routePath = router.currentRoute.value.path;
    const target = stack.previous(current);
    const intercept = shouldInterceptAndroidBack(routePath, target);

    if (intercept) {
      if (!listener) {
        listener = (await onBackButtonPress(handleBack)) as AndroidBackListener;
      }
      setState("intercepting");
      return;
    }

    if (listener) {
      const staleListener = listener;
      listener = null;
      await staleListener.unregister();
    }
    setState("system-root");
  };

  const scheduleSync = (): Promise<void> => {
    syncChain = syncChain.then(syncRegistration).catch((error) => {
      setState("failed");
      console.error("PETACCESS_ANDROID_BACK registration sync failed", error);
      throw error;
    });
    return syncChain;
  };

  router.afterEach((to) => {
    stack.record(to.fullPath);
    void scheduleSync().catch(() => {
      // The visible failed state is consumed by Android runtime acceptance.
    });
  });

  await scheduleSync();
}
