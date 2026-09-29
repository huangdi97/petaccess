/**
 * UI Oracle — page-eval.ts
 *
 * Transfers a probe function (plus any helper functions it closes over) into
 * the browser via source serialization. Playwright's page.evaluate only
 * serializes the passed function itself — module-level imports like
 * `measureElement` are not resolvable inside the page. This module rebuilds
 * the helpers as `const` bindings in the same closure as the function, so
 * name references inside the function resolve lexically, then invokes it.
 */
import type { Page } from "@playwright/test";

export interface InPageEvalOptions<T> {
  /** Primary function to run in the page (must be DOM-only, no imports). */
  fn: (a: unknown) => unknown;
  /** Helper functions the primary fn references by name (source-injected as const). */
  helpers?: Record<string, (...args: never[]) => unknown>;
  /** Argument object passed to fn. */
  arg?: T;
}

/**
 * Evaluate `fn(arg)` inside the page. `helpers` are injected as local `const`
 * bindings in the same closure as the serialized `fn`. Returns a
 * JSON-serializable result.
 */
export async function pageEval<T>(page: Page, opts: InPageEvalOptions<T>): Promise<unknown> {
  const helperSrc = Object.entries(opts.helpers ?? {})
    .map(([name, h]) => `const ${name} = (${h.toString()});`)
    .join("\n");
  const fnSrc = opts.fn.toString();
  return page.evaluate(
    ({ helperSrc, fnSrc, arg }) => {
      // Serialize the helper bindings and the function into one closure so the
      // function's name references resolve lexically inside the page.
      const factory = new Function(
        "helperSrc",
        "fnSrc",
        `
        return (function run() {
          ${helperSrc}
          return (${fnSrc});
        })();
      `,
      );
      const fn = factory(helperSrc, fnSrc) as (a: unknown) => unknown;
      return fn.call(null, arg);
    },
    { helperSrc, fnSrc, arg: opts.arg },
  );
}
