/**
 * Consumer repository — M3.1 corrective closure (UI_RECONSTRUCTION_GOAL §8).
 *
 * The ONLY module Home / Search / Map / Place read for consumer data. Contract:
 *
 *   - CoexistenceSnapshot SSOT (§8.1): rows and the preview / dossier read the
 *     SAME server aggregate. Nothing here recomputes Rule / Reality from raw
 *     rules; `rowFacts` projects the snapshot's rule_answer / reality_answer.
 *   - Transport errors are never cached (§8.2): a failed fetch throws; the
 *     cache stores only successful responses. A null answer is NOT written, so
 *     a later "network recovered" request re-fetches instead of hitting a TTL
 *     slot that contains an error.
 *   - Cache key completeness (§8.3): every key includes the full query context
 *     (placeId, animal/species, service_role, declared_role, action, zone).
 *     Switching from an ordinary-dog query to a service-dog query changes the
 *     key, so the old snapshot is never served for the new question.
 *   - Offline / stale wiring (§8.4): `snapshotFor` / `searchPlaces` /
 *     `nearbyPlaces` return freshness metadata (stale, fetchedAtMs) and serve
 *     stale entries immediately while a background refresh re-fetches when
 *     online. Client cache freshness is reported; it is never labelled as
 *     Rule / Reality domain freshness.
 *   - Lens (§8.5) is a pure consumer projection on top of this layer (see
 *     `rowView.ts`); this module never lets a lens change what it requests.
 *
 * This module performs NO domain calculation — every semantic value comes from
 * the server snapshot or the shared client-core vocabularies.
 */
import {
  client,
  mapQueryRadiusForZoom,
  session,
  synthDemoCamera,
  type AccessAnswer,
  type MapCamera,
  type CoexistenceSnapshot,
  type PlaceSummary,
  type RealityAnswer,
} from "@petaccess/client-core";
import { isOnline } from "../composables/useOnline";
import { ConsumerCache } from "./cache";

export interface RowFacts {
  /** The authoritative aggregate behind every projected consumer fact. */
  snapshot: CoexistenceSnapshot | null;
  answer: AccessAnswer | null;
  /** true when the snapshot fetch failed at transport level (NOT domain UNKNOWN). */
  answerError: boolean;
  reality: RealityAnswer | null;
  /** true when the snapshot fetch failed (NOT "no recent record"). */
  realityError: boolean;
  /** entry was older than TTL when served (stale); null when absent. */
  stale: boolean;
  fetchedAtMs: number | null;
}

export interface ListResult<T> {
  items: T[];
  stale: boolean;
  fetchedAtMs: number | null;
}

export interface SnapshotResult {
  snapshot: CoexistenceSnapshot;
  stale: boolean;
  fetchedAtMs: number | null;
}

/**
 * The query context that actually changes the answer, derived from the API
 * contract (`POST /places/{id}/coexistence` body). `action` is the canonical
 * consumer action ("enter" — 进入); zone queries pass their own zone_id at
 * the call site and are never folded into a place-level verdict.
 */
export interface QueryContext {
  animal: string;
  service_role: string;
  declared_role: string | null;
  action: string;
  zone_id: string | null;
}

export function currentQueryContext(): QueryContext {
  // service-dog mode asks as a working (assistance) dog even without a pet
  // profile (mirrors PlaceView.queryServiceRole, ADR-025).
  const serviceDogQuery = session.mode === "service_dog";
  const serviceRole = serviceDogQuery ? "working" : (session.activePet?.service_role ?? "none");
  return {
    // Service-dog mode is always a dog query. Reusing an active cat/other pet
    // here would create an impossible animal=cat + service_role=working request.
    animal: serviceDogQuery ? "dog" : (session.activePet?.species ?? "dog"),
    service_role: serviceRole,
    declared_role: serviceDogQuery
      ? (session.declaredRole ?? session.activePet?.declared_role ?? null)
      : null,
    action: "enter",
    zone_id: null,
  };
}

const cache = new ConsumerCache(60_000);

/** Normalised snapshot key: full context, never an invented subset. */
export function snapshotKey(placeId: string, ctx: QueryContext = currentQueryContext()): string {
  return ConsumerCache.key([
    "snapshot",
    placeId,
    ctx.animal,
    ctx.service_role,
    ctx.declared_role ?? "",
    ctx.action,
    ctx.zone_id ?? "",
  ]);
}

function fetchSnapshot(placeId: string, ctx: QueryContext): Promise<CoexistenceSnapshot> {
  return client.coexistenceSnapshot(placeId, {
    animal: ctx.animal,
    service_role: ctx.service_role,
    declared_role: ctx.declared_role,
    action: ctx.action,
    zone_id: ctx.zone_id,
  });
}

/**
 * Background refresh for a stale-but-served entry. Never throws to the caller:
 * the stale value stays visible with its marker; a failed refresh is logged and
 * the next access re-attempts.
 */
function refresh<T>(key: string, fetchFn: () => Promise<T>): void {
  void cache.coalesce<T>(key, fetchFn).catch((e: unknown) => {
    // SAFETY: background refresh failure must not unhandled-reject; the page
    // already shows the stale marker. The request itself stays the source of
    // truth, so a silent failure only means "still the old value".
    console.warn("[consumer] background refresh failed", e);
  });
}

/**
 * One row's facts, projected from the SAME CoexistenceSnapshot the preview
 * uses (SSOT). Transport failure throws through `snapshotFor` and is reported
 * as answerError + realityError — never converted into UNKNOWN / empty.
 */
export async function rowFacts(place: PlaceSummary): Promise<RowFacts> {
  try {
    const { snapshot, stale, fetchedAtMs } = await snapshotFor(place.id);
    return {
      snapshot,
      answer: snapshot.rule_answer,
      answerError: false,
      reality: snapshot.reality_answer,
      realityError: false,
      stale,
      fetchedAtMs,
    };
  } catch {
    return {
      snapshot: null,
      answer: null,
      answerError: true,
      reality: null,
      realityError: true,
      stale: false,
      fetchedAtMs: null,
    };
  }
}

/**
 * Bounded-concurrency enrichment over a list. Never fans out N requests at
 * once — `limit` workers drain a queue, and each row's snapshot is cached so
 * revisits are free.
 */
export async function enrichRows(list: PlaceSummary[], limit = 4): Promise<Map<string, RowFacts>> {
  const out = new Map<string, RowFacts>();
  const queue = [...list];
  const worker = async () => {
    for (;;) {
      const p = queue.shift();
      if (!p) return;
      try {
        out.set(p.id, await rowFacts(p));
      } catch {
        out.set(p.id, {
          snapshot: null,
          answer: null,
          answerError: true,
          reality: null,
          realityError: true,
          stale: false,
          fetchedAtMs: null,
        });
      }
    }
  };
  await Promise.all(Array.from({ length: Math.min(limit, list.length) }, worker));
  return out;
}

/**
 * Cached CoexistenceSnapshot with freshness metadata (SSOT for rows + preview).
 *
 * Fresh (inside TTL): served from cache. Stale: served immediately and, when
 * online, refreshed in the background. Offline: cached entry is served with
 * its last-fetched time; no cache at all → the request throws so the caller
 * presents the explicit Offline state. Success is stored; transport errors
 * never are.
 */
export async function snapshotFor(
  placeId: string,
  ctx: QueryContext = currentQueryContext(),
): Promise<SnapshotResult> {
  const key = snapshotKey(placeId, ctx);
  const cached = cache.get<CoexistenceSnapshot>(key);

  if (cached && cache.isFresh(key)) {
    return { snapshot: cached, stale: false, fetchedAtMs: cache.fetchedAtMs(key) };
  }
  if (cached && cache.isStale(key)) {
    // Online + stale → stale visible + background refresh; offline + cached →
    // the same stale value with an explicit age (never silently "fresh").
    if (isOnline()) refresh(key, () => fetchSnapshot(placeId, ctx));
    return { snapshot: cached, stale: true, fetchedAtMs: cache.fetchedAtMs(key) };
  }

  const res = await cache.coalesce<CoexistenceSnapshot>(key, () => fetchSnapshot(placeId, ctx), {
    offlineFallback: true,
  });
  return { snapshot: res.value, stale: res.stale, fetchedAtMs: cache.fetchedAtMs(key) };
}

/** Cached search by name / alias, with the same freshness semantics. */
export async function searchPlaces(q: string): Promise<ListResult<PlaceSummary>> {
  const key = ConsumerCache.key(["search", q]);
  const cached = cache.get<PlaceSummary[]>(key);
  if (cached && cache.isFresh(key)) {
    return { items: cached, stale: false, fetchedAtMs: cache.fetchedAtMs(key) };
  }
  if (cached && cache.isStale(key)) {
    if (isOnline()) refresh(key, () => client.searchPlaces(q));
    return { items: cached, stale: true, fetchedAtMs: cache.fetchedAtMs(key) };
  }
  const res = await cache.coalesce<PlaceSummary[]>(key, () => client.searchPlaces(q), {
    offlineFallback: true,
  });
  return { items: res.value, stale: res.stale, fetchedAtMs: cache.fetchedAtMs(key) };
}

/** Cached nearby list for the actual map camera, with the same freshness semantics.
 * Home may omit the camera and use the Shanghai pilot default; Map must always
 * pass its live one-shot-location/default camera so moving the camera changes
 * the spatial query instead of only moving the drawing surface. */
export async function nearbyPlaces(
  camera: MapCamera = synthDemoCamera(),
  radiusM = mapQueryRadiusForZoom(camera.zoom),
): Promise<ListResult<PlaceSummary>> {
  const key = ConsumerCache.key(["nearby", camera.lat.toFixed(5), camera.lng.toFixed(5), radiusM]);
  const fetchFn = () => client.nearby(camera.lat, camera.lng, radiusM);
  const cached = cache.get<PlaceSummary[]>(key);
  if (cached && cache.isFresh(key)) {
    return { items: cached, stale: false, fetchedAtMs: cache.fetchedAtMs(key) };
  }
  if (cached && cache.isStale(key)) {
    if (isOnline()) refresh(key, fetchFn);
    return { items: cached, stale: true, fetchedAtMs: cache.fetchedAtMs(key) };
  }
  const res = await cache.coalesce<PlaceSummary[]>(key, fetchFn, { offlineFallback: true });
  return { items: res.value, stale: res.stale, fetchedAtMs: cache.fetchedAtMs(key) };
}

/** Clear all consumer cache (logout / session switch). */
export function clearConsumerCache(): void {
  cache.clear();
}

/**
 * Request epoch guard — the classic "slow old request must not overwrite a
 * fast new one". Create one epoch per page; each async load captures the
 * current epoch and drops its result if a newer load already started.
 */
export function createEpoch() {
  let current = 0;
  return {
    begin(): number {
      current += 1;
      return current;
    },
    isCurrent(n: number): boolean {
      return n === current;
    },
  };
}
