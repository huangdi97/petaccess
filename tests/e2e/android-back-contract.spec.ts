import { expect, test } from "@playwright/test";
import {
  ConsumerRouteStack,
  decideAndroidBackAction,
  shouldInterceptAndroidBack,
} from "../../apps/client-h5/src/runtime/androidBack";

test.describe("Android Consumer Back contract", () => {
  test("fresh Home is system-owned and exits instead of inventing app history", () => {
    expect(decideAndroidBackAction("/", null)).toBe("exit");
    expect(shouldInterceptAndroidBack("/", null)).toBe(false);
  });

  test("a non-root route without Consumer history returns Home", () => {
    expect(decideAndroidBackAction("/settings", null)).toBe("home");
    expect(shouldInterceptAndroidBack("/settings", null)).toBe(true);
  });

  test("Place → Reality → Evidence consumes back to Reality", () => {
    const stack = new ConsumerRouteStack("/");
    stack.record("/place/place-1");
    stack.record("/place/place-1/reality");
    stack.record("/place/place-1/evidence");

    expect(stack.previous("/place/place-1/evidence")).toBe("/place/place-1/reality");
    expect(stack.consumeBack("/place/place-1/evidence")).toBe("/place/place-1/reality");
    expect(stack.previous("/place/place-1/reality")).toBe("/place/place-1");
  });

  test("query/view changes on one Consumer route do not create extra Back layers", () => {
    const stack = new ConsumerRouteStack("/");
    stack.record("/place/place-1");
    stack.record("/place/place-1?view=rules");
    stack.record("/place/place-1?view=space");

    expect(stack.previous("/place/place-1?view=space")).toBe("/");
    expect(stack.consumeBack("/place/place-1?view=space")).toBe("/");
  });

  test("recording the same path twice is idempotent", () => {
    const stack = new ConsumerRouteStack("/");
    stack.record("/map");
    stack.record("/map");

    expect(stack.previous("/map")).toBe("/");
    expect(stack.consumeBack("/map")).toBe("/");
    expect(stack.previous("/")).toBeNull();
  });
});
