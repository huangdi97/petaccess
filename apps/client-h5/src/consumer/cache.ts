/**
 * Consumer cache — M3 (V020_M3_CONSUMER_CORE).
 *
 * One small cache for read-only consumer data (search, nearby, answer,
 * reality, snapshot). Contract:
 *
 *   - key        = endpoint identity + every query parameter that changes the
 *                 domain answer (never invented params — derived from the API).
 *   - dedupe     = concurrent in-flight requests for the same key share one
 *                 promise (request coalescing); no duplicate HTTP.
 *   - TTL        = how long an entry is considered fresh.
 *   - stale      = an entry older than TTL is kept (last-fetched timestamp) so
 *                 offline / error states can fall back to it, and callers can
 *                 show "stale" instead of a blank.
 *   - invalidation = `clear` for the whole consumer layer (logout / session
 *                 change) and per-key overwrite on refresh.
 *
 * Transport errors are NEVER stored as domain facts: a failed fetch simply
 * does not write an entry (the caller sees the error). Offline fallback reads
 * the last successful entry and reports its age.
 */
import { isOnline } from "../composables/useOnline";

export interface CacheEntry<T> {
  value: T;
  fetchedAt: number;
}

const DEFAULT_TTL_MS = 60_000;

export class ConsumerCache {
  private readonly store = new Map<string, CacheEntry<unknown>>();
  private readonly inflight = new Map<string, Promise<unknown>>();
  private readonly ttlMs: number;

  constructor(ttlMs: number = DEFAULT_TTL_MS) {
    this.ttlMs = ttlMs;
  }

  /** Normalise a cache key from parts. Callers pass the exact query context. */
  static key(parts: Array<string | number | null | undefined>): string {
    return parts.map((p) => (p == null ? "" : String(p))).join("|");
  }

  /** Whether an entry exists and is still inside its TTL. */
  isFresh(key: string): boolean {
    const e = this.store.get(key);
    if (!e) return false;
    return Date.now() - e.fetchedAt <= this.ttlMs;
  }

  /** Age of the entry in ms; null when absent. */
  ageMs(key: string): number | null {
    const e = this.store.get(key);
    return e ? Date.now() - e.fetchedAt : null;
  }

  get<T>(key: string): T | null {
    return (this.store.get(key)?.value as T | undefined) ?? null;
  }

  set<T>(key: string, value: T): void {
    this.store.set(key, { value, fetchedAt: Date.now() });
  }

  /** Remove one key. */
  delete(key: string): void {
    this.store.delete(key);
    this.inflight.delete(key);
  }

  /** Clear the whole consumer cache (logout, session switch). */
  clear(): void {
    this.store.clear();
    this.inflight.clear();
  }

  /**
   * Coalesced fetch: concurrent callers for the same key share one request.
   * On success the entry is stored (fresh). On failure nothing is stored and
   * the error propagates — transport error never becomes a cached domain fact.
   * When offline, a stored entry (any age) is returned so the app degrades to
   * cached state instead of a blank; `stale` is true when it exceeded TTL.
   */
  async coalesce<T>(
    key: string,
    fetchFn: () => Promise<T>,
    opts: { offlineFallback?: boolean } = {},
  ): Promise<{ value: T; stale: boolean }> {
    const cached = this.store.get(key);
    if (opts.offlineFallback && !isOnline() && cached) {
      return { value: cached.value as T, stale: Date.now() - cached.fetchedAt > this.ttlMs };
    }
    if (this.isFresh(key) && cached) {
      return { value: cached.value as T, stale: false };
    }
    const existing = this.inflight.get(key);
    if (existing) {
      const value = (await existing) as T;
      return { value, stale: false };
    }
    const p: Promise<unknown> = fetchFn().then((value) => {
      this.store.set(key, { value, fetchedAt: Date.now() });
      this.inflight.delete(key);
      return value;
    });
    this.inflight.set(key, p);
    try {
      const value = (await p) as T;
      return { value, stale: false };
    } catch (e) {
      this.inflight.delete(key);
      throw e;
    }
  }
}
