import { nextTick, ref, watch } from "vue";

const FOCUSABLE =
  'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

/**
 * Shared keyboard focus model for modal surfaces.
 *
 * The caller owns Escape/close semantics. This composable only makes the
 * surface a real modal interaction: focus enters on open, Tab/Shift+Tab stay
 * inside, and focus returns to the invoking control after close.
 */
export function useDialogFocus(isOpen: () => boolean) {
  const panel = ref<HTMLElement | null>(null);
  let returnFocus: HTMLElement | null = null;

  function focusInside() {
    const target = panel.value?.querySelector<HTMLElement>(FOCUSABLE) ?? panel.value;
    target?.focus();
  }

  watch(
    isOpen,
    async (open) => {
      if (open) {
        returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null;
        await nextTick();
        focusInside();
        return;
      }
      if (returnFocus) {
        await nextTick();
        returnFocus.focus();
        returnFocus = null;
      }
    },
    { immediate: true },
  );

  function keepFocusInside(event: KeyboardEvent) {
    if (event.key !== "Tab" || !panel.value) return;
    const items = [...panel.value.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
      (item) => item.offsetParent !== null,
    );
    if (!items.length) {
      event.preventDefault();
      panel.value.focus();
      return;
    }
    const first = items[0]!;
    const last = items[items.length - 1]!;
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  return { panel, keepFocusInside };
}
