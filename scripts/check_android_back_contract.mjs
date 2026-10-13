import assert from "node:assert/strict";
import {
  ConsumerRouteStack,
  decideAndroidBackAction,
} from "../apps/client-h5/src/runtime/androidBack.ts";

const decisions = [
  ["/", null, "exit"],
  ["/place/demo", null, "home"],
  ["/place/demo/evidence", "/place/demo/reality", "back"],
];

for (const [route, target, expected] of decisions) {
  assert.equal(decideAndroidBackAction(route, target), expected);
}

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

const deepLink = new ConsumerRouteStack("/place/demo");
assert.equal(deepLink.previous("/place/demo"), null);
assert.equal(decideAndroidBackAction("/place/demo", deepLink.previous("/place/demo")), "home");

console.log("ANDROID_BACK_CONTRACT=PASS decisions=3 stack=5 deepLink=1");
