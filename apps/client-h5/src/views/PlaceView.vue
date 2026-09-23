<script setup lang="ts">
/**
 * Place Detail — the full 10-section layout (spec §2.4).
 *
 * Section 1 current answer (ordinary pet / my pet / my boundary)
 * Section 2 where you can and cannot go (zones + floors)
 * Section 3 conditions            Section 4 coexistence boundary
 * Section 5 how to get in         Section 6 facilities
 * Section 7 sources & freshness   Section 8 field records (≠ policy)
 * Section 9 history (superseded)  Section 10 corrections / operator claim
 *
 * Data comes from the public place endpoints; the structured extras (coexistence,
 * amenities, entrances, paths, events) come from /places/{id}/extras, and the
 * normative answer from the explainable resolver.
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { type StatusKey } from "@petaccess/design-tokens";
import {
  client,
  conditionLabel,
  placeTypeLabel,
  provenanceSummary,
  session,
  type AccessAnswer,
  type BoundaryMatchResult,
  type ObservationView,
  type PlaceDetail,
  type PlaceExtras,
  type RuleView,
  type SourceView,
  type Zone,
} from "@petaccess/client-core";
import RealityPanel from "../components/RealityPanel.vue";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import SourceBadge from "../components/SourceBadge.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import { answerConditions, answerStatusKey, answerVerdictLabel } from "../answer";

const route = useRoute();

/**
 * Reactive, and that is load-bearing.
 *
 * Vue Router reuses this component across `/place/:id` changes, so reading
 * `route.params.id` once at setup pinned the page to whichever place was opened
 * first: navigating to a second place — from a search result, from the map, or
 * with the browser's back button — kept rendering the *previous* place. Only a
 * hard reload showed the right one. The probe that caught it:
 *
 *     goto   /#/place/<cafe>   -> h1 "星河咖啡·测试店"
 *     hash -> /#/place/<mall>  -> h1 "星河咖啡·测试店"   <- wrong
 *     reload                   -> h1 "云栖中心·测试商场"
 *
 * For a rule-lookup product that is the worst possible failure: another place's
 * rules, presented under this place's name and address.
 */
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));

const place = ref<PlaceDetail | null>(null);
const zones = ref<Zone[]>([]);
const rules = ref<RuleView[]>([]);
const observations = ref<ObservationView[]>([]);
const verifications = ref<{ occurred_at: string; result: string; note: string | null }[]>([]);
const sources = ref<SourceView[]>([]);
const extras = ref<PlaceExtras | null>(null);
const boundaryMatch = ref<BoundaryMatchResult | null>(null);
/**
 * The unified answer model (design §10) — this page's ONLY source of a rule
 * conclusion, scope and provenance.
 *
 * Two answers are held because Section 1 shows the visitor's own result next to
 * the plain-dog baseline; both come from the server. Nothing here folds zones
 * into a place verdict, which the previous implementation did: it asked the v1
 * evaluator once per zone and then took the most favourable result, so a mall
 * with one pet-friendly zone read as enterable overall. That is the zone →
 * place flattening the domain forbids.
 */
const answer = ref<AccessAnswer | null>(null);
const ordinaryAnswer = ref<AccessAnswer | null>(null);
const error = ref("");
const loading = ref(true);
const partial = ref<string[]>([]);
const watching = ref(false);
const quickMsg = ref("");
const zoneAnswer = ref<string | null>(null);
// Per-zone resolution, fetched on demand. A zone's answer is NOT the place
// answer: the cafe's indoor dining area is `prohibited` while the place-level
// result is `unknown`, so reusing the place-level set here would tell a user
// "尚未核验" about a zone that is explicitly restricted.
const zoneAnswers = ref<Record<string, AccessAnswer>>({});
const zoneErrors = ref<Record<string, boolean>>({});

// ---- v0.9-R1 Reality Layer: the ONE snapshot for the passport (AC9/AC10) ----
const coexistence = ref<import("@petaccess/client-core").CoexistenceSnapshot | null>(null);
const coexistenceLoaded = ref(false);
/** §12.4 — 「进入前需满足」, assembled by the answer adapter. */
const answerConditionList = computed(() => answerConditions(answer.value));

const sourceMap = computed(() => {
  const m = new Map<string, SourceView>();
  for (const s of sources.value) m.set(s.id, s);
  return m;
});
const prov = computed(() => provenanceSummary(rules.value, verifications.value));

const currentRules = computed(() => rules.value.filter((r) => r.status === "current"));
const historyRules = computed(() => rules.value.filter((r) => r.status !== "current"));

/** Section 3: every distinct condition across current rules, human-labelled. */
const conditions = computed(() => {
  const seen = new Set<string>();
  for (const r of currentRules.value) {
    for (const o of obligationsFor(r)) seen.add(o);
  }
  return [...seen];
});

const STALE_DAYS = 180;
function isStale(r: RuleView): boolean {
  if (!r.last_verified_at) return true;
  const age = (Date.now() - new Date(r.last_verified_at).getTime()) / 86_400_000;
  return age > STALE_DAYS;
}

function obligationsFor(r: RuleView): string[] {
  const raw = (r as unknown as { conditions?: { condition_type?: string }[] }).conditions ?? [];
  return raw.map((c) => conditionLabel(c.condition_type ?? ""));
}

const layerLabel: Record<string, string> = {
  LEGAL: "法规",
  REGULATORY_GUIDANCE: "监管指引",
  OPERATOR_POLICY: "运营方政策",
  TEMPORARY_POLICY: "临时/事件政策",
};
const forceLabel: Record<string, string> = {
  mandatory: "强制",
  advisory: "建议",
  operator_discretion: "运营方裁量",
};

const AMENITY_LABELS: Record<string, string> = {
  PET_WATER: "宠物饮水",
  WASTE_BAG: "拾便袋",
  PET_TOILET: "宠物厕所",
  PET_WASH: "宠物清洗",
  STROLLER_RENTAL: "推车租借",
  TIE_UP: "拴宠点",
  PET_HOLDING: "宠物寄存",
  PET_ELEVATOR: "宠物电梯",
  PET_ENTRANCE: "宠物入口",
  PET_ACTIVITY_AREA: "宠物活动区",
};

const ENTRANCE_LABELS: Record<string, string> = {
  GENERAL: "通用入口",
  PET_DESIGNATED: "指定携宠入口",
  SERVICE: "服务通道",
  PARKING_CONNECTION: "车库连接",
  OTHER: "其他",
};

const COEXISTENCE_LABELS: Record<string, string> = {
  ordinary_pet_indoor_dining: "室内堂食",
  ordinary_pet_outdoor_dining: "户外堂食",
  animal_on_customer_seat: "顾客座椅",
  animal_on_table_surface: "桌面",
  animal_near_food_service_area: "食品服务区附近",
  animal_in_self_service_food_area: "食品自助区",
  animal_use_customer_tableware: "使用顾客餐具",
  dedicated_pet_tableware: "专用宠物餐具",
  dedicated_pet_zone: "独立携宠区",
  zone_separation: "区域分隔",
};

/** Query role for the current mode: service-dog mode asks as a working
 * (assistance) dog even without a pet profile; other modes use the active
 * pet's declared role (ADR-025). Mirrors the pre-AccessAnswer modeQuery
 * mapping so the mode switch keeps meaning "evaluate as a service dog". */
function queryServiceRole(): string {
  if (session.mode === "service_dog") return "working";
  return session.activePet?.service_role ?? "none";
}

async function evaluate() {
  const animal = session.activePet?.species ?? "dog";
  const serviceRole = queryServiceRole();
  // ADR-025: declare the role when the profile pins one, so a hearing-dog
  // question never inherits a guide-dog proviso.
  const declaredRole = session.activePet?.declared_role ?? null;

  answer.value = await client.accessAnswer(placeId.value, {
    animal,
    service_role: serviceRole,
    declared_role: declaredRole,
    action: "enter",
  });
  // Section 1 also shows the "ordinary pet" baseline so the user can separate
  // "what applies to me" from "what applies to a plain dog".
  ordinaryAnswer.value = await client.accessAnswer(placeId.value, {
    animal: "dog",
    service_role: "none",
    action: "enter",
  });
}

watch(
  () => [session.mode, session.activePet],
  () => {
    void evaluate();
  },
);

/** Load every section; a failed sub-call degrades to PARTIAL, never to a blank page. */
async function load() {
  loading.value = true;
  error.value = "";
  partial.value = [];
  const degrade = (label: string) => partial.value.push(label);
  try {
    place.value = await client.place(placeId.value);
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
    loading.value = false;
    return;
  }
  try {
    zones.value = await client.zones(placeId.value);
  } catch {
    degrade("分区域");
  }
  try {
    rules.value = await client.rules(placeId.value);
  } catch {
    degrade("规则");
  }
  try {
    observations.value = await client.observations(placeId.value);
  } catch {
    degrade("现场记录");
  }
  try {
    verifications.value = await client.verifications(placeId.value);
  } catch {
    degrade("核验历史");
  }
  try {
    sources.value = (await client.allSources()).filter((s) =>
      rules.value.some((r) => r.source_id === s.id),
    );
  } catch {
    degrade("来源");
  }
  try {
    extras.value = await client.placeExtras(placeId.value);
  } catch {
    degrade("共处边界/设施");
  }
  // One fetch, inside evaluate(), now covers conclusion + scope + provenance.
  // Account-scoped: a signed-out visitor has no stored boundary, so asking is
  // a 401 rather than an empty answer. Only call it when there is an account.
  if (session.signedIn) {
    try {
      boundaryMatch.value = await client.boundaryMatch(placeId.value);
    } catch {
      boundaryMatch.value = null; // no boundary set is not an error
    }
  }
  try {
    await evaluate();
  } catch {
    degrade("当前答案");
  }
  // v0.9-R1: the CoexistenceSnapshot powers the Reality panel. It degrades
  // gracefully when the reality layer is absent (BLOCKED / not yet populated).
  try {
    coexistence.value = await client.coexistenceSnapshot(placeId.value, {
      animal: "dog",
      service_role: "none",
      action: "enter",
    });
  } catch {
    coexistence.value = null;
  }
  coexistenceLoaded.value = true;
  loading.value = false;
}

/**
 * Drop every per-place ref before loading the next one.
 *
 * `load()` already clears `loading`/`error`/`partial`, but not the data itself.
 * When the page switches places the old rules would sit on screen under the new
 * place's name until each request returned — and if a sub-call degraded, the
 * new place's `partial` list would be seeded by the old place's sections.
 */
function resetForPlace() {
  place.value = null;
  zones.value = [];
  rules.value = [];
  observations.value = [];
  verifications.value = [];
  sources.value = [];
  extras.value = null;
  boundaryMatch.value = null;
  answer.value = null;
  ordinaryAnswer.value = null;
  error.value = "";
  partial.value = [];
  quickMsg.value = "";
  zoneAnswer.value = null;
  zoneAnswers.value = {};
  zoneErrors.value = {};
  coexistence.value = null;
  coexistenceLoaded.value = false;
}

// `immediate` does the job `onMounted(load)` used to, and also covers the case
// that was missed: a route-param change on the reused component instance.
watch(
  placeId,
  () => {
    resetForPlace();
    if (!placeId.value) return;
    void load();
  },
  { immediate: true },
);

/** A zone's neutral status — from that zone's own answer, never the place's. */
function zoneSemantic(zoneId: string): StatusKey {
  return answerStatusKey(zoneAnswers.value[zoneId]);
}

/** Expand a zone and resolve it for this visitor (cached after the first call). */
async function toggleZone(zoneId: string) {
  if (zoneAnswer.value === zoneId) {
    zoneAnswer.value = null;
    return;
  }
  zoneAnswer.value = zoneId;
  if (zoneAnswers.value[zoneId] || zoneErrors.value[zoneId]) return;
  try {
    const res = await client.accessAnswer(placeId.value, {
      animal: session.activePet?.species ?? "dog",
      service_role: queryServiceRole(),
      declared_role: session.activePet?.declared_role ?? null,
      zone_id: zoneId,
      action: "enter",
    });
    zoneAnswers.value = { ...zoneAnswers.value, [zoneId]: res };
  } catch {
    // an unresolved zone is reported as UNKNOWN, never guessed
    zoneErrors.value = { ...zoneErrors.value, [zoneId]: true };
  }
}

async function quickConfirm(ruleId: string, result: "still_valid" | "changed" | "uncertain") {
  quickMsg.value = "";
  try {
    await client.verify({
      place_id: placeId.value,
      rule_id: ruleId,
      result,
      note: "Quick Confirm（现场快捷确认）",
      proximity_verified: true,
      distance_bucket: "<100m",
      accuracy_bucket: "10-50m",
    });
    quickMsg.value =
      result === "still_valid"
        ? "已记录：规则仍有效 ✓"
        : result === "changed"
          ? "已记录：规则已变化，进入复核"
          : "已记录：不确定";
    verifications.value = await client.verifications(placeId.value);
  } catch (e) {
    quickMsg.value = e instanceof Error ? `需要登录后才能核验：${e.message}` : String(e);
  }
}

async function toggleWatch() {
  try {
    const mine = await client.myWatches();
    const existing = mine.find((w) => w.target_type === "place" && w.target_id === placeId.value);
    if (existing) {
      await client.unwatch(existing.id);
      watching.value = false;
    } else {
      await client.watch("place", placeId.value);
      watching.value = true;
    }
  } catch (e) {
    quickMsg.value = e instanceof Error ? `关注失败（需登录）：${e.message}` : String(e);
  }
}

async function disputeFirstRule() {
  const target = currentRules.value[0];
  if (!target) return;
  quickMsg.value = "";
  try {
    await client.submitDispute({
      target_type: "access_rule",
      target_id: target.id,
      reason_code: "rule_inaccurate",
      notice_text: "用户报告：现场规则与收录内容不一致（请补充现场情况）",
    });
    quickMsg.value = "异议已提交，进入人工复核流程";
  } catch (e) {
    quickMsg.value = e instanceof Error ? `提交失败（需登录）：${e.message}` : String(e);
  }
}

async function claimOperator() {
  quickMsg.value = "";
  try {
    await client.submitClaim({
      place_id: placeId.value,
      operator_id: "self-declared",
      verification_method: "operator_self_claim",
      evidence_refs: { note: "管理方认领（需人工核验）" },
    });
    quickMsg.value = "已提交管理方认领申请，等待人工核验";
  } catch (e) {
    quickMsg.value = e instanceof Error ? `认领提交失败（需登录）：${e.message}` : String(e);
  }
}
</script>

<template>
  <AppShell>
    <SkeletonList v-if="loading" :rows="4" />
    <StateMessage v-else-if="error" kind="ERROR" :description="`未能取得场所信息：${error}`">
      <template #action>
        <button class="primary" @click="load">重试</button>
      </template>
    </StateMessage>
    <StateMessage
      v-else-if="!place"
      kind="EMPTY"
      description="该场所尚未收录，或已被移除。未收录不代表该场所没有规则。"
    />
    <template v-else>
      <StateMessage
        v-if="partial.length"
        kind="PARTIAL"
        :description="`部分板块未能加载：${partial.join('、')}。已加载内容仍可查看，缺失部分不代表无规则。`"
      >
        <template #action>
          <button class="primary" @click="load">重新加载</button>
        </template>
      </StateMessage>

      <div class="panel">
        <h1>{{ place.canonical_name }}</h1>
        <div class="muted" style="margin-top: 4px">
          {{ placeTypeLabel(place.place_type) }} · {{ place.canonical_address ?? "地址未收录" }} ·
          生效规则 {{ prov.ruleCount }} 条
        </div>
        <div class="row" style="margin-top: 10px">
          <button @click="toggleWatch">
            {{ watching ? "已关注规则变化 ✓（点击取消）" : "关注此场所规则变化" }}
          </button>
          <RouterLink :to="`/place/${placeId}/why`">
            <button class="primary" data-testid="open-why">为什么是这个结果</button>
          </RouterLink>
        </div>
      </div>

      <!-- Section 1 — current answer -->
      <h2>1. 当前答案</h2>
      <div class="panel" data-testid="section-answer">
        <div v-if="ordinaryAnswer" class="sub-answer" data-testid="answer-ordinary">
          <div class="muted">普通宠物（基线）</div>
          <StatusBadge :semantic="answerStatusKey(ordinaryAnswer)" block />
          <div class="muted">{{ answerVerdictLabel(ordinaryAnswer) }}</div>
        </div>
        <div v-if="answer" class="sub-answer" data-testid="answer">
          <div class="muted">
            {{
              session.activePet ? `我的宠物：${session.activePet.display_name}` : "我的宠物：未设置"
            }}
            · 模式：{{
              session.mode === "with_pet"
                ? "带宠出行"
                : session.mode === "restrictions"
                  ? "普通宠物限制"
                  : session.mode === "service_dog"
                    ? "服务犬通行"
                    : "规则地图"
            }}
          </div>
          <StatusBadge :semantic="answerStatusKey(answer)" block />
          <div class="status" data-testid="answer-status">{{ answerVerdictLabel(answer) }}</div>
          <div v-if="answerConditionList.length" class="muted" data-testid="answer-conditions">
            条件：{{ answerConditionList.join(" · ") }}
          </div>
          <div
            v-if="answer.condition_evaluation.missing_inputs.length"
            class="muted"
            data-testid="answer-missing-inputs"
          >
            需要补充：{{
              answer.condition_evaluation.missing_inputs.join("、")
            }}（不猜测；现在不是「允许」）
          </div>
          <div
            v-if="answer.scope_summary.scope_level === 'none'"
            class="muted"
            data-testid="answer-uncovered"
          >
            本次查询范围内没有已发布规则 —— 未知 ≠ 允许。
          </div>
        </div>
        <div class="sub-answer" data-testid="answer-boundary">
          <div class="muted">我的共处边界</div>
          <template v-if="boundaryMatch">
            <div class="muted">
              符合 {{ boundaryMatch.summary.match }} · 冲突 {{ boundaryMatch.summary.conflict }} ·
              未知
              {{ boundaryMatch.summary.unknown }}
            </div>
            <div v-for="r in boundaryMatch.results" :key="r.attribute" class="zone-row">
              <span>{{ COEXISTENCE_LABELS[r.attribute] ?? r.attribute }}</span>
              <StatusBadge
                :semantic="
                  r.verdict === 'MATCH'
                    ? 'ALLOWED'
                    : r.verdict === 'CONFLICT'
                      ? 'RESTRICTED'
                      : 'UNKNOWN'
                "
              />
            </div>
            <div class="notice">{{ boundaryMatch.summary.note }}</div>
          </template>
          <div v-else class="muted">
            未设置共处边界。<RouterLink class="btn-inline" to="/boundary">前往设置</RouterLink>
          </div>
        </div>
        <div class="notice">
          来源：{{
            currentRules[0]
              ? (sourceMap.get(currentRules[0].source_id)?.issuer ?? "待收录")
              : "待收录"
          }}
          · 最近核验：{{ prov.latestVerified ? prov.latestVerified.slice(0, 10) : "暂无" }}
        </div>
        <!--
          Scope and provenance come from the unified answer model. The scope line
          exists so a zone-scoped rule is never read as a venue-wide verdict; the
          provenance line exists so a government platform relaying the operator
          is never rendered as the operator's own confirmation.
        -->
        <div v-if="answer" class="notice" data-testid="answer-scope">
          适用范围：{{
            answer.scope_summary.scope_level === "zone"
              ? (answer.scope_summary.zone?.name ?? "该区域")
              : answer.scope_summary.scope_level === "none"
                ? "尚无已发布规则覆盖本次查询（未知 ≠ 允许）"
                : answer.scope_summary.scope_level === "jurisdiction"
                  ? "辖区法规"
                  : "场所整体"
          }}
        </div>
        <div
          v-if="answer?.evidence_state.rules.length"
          class="notice"
          data-testid="answer-provenance"
        >
          {{ answer?.evidence_state.rules[0].provenance_statement }}
        </div>
      </div>

      <!-- v0.9-R1: Reality panel -- the observed layer of the passport (AC10) -->
      <RealityPanel :snapshot="coexistence" :loading="!coexistenceLoaded" />

      <!-- Section 2 -- where -->
      <h2>2. 哪里可以 / 不可以</h2>
      <div class="panel" data-testid="zones">
        <div v-if="!zones.length" class="muted">暂无分区域信息（信息不足 ≠ 允许）</div>
        <div v-for="z in zones" :key="z.id" class="zone-row">
          <span>
            {{ z.name }}
            <span v-if="z.floor_ref" class="tag" style="margin-left: 6px">{{ z.floor_ref }}</span>
            <span class="tag" style="margin-left: 6px">{{ z.zone_type }}</span>
          </span>
          <span>
            <template v-if="zoneAnswer === z.id">
              <StatusBadge :semantic="zoneSemantic(z.id)" />
              <span v-if="zoneErrors[z.id]" class="muted" style="margin-left: 6px">
                该分区未能取得结论
              </span>
            </template>
            <button
              style="padding: 4px 8px"
              :data-testid="`zone-toggle-${z.id}`"
              @click="toggleZone(z.id)"
            >
              {{ zoneAnswer === z.id ? "收起" : "查看" }}
            </button>
          </span>
        </div>
      </div>

      <!-- Section 3 — conditions -->
      <h2>3. 条件</h2>
      <div class="panel" data-testid="conditions">
        <div v-if="!conditions.length" class="muted">暂无明确条件（未收录条件 ≠ 无限制）</div>
        <div v-else class="row">
          <span v-for="c in conditions" :key="c" class="tag">{{ c }}</span>
        </div>
      </div>

      <!-- Section 4 — coexistence boundary -->
      <h2>4. 共处边界</h2>
      <div class="panel" data-testid="coexistence">
        <div v-if="!extras?.coexistence.length" class="muted">暂无共处边界结构化记录</div>
        <div v-for="c in extras?.coexistence ?? []" :key="c.id" class="zone-row">
          <span>{{ COEXISTENCE_LABELS[c.attribute] ?? c.attribute }}</span>
          <span class="muted"
            >{{ c.value
            }}<span v-if="c.verified_at"> · {{ c.verified_at.slice(0, 10) }}</span></span
          >
        </div>
        <div class="notice">共处边界是来自来源的空间事实，不对人作评价。</div>
      </div>

      <!-- Section 5 — how to get in -->
      <h2>5. 怎么进入</h2>
      <div class="panel" data-testid="entrances">
        <div v-if="!extras?.entrances.length && !extras?.access_paths.length" class="muted">
          暂无入口 / 路径信息
        </div>
        <div v-for="e in extras?.entrances ?? []" :key="e.id" class="zone-row">
          <span
            >{{ e.name
            }}<span class="tag" style="margin-left: 6px">{{
              ENTRANCE_LABELS[e.entrance_type] ?? e.entrance_type
            }}</span></span
          >
          <span class="muted">{{ e.access_notes ?? "" }}</span>
        </div>
        <div v-for="p in extras?.access_paths ?? []" :key="p.id" class="zone-row">
          <span>{{ p.from_node }} → {{ p.to_node }}</span>
          <span class="muted">{{ p.name }}</span>
        </div>
      </div>

      <!-- Section 6 — facilities -->
      <h2>6. 设施</h2>
      <div class="panel" data-testid="amenities">
        <div v-if="!extras?.amenities.length" class="muted">暂无设施记录</div>
        <div class="row">
          <span v-for="a in extras?.amenities ?? []" :key="a.id" class="tag">
            {{ AMENITY_LABELS[a.amenity_type] ?? a.amenity_type }} · {{ a.status }}
          </span>
        </div>
      </div>

      <!-- Section 7 — sources & freshness -->
      <h2>7. 来源与时效</h2>
      <div class="panel" data-testid="sources">
        <div v-if="!currentRules.length" class="muted">暂无已收录规则</div>
        <div v-for="r in currentRules" :key="r.id" class="zone-row">
          <span>
            {{ sourceMap.get(r.source_id)?.issuer ?? "来源 " + r.source_id.slice(0, 8) }}
            <SourceBadge :source-type="sourceMap.get(r.source_id)?.source_type" />
            <span v-if="r.rule_layer" class="tag" style="margin-left: 6px">
              {{ layerLabel[r.rule_layer] ?? r.rule_layer }}
            </span>
            <span v-if="r.mandatory_level" class="tag" style="margin-left: 4px">
              {{ forceLabel[r.mandatory_level] ?? r.mandatory_level }}
            </span>
          </span>
          <span>
            <StatusBadge :effect="r.effect" />
            <StatusBadge v-if="isStale(r)" semantic="STALE" />
          </span>
        </div>
        <!--
          Per-rule provenance, straight from the unified answer. Rendered verbatim
          rather than re-worded: `source_type_semantics` is only filled in for
          source types a named reviewer actually adjudicated, and when it is empty
          the raw enum value is what the reader sees.
        -->
        <div
          v-if="answer?.evidence_state.rules.length"
          class="provenance"
          data-testid="source-provenance"
        >
          <div v-for="e in answer.evidence_state.rules" :key="e.rule_id" class="muted">
            · {{ e.provenance_statement }}
          </div>
        </div>
        <div
          v-if="answer?.normative_result.compliance_state === 'POTENTIAL_CONFLICT'"
          class="notice"
        >
          来源存在不一致：<StatusBadge semantic="CONFLICT" />
          已保留全部规则，按最严结论展示，等待复核。
        </div>
        <div v-if="answer?.normative_result.compliance_state === 'REVIEW_REQUIRED'" class="notice">
          部分规则缺少分层信息，需要人工复核（不猜测）。
        </div>
        <div v-if="answer?.conflict_state.suppressed.length" class="notice">
          被遮蔽的规则（{{ answer.conflict_state.suppressed.length }} 条）：
          <div v-for="s in answer.conflict_state.suppressed" :key="s.rule" class="muted">
            · {{ s.reason }}
          </div>
        </div>
      </div>

      <!-- Section 8 — field records -->
      <h2>8. 现场记录</h2>
      <div class="panel" data-testid="observations">
        <div class="notice" data-testid="observation-disclaimer">
          现场记录 ≠ 场所正式政策。以下为用户/现场记录，不构成规则。
        </div>
        <div v-for="o in observations" :key="o.id" class="zone-row">
          <span
            >{{ o.occurred_at.slice(0, 10) }} · {{ o.animal_scope }} {{ o.observed_action }}</span
          >
          <span class="muted">{{ o.staff_action }}</span>
        </div>
        <div v-if="!observations.length" class="muted">暂无现场记录</div>
      </div>

      <!-- Section 9 — history -->
      <h2>9. 历史版本</h2>
      <div class="panel" data-testid="history">
        <div v-if="!historyRules.length" class="muted">暂无历史版本</div>
        <div v-for="r in historyRules" :key="r.id" class="zone-row">
          <span>{{ r.animal_scope }} · {{ r.action }}</span>
          <span class="muted">
            <StatusBadge :effect="r.effect" />
            <span class="tag" style="margin-left: 6px">{{ r.status }}</span>
          </span>
        </div>
      </div>

      <!-- Section 10 — corrections -->
      <h2>10. 纠错 / 补充</h2>
      <div class="panel" data-testid="corrections">
        <div class="row">
          <RouterLink :to="`/contribute/${placeId}`" class="pill">报告规则 / 贡献</RouterLink>
          <button @click="disputeFirstRule">对此处规则提出异议</button>
          <button @click="claimOperator">我是管理方（认领）</button>
        </div>
        <div class="muted" style="margin-top: 8px">
          管理方声明与用户观察并存：认领后管理方规则标注来源，用户仍可提交现场记录。
        </div>
      </div>

      <!-- Quick confirm -->
      <h2>快速确认</h2>
      <div class="panel" data-testid="quick-confirm">
        <div class="muted">页面显示当前规则，目前仍然如此吗？</div>
        <div class="row" style="margin-top: 8px">
          <button @click="quickConfirm(currentRules[0]?.id ?? '', 'still_valid')">仍然如此</button>
          <button @click="quickConfirm(currentRules[0]?.id ?? '', 'changed')">已变化</button>
          <button @click="quickConfirm(currentRules[0]?.id ?? '', 'uncertain')">不确定</button>
        </div>
        <div v-if="quickMsg" class="notice" data-testid="quick-msg">{{ quickMsg }}</div>
      </div>
    </template>
  </AppShell>
</template>
