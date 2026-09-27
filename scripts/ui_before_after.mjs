/**
 * 生成 artifacts/ui-audit/UI_M3_BEFORE_AFTER_GALLERY.html。
 * 展示 current（BEFORE）与 m3-final（AFTER）对照 + WHAT CHANGED + WHY + DESIGN RULE。
 */
import { existsSync, readdirSync, writeFileSync } from "node:fs";
import path from "node:path";

function pngs(stage, vp) {
  const dir = path.resolve("artifacts/ui-audit", stage, vp);
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

const changes = {
  "home-ready": {
    what: "移除旧 AppShell 双层 chrome（ModeBar/档案 panel）；结果行加入 Reality 摘要与 Evidence 元数据；行级统一 PlaceResultRow 呈现 identity→Rule→Reality→Freshness/Evidence。",
    why: "Critique：Rail+ModeBar+panel 三层 chrome 重复；Reality 层缺位；Rule 结论弱化为小徽标。",
    rule: "行级信息：Place identity → Rule 主结论 → Reality 摘要 → Freshness/Evidence；DESIGN §5/§7",
  },
  "home-empty": {
    what: "空态保持产品文案，视觉随 AppShell 移除后更干净。",
    why: "Home empty 已是正式产品空态（BEFORE 已合格）；本轮仅随共享层自然变化。",
    rule: "Empty 是产品一级状态（§72）",
  },
  "home-loading": {
    what: "骨架保持；移除双重 chrome 后 skeleton 对应真实内容结构。",
    why: "Loading 应对应真实内容结构防 layout shift（§73）。",
    rule: "Skeleton 对齐内容结构（§73）",
  },
  "home-error": {
    what: "统一 ERROR 态保留；标题/Retry 保持。",
    why: "Error UI 回答发生了什么+Retry（§74）。",
    rule: "Error 回答 5 问（§74）",
  },
  "home-offline": {
    what: "GlobalOfflineBanner 保留；内容保留。",
    why: "Offline ≠ unusable（§75）。",
    rule: "Offline 显示 banner + 保留内容（§75）",
  },
  "search-ready": {
    what: "移动端结果行加入 Reality 摘要 + Evidence/Freshness 元数据；标签减负（conflict 显式、其余并入 meta）；移除旧 AppShell 包裹。",
    why: "Critique：移动端看不到现场层；每行最多 5 个 tag 过载；桌面 split 保留。",
    rule: "Search 首层 = identity/Rule/Reality/Freshness/Evidence（§78）；Badge 只用于重要语义（§69）",
  },
  "search-empty": {
    what: "空态保留（标题/贡献 CTA/清筛选）。",
    why: "No results ≠ dead end（UI UX Pro Max research）。",
    rule: "Empty 给出出路（§72/§2）",
  },
  "search-error": {
    what: "统一 ERROR 态 + Retry 保留。",
    why: "与基线一致，无泄漏。",
    rule: "Error 不泄漏内部实现（§74）",
  },
  "search-offline": {
    what: "离线按钮阻止 + banner 保留。",
    why: "Offline 下搜索不可提交，诚实提示。",
    rule: "Offline ≠ unusable；读操作可导航（§75）",
  },
  "map-ready": { what: "仅共享层自然影响（AppShell/Token）。", why: "Map 属 M4 范围。", rule: "不吞并 M4（契约 §57）" },
  "place-ready": { what: "仅共享层自然影响。", why: "Place Passport 属 M4。", rule: "不吞并 M4" },
  "contribute-ready": { what: "仅共享层自然影响（AppShell 保留旧框架）。", why: "Contribution 属 M7。", rule: "不吞并 M7" },
  "mine-ready": { what: "无变化（FINAL 页面）。", why: "Mine 已收口（M2/M7）。", rule: "不扩大范围" },
};

const fallback = { what: "视觉随共享层自然变化。", why: "见 DESIGN.md。", rule: "DESIGN.md" };
const rows = [];
for (const vp of viewports) {
  for (const f of pngs("current", vp)) {
    const before = `current/${vp}/${f}`;
    const afterExists = existsSync(path.resolve("artifacts/ui-audit/m3-final", vp, f));
    const after = afterExists ? `m3-final/${vp}/${f}` : before;
    const base = f.replace(/\.png$/, "");
    const c = changes[base] ?? fallback;
    rows.push(
      `<tr>
  <td>${base.split("-")[0]}</td><td>${base.split("-").slice(1).join(" ")}</td><td>${vpLabel[vp]}</td>
  <td class="shot"><img src="${before}" alt="BEFORE ${f}"></td>
  <td class="shot"><img src="${after}" alt="AFTER ${f}"></td>
  <td>${c.what}</td><td>${c.why}</td><td>${c.rule}</td>
</tr>`,
    );
  }
}

const html = `<!doctype html>
<html lang="zh"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>PetAccess M3 Before / After Gallery</title>
<style>
  body { font-family: "Segoe UI", system-ui, sans-serif; background: #f4f6f8; color: #1d2733; margin: 0; padding: 24px; }
  h1 { font-size: 20px; } .meta { color: #5c6772; font-size: 13px; margin: 4px 0 16px; }
  table { border-collapse: collapse; width: 100%; background: #fff; font-size: 13px; }
  th, td { border: 1px solid #e4e8ec; padding: 8px 10px; vertical-align: top; text-align: left; }
  th { background: #eef1f4; position: sticky; top: 0; }
  img { max-width: 260px; width: 100%; border: 1px solid #e4e8ec; display: block; }
  td.shot { width: 260px; }
</style></head><body>
<h1>PetAccess M3 Consumer Core — Before / After</h1>
<p class="meta">BEFORE = current（commit 049fc39）· AFTER = m3-final（当前 HEAD）· 同 Route/Fixture/Viewport/Runtime（visual_db_reset seed + API :8011 + preview :5175）· 截图 ${rows.length} 组</p>
<table><thead><tr><th>页面</th><th>状态</th><th>Viewport</th><th>BEFORE</th><th>AFTER</th><th>WHAT CHANGED</th><th>WHY</th><th>DESIGN RULE</th></tr></thead>
<tbody>${rows.join("\n")}</tbody></table>
</body></html>`;

const out = path.resolve("artifacts/ui-audit/UI_M3_BEFORE_AFTER_GALLERY.html");
writeFileSync(out, html, "utf-8");
console.log(`wrote ${out} (${rows.length} rows)`);