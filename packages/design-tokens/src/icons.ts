/**
 * @petaccess/design-tokens — the fixed icon family (M2 §11).
 *
 * One icon family for the whole product: stroke-based, 24×24 grid, 1.8px
 * stroke, round caps/joins, `currentColor`. Mixing Lucide / Heroicons /
 * Material / emoji is forbidden; if an icon is missing, add it HERE so the
 * whole product gains it consistently, and render it with `PaIcon` (client) —
 * never hand-roll a one-off SVG in a page.
 *
 * Each entry is a list of `d` path strings drawn on the 24×24 grid.
 */

export interface IconGlyph {
  readonly paths: readonly string[];
  /** Screen-reader text; the visual label usually comes from the component. */
  readonly ariaLabel?: string;
}

/** All icon names the product may use. The single allow-list. */
export const ICON_NAMES = [
  "arrow-left",
  "arrow-right",
  "building",
  "camera",
  "check",
  "check-circle",
  "chevron-down",
  "clock",
  "close",
  "document",
  "eye",
  "flag",
  "home",
  "info",
  "list",
  "location",
  "map",
  "offline",
  "plus",
  "question-circle",
  "refresh",
  "search",
  "settings",
  "shield",
  "shield-alert",
  "shield-check",
  "sliders",
  "user",
  "warning",
  "x-circle",
] as const;

export type IconName = (typeof ICON_NAMES)[number];

/**
 * Fixed icon family glyphs. Stroke settings are constant (1.8px, round caps,
 * no fill) and applied by the renderer, so every icon reads identically.
 */
export const ICONS: Readonly<Record<IconName, IconGlyph>> = {
  "arrow-left": { paths: ["M19 12H5", "M11 18l-6-6 6-6"] },
  "arrow-right": { paths: ["M5 12h14", "M13 6l6 6-6 6"] },
  building: {
    paths: [
      "M4 21V6a1 1 0 0 1 1-1h9a1 1 0 0 1 1 1v15",
      "M15 21v-5h5v5",
      "M3 21h18",
      "M7 8h2M7 11h2M7 14h2M11 8h2M11 11h2M11 14h2",
    ],
  },
  camera: {
    paths: [
      "M4 8h3l1.5-2.2A1 1 0 0 1 9.3 5.5h5.4a1 1 0 0 1 .8.3L17 8h3a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z",
      "M12 17a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z",
    ],
  },
  check: { paths: ["M4.5 12.5l5 5L19.5 6.5"] },
  "check-circle": { paths: ["M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18z", "M8.2 12.4l2.5 2.6 5-5.4"] },
  "chevron-down": { paths: ["M6 9.5l6 6 6-6"] },
  clock: { paths: ["M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18z", "M12 7.5V12l3 2"] },
  close: { paths: ["M6 6l12 12", "M18 6L6 18"] },
  document: {
    paths: [
      "M7 3h7l4 4v14H7a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z",
      "M14 3v4h4",
      "M10 12h5",
      "M10 15.5h5",
      "M10 8.5h2",
    ],
  },
  eye: {
    paths: [
      "M2.5 12S6 5.8 12 5.8 21.5 12 21.5 12 18 18.2 12 18.2 2.5 12 2.5 12z",
      "M12 14.2a2.2 2.2 0 1 0 0-4.4 2.2 2.2 0 0 0 0 4.4z",
    ],
  },
  flag: { paths: ["M6 21V4", "M6 5h11l-2.2 3.5L17 12H6"] },
  home: { paths: ["M4 11.5L12 4l8 7.5", "M5.5 10.5V20h13v-9.5", "M9.5 20v-6h5v6"] },
  info: { paths: ["M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18z", "M12 11v5.5", "M12 7.5h.01"] },
  list: { paths: ["M8.5 6h10M8.5 12h10M8.5 18h10", "M4.5 6h.01M4.5 12h.01M4.5 18h.01"] },
  location: {
    paths: ["M12 21s7-6.1 7-11a7 7 0 1 0-14 0c0 4.9 7 11 7 11z", "M12 12.5a2.3 2.3 0 1 0 0-4.6 2.3 2.3 0 0 0 0 4.6z"],
  },
  map: {
    paths: [
      "M4 5.5L9 3.5l6 2 5-2v15l-5 2-6-2-5 2v-15z",
      "M9 3.5v15",
      "M15 5.5v15",
      "M4 8.5l5 1.2M15 10.5l5-1.2",
    ],
  },
  offline: {
    paths: [
      "M5 9.7A11 11 0 0 1 12 7",
      "M18.8 10.6A9 9 0 0 0 15.5 8.4",
      "M7.5 13.2a6 6 0 0 1 3.8-1.7",
      "M3 3l18 18",
      "M5.5 13.5a4 4 0 0 1 1.2-.8",
    ],
  },
  plus: { paths: ["M12 5v14", "M5 12h14"] },
  "question-circle": {
    paths: ["M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18z", "M9.8 9.2a2.3 2.3 0 1 1 3.2 2.1c-.7.4-1.05.9-1.05 1.7", "M12 16.3h.01"],
  },
  refresh: {
    paths: [
      "M20 12a8 8 0 1 1-2.1-5.3",
      "M20 3.5V7h-3.5",
    ],
  },
  search: { paths: ["M10.5 4.5a6 6 0 1 0 0 12 6 6 0 0 0 0-12z", "M15 15l5.5 5.5"] },
  settings: {
    paths: [
      "M12 3v3M12 18v3M3 12h3M18 12h3",
      "M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z",
    ],
  },
  shield: { paths: ["M12 3l7 2.5V11c0 4.6-3.1 7.6-7 9-3.9-1.4-7-4.4-7-9V5.5L12 3z"] },
  "shield-alert": {
    paths: ["M12 3l7 2.5V11c0 4.6-3.1 7.6-7 9-3.9-1.4-7-4.4-7-9V5.5L12 3z", "M12 8.5V13", "M12 16h.01"],
  },
  "shield-check": {
    paths: [
      "M12 3l7 2.5V11c0 4.6-3.1 7.6-7 9-3.9-1.4-7-4.4-7-9V5.5L12 3z",
      "M9.2 11.8l2 2 3.6-3.8",
    ],
  },
  sliders: {
    paths: [
      "M4 7h15M4 12h8M15 12h5M4 17h11M18 17h2",
      "M21 5.5a1.8 1.8 0 1 0-2.4 1.7M8 10.5a1.8 1.8 0 1 0 3.4-.6M11 15.5a1.8 1.8 0 1 1 3.4.6",
    ],
  },
  user: { paths: ["M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z", "M4.5 20c1.4-3.6 4.2-5 7.5-5s6.1 1.4 7.5 5"] },
  warning: {
    paths: ["M12 4.5L3.5 19h17L12 4.5z", "M12 9.5v4", "M12 16.3h.01"],
  },
  "x-circle": {
    paths: ["M12 3a9 9 0 1 0 0 18 9 9 0 1 0 0-18z", "M9.2 9.2l5.6 5.6M14.8 9.2l-5.6 5.6"],
  },
};

/**
 * Fixed semantic icon mapping (M2 §11): the six user-facing fact dimensions.
 * Signage/rule facts render as `document`, on-site facts as `eye`, evidence as
 * `shield`, facilities as `building`, contribution as `plus`, navigation as
 * `location`. Pages must not pick a different glyph for the same concept.
 */
export const SEMANTIC_ICONS = {
  RULE: "document",
  REALITY: "eye",
  EVIDENCE: "shield",
  FACILITY: "building",
  CONTRIBUTION: "plus",
  NAVIGATION: "location",
} as const satisfies Readonly<Record<string, IconName>>;

/** Whether a name is part of the fixed family (guards against stray glyphs). */
export function isIconName(name: string): name is IconName {
  return (ICON_NAMES as readonly string[]).includes(name);
}