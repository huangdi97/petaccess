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

On mobile/tablet, the first contribution step keeps the **target place visible as lightweight context** before the question. This prevents fast field capture from being attached to the wrong venue. The context is divider-led text, not another card; later structured steps may carry their own place/zone context and must not duplicate a permanent dashboard rail.

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

The Home hero is **orientation, not marketing**. On desktop, coverage and map shortcuts remain utility text rather than promotional pills; the decorative city scene must stay compact enough that nearby spatial facts enter immediately after the primary search task.

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

On mobile, persistent map chrome should resolve to **at most two overlay rows** above the spatial canvas:

1. in-map search / locate;
2. compact query context + current Lens selector + map/list control.

Rule / Reality / Facility / Divergence remain four first-class lenses, but mobile does not need four permanently expanded buttons. Desktop may keep the segmented four-lens row because horizontal space is not the scarce resource there.

The second mobile overlay row is one **adaptive layout group**, not three unrelated absolutely positioned widgets. Query context grows and truncates first; Lens and map/list controls keep their touch targets. The group must preserve a visible gap at 320 / 360 / 390 / 430px and survive label/font changes without offset tuning.

When a real map provider is unavailable, the fallback map must still read as an urban spatial canvas rather than a test grid: it may use illustrative road hierarchy, blocks, open-space patches, water and building mass hints. It must remain explicitly disclosed as a non-surveyed illustrative basemap and must never invent venue names, operator facts or rule data.

Fallback truth should be disclosed **once**. Do not stack a provider caption and a second app-level disclosure for the same fact. Do not show metric scale, zoom-level prose or other pseudo-precision on an illustrative basemap; real zoom interaction may remain.

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

The Overview has one recognizable PetAccess signature: **Rule and Reality are visibly named as two independent fact dimensions**. Rule may use its status rail; Reality uses its own observed-fact rail. They stay in one reading sequence and never collapse into a score, friendliness verdict, or blended state. On mobile the labels remain visible rather than relying on colour or position alone.

On desktop Overview, the dossier itself is the **single owner** of the full Rule decision and the destination narrative. Do not reserve a second column merely to repeat the same verdict. A sticky decision rail is allowed only on secondary Place views (Rules / Reality / Space / Evidence), where preserving the current decision while reading another dimension adds real context. Automated tests must bind Overview Rule/error assertions to the dossier surface, not to a hidden or duplicate inspector.

When governed scene media exists, it may become a destination surface rather than another inset card. On mobile it may bleed to the page edge so the place reads as a real location. Actions over the hero stay lightweight; do not rebuild a row of large pill buttons.

Governed media is orientation, not the decision itself. The Rule section must begin inside the initial viewport on both desktop and mobile Human Review captures; enlarging the hero until Rule drops below the fold is a visual regression.

When governed media does not exist, stay text-led. Never fill the visual gap with a generic venue illustration.

### Selected place on Map

The selected-place sheet/card is the bridge between spatial browsing and a Place page, not a mini dossier.

The active fact dimension may use one restrained semantic rail as a supporting cue — Rule status, Reality, Facility or Divergence — but the natural-language label and conclusion remain mandatory. Colour never becomes a friendliness score or the only carrier of meaning.

Half state prioritizes:

```text
place identity
→ active map lens fact
→ one cross-dimension fact when useful
→ open place
```

Semantic rules:

- when the active lens is not Rule, Rule may appear once as an explicitly labelled secondary fact;
- when Reality is the active lens, Reality appears once, followed by Rule as the cross-dimension fact — never a duplicate “最近现场 / 现场概览” block;
- a Rule condition must never sit directly under a Reality / Facility / Divergence headline without an explicit Rule label;
- repeating the same verdict as both a badge and a large headline is forbidden;
- evidence details belong to expanded state or the Place page.

Destination identity rules:

- governed scene photo: a small thumbnail may strengthen identity in half state and a larger governed image may appear in expanded state;
- no governed scene photo: use the place-type glyph or text-led identity only;
- never insert a generic category scene merely to fill visual space.

The compact bridge must stay glanceable: selecting a place should reveal a decision surface, not replace the map with a second detail page.

### Reality

The timeline is the page. The header provides title, scope and filters but must not read as a dashboard card.

A standalone Reality route must preserve **place context** before the timeline: show the current place name as a lightweight return/context link, not as a second destination hero. Loading that identity is supporting UI only and must never block published Reality facts if the place-detail lookup is slow or unavailable.

### Evidence

Evidence is a provenance surface, not another place-detail page. The visible page purpose is **证据与来源**; place identity is subordinate context. Provenance stages, observed/submitted/reviewed time and source identity carry the hierarchy. Evidence styling must not imitate Rule decision styling or Reality timeline styling.

On mobile, when no governed public media leads the record, the **provenance chain precedes the dense governance summary** and must enter the initial viewport. This makes “how do we know this?” the first Evidence-specific answer instead of presenting another status table before the source path. The summary remains available immediately below; no evidence fact or governance state is removed.

### Secondary reading surfaces

Mine, Settings, Privacy and About must feel like the same Urban Spatial Guide after the user leaves the map.

- one strong identity anchor is allowed on Mine, but empty states and settings groups do not become repeated cards;
- Settings / Privacy / About use editorial headers, section dividers and row-level hierarchy;
- explanatory content is a reading surface, not a stack of feature cards;
- destructive or permission-sensitive actions may keep explicit controls, but the surrounding explanation stays quiet.

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
- Evidence desktop + mobile;
- Contribution chooser mobile;
- one secondary-surface sweep covering Mine, Settings, Privacy, Notifications and Onboarding.

The secondary sweep is not cosmetic scope creep: it proves that leaving the map/place journey does not resurrect the legacy rounded-card/SaaS visual system.

`UI_HUMAN_VISUAL_ACCEPTANCE` remains pending until these rendered states are reviewed by a human.
