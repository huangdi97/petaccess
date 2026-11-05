/**
 * VisualViewport + native Android IME runtime bridge.
 *
 * Android WebView M139+ resizes the visual viewport while the IME is visible.
 * Older system WebViews can show the keyboard without changing
 * `window.visualViewport`, so the Tauri Android shell also publishes
 * authoritative WindowInsets.Type.ime() state through `petaccess:native-ime`.
 *
 * Browsers keep using the VisualViewport heuristic. Packaged Android prefers
 * native state when the bridge is present; both sources drive the same DOM
 * contract so app chrome never needs route-specific keyboard hacks.
 */

interface NativeImeState {
  visible: boolean;
  height: number;
}

declare global {
  interface Window {
    __PETACCESS_NATIVE_IME__?: NativeImeState;
  }

  interface WindowEventMap {
    "petaccess:native-ime": CustomEvent<NativeImeState>;
  }
}

export function isTextEntryElement(element: Element | null): boolean {
  if (!element) return false;

  const tag = element.tagName.toLowerCase();
  if (tag === "textarea" || tag === "select") return true;

  if (tag === "input") {
    const type = (element.getAttribute("type") ?? "text").toLowerCase();
    return ![
      "button",
      "checkbox",
      "color",
      "file",
      "hidden",
      "image",
      "radio",
      "range",
      "reset",
      "submit",
    ].includes(type);
  }

  return element instanceof HTMLElement && element.isContentEditable;
}

export function isImeOcclusionLikely(
  baselineHeight: number,
  visualHeight: number,
  visualOffsetTop: number,
  hasTextEntryFocus: boolean,
): boolean {
  if (!hasTextEntryFocus || baselineHeight <= 0 || visualHeight <= 0) return false;

  const visibleBottom = visualOffsetTop + visualHeight;
  const occluded = Math.max(0, baselineHeight - visibleBottom);
  const threshold = Math.min(160, Math.max(96, baselineHeight * 0.15));
  return occluded >= threshold;
}

export function normaliseNativeImeState(value: unknown): NativeImeState | null {
  if (!value || typeof value !== "object") return null;

  const candidate = value as Partial<NativeImeState>;
  if (typeof candidate.visible !== "boolean") return null;
  if (typeof candidate.height !== "number" || !Number.isFinite(candidate.height)) return null;

  return {
    visible: candidate.visible,
    height: Math.max(0, candidate.height),
  };
}

export function installVisualViewportState(): () => void {
  const viewport = window.visualViewport;
  const root = document.documentElement;

  let nativeImeState = normaliseNativeImeState(window.__PETACCESS_NATIVE_IME__);
  let baselineHeight = Math.max(
    window.innerHeight,
    viewport ? viewport.height + viewport.offsetTop : window.innerHeight,
  );
  let frame = 0;

  const apply = (): void => {
    frame = 0;
    const hasTextEntryFocus = isTextEntryElement(document.activeElement);
    const visualHeight = viewport?.height ?? window.innerHeight;
    const visualOffsetTop = viewport?.offsetTop ?? 0;

    if (!hasTextEntryFocus && !nativeImeState?.visible) {
      baselineHeight = Math.max(window.innerHeight, visualHeight + visualOffsetTop);
    }

    const browserImeVisible = viewport
      ? isImeOcclusionLikely(
          Math.max(baselineHeight, window.innerHeight),
          visualHeight,
          visualOffsetTop,
          hasTextEntryFocus,
        )
      : false;

    const visibleBottom = visualOffsetTop + visualHeight;
    const browserOccludedBottom = Math.max(
      0,
      Math.max(baselineHeight, window.innerHeight) - visibleBottom,
    );

    const imeVisible = nativeImeState?.visible ?? browserImeVisible;
    const occludedBottom = nativeImeState
      ? nativeImeState.visible
        ? nativeImeState.height
        : 0
      : browserImeVisible
        ? browserOccludedBottom
        : 0;

    root.dataset.ime = imeVisible ? "visible" : "hidden";
    root.dataset.imeSource = nativeImeState ? "native" : viewport ? "visual-viewport" : "none";
    root.style.setProperty("--pa-visual-viewport-height", `${visualHeight}px`);
    root.style.setProperty("--pa-visual-viewport-top", `${visualOffsetTop}px`);
    root.style.setProperty("--pa-ime-occluded-bottom", `${occludedBottom}px`);
  };

  const schedule = (): void => {
    if (frame) cancelAnimationFrame(frame);
    frame = requestAnimationFrame(apply);
  };

  const onNativeIme = (event: WindowEventMap["petaccess:native-ime"]): void => {
    const next = normaliseNativeImeState(event.detail);
    if (!next) return;
    nativeImeState = next;
    window.__PETACCESS_NATIVE_IME__ = next;
    schedule();
  };

  viewport?.addEventListener("resize", schedule);
  viewport?.addEventListener("scroll", schedule);
  window.addEventListener("resize", schedule);
  window.addEventListener("orientationchange", schedule);
  window.addEventListener("petaccess:native-ime", onNativeIme);
  document.addEventListener("focusin", schedule);
  document.addEventListener("focusout", schedule);

  apply();

  return () => {
    if (frame) cancelAnimationFrame(frame);
    viewport?.removeEventListener("resize", schedule);
    viewport?.removeEventListener("scroll", schedule);
    window.removeEventListener("resize", schedule);
    window.removeEventListener("orientationchange", schedule);
    window.removeEventListener("petaccess:native-ime", onNativeIme);
    document.removeEventListener("focusin", schedule);
    document.removeEventListener("focusout", schedule);
  };
}
