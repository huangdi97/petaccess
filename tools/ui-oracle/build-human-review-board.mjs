/**
 * Static, source-linked Human Visual Acceptance board for direct-v8.
 *
 * Machine geometry cannot approve a visual design. This report puts the
 * approved composite beside each screenshot from the current checked-out
 * commit. It deliberately reports PENDING, never PASS.
 *
 * No image manipulation and no third-party assets or dependencies.
 */
import { execFileSync } from "node:child_process";
import {
  copyFileSync,
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  writeFileSync,
} from "node:fs";
import path from "node:path";

const out = path.resolve("artifacts/ui-direct-v8/HUMAN_REVIEW");
const reference = path.resolve("docs/ui/reference/PetAccess_UI_APPROVED_REFERENCE_2026-09-27.png");
mkdirSync(out, { recursive: true });

const escapeHtml = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character],
  );

const head = (() => {
  try {
    return execFileSync("git", ["rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  } catch {
    return "unverified";
  }
})();

const hasReference = existsSync(reference);
if (hasReference) copyFileSync(reference, path.join(out, "approved-reference.png"));

const screens = ["desktop", "tablet", "mobile"].flatMap((scope) => {
  const folder = path.join(out, scope);
  const manifestFile = path.join(folder, "manifest.json");
  if (!existsSync(manifestFile)) return [];
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(manifestFile, "utf8"));
  } catch {
    return []; // Fail closed: untraceable screenshots are never represented as current.
  }
  // The screenshot generator supplies a HEAD-bound manifest. A leftover local
  // file from a previous build must not be relabelled as this commit's evidence.
  if (manifest.sourceHead !== head) return [];
  const captured = new Set((manifest.shots ?? []).map((shot) => `${shot.name}.png`));
  return readdirSync(folder)
    .filter((name) => name.endsWith(".png") && captured.has(name))
    .sort()
    .map((name) => ({ scope, name, url: `${scope}/${encodeURIComponent(name)}` }));
});

const cards = screens
  .map(
    ({ scope, name, url }) => `
  <article class="comparison">
    <header><strong>${escapeHtml(scope)} · ${escapeHtml(name)}</strong><span>人工判断：待确认</span></header>
    <div class="pair">
      <figure>
        <a href="approved-reference.png"><img loading="lazy" src="approved-reference.png" alt="批准参考设计完整拼图" /></a>
        <figcaption>批准参考（完整拼图，非逐像素基准）</figcaption>
      </figure>
      <figure>
        <a href="${url}"><img loading="lazy" src="${url}" alt="${escapeHtml(name)} 的最新运行截图" /></a>
        <figcaption>${escapeHtml(scope)} · 本次实际运行截图</figcaption>
      </figure>
    </div>
  </article>`,
  )
  .join("\n");

const html = `<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>PetAccess · 人工视觉对照板</title>
<style>
:root {color-scheme:light;font-family:system-ui,"Microsoft YaHei",sans-serif;background:#f4f7f8;color:#172d40}
*{box-sizing:border-box} body{margin:0;padding:24px;max-width:1800px;margin-inline:auto}
h1{margin:0;font-size:26px} p{line-height:1.6} .meta{margin:14px 0 28px;color:#486174}
code{overflow-wrap:anywhere} .comparison{background:white;border:1px solid #dae4e9;border-radius:9px;margin:18px 0;padding:16px}
.comparison header{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;padding-bottom:12px;border-bottom:1px solid #e0e9ec}
.comparison header span{color:#7a5361} .pair{display:grid;grid-template-columns:1fr 1fr;gap:16px;align-items:start}
figure{margin:12px 0 0;min-width:0} img{width:100%;height:auto;object-fit:contain;background:#f8fafb;border:1px solid #e1e9ed}
figcaption{color:#60798d;font-size:13px;margin:7px 0} a{color:inherit}
@media(max-width:850px){body{padding:12px}.pair{grid-template-columns:1fr}}
</style></head><body>
<h1>PetAccess · Human Visual Acceptance 对照板</h1>
<p class="meta">运行 HEAD：<code>${escapeHtml(head)}</code> · 截图 ${screens.length} 张 · HUMAN_VISUAL_ACCEPTANCE = PENDING</p>
<p>左侧是已批准的完整参考拼图，右侧是本次 CI 实际运行画面。请逐页比较首屏任务、Rule/Reality/Evidence 层级、空间感、导航、移动端与异常态。此页不计算或声称人工 PASS；图片缺失也不能补造。</p>
${!hasReference ? "<p>批准参考图片缺失，无法完成对照。</p>" : ""}
${screens.length ? cards : "<p>本次未生成截图；截图捕获失败不能视为视觉验收完成。</p>"}
</body></html>`;

writeFileSync(path.join(out, "review-board.html"), html, "utf8");
console.log(`review-board: ${screens.length} screenshots, reference=${hasReference}, head=${head}`);
