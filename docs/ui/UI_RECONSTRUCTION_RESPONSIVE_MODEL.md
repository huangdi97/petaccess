# UI Reconstruction — Responsive Model

> Design Freeze §9 / §29. Desktop and Mobile are real transformations, never a
> scaled H5. Tablet (800px) is verified independently — it is not assumed to
> inherit either column layout automatically.

## Breakpoints (design tokens)

`sm 0–479` mobile portrait · `md 480–767` mobile landscape/small tablet ·
`lg 768–1023` tablet (rail starts) · `xl 1024+` desktop.

## Per-page transformation

| Page | Desktop (≥768, rail) | Mobile (<768, tabbar) |
|---|---|---|
| Home | wide container, QueryContextBar line, divider rows | single column, QueryContextBar strip |
| Search | 400px result pane + DecisionInspector (sticky) | results list only → tap → Place (no two-pane squeeze) |
| Map | result pane + full map canvas; floating PlacePreview on selection | full map + bottom sheet (collapsed/medium/full) |
| Place | dossier (flex 1) + 320px sticky inspector | single column dossier |
| Reality | wide timeline (2-col fact/review + event rows) | single timeline |
| Evidence | media/record + provenance side-by-side where data allows | media → facts → provenance |
| Contribution | focused centered flow | full-screen linear flow |

## Rules

1. `scrollWidth <= clientWidth` on all key viewports (360/430/800/1280/1440),
   except surfaces explicitly designed to scroll horizontally (none in the
   consumer app today).
2. Desktop panes use `--pa-layout-result-pane` (400px) and
   `--pa-layout-inspector` (320px); content never centers a mobile column on
   desktop.
3. Mobile never renders two squeezed columns; the detail surface either
   replaces the list (Search) or overlays it (Map bottom sheet).
4. Tablet (800px) is captured in the visual matrix with `isMobile: false,
   hasTouch: true` and must not overflow or squeeze.
5. Sticky elements: rail (fixed left), DecisionInspector (top sticky on
   desktop), QueryContextBar (top of page content, not fixed).
6. Safe areas: shell consumes `env(safe-area-inset-*)`; pages never re-add
   tabbar/rail padding.
