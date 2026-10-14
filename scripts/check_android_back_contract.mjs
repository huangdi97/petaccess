import assert from "node:assert/strict";
import {
  ConsumerRouteStack,
  decideAndroidBackAction,
  shouldInterceptAndroidBack,
} from "../apps/client-h5/src/runtime/androidBack.ts";

const decisions = [
  ["/", null, "exit"],
  ["/place/demo", null, "home"],
  ["/place/demo/evidence", "/place/demo/reality", "back"],
];

for (const [route, target, expected] of decisions) {
  assert.equal(decideAndroidBackAction(route, target), expected);
}

assert.equal(shouldInterceptAndroidBack("/", null), false);
assert.equal(shouldInterceptAndroidBack("/place/demo", null), true);
assert.equal(shouldInterceptAndroidBack("/place/demo/evidence", "/place/demo/reality"), true);

const stack = new ConsumerRouteStack("/");
for (const path of [
  "/search",
  "/map",
  "/place/demo",
  "/place/demo/reality",
  "/place/demo/evidence",
]) {
  stack.record(path);
}

assert.equal(stack.previous("/place/demo/evidence"), "/place/demo/reality");
assert.equal(stack.consumeBack("/place/demo/evidence"), "/place/demo/reality");
assert.equal(stack.previous("/place/demo/reality"), "/place/demo");
assert.equal(stack.consumeBack("/place/demo/reality"), "/place/demo");

// Re-recording the current route must not create a fake extra Back stop.
const duplicate = new ConsumerRouteStack("/");
duplicate.record("/search");
duplicate.record("/search");
assert.equal(duplicate.previous("/search"), "/");
assert.equal(duplicate.consumeBack("/search"), "/");
assert.equal(duplicate.previous("/"), null);

// If router state is replaced outside the stack, previous() trims stale
// destinations until it reaches the actual current route.
const replaced = new ConsumerRouteStack("/");
replaced.record("/search");
replaced.record("/map");
assert.equal(replaced.previous("/search"), "/");
assert.equal(replaced.consumeBack("/search"), "/");

// The stack is intentionally bounded. A long session must keep only 64
// meaningful destinations instead of growing forever.
const bounded = new ConsumerRouteStack("/");
for (let i = 1; i <= 100; i += 1) {
  bounded.record(`/place/${i}`);
}
let current = "/place/100";
let consumed = 0;
while (true) {
  const target = bounded.consumeBack(current);
  if (!target) break;
  consumed += 1;
  current = target;
}
assert.equal(consumed, 63);
assert.equal(current, "/place/37");

const deepLink = new ConsumerRouteStack("/place/demo");
assert.equal(deepLink.previous("/place/demo"), null);
assert.equal(decideAndroidBackAction("/place/demo", deepLink.previous("/place/demo")), "home");
deepLink.reset("/");
assert.equal(deepLink.previous("/"), null);
assert.equal(decideAndroidBackAction("/", deepLink.previous("/")), "exit");

console.log(
  "ANDROID_BACK_CONTRACT=PASS decisions=3 ownership=3 stack=5 duplicate=3 replace=2 bounded=63 deepLink=2",
);
