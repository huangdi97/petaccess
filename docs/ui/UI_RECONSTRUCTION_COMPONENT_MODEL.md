# UI Reconstruction — Component Model

> Design Freeze §9 + Surface Model §5. Every consumer component has one job;
> data flows in as props from the consumer repository (CoexistenceSnapshot
> SSOT). No component fetches or re-derives domain facts.

## Layer map

```text
ConsumerAppShell (frame only: rail/tabbar/safe-area/offline/toast/dialog)
  └─ QueryContextBar          current query line + editor (mode → cache key → refetch)
  └─ page workspaces
      ├─ HomeView        → QueryContextBar + search + PlaceResultRow list
      ├─ SearchView      → QueryContextBar + ResultPane(list) + DecisionInspector
      ├─ MapView         → QueryContextBar + ResultPane + MapCanvas + PlacePreview(floating)
      ├─ PlaceView       → QueryContextBar + Dossier(sections) + DecisionInspector(sticky)
      ├─ RealityTraceView→ QueryContextBar + TemporalEventLog
      ├─ EvidenceView    → QueryContextBar + Provenance + evidence rows + sources
      └─ ContributeView  → (place gate) + QueryContextBar + step machine
```

## Reusable components

| Component | Job | Data (props) | Notes |
|---|---|---|---|
| `QueryContextBar` | show/switch current query | session (store) | editor dialog; changes `session.mode` → repository key changes |
| `PlaceResultRow` | one divider row (identity → rule → reality → evidence) | place, answer, reality, error flags, lens | shared by Home / Search rows |
| `DecisionInspector` | flat inspector (context/conclusion/scope/conditions/divergence/reality/freshness) | place, answer, reality, snapshot, stale, fetchedAt | Search detail pane + Place sticky inspector |
| `PlacePreview` | floating preview surface (map) | place, status, snapshot | elevation + 10–12px radius (freeze §5) |
| `StatusBadge` | shape+word+color status | semantic/status/effect | never color-only |
| `EvidenceStatus` / `EvidenceMeta` / `FreshnessStatus` | evidence/freshness metadata | state + counts | shared vocabulary |
| `PaDialog` / `BottomSheet` | editing + mobile sheets | open/title | overlay surfaces |

## Workspace layout primitives (styles.css)

- `.surface-row` — divider-led row used by lists / dossier / timeline / provenance.
- `.workspace-pane` — quiet left column with a divider border (result panes).
- `.search-workspace__body--split` / `.place-workspace__body--split` — desktop row
  layout with `--pa-layout-result-pane` (400px) / `--pa-layout-inspector` (320px).
- `.panel` — flattened primary surface (radius 0); never used as a card wall.

## Component size rule

A Vue SFC stays ≤ 200 lines where feasible; pages that exceed it split at real
semantic boundaries (result pane, inspector, dossier section groups), never
into dozens of meaningless fragments. All new surfaces read design tokens.
