/**
 * Generate artifacts/ui-reconstruction/UI_RECONSTRUCTION_BEFORE_AFTER_GALLERY.html.
 *
 * Pairs the committed baseline (BEFORE) with a later stage (AFTER, default
 * `phase1`; pass --after <stage> to point at a different one). Each cell shows
 * route / viewport / state / commit / before / after / what changed / why.
 *
 * Usage:
 *   node scripts/ui_reconstruction_gallery.mjs [--after phase1]
 */
import { existsSync, readdirSync, writeFileSync } from "node:fs";
import path from "node:path";

const afterArg = process.argv.indexOf("--after");
const AFTER = afterArg !== -1 ? process.argv[afterArg + 1] : "phase1";
const BEFORE = "baseline";

function pngs(stage, vp) {
  const dir = path.resolve("artifacts/ui-reconstruction", stage, vp);
  if (!existsSync(dir)) return [];
  return readdirSync(dir).filter((f) => f.endsWith(".png")).sort();
}

const viewports = ["ui-360", "ui-430", "ui-800", "ui-1280", "ui-1440"];
const vpLabel = {
  "ui-360": "360×740",
  "ui-430": "430×740",
  "ui-800": "800×900",
  "ui-1280": "1280×800",
  "ui-1440": "1440×900",
};

const stateLabel = (name) => {
  const m = /^(home|search|map|place|reality|contribute|mine)-(ready|loading|empty|error|offline|unknown)$/.exec(
    name,
  );
  if (!m) return name;
  return `${m[1]} · ${m[2]}`;
};

const changes = {
  "search-ready": {
    what: "List–Detail Workspace：400px result pane + DecisionInspector；divider rows、subtle selected tint、light filter panel（非 pill wall）；QueryContextBar 顶部。",
    why: "Approved Reference / Design Freeze §9：Search 是 List–Detail Workspace，不是灰底白卡结果墙。",
    rule: "Search = List–Detail Workspace（§9）；Surface Model 无 card（§5）",
  },
  "search-empty": {
    what: "空态保留（标题/贡献 CTA/清除筛选），样式随 workspace 对齐。",
    why: "No results ≠ dead end；空态给出去路。",
    rule: "Empty 给出去路（§66）",
  },
  "search-error": {
    what: "统一 ERROR 态 + Retry 保留，样式对齐新 workspace。",
    why: "与冻结一致，无泄漏。",
    rule: "Error 不泄漏内部实现",
  },
  "search-loading": {
    what: "骨架保留，布局对齐新 result pane。",
    why: "Loading 对应真实内容结构防 layout shift。",
    rule: "Skeleton 对齐内容结构",
  },
  "search-offline": {
    what: "离线仍显示结果列表与 query context，GlobalOfflineBanner 保留。",
    why: "Offline ≠ unusable。",
    rule: "Offline 显示 banner + 保留内容",
  },
  "place-ready": {
    what: "Dossier + Sticky DecisionInspector：主档案 divider 分区 + 右侧 320px 决策检查器；空间与区域为 divider 行而非 cards。",
    why: "Approved Reference / Design Freeze §9：Place 是 Dossier + Decision Inspector，不做大照片 Hero。",
    rule: "Place = Dossier + Inspector（§9）；无 hero",
  },
  "place-unknown": {
    what: "未知场所统一 EMPTY 态，风格对齐新 dossier。",
    why: "未收录 ≠ 无规则。",
    rule: "未收录 ≠ 没有规则",
  },
  "home-ready": {
    what: "保留当前 Home（Task Launcher 收口在 Phase 2）。",
    why: "Phase 1 只改 Search/Place；Home 视觉在 Phase 2 落地。",
    rule: "Home = Task Launcher（Phase 2）",
  },
};

function cell(name, vp) {
  const before = `../artifacts/ui-reconstruction/${BEFORE}/${vp}/${name}.png`;
  const after = `../artifacts/ui-reconstruction/${AFTER}/${vp}/${name}.png`;
  const bExists = existsSync(path.resolve("artifacts/ui-reconstruction", BEFORE, vp, `${name}.png`));
  const aExists = existsSync(path.resolve("artifacts/ui-reconstruction", AFTER, vp, `${name}.png`));
  const c = changes[name] ?? {
    what: "见页面具体 diff。",
    why: "State / styling alignment.",
    rule: "遵循 Design Freeze",
  };
  return `<tr>
    <td class="meta">
      <strong>${stateLabel(name)}</strong><br/>
      <span>viewport ${vpLabel[vp]}</span>
    </td>
    <td class="cell">
      ${bExists ? `<img loading="lazy" src="${before}" alt="before ${name} ${vp}"/>` : "<div class='na'>no before</div>"}
    </td>
    <td class="cell">
      ${aExists ? `<img loading="lazy" src="${after}" alt="after ${name} ${vp}"/>` : "<div class='na'>no after</div>"}
    </td>
    <td class="why">
      <div class="what">${c.what}</div>
      <div class="why-line">${c.why}</div>
      <div class="rule">${c.rule}</div>
    </td>
  </tr>`;
}

const rows = [];
for (const name of pngs(AFTER, "ui-1440")) {
  for (const vp of viewports) {
    rows.push(cell(name, vp));
  }
}

const commit = process.env.GIT_SHA_SHORT ?? "";
const html = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>PetAccess UI Reconstruction — Before / After Gallery (${BEFORE} → ${AFTER})</title>
<style>
  body { font-family: "PingFang SC","Microsoft YaHei",system-ui,sans-serif; margin: 0; background: #f4f6f8; color: #1d2733; }
  header { padding: 24px 32px; border-bottom: 1px solid #e4e8ec; background: #fff; }
  h1 { margin: 0 0 8px; font-size: 22px; }
  .sub { color: #5c6772; font-size: 13px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { padding: 12px 16px; vertical-align: top; border-bottom: 1px solid #e4e8ec; }
  th { text-align: left; font-size: 13px; color: #5c6772; background: #eef1f4; }
  td.meta { width: 140px; }
  td.cell { width: 42%; }
  td.cell img { width: 100%; height: auto; border: 1px solid #e4e8ec; border-radius: 4px; }
  .na { color: #9aa4ad; font-size: 12px; padding: 40px 0; text-align: center; }
  td.why { width: 16%; min-width: 220px; font-size: 13px; }
  .what { font-weight: 600; margin-bottom: 6px; }
  .why-line { color: #4a5560; margin-bottom: 6px; }
  .rule { color: #34618e; }
</style>
</head>
<body>
<header>
  <h1>PetAccess UI Reconstruction — Before / After Gallery</h1>
  <div class="sub">BEFORE = baseline（commit ${commit} 前）· AFTER = ${AFTER} · ${rows.length} cells · route/viewport/state 逐格对照</div>
</header>
<table>
  <thead><tr><th>Route · viewport · state</th><th>BEFORE (baseline)</th><th>AFTER (${AFTER})</th><th>What changed · Why · Design rule</th></tr></thead>
  <tbody>${rows.join("")}</tbody>
</table>
</body>
</html>`;

writeFileSync(
  path.resolve("artifacts/ui-reconstruction", "UI_RECONSTRUCTION_BEFORE_AFTER_GALLERY.html"),
  html,
  "utf-8",
);
console.log(`wrote UI_RECONSTRUCTION_BEFORE_AFTER_GALLERY.html with ${rows.length} cells (${BEFORE} → ${AFTER})`);
