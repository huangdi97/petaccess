/**
 * Consumer repository — M3 (V020_M3_CONSUMER_CORE).
 *
 * The ONLY module Home / Search read for consumer data. Responsibilities:
 *
 *   - search / nearby lists (cached, coalesced)
 *   - per-row facts (rule answer + reality) via **bounded concurrency**
 *     (never an unbounded Promise.all over N rows)
 *   - CoexistenceSnapshot for the preview / detail surface (cached)
 *   - request epoch: a slow previous request can never overwrite a newer one
 *
 * Transport errors stay transport errors: a failed row enrichment is reported
 * as `answerError` / `realityError`, never converted into UNKNOWN / empty.
 * This module performs NO domain calculation — every semantic value comes from
 * the server answer or the shared client-core vocabularies.
 */
import {
  client,
  session,
  synthDemoCamera,
  type AccessAnswer,
  type CoexistenceSnapshot,
  type PlaceSummary,
  type RealityAnswer,
} from "@petaccess/client-core";
import { ConsumerCache } from "./cache";

export interface RowFacts {
  answer: AccessAnswer | null;
  /** true when the rule answer failed at transport level (NOT domain UNKNOWN). */
  answerError: boolean;
  reality: RealityAnswer | null;
  /** true when the reality request failed (NOT "no recent record"). */
  realityError: boolean;
}

const cache = new ConsumerCache(60_000);

/** Query context that actually changes the answer (derived from the API). */
function answerKey(placeId: string): string {
  return ConsumerCache.key([
    "answer",
    placeId,
    session.activePet?.species ?? "dog",
    session.activePet?.service_role ?? "none",
    session.activePet?.declared_role ?? null,
  ]);
}

function realityKey(placeId: string): string {
  return ConsumerCache.key(["reality", placeId]);
}

async function fetchAnswer(placeId: string): Promise<AccessAnswer> {
  return client.accessAnswer(placeId, {
    animal: session.activePet?.species ?? "dog",
    service_role: session.activePet?.service_role ?? "none",
    declared_role: session.activePet?.declared_role ?? null,
  });
}

/**
 * One row's facts: rule answer + reality, cached and coalesced.
 *
 * The answer is fetched with a null fallback so transport failure does not
 * crash the row; the `answerError` flag lets the UI say "暂时无法取得" instead
 * of implying the honest domain UNKNOWN ("尚未核验").
 */
export async function rowFacts(place: PlaceSummary): Promise<RowFacts> {
  const [a, r] = await Promise.all([
    cache.coalesce<AccessAnswer | null>(answerKey(place.id), () =>
      fetchAnswer(place.id).catch(() => null),
    ),
    cache.coalesce<RealityAnswer | null>(realityKey(place.id), () =>
      client.placeReality(place.id).catch(() => null),
    ),
  ]);
  return {
    answer: a.value as AccessAnswer | null,
    answerError: a.value === null,
    reality: r.value as RealityAnswer | null,
    realityError: r.value === null,
  };
}

/**
 * Bounded-concurrency enrichment over a list. Never fans out N requests at
 * once — `limit` workers drain a queue, and each row's requests are cached so
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
          answer: null,
          answerError: true,
          reality: null,
          realityError: true,
        });
      }
    }
  };
  await Promise.all(Array.from({ length: Math.min(limit, list.length) }, worker));
  return out;
}

/** Cached CoexistenceSnapshot for the preview / detail surface. */
export async function snapshotFor(placeId: string): Promise<CoexistenceSnapshot> {
  const key = ConsumerCache.key(["snapshot", placeId, session.activePet?.species ?? "dog"]);
  const res = await cache.coalesce<CoexistenceSnapshot>(key, () =>
    client.coexistenceSnapshot(placeId, {
      animal: session.activePet?.species ?? "dog",
      service_role: session.activePet?.service_role ?? "none",
      declared_role: session.activePet?.declared_role ?? null,
      action: "enter",
    }),
  );
  return res.value;
}

/** Cached search by name / alias. */
export async function searchPlaces(q: string): Promise<PlaceSummary[]> {
  const key = ConsumerCache.key(["search", q]);
  const res = await cache.coalesce<PlaceSummary[]>(key, () => client.searchPlaces(q));
  return res.value;
}

/** Cached nearby list (demo camera, fixed radius). */
export async function nearbyPlaces(): Promise<PlaceSummary[]> {
  const key = ConsumerCache.key(["nearby"]);
  const cam = synthDemoCamera();
  const res = await cache.coalesce<PlaceSummary[]>(key, () =>
    client.nearby(cam.lat, cam.lng, 5000),
  );
  return res.value;
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
