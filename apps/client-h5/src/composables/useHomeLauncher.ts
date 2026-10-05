/**
 * useHomeLauncher — Home page data, actions and derived rows (freeze §9).
 *
 * All row data comes from the consumer repository (CoexistenceSnapshot SSOT):
 * nearbyPlaces() + enrichRows() under a request epoch so a stale load never
 * overwrites a newer one. Transport failures surface as an error line, never
 * as UNKNOWN or an empty state. Recent history is localStorage-backed and
 * re-evaluated on open — old answers are never reused.
 */
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { session, type PlaceSummary } from "@petaccess/client-core";
import { type IconName, type StatusKey } from "@petaccess/design-tokens";
import { ANSWERED_STATUSES, answerConditions, answerScopeLabel, answerStatusKey } from "../answer";
import { bootStage } from "../config/bootTrace";
import { createEpoch, enrichRows, nearbyPlaces, type RowFacts } from "../consumer/repository";
import type { ConsumerLens } from "../consumer/rowView";
import { presentDescription } from "../errors";
import { useOnline } from "./useOnline";

export type Perspective = "rules" | "animal" | "coexist";

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

export const PERSPECTIVES: { key: Perspective; label: string }[] = [
  { key: "rules", label: "看场所规则" },
  { key: "animal", label: "携带动物" },
  { key: "coexist", label: "共处偏好" },
];

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
  const perspective = ref<Perspective>("rules");
  const listStale = ref(false);
  const nearbyFetchedAtMs = ref<number | null>(null);
  const { online } = useOnline();
  const query = ref("");
  const recent = ref<{ id: string; name: string }[]>([]);
  /** Lightweight attention preference: only changes Consumer ordering/emphasis. */
  const interest = ref<ConsumerLens>("");
  const epoch = createEpoch();

  const speciesLabel = computed(() => {
    const s = session.activePet?.species ?? "dog";
    if (session.activePet?.service_role === "working") return "服务犬";
    return s === "dog" ? "普通犬" : s === "cat" ? "猫" : "其他宠物";
  });

  const verified = computed(() => cards.value.filter((c) => ANSWERED_STATUSES.includes(c.status)));
  const pending = computed(() => cards.value.filter((c) => !ANSWERED_STATUSES.includes(c.status)));

  function setPerspective(p: Perspective) {
    perspective.value = p;
    if (p === "coexist") {
      void router.push({ name: "boundary" });
      return;
    }
    session.mode = p === "rules" ? "rules_only" : "with_pet";
    void load();
  }

  function submitSearch() {
    const q = query.value.trim();
    if (!q) return;
    void router.push({ name: "search", query: { q } });
  }

  function goEntry(key: string) {
    const next = HOME_INTERESTS.has(key as ConsumerLens) ? (key as ConsumerLens) : "";
    interest.value = next;
    try {
      if (next) localStorage.setItem(HOME_INTEREST_KEY, next);
      else localStorage.removeItem(HOME_INTEREST_KEY);
    } catch {
      /* preference persistence is optional */
    }
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
    const name = cards.value.find((c) => c.place.id === id)?.place.canonical_name ?? id;
    recent.value = [{ id, name }, ...recent.value.filter((r) => r.id !== id)].slice(0, MAX_RECENT);
    try {
      localStorage.setItem(RECENT_KEY, JSON.stringify(recent.value));
    } catch {
      /* storage unavailable (private mode): history simply does not persist */
    }
  }

  function clearRecent() {
    recent.value = [];
    try {
      localStorage.removeItem(RECENT_KEY);
    } catch {
      /* ignore */
    }
  }

  function loadRecent() {
    try {
      const raw = localStorage.getItem(RECENT_KEY);
      recent.value = raw
        ? (JSON.parse(raw) as { id: string; name: string }[]).slice(0, MAX_RECENT)
        : [];
    } catch {
      recent.value = [];
    }
  }

  function loadInterest() {
    try {
      const saved = localStorage.getItem(HOME_INTEREST_KEY) as ConsumerLens | null;
      interest.value = saved && HOME_INTERESTS.has(saved) ? saved : "";
    } catch {
      interest.value = "";
    }
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
          snapshot: null,
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

  onMounted(async () => {
    await session.restore();
    loadRecent();
    loadInterest();
    await load();
    bootStage("HOME_READY");
  });

  return {
    query,
    perspective,
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
    setPerspective,
    submitSearch,
    goEntry,
    open,
    why,
    clearRecent,
    load,
  };
}
