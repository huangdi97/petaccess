import type { Router } from "vue-router";

export type AndroidBackAction = "back" | "home" | "exit";

export function decideAndroidBackAction(
  routePath: string,
  consumerBackTarget: string | null,
): AndroidBackAction {
  if (consumerBackTarget) return "back";
  return routePath === "/" ? "exit" : "home";
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
 * Install PetAccess' Android hardware-back contract.
 *
 * Product navigation is governed by the Consumer route stack, not WebView's
 * internal history. Hash-router/WebView history can diverge from meaningful
 * PetAccess destinations, especially after packaged navigation or a fresh
 * deep link.
 */
export async function installAndroidBackHandler(router: Router): Promise<void> {
  const [{ onBackButtonPress }, { invoke }] = await Promise.all([
    import("@tauri-apps/api/app"),
    import("@tauri-apps/api/core"),
  ]);

  const stack = new ConsumerRouteStack(router.currentRoute.value.fullPath);
  router.afterEach((to) => stack.record(to.fullPath));

  await onBackButtonPress(({ canGoBack }) => {
    const current = router.currentRoute.value.fullPath;
    const routePath = router.currentRoute.value.path;
    const target = stack.previous(current);
    const action = decideAndroidBackAction(routePath, target);

    console.info(
      `PETACCESS_ANDROID_BACK action=${action} route=${routePath} target=${target ?? "-"} webviewCanGoBack=${canGoBack}`,
    );

    if (action === "back") {
      const consumed = stack.consumeBack(current);
      if (consumed) void router.replace(consumed);
      return;
    }

    if (action === "home") {
      stack.reset("/");
      void router.replace("/");
      return;
    }

    void invoke("exit_app").catch((error) => {
      console.error("PETACCESS_ANDROID_BACK exit_app failed", error);
    });
  });
}
