/**
 * useBreakpoint — reactive viewport bucket matching the design tokens
 * (V020_DESIGN_SYSTEM_SPEC §8). The shell renders mobile bottom navigation
 * below `lg` and the navigation rail from `lg` (768px) upward; pages use the
 * bucket to switch layouts without duplicating media queries.
 */
import { computed, onScopeDispose, ref, type ComputedRef } from "vue";
import { BREAKPOINTS, type BreakpointKey } from "@petaccess/design-tokens";

function resolveFromWidth(width: number): BreakpointKey {
  if (width >= BREAKPOINTS.xl) return "xl";
  if (width >= BREAKPOINTS.lg) return "lg";
  if (width >= BREAKPOINTS.md) return "md";
  return "sm";
}

const breakpoint = ref<BreakpointKey>(
  typeof window === "undefined" ? "sm" : resolveFromWidth(window.innerWidth),
);

/** Listeners are shared, so the first consumer attaches and others reuse. */
let refCount = 0;
const cleanup: (() => void)[] = [];

function attach() {
  if (typeof window === "undefined") return;
  refCount += 1;
  if (refCount > 1) return;
  const onChange = () => {
    breakpoint.value = resolveFromWidth(window.innerWidth);
  };
  const queries = [
    { key: "lg" as const, mql: window.matchMedia(`(min-width: ${BREAKPOINTS.lg}px)`) },
    { key: "xl" as const, mql: window.matchMedia(`(min-width: ${BREAKPOINTS.xl}px)`) },
  ];
  for (const { key, mql } of queries) {
    const listener = (e: MediaQueryListEvent) => {
      if (e.matches) breakpoint.value = key;
    };
    mql.addEventListener("change", listener);
    cleanup.push(() => mql.removeEventListener("change", listener));
  }
  window.addEventListener("resize", onChange);
  cleanup.push(() => window.removeEventListener("resize", onChange));
  onChange();
}

function detach() {
  refCount -= 1;
  if (refCount > 0) return;
  cleanup.splice(0).forEach((fn) => fn());
}

export interface BreakpointState {
  breakpoint: ComputedRef<BreakpointKey>;
  /** True below the tablet rail breakpoint (viewport < 768px). */
  mobile: ComputedRef<boolean>;
  /** True from the tablet rail breakpoint upward (viewport >= 768px). */
  desktop: ComputedRef<boolean>;
}

export function useBreakpoint(): BreakpointState {
  attach();
  onScopeDispose(detach);
  return {
    breakpoint: computed(() => breakpoint.value),
    mobile: computed(() => breakpoint.value === "sm" || breakpoint.value === "md"),
    desktop: computed(() => breakpoint.value === "lg" || breakpoint.value === "xl"),
  };
}