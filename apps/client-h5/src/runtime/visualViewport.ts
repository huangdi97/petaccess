/**
 * VisualViewport runtime bridge.
 *
 * Android WebView resizes the visual viewport while the IME is visible. Keep
 * that platform fact explicit in DOM state so app chrome can react without
 * route-specific hacks. The heuristic also works in mobile browsers and
 * deliberately requires a text-entry focus to avoid treating browser chrome
 * changes as an IME.
 */

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

export function installVisualViewportState(): () => void {
  const viewport = window.visualViewport;
  const root = document.documentElement;

  if (!viewport) {
    root.dataset.ime = "unsupported";
    return () => undefined;
  }

  let baselineHeight = Math.max(
    window.innerHeight,
    viewport.height + viewport.offsetTop,
  );
  let frame = 0;

  const apply = (): void => {
    frame = 0;
    const hasTextEntryFocus = isTextEntryElement(document.activeElement);

    if (!hasTextEntryFocus) {
      baselineHeight = Math.max(
        baselineHeight,
        window.innerHeight,
        viewport.height + viewport.offsetTop,
      );
    }

    const imeVisible = isImeOcclusionLikely(
      Math.max(baselineHeight, window.innerHeight),
      viewport.height,
      viewport.offsetTop,
      hasTextEntryFocus,
    );

    const visibleBottom = viewport.offsetTop + viewport.height;
    const occludedBottom = Math.max(
      0,
      Math.max(baselineHeight, window.innerHeight) - visibleBottom,
    );

    root.dataset.ime = imeVisible ? "visible" : "hidden";
    root.style.setProperty("--pa-visual-viewport-height", `${viewport.height}px`);
    root.style.setProperty("--pa-visual-viewport-top", `${viewport.offsetTop}px`);
    root.style.setProperty(
      "--pa-ime-occluded-bottom",
      `${imeVisible ? occludedBottom : 0}px`,
    );
  };

  const schedule = (): void => {
    if (frame) cancelAnimationFrame(frame);
    frame = requestAnimationFrame(apply);
  };

  viewport.addEventListener("resize", schedule);
  viewport.addEventListener("scroll", schedule);
  window.addEventListener("resize", schedule);
  window.addEventListener("orientationchange", schedule);
  document.addEventListener("focusin", schedule);
  document.addEventListener("focusout", schedule);

  apply();

  return () => {
    if (frame) cancelAnimationFrame(frame);
    viewport.removeEventListener("resize", schedule);
    viewport.removeEventListener("scroll", schedule);
    window.removeEventListener("resize", schedule);
    window.removeEventListener("orientationchange", schedule);
    document.removeEventListener("focusin", schedule);
    document.removeEventListener("focusout", schedule);
  };
}
