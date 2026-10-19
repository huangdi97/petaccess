/**
 * Static, source-linked Human Visual Acceptance board for direct-v8.
 *
 * Machine geometry cannot approve a visual design. v11 has reopened the
 * Consumer visual direction, so the previous composite is retained only as a
 * historical IA/semantic reference beside current screenshots. It deliberately
 * reports PENDING, never PASS.
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
        <a href="approved-reference.png"><img loading="lazy" src="approved-reference.png" alt="历史参考设计完整拼图" /></a>
        <figcaption>历史参考 · 仅继承 IA/语义，不是 v11 视觉目标</figcaption>
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
<p>右侧是本次 CI 实际运行画面。左侧旧拼图只保留作历史 IA / Rule-Reality-Evidence 语义参考；Consumer v11 已按 <code>docs/ui/PETACCESS_CONSUMER_V11_URBAN_SPATIAL_GUIDE.md</code> 重新打开视觉方向，不能再拿旧拼图冒充批准外观。请重点检查地图是否成为主表面、地点是否像真实目的地、Rule / Reality / Evidence 是否使用不同视觉语法，以及移动端是否仍有 card-wall / dashboard 感。此页不计算或声称人工 PASS。</p>
${!hasReference ? "<p>历史参考图片缺失；这不阻塞 v11 当前画面的人审。</p>" : ""}
${screens.length ? cards : "<p>本次未生成截图；截图捕获失败不能视为视觉验收完成。</p>"}
</body></html>`;

writeFileSync(path.join(out, "review-board.html"), html, "utf8");
console.log(`review-board: ${screens.length} screenshots, reference=${hasReference}, head=${head}`);
