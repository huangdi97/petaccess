import { STATUS_GLYPHS, type MapMarker } from "@petaccess/client-core";

function tokenColor(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || "currentColor";
}

export function tencentMarkerColor(lens: string, status: MapMarker["status"]): string {
  if (lens === "reality") {
    if (status === "ALLOWED") return tokenColor("--pa-color-reality-observed");
    if (status === "CONFLICT") return tokenColor("--pa-color-reality-disputed");
    return tokenColor("--pa-color-reality-insufficient");
  }
  if (lens === "facility") {
    return status === "ALLOWED"
      ? tokenColor("--pa-color-facility-confirmed")
      : tokenColor("--pa-color-facility-unverified");
  }
  if (lens === "divergence") {
    if (status === "CONFLICT") return tokenColor("--pa-color-status-conflict");
    if (status === "CONDITIONAL") return tokenColor("--pa-color-status-conditional");
    if (status === "STALE") return tokenColor("--pa-color-status-stale");
    if (status === "ALLOWED") return tokenColor("--pa-color-reality-observed");
    return tokenColor("--pa-color-reality-insufficient");
  }
  const tokenByStatus: Record<string, string> = {
    ALLOWED: "--pa-color-status-allowed",
    CONDITIONAL: "--pa-color-status-conditional",
    RESTRICTED: "--pa-color-status-restricted",
    CONFLICT: "--pa-color-status-conflict",
    STALE: "--pa-color-status-stale",
    UNKNOWN: "--pa-color-status-unknown",
  };
  return tokenColor(tokenByStatus[status] ?? "--pa-color-status-unknown");
}

export function tencentMarkerSvg(
  color: string,
  count: number,
  selected: boolean,
  status: MapMarker["status"],
): string {
  const accent = tokenColor("--pa-color-accent");
  const surface = tokenColor("--pa-color-surface");
  const textPrimary = tokenColor("--pa-color-text-primary");
  const ring = selected
    ? `<circle cx="18" cy="18" r="15" fill="none" stroke="${accent}" stroke-width="3"/>`
    : "";

  if (count > 1) {
    const cluster = `<circle cx="18" cy="18" r="${selected ? 10 : 9}" fill="${color}" stroke="${surface}" stroke-width="2"/><text x="18" y="22" text-anchor="middle" font-family="Arial,sans-serif" font-size="12" font-weight="700" fill="${surface}">${Math.min(count, 99)}</text>`;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">${ring}${cluster}</svg>`;
    return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
  }

  const size = selected ? 10 : 9;
  let shape = `<circle cx="18" cy="18" r="${size}" fill="${color}" stroke="${surface}" stroke-width="2"/>`;
  let glyphFill = surface;

  if (status === "CONDITIONAL") {
    shape = `<circle cx="18" cy="18" r="${size}" fill="${surface}" stroke="${color}" stroke-width="3"/>`;
    glyphFill = color;
  } else if (status === "UNKNOWN") {
    shape = `<circle cx="18" cy="18" r="${size}" fill="${surface}" stroke="${color}" stroke-width="2"/>`;
    glyphFill = color;
  } else if (status === "RESTRICTED") {
    shape = `<rect x="9" y="13" width="18" height="10" rx="3" fill="${color}" stroke="${surface}" stroke-width="2"/>`;
  } else if (status === "CONFLICT") {
    shape = `<polygon points="18,7 29,18 18,29 7,18" fill="${color}" stroke="${surface}" stroke-width="2"/>`;
  } else if (status === "STALE") {
    shape = `<circle cx="18" cy="18" r="${size}" fill="${surface}" stroke="${color}" stroke-width="2" stroke-dasharray="3 2"/>`;
    glyphFill = color;
  }

  const glyph = STATUS_GLYPHS[status] ?? STATUS_GLYPHS.UNKNOWN;
  const glyphText = `<text x="18" y="21" text-anchor="middle" font-family="Arial,sans-serif" font-size="8" font-weight="700" fill="${glyphFill || textPrimary}">${glyph}</text>`;
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 36 36">${ring}${shape}${glyphText}</svg>`;
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}
