import assert from "node:assert/strict";
import { decideAndroidBackAction } from "../apps/client-h5/src/runtime/androidBack.ts";

const cases = [
  {
    name: "fresh Home exits even when WebView itself might have history",
    route: "/",
    back: null,
    expected: "exit",
  },
  {
    name: "Home with a real Consumer back target navigates back",
    route: "/",
    back: "/map",
    expected: "back",
  },
  {
    name: "Evidence with Consumer history navigates back",
    route: "/place/demo/evidence",
    back: "/place/demo/reality",
    expected: "back",
  },
  {
    name: "deep-linked Place without Consumer history returns Home",
    route: "/place/demo",
    back: null,
    expected: "home",
  },
] as const;

for (const item of cases) {
  assert.equal(
    decideAndroidBackAction(item.route, item.back),
    item.expected,
    item.name,
  );
}

console.log(`ANDROID_BACK_CONTRACT=PASS cases=${cases.length}`);
