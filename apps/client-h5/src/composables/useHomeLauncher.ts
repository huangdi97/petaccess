/**
 * useHomeLauncher — Home page data, actions and derived rows (freeze §9).
 *
 * All row data comes from the consumer repository (CoexistenceSnapshot SSOT):
 * nearbyPlaces() + enrichRows() under a request epoch so a stale load never
 * overwrites a newer one. Transport failures surface as an error line, never
 * as UNKNOWN or an empty state. Recent history is platform-storage-backed
 * and re-evaluated on open — old answers are never reused.
 */
import { computed, onMounted, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { platformStorage, session, type PlaceSummary } from "@petaccess/client-core";
import { type IconName, type StatusKey } from "@petaccess/design-tokens";
import { ANSWERED_STATUSES, answerConditions, answerScopeLabel, answerStatusKey } from "../answer";
import { bootStage } from "../config/bootTrace";
import {
  createEpoch,
  currentQueryContext,
  enrichRows,
  nearbyPlaces,
  type RowFacts,
} from "../consumer/repository";
import type { ConsumerLens } from "../consumer/rowView";
import { queryAnimalLabel } from "../consumer/queryContext";
import { presentDescription } from "../errors";
import { useOnline } from "./useOnline";

/** One derived home row: rule conclusion + reality summary over one place. */
export interface HomeCard {
  place: PlaceSummary;
  facts: RowFacts;
  status: StatusKey;
  scope: string;
  conditions: string[];
}

const RECENT_KEY = "pa.recent.v1";
const HOME_INTEREST_KEY = "pa.homeInterest.v1";
const MAX_RECENT = 3;
const HOME_INTERESTS = new Set<ConsumerLens>(["presence", "indoor", "dining", "rules"]);

export const CONDITION_ZH: Record<string, string> = {
  leash_required: "全程牵引",
  muzzle_required: "佩戴嘴套",
  carrier_required: "装载（笼/包）",
  stroller_required: "使用推车",
  no_ground: "不可落地",
  vaccination_required: "免疫证明",
  registration_required: "登记证明",
  reservation_required: "需预约",
};

export const HOME_ENTRIES: { key: string; label: string; hint: string; icon: IconName }[] = [
  { key: "presence", label: "现场是否有动物出现", hint: "看近期现场记录", icon: "eye" },
  { key: "indoor", label: "室内空间情况", hint: "商场 · 餐厅 · 场馆室内", icon: "building" },
  { key: "dining", label: "餐饮区域情况", hint: "堂食区 · 户外座位", icon: "map" },
  { key: "rules", label: "完整规则", hint: "场所全部规则与来源", icon: "document" },
];

export function useHomeLauncher() {
  const router = useRouter();
  const loading = ref(true);
  const error = ref("");
  const places = ref<PlaceSummary[]>([]);
  const cards = ref<HomeCard[]>([]);
  const listStale = ref(false);
  const nearbyFetchedAtMs = ref<number | null>(null);
  const { online } = useOnline();
  const query = ref("");
  const recent = ref<{ id: string; name: string }[]>([]);
  /** Lightweight attention preference: only changes Consumer ordering/emphasis. */
  const interest = ref<ConsumerLens>("");
  const epoch = createEpoch();

  const speciesLabel = computed(() => queryAnimalLabel());

  // Home is Rule + Reality, not a "rules verified" dashboard. A place with
  // useful published Reality evidence remains a substantive digest row even
  // when Rule is UNKNOWN; otherwise the UI would hide the exact divergence
  // the product is designed to surface.
  const hasUsefulPublishedFact = (card: HomeCard) => {
    if (ANSWERED_STATUSES.includes(card.status)) return true;
    if ((card.facts.reality?.evidence_count ?? 0) > 0) return true;
    if ((card.facts.snapshot?.evidence_summary.reality_evidence_count ?? 0) > 0) return true;
    return (card.facts.snapshot?.evidence_summary.rule_evidence.length ?? 0) > 0;
  };
  const hasTransportFailure = (card: HomeCard) =>
    Boolean(card.facts.answerError || card.facts.realityError);

  const verified = computed(() => cards.value.filter(hasUsefulPublishedFact));
  const unavailable = computed(() =>
    cards.value.filter((card) => !hasUsefulPublishedFact(card) && hasTransportFailure(card)),
  );
  const pending = computed(() =>
    cards.value.filter(
      (card) => !hasUsefulPublishedFact(card) && !hasTransportFailure(card),
    ),
  );

  function submitSearch() {
    const q = query.value.trim();
    if (!q) return;
    void router.push({ name: "search", query: { q } });
  }

  function goEntry(key: string) {
    const next = HOME_INTERESTS.has(key as ConsumerLens) ? (key as ConsumerLens) : "";
    interest.value = next;
    if (next) platformStorage.set(HOME_INTEREST_KEY, next);
    else platformStorage.remove(HOME_INTEREST_KEY);
    void router.push({ name: "search", query: { lens: next || undefined } });
  }

  function open(id: string) {
    remember(id);
    void router.push({ name: "place", params: { id } });
  }

  function why(id: string) {
    void router.push({ name: "match-explain", params: { id } });
  }

  function remember(id: string) {
    const name =
      cards.value.find((c) => c.place.id === id)?.place.canonical_name ?? "最近查看的场所";
    recent.value = [{ id, name }, ...recent.value.filter((r) => r.id !== id)].slice(0, MAX_RECENT);
    platformStorage.set(RECENT_KEY, JSON.stringify(recent.value));
  }

  function clearRecent() {
    recent.value = [];
    platformStorage.remove(RECENT_KEY);
  }

  function loadRecent() {
    const raw = platformStorage.get(RECENT_KEY);
    try {
      recent.value = raw
        ? (JSON.parse(raw) as { id: string; name: string }[]).slice(0, MAX_RECENT)
        : [];
    } catch {
      recent.value = [];
      platformStorage.remove(RECENT_KEY);
    }
  }

  function loadInterest() {
    const saved = platformStorage.get(HOME_INTEREST_KEY) as ConsumerLens | undefined;
    interest.value = saved && HOME_INTERESTS.has(saved) ? saved : "";
  }

  async function load() {
    const n = epoch.begin();
    loading.value = true;
    error.value = "";
    listStale.value = false;
    try {
      const res = await nearbyPlaces();
      if (!epoch.isCurrent(n)) return; // a newer load superseded this one
      places.value = res.items;
      listStale.value = res.stale;
      nearbyFetchedAtMs.value = res.fetchedAtMs;
      const facts = await enrichRows(places.value);
      if (!epoch.isCurrent(n)) return; // a newer load superseded this one
      cards.value = places.value.map((p) => {
        const f = facts.get(p.id) ?? {
          snapshot: null,
          answer: null,
          answerError: true,
          reality: null,
          realityError: true,
          stale: false,
          fetchedAtMs: null,
        };
        return {
          place: p,
          facts: f,
          status: answerStatusKey(f.answer),
          scope: answerScopeLabel(f.answer, speciesLabel.value),
          conditions: answerConditions(f.answer, CONDITION_ZH),
        };
      });
    } catch (e) {
      if (epoch.isCurrent(n)) error.value = presentDescription(e);
    } finally {
      if (epoch.isCurrent(n)) loading.value = false;
    }
  }

  let queryContextReady = false;

  watch(currentQueryContext, () => {
    if (!queryContextReady) return;
    void load();
  });

  onMounted(async () => {
    await session.restore();
    loadRecent();
    loadInterest();
    await load();
    queryContextReady = true;
    bootStage("HOME_READY");
  });

  return {
    query,
    interest,
    recent,
    loading,
    error,
    places,
    listStale,
    nearbyFetchedAtMs,
    online,
    speciesLabel,
    verified,
    pending,
    unavailable,
    submitSearch,
    goEntry,
    open,
    why,
    clearRecent,
    load,
  };
}
