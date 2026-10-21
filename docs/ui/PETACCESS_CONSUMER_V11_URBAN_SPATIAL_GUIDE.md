# PetAccess Consumer v11 — Urban Spatial Guide

Status: implementation direction on `feat/ui-direct-craft-v8`  
Scope: Consumer presentation only. Domain facts, API contracts, governance and runtime boundaries stay unchanged.

## 1. Product visual definition

PetAccess is a **city-space rule and reality guide**.

It should feel like opening a calm spatial guide before entering a place:

```text
Where am I going?
→ What is the applicable rule?
→ What is happening there recently?
→ What part of the place does it apply to?
→ What supports that statement?
```

It must not visually collapse into:

- a pet community;
- a business-rating directory;
- a SaaS dashboard;
- a rule database;
- a card wall;
- a traffic-light "friendly / unfriendly" score.

Canonical semantics remain:

```text
Rule != Reality
Observation != Rule
StaffResponse != OperatorPolicy
Facility != EntryPolicy
Unknown != Allowed
Unknown != Forbidden
```

## 2. Reference principles

### Map-first spatial context

The mobile map remains visually dominant. Search, query context, lens controls and selected-place context float over or rise from the map instead of consuming permanent vertical bands.

Use a muted basemap when PetAccess overlays are information-rich. Selected locations must remain visually distinct.

### Place as destination, not dossier software

A Place page starts with place identity. If a governed real scene photo exists, it may lead the destination header.

If no governed scene photo exists:

- do not fabricate a photo;
- do not reuse a generic city illustration as if it represents the place;
- use a compact honest place identity surface until a location-specific map crop or governed media is available.

### Different facts use different visual grammar

Rule:
- decision-led;
- large natural-language conclusion;
- condition and scope directly attached.

Reality:
- time-led;
- chronological event log;
- event time, location and fact remain primary.

Evidence:
- source-led;
- provenance record;
- source, observed/submitted/reviewed time and verification state remain explicit.

These dimensions should not become three visually identical cards.

### Contribution as focused field capture

Contribution remains a short multi-step question flow. One screen asks one factual question. User submissions remain pending review and never directly promote themselves to Rule truth.

## 3. v11 page composition

### Home

Priority:

```text
city / current query
→ restrained discovery hero + search
→ nearby places
→ secondary spatial questions
→ recent history / methodology / contribution
```

The spatial-question entry set is secondary navigation, not a feature catalogue.

### Search

Search is a place list, not a collection of floating cards.

Rows are divider-led:

```text
scene/glyph | place identity
            | type / distance
            | primary decision
            | one condition
            | recent reality
```

Selection uses a subtle background/left indicator rather than a second card style.

### Map

Mobile:

```text
full spatial canvas
+ floating current-query context
+ floating compact lens selector
+ floating map/list control
+ in-map search
+ selected-place bottom sheet
```

No explanatory paragraph may permanently consume map height.

Desktop:

```text
result pane | dominant map canvas
                 + one selected-place preview
```

### Place

```text
place identity
→ section navigation
→ Rule decision
→ Reality summary/timeline
→ Space
→ Evidence
```

Ordinary sections are editorial/divider-led. Large rounded containers are reserved for true floating surfaces or governed scene media.

When a governed scene photo exists, it can create a destination-led header, but the photo header must not repeat the Rule verdict as a decorative badge. The Rule decision begins immediately below as its own semantic layer.

When no governed scene photo exists, the identity stays text-led. A generic category scene must not be inserted merely to fill the visual gap.

### Selected place on Map

The selected-place sheet/card is the bridge between spatial browsing and a Place page, so it must preserve semantic separation even in a compact surface:

```text
place identity
→ active map lens fact
→ Rule as a separately labelled secondary fact when the active lens is not Rule
→ recent Reality
→ open place
```

A Rule condition must never appear directly beneath a Reality/Facility/Divergence headline without an explicit Rule label. Repeating the same verdict as both a status badge and a large text headline is forbidden.

The active lens fact must not be repeated again as its own secondary block. In particular, when Reality is the active lens, the selected-place bridge shows Reality once, then Rule as the cross-dimension fact; it does not render a second identical “最近现场 / 现场概览” row.

### Reality

The timeline is the page. The header provides title, scope and filters but must not read as a dashboard card.

## 4. Visual system

- warm neutral canvas;
- white reading surfaces only where a surface is actually needed;
- one deep forest brand/action accent;
- semantic conditional/restricted/reality colours remain supporting signals;
- restrained elevation;
- 10–16px radii for real surfaces;
- no repeated 20–24px "AI card" treatment;
- body information density should come from hierarchy, not borders.

## 5. Authenticity

Never improve appearance by manufacturing evidence.

- governed scene photo: allowed;
- real map/provider view: allowed;
- deterministic category illustration: allowed only when explicitly labelled as illustration, never as venue evidence;
- generated/fabricated venue photo: forbidden;
- unreviewed/private/failed media: fail closed.

## 6. Human visual gate

Automation can prove route/state/overflow/contracts. It cannot approve visual quality.

For v11, review at minimum:

- Home desktop + mobile;
- Search desktop + mobile;
- Map desktop + mobile + selected sheet;
- Place with governed photo;
- Place without governed photo;
- Reality desktop + mobile;
- Contribution chooser mobile.

`UI_HUMAN_VISUAL_ACCEPTANCE` remains pending until these rendered states are reviewed by a human.
