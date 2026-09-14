/**
 * Online/offline awareness (Master Goal §5.5 — every core page needs an
 * offline state).
 *
 * The product deliberately does NOT queue writes while offline: a verification
 * or a contribution submitted without a confirmed round-trip would create a
 * false record, and evidence integrity is the whole point of the platform. So
 * this composable only reports connectivity; callers disable mutating actions
 * and explain why.
 */
import { onScopeDispose, readonly, ref } from "vue";

function currentOnline(): boolean {
  if (typeof navigator === "undefined") return true;
  // navigator.onLine is a hint, not a guarantee: it is true on a captive portal
  // and false on some emulators. It is good enough to decide whether to *show*
  // the offline affordance; the request itself remains the source of truth.
  return navigator.onLine !== false;
}

const online = ref(currentOnline());

let listeners = 0;

function attach() {
  if (typeof window === "undefined") return;
  listeners += 1;
  if (listeners > 1) return;
  window.addEventListener("online", () => (online.value = true));
  window.addEventListener("offline", () => (online.value = false));
}

export function useOnline() {
  attach();
  onScopeDispose(() => {
    listeners = Math.max(0, listeners - 1);
  });
  return { online: readonly(online) };
}

/** Non-reactive probe, for use outside a component scope. */
export function isOnline(): boolean {
  return currentOnline();
}
