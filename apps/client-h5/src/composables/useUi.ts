/**
 * Global UI state for the app shell (V020_APP_SHELL_SPEC §shell-state).
 *
 * The ConsumerAppShell hosts one toaster and one dialog host for the whole
 * app; pages never render their own alert() / toast stacks. This module owns
 * the reactive state so any page can `useUi()` and trigger a toast or a
 * confirm dialog without prop drilling.
 */
import { computed, reactive, readonly, type ComputedRef } from "vue";

export type ToastKind = "success" | "info" | "warning" | "error";

export interface ToastItem {
  id: number;
  kind: ToastKind;
  message: string;
  /** Auto-dismiss in ms; 0 = sticky until dismissed. */
  duration: number;
}

export interface DialogOptions {
  title: string;
  message?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  danger?: boolean;
}

export interface UiState {
  toasts: ToastItem[];
  dialog: { open: boolean; options: DialogOptions } | null;
}

export type DialogState = Readonly<{ open: boolean; options: DialogOptions }> | null;

const state = reactive<UiState>({ toasts: [], dialog: null });

/** Typed reactive window into the dialog state (readonly() chokes on the null union). */
const dialogState = computed<DialogState>(() => state.dialog);

let nextId = 1;
let dialogResolve: ((ok: boolean) => void) | null = null;

export interface UseUi {
  toasts: readonly ToastItem[];
  dialog: ComputedRef<DialogState>;
  toast: (kind: ToastKind, message: string, duration?: number) => number;
  success: (message: string) => number;
  info: (message: string) => number;
  warning: (message: string) => number;
  error: (message: string) => number;
  dismissToast: (id: number) => void;
  confirm: (options: DialogOptions) => Promise<boolean>;
  closeDialog: (ok: boolean) => void;
}

export function useUi(): UseUi {
  /** Show a toast. Returns a dismiss handle. */
  function toast(kind: ToastKind, message: string, duration = 3500): number {
    const id = nextId++;
    state.toasts.push({ id, kind, message, duration });
    if (duration > 0) {
      window.setTimeout(() => dismissToast(id), duration);
    }
    return id;
  }

  function success(message: string): number {
    return toast("success", message);
  }

  function info(message: string): number {
    return toast("info", message);
  }

  function warning(message: string): number {
    return toast("warning", message);
  }

  function error(message: string): number {
    return toast("error", message, 6000);
  }

  function dismissToast(id: number) {
    const i = state.toasts.findIndex((t) => t.id === id);
    if (i >= 0) state.toasts.splice(i, 1);
  }

  /** Open a modal dialog; resolves true on confirm, false on cancel. */
  function confirm(options: DialogOptions): Promise<boolean> {
    if (dialogResolve) dialogResolve(false); // close a previous pending dialog
    state.dialog = { open: true, options };
    return new Promise((resolve) => {
      dialogResolve = resolve;
    });
  }

  function closeDialog(ok: boolean) {
    state.dialog = null;
    if (dialogResolve) {
      dialogResolve(ok);
      dialogResolve = null;
    }
  }

  return {
    toasts: readonly(state.toasts),
    dialog: dialogState,
    toast,
    success,
    info,
    warning,
    error,
    dismissToast,
    confirm,
    closeDialog,
  };
}

/** Non-reactive probe for tests / shell decisions. */
export function hasOpenDialog(): boolean {
  return state.dialog !== null;
}