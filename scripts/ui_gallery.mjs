/**
 * 鐢熸垚 artifacts/ui-audit/UI_*_GALLERY.html銆? * 鐢ㄦ硶: node scripts/ui_gallery.mjs <stage:current|m3-final> [--after]
 * 璇诲彇 artifacts/ui-audit/{stage}/{viewport}/*.png 骞惰緭鍑哄彲鐩存帴鎵撳紑鐨勭敾寤婇〉銆? */
import { readdirSync, writeFileSync, existsSync } from "node:fs";
import path from "node:path";

const stage = process.argv[2] ?? "current";
const withAfter = process.argv.includes("--after");
const root = path.resolve("artifacts/ui-audit", stage);
if (!existsSync(root)) {
  console.error(`stage dir missing: ${root}`);
  process.exit(1);
}

const commit = process.env.GALLERY_SHA ?? "049fc39";
const ts = new Date().toISOString();
const viewports = ["ui-360", "ui-430", "ui-800", "ui-1280", "ui-1440"];
const viewportLabel = {
  "ui-360": "360脳740 (mobile)",
  "ui-430": "430脳740 (mobile)",
  "ui-800": "800脳900 (tablet)",
  "ui-1280": "1280脳800 (desktop)",
  "ui-1440": "1440脳900 (desktop)",
};
const stateLabel = {
  ready: "Ready",
  loading: "Loading",
  empty: "Empty",
  error: "Error",
  offline: "Offline",
  stale: "Stale",
};

const rows = [];
for (const vp of viewports) {
  const dir = path.join(root, vp);
  if (!existsSync(dir)) continue;
  for (const f of readdirSync(dir)
    .filter((f) => f.endsWith(".png"))
    .sort()) {
    const base = f.replace(/\.png$/, "");
    const [slug, state] = base.split("-");
    const page =
      slug === "search"
        ? "Search"
        : slug === "place"
          ? "Place"
          : slug === "map"
            ? "Map"
            : slug === "contribute"
              ? "Contribution"
              : slug === "mine"
                ? "Mine"
                : "Home";
    rows.push({ vp, f, base, page, state });
  }
}

const afterRoot = withAfter ? path.resolve("artifacts/ui-audit", "m3-final") : null;
const cells = rows
  .map((r) => {
    const after = afterRoot ? existsSync(path.join(afterRoot, r.vp, r.f)) : false;
    return `
  <tr>
    <td>${r.page}</td>
    <td>${stateLabel[r.state] ?? r.state}</td>
    <td>${viewportLabel[r.vp]}</td>
    <td class="shot"><img src="${stage}/${r.vp}/${r.f}" alt="${r.page} ${r.state} @ ${r.vp}"></td>
    ${after ? `<td class="shot"><img src="m3-final/${r.vp}/${r.f}" alt="AFTER ${r.page} ${r.state} @ ${r.vp}"></td>` : ""}
  </tr>`;
  })
  .join("\n");

const afterCol = withAfter ? "<th>AFTER (m3-final)</th>" : "";
const html = `<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PetAccess UI Gallery 鈥?${stage === "current" ? "CURRENT STATE" : "M3 FINAL"} (${stage})</title>
<style>
  body { font-family: "Segoe UI", system-ui, sans-serif; background: #f4f6f8; color: #1d2733; margin: 0; padding: 24px; }
  h1 { font-size: 20px; }
  .meta { color: #5c6772; font-size: 13px; margin: 4px 0 16px; }
  table { border-collapse: collapse; width: 100%; background: #fff; }
  th, td { border: 1px solid #e4e8ec; padding: 8px 10px; vertical-align: top; text-align: left; }
  th { background: #eef1f4; font-size: 13px; position: sticky; top: 0; }
  img { max-width: 320px; width: 100%; border: 1px solid #e4e8ec; display: block; }
  td.shot { width: 320px; }
</style>
</head>
<body>
<h1>PetAccess UI Gallery 鈥?${stage === "current" ? "褰撳墠鐘舵€?(BEFORE)" : "M3 鏈€缁?(AFTER)"}</h1>
<p class="meta">
  Stage: ${stage} 路 Screenshots: ${rows.length} 路 Commit SHA: ${commit} 路 Timestamp: ${ts}<br>
  Runtime: Playwright Chromium headless 路 鏈嶅姟鏍? petaccess_visual 纭畾鎬?seed 鈫?API :8011 鈫?H5 preview :5175
</p>
<table>
<thead><tr><th>椤甸潰</th><th>鐘舵€?/th><th>Viewport</th><th>鎴浘</th>${afterCol}</tr></thead>
<tbody>${cells}
</tbody>
</table>
</body>
</html>`;

const out = path.resolve(
  "artifacts/ui-audit",
  `UI_${stage === "current" ? "CURRENT_STATE" : "M3_FINAL"}_GALLERY.html`,
);
writeFileSync(out, html, "utf-8");
console.log(`wrote ${out} (${rows.length} rows)`);
