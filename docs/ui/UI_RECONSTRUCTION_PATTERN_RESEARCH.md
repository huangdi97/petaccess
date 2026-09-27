# UI Reconstruction — Pattern Research

> Targeted UI UX Pro Max queries for open UI questions (contract §14.4). Only
> results that actually changed a decision are kept. The frozen Design Freeze
> and Approved Reference remain the authority; no query result overrides them.

## Query log (2026-09-28, `ui-ux-pro-max` search.py)

| Question | Query | Domain | Result |
|---|---|---|---|
| Search desktop workspace structure | `list detail desktop workspace selected row inspector panel` | ux | 0 matches (no verified database hit; fallback = contract's frozen archetype: rail 64–72px + result pane 360–420px + inspector) |
| List–detail density/rows | `list detail workspace split pane density` | ux | 0 matches (fallback: divider-based rows, no cards — Design Freeze §17) |
| Map mobile bottom sheet | `map bottom sheet mobile place preview` | ux | 4 generic hits (mobile-first, keyboard, pull-to-refresh, viewport meta) — none changed decisions; Map sheet states are frozen (collapsed/medium/full) |
| Temporal event log readability | `timeline event log temporal metadata readability` | ux | 3 generic hits (number formatting, line height 1.5–1.75, contrast) — line-height token already 1.5; no change |
| Selected row states | `selected row states list` | ux | 4 generic hits (hover cursor, loading feedback, active press state) — reinforces: hover cursor + subtle tint selected state (already the plan) |
| Dense factual progressive disclosure | `progressive disclosure dense factual data` | ux | 3 generic hits — no change; dossier sections stay on one page with divider hierarchy (freeze) |

## Adopted (verified patterns)

1. **Hover feedback on interactive rows** (Interaction/Hover): pointer cursor + subtle background change. Adopted for Search result rows / Place zone rows.
2. **Loading feedback via skeletons** (Animation/Loading): skeleton screens during async loads — already the app's pattern (`SkeletonList`), kept.
3. **Line-height 1.5–1.75 for body** (Typography): `--pa-line-height-base: 1.5` already satisfies this.
4. **Active/pressed state on interactive elements** (Interaction/Active): keep pressed feedback on buttons/rows.

## Explicitly NOT adopted

- "Bulk actions / checkbox columns" (Bulk Actions): PetAccess is a read/dossier tool; bulk edit would add decision weight the domain forbids.
- Auto-play media (Sustainability): evidence images are click-to-view only.
- Any query's suggestion to card-ify or pill-ify results: conflicts with the frozen Surface Model (§17).

## Implementation consequence

No new visual system was introduced from research; it confirmed the frozen archetypes. Remaining page-level craft follows the Design Freeze + Approved Reference.
