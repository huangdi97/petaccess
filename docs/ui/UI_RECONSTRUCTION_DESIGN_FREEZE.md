# UI Reconstruction — Design Freeze

> Derived from v0.10-R1 Canonical Master and Approved Visual Reference.
> **Canonical wins on conflict.** Supersedes the M3 freeze only in scope: this
> round adds the Spatial Dossier page archetypes and Query Context primitive.

## 1. Product position (unchanged, frozen)

PetAccess = **mature urban information tool** for checking animal-access rules,
on-site facts and evidence provenance of a city space. NOT a pet-friendly app,
community, lifestyle app, rating app, SaaS dashboard, admin console or
government portal. No pet-friendliness scores, no recommendation/avoidance
lists, no employee-attitude scores, no "green = good / red = bad" semantics.

Design attributes: **Clear · Calm · Spatial · Evidence-led · Dense but Quiet**
(清楚 / 克制 / 空间化 / 证据导向 / 信息密而视觉静).

## 2. Permanent semantic invariants

```text
Access ≠ Friendly; Observation ≠ Rule; Reality ≠ Rule;
StaffResponse ≠ OperatorPolicy; Facility ≠ EntryPolicy; Report ≠ Claim;
AI ≠ final rule judge; UNKNOWN ≠ ALLOWED/PROHIBITED;
No Observation ≠ No Animal Presence; External Content ≠ Official Policy;
Place Mention ≠ Exact Place Match; Publication Time ≠ Event Time.
```

## 3. Page archetypes (frozen)

| Page | Archetype | Core body | Card target |
|---|---|---|---|
| Home | Task Launcher | search + recent/nearby + secondary lens | 0–1 |
| Search | List–Detail Workspace | result pane + detail inspector | 0 |
| Map | Spatial Workspace | map canvas; UI = pane/overlay | only floating preview 1 |
| Place | Dossier + Decision Inspector | dossier + sticky inspector | 0–1 |
| Reality | Temporal Event Log | timeline | 0 |
| Evidence | Evidence Record + Provenance | evidence + provenance | 0–1 media surface |
| Contribution | Transaction Flow | question flow | 0 |

No seven-page template reuse: no big sidebar + grey bg + white cards + pills.

## 4. Global navigation

- Desktop: 64–72px rail. Top: Home / Search / Map / Contribution. Bottom:
  Mine / Settings. About moves into Settings. No ≥200px persistent sidebar.
- Mobile: 首页 / 地图 / 贡献 / 我的 (4 tabs). Search is entered from Home/Map,
  never a fifth tab.

## 5. Surface model

Only three surfaces: **Canvas**, **Primary Surface**, **Floating/Overlay**.
Lists, sections, inspector, timeline are NOT cards. No card-in-card /
panel-in-panel / section-in-card-in-page.

- radius: input/button 6–8px · floating map preview 10–12px · bottom sheet top
  16px · list row 0 · section 0 · inspector 0 · page 0.
- shadow: none by default; light shadow only on map preview / dialog / popover /
  bottom sheet.

## 6. Typography hierarchy (primary signal)

```text
Place/Page identity     28–32 desktop / 22–24 mobile
Primary Decision        22–26 / 20–22
Section                 17–19
Body                    15–16
Metadata / Evidence     13–14
```

Actual values land in design tokens; pages must not invent sizes.

## 7. Color / status

90% neutral, 10% accent/semantic. Status = shape + word primary, colour
secondary:

```text
● 允许进入   ◐ 有条件进入   ▬ 当前限制   ○ 信息不足   ◇ 信息冲突
```

No traffic-light feel; no colour-only status; no green/red friendliness map
markers. Consumer copy is factual and neutral.

## 8. Query Context primitive (new)

One unified consumer primitive shown on Home / Search / Map / Place:
`当前查询：普通犬 / 进入 / 公共区域`. Desktop: toolbar/inspector line.
Mobile: light sticky strip. Editing: desktop popover/panel, mobile bottom
sheet. Fields come from the API contract (animal, service_role, declared_role,
action, zone). Changing it must change cache keys, refetch snapshot/summary,
and never let an old request overwrite the new context.

## 9. Page-specific freeze

### Home — Task Launcher
Location → 当前查询 → primary search → recent/nearby → secondary lens.
No hero photo, no perspective pill trio, no colourful feature cards, no
category chip wall, no feature catalogue.

### Search — List–Detail Workspace
Desktop: rail + 360–420px result pane + remaining detail inspector. Result
rows are divider-based: identity/distance → conclusion/conditions → recent
reality + sources. Selected row = subtle tint. Filter opens as a light panel
(`筛选 N`), never a pill wall. Mobile: results → tap → place, no squeezed
two-pane.

### Map — Spatial Workspace
Map is the canvas; UI is pane/overlay. Desktop: rail + result pane + full map.
Selected place shows the one floating preview. Markers = shape + semantic
state (●◐▬○◇). Mobile: full map + bottom sheet (collapsed/medium/full).

### Place — Dossier + Decision Inspector
Desktop: rail + main dossier (Identity / Overview / Space-Zones / Rules /
Reality / Staff-Facilities / Evidence) + sticky inspector (only 3–5 key
facts: current context / primary status / conditions / major exception /
source-verified-freshness). Zones render as divider rows, not cards. No big
photo hero. Mobile: single column.

### Reality — Temporal Event Log
TIME → EVENT → LOCATION → EVIDENCE. Events are rows on a timeline, not cards.
Filters are a lightweight select/popover.

### Evidence — Evidence Record + Provenance
Images only when they carry evidence value (rule signage / notice / entrance /
animal on site / facility / raw upload). Provenance chain
(photo exists → place matched → observed time → source confirmed → human
reviewed) with Observed / Submitted / Reviewed times separated. Permanent
line: 现场事实不代表正式准入规则.

### Contribution — Transaction Flow
First question: 你刚刚知道了什么？ Consumer-language options
(我看到了新的规则 / 我在现场看到动物 / 工作人员进行了处理 / 我发现了相关设施 /
场所信息有误). Dynamic flow per choice. Result: 已提交待核验 — never
"规则已更新". No internal domain nouns.

## 10. Forbidden (generic-AI-UI bans)

White card wall · pill wall · nested cards · 16–24px radius everywhere ·
gradient · glassmorphism · heavy shadow · decorative hero · lifestyle city
photography as primary visual · huge marketing headline · oversized icon tiles
· paw/bone/heart motifs · pet-friendliness score · desktop-centred mobile
column · colour-only status · domain enum leakage.
