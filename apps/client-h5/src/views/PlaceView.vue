<script setup lang="ts">
/**
 * Place Detail — Dossier + Decision Inspector (Design Freeze §9; Goal §34).
 *
 * VISUAL FIDELITY (Goal §3.2): the dossier reads as a *judgment document*,
 * not a schema dump. Section order is frozen: Identity → Current Query +
 * Decision → Recent Reality → Space/Zones → Rules+Conditions →
 * Evidence/Provenance → Staff/Facilities → History/Correction (sank last).
 * All raw enums (zone_type, animal_scope, action, status, floor…) are mapped
 * through the shared consumer label mapper — they never reach visible text.
 * History/provenance are secondary and use progressive disclosure on mobile.
 *
 * Data comes from the public place endpoints; the structured extras
 * (coexistence, amenities, entrances, paths, events) come from
 * /places/{id}/extras, and the normative answer from the explainable
 * resolver. The ONE snapshot for the Reality panel comes from the consumer
 * repository (CoexistenceSnapshot SSOT).
 */
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { type StatusKey } from "@petaccess/design-tokens";
import {
  client,
  freshnessLabel,
  conditionLabel,
  placeTypeLabel,
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
import DecisionInspector from "../components/domain/DecisionInspector.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import SkeletonList from "../components/SkeletonList.vue";
import SourceBadge from "../components/SourceBadge.vue";
import StateMessage from "../components/StateMessage.vue";
import StatusBadge from "../components/StatusBadge.vue";
import EvidenceMeta from "../components/domain/EvidenceMeta.vue";
import EvidenceStatus from "../components/domain/EvidenceStatus.vue";
import FreshnessStatus from "../components/domain/FreshnessStatus.vue";
import {
  animalScopeLabel,
  amenityLabel,
  coexistenceLabel,
  coexistenceValueLabel,
  entranceLabel,
  facilityStateLabel,
  mandatoryLevelLabel,
  observedActionLabel,
  ruleLayerLabel,
  ruleStatusLabel,
  ruleSubjectLine,
  sourceLabel,
  staffActionLabel,
  zoneConsumerLine,
} from "../consumer/labels";
import { answerConditions, answerStatusKey, answerVerdictLabel } from "../answer";
import { presentDescription } from "../errors";
import { useBreakpoint } from "../composables/useBreakpoint";
import { snapshotFor } from "../consumer/repository";
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

const { desktop: isDesktop } = useBreakpoint();
const speciesLabel = computed(() => {
  const s = session.activePet?.species ?? "dog";
  if (session.activePet?.service_role === "working") return "服务犬";
  return s === "dog" ? "普通犬" : s === "cat" ? "猫" : "其他宠物";
});

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

/** M4 B3 — passport evidence visual language (verified/pending/disputed/historical). */
const passportEvidence = computed(() => {
  const s = coexistence.value?.evidence_summary;
  if (!s) return null;
  const raw = s.reality_verification_state;
  const state: "verified" | "pending" | "disputed" | "historical" =
    raw === "VERIFIED"
      ? "verified"
      : raw === "DISPUTED"
        ? "disputed"
        : raw === "HISTORICAL"
          ? "historical"
          : "pending";
  return {
    state,
    ruleCount: s.rule_evidence.length,
    realityCount: s.reality_evidence_count,
    sources: s.reality_distinct_source_count,
  };
});
/** §12.4 — 「进入前需满足」, assembled by the answer adapter. */
const answerConditionList = computed(() => answerConditions(answer.value));

const sourceMap = computed(() => {
  const m = new Map<string, SourceView>();
  for (const s of sources.value) m.set(s.id, s);
  return m;
});
const prov = computed(() => {
  const current = currentRules.value;
  const latest = current
    .map((r) => r.last_verified_at)
    .filter((v): v is string => Boolean(v))
    .sort()
    .at(-1);
  return {
    ruleCount: current.length,
    latestVerified: latest ?? null,
  };
});

const currentRules = computed(() => rules.value.filter((r) => r.status === "current"));
const historyRules = computed(() => rules.value.filter((r) => r.status !== "current"));

/** Every distinct condition across current rules, human-labelled. */
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
    error.value = presentDescription(e);
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
  // M3.1: routed through the consumer repository so rows and the dossier share
  // the SAME cached snapshot and query context (SSOT, UI_RECONSTRUCTION_GOAL
  // §8.1) — never a second client-side resolver.
  try {
    coexistence.value = (await snapshotFor(placeId.value)).snapshot;
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
    quickMsg.value = `需要登录后才能核验：${presentDescription(e)}`;
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
    quickMsg.value = `关注失败（需登录）：${presentDescription(e)}`;
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
    quickMsg.value = `提交失败（需登录）：${presentDescription(e)}`;
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
    quickMsg.value = `认领提交失败（需登录）：${presentDescription(e)}`;
  }
}

const historyOpen = ref(false);

/**
 * O6 capture-state integrity (v0.2.3 §14): page/state/fixture narrated from
 * ACTUAL loaded data. `unknown` covers BOTH a missing answer and an answer
 * whose honest verdict is UNKNOWN (信息不足) — never a pretend "ready".
 */
const placeState = computed<string>(() => {
  if (error.value || !place.value) return "unavailable";
  if (loading.value) return "loading";
  if (!answer.value) return "unknown";
  return answerStatusKey(answer.value) === "UNKNOWN" ? "unknown" : "ready";
});
const placeFixture = computed<string>(() => {
  if (placeState.value === "ready") return "place-ready-v1";
  if (placeState.value === "unknown") return "place-unknown-v1";
  return "place-state-v1";
});
</script>
<template>
  <div
    class="place-workspace"
    data-testid="place-workspace"
    data-ui="place-shell"
    data-ui-page="place"
    :data-ui-state="placeState"
    :data-ui-fixture="placeFixture"
    :data-ui-entity-id="placeId"
  >
    <QueryContextBar />
    <div class="place-workspace__body" :class="{ 'place-workspace__body--split': isDesktop }">
      <!-- main dossier -->
      <main class="place-dossier" data-ui="place-dossier" aria-label="场所档案">
        <SkeletonList v-if="loading" :rows="4" />
        <StateMessage v-else-if="error" kind="ERROR" title="未能取得场所信息" :description="error">
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

          <!-- 1. Identity -->
          <header class="place-dossier__head" data-ui="place-identity">
            <h1 class="place-dossier__name" data-ui="place-name">{{ place.canonical_name }}</h1>
            <p class="muted place-dossier__meta">
              {{ placeTypeLabel(place.place_type) }} ·
              {{ place.canonical_address ?? "地址未收录" }}
            </p>
            <div class="row place-dossier__actions">
              <button @click="toggleWatch">
                {{ watching ? "已关注规则变化 ✓（点击取消）" : "关注此场所规则变化" }}
              </button>
              <RouterLink :to="`/place/${placeId}/why`">
                <button class="primary" data-testid="open-why">为什么是这个结果</button>
              </RouterLink>
            </div>
          </header>

          <!-- 2. Current Query + Decision -->
          <section class="place-section" data-testid="section-answer" data-ui="place-decision">
            <h2 class="place-section__title">当前结论</h2>
            <div v-if="answer" class="sub-answer sub-answer--mine" data-testid="answer">
              <div class="sub-answer__context muted">
                {{
                  session.activePet
                    ? `我的宠物：${session.activePet.display_name}`
                    : "我的宠物：未设置"
                }}
                · 查询：{{ speciesLabel }} · 进入 · 公共区域
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
            <div v-if="ordinaryAnswer" class="sub-answer" data-testid="answer-ordinary">
              <div class="muted">普通宠物（基线）</div>
              <StatusBadge :semantic="answerStatusKey(ordinaryAnswer)" block />
              <div class="muted">{{ answerVerdictLabel(ordinaryAnswer) }}</div>
            </div>
            <div class="sub-answer" data-testid="answer-boundary">
              <div class="muted">我的共处边界</div>
              <template v-if="boundaryMatch">
                <div class="muted">
                  符合 {{ boundaryMatch.summary.match }} · 冲突
                  {{ boundaryMatch.summary.conflict }} · 未知
                  {{ boundaryMatch.summary.unknown }}
                </div>
                <div v-for="r in boundaryMatch.results" :key="r.attribute" class="zone-row">
                  <span>{{ coexistenceLabel(r.attribute) }}</span>
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
                sourceLabel(
                  currentRules[0]
                    ? (sourceMap.get(currentRules[0].source_id)?.issuer ?? null)
                    : null,
                  currentRules.length > 0,
                )
              }}
              · 最近核验：{{ prov.latestVerified ? prov.latestVerified.slice(0, 10) : "暂无" }}
            </div>
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
          </section>
          <!-- 3. Recent Reality -->
          <section class="place-section" data-ui="place-reality">
            <RealityPanel
              :snapshot="coexistence"
              :loading="!coexistenceLoaded"
              :place-id="placeId"
            />
          </section>

          <section class="place-section" data-testid="zones" data-ui="place-zones">
            <h2 class="place-section__title">空间与区域</h2>
            <p v-if="!zones.length" class="muted">暂无分区域信息（信息不足 ≠ 允许）</p>
            <div v-for="z in zones" :key="z.id" class="zone-row" data-ui="zone-row">
              <span class="zone-row__name">
                {{ zoneConsumerLine(z) }}
              </span>
              <span class="zone-row__control">
                <template v-if="zoneAnswer === z.id">
                  <StatusBadge :semantic="zoneSemantic(z.id)" />
                  <span v-if="zoneErrors[z.id]" class="muted" style="margin-left: 6px">
                    该分区未能取得结论
                  </span>
                </template>
                <button :data-testid="`zone-toggle-${z.id}`" @click="toggleZone(z.id)">
                  {{ zoneAnswer === z.id ? "收起" : "查看" }}
                </button>
              </span>
            </div>
          </section>

          <!-- 5. Rules + Conditions -->
          <section class="place-section" data-testid="conditions" data-ui="place-rules">
            <h2 class="place-section__title">规则依据</h2>
            <div v-if="!currentRules.length" class="muted">
              暂无可靠规则结论（未收录 ≠ 没有规则）。
            </div>
            <div v-for="r in currentRules" :key="r.id" class="zone-row" data-testid="rule-row">
              <span class="zone-row__name">
                {{ ruleSubjectLine(r.animal_scope, r.action) }}
                <span v-if="r.rule_layer" class="tag zone-row__layer">
                  {{ ruleLayerLabel(r.rule_layer) }}
                </span>
                <span v-if="r.mandatory_level" class="tag zone-row__force">
                  {{ mandatoryLevelLabel(r.mandatory_level) }}
                </span>
              </span>
              <span class="zone-row__control">
                <StatusBadge :effect="r.effect" />
                <StatusBadge v-if="isStale(r)" semantic="STALE" />
              </span>
            </div>

            <h3 class="place-section__subtitle">进入前需满足</h3>
            <div v-if="!conditions.length" class="muted">暂无明确条件（未收录条件 ≠ 无限制）</div>
            <div v-else class="row">
              <span v-for="c in conditions" :key="c" class="tag">{{ c }}</span>
            </div>
          </section>

          <!-- 6. Evidence / Provenance -->
          <section class="place-section" data-testid="sources" data-ui="place-evidence">
            <h2 class="place-section__title">来源与时效</h2>
            <div
              v-if="passportEvidence"
              class="row"
              data-testid="passport-evidence"
              style="margin: 8px 0"
            >
              <EvidenceStatus :state="passportEvidence.state" />
              <span class="muted">
                <EvidenceMeta
                  :evidence-count="passportEvidence.ruleCount + passportEvidence.realityCount"
                  :distinct-source-count="passportEvidence.sources"
                />
              </span>
              <FreshnessStatus :last-verified-at="prov.latestVerified" />
            </div>
            <div v-if="!currentRules.length" class="muted">
              暂无可靠规则结论（未收录 ≠ 没有规则）。
            </div>
            <div v-for="r in currentRules" :key="r.id" class="zone-row" data-testid="rule-source">
              <span class="zone-row__name">
                {{ sourceLabel(sourceMap.get(r.source_id)?.issuer ?? null, true) }}
                <SourceBadge :source-type="sourceMap.get(r.source_id)?.source_type" />
              </span>
              <span class="muted">
                {{ r.last_verified_at ? freshnessLabel(r.last_verified_at) : "尚未核验" }}
              </span>
            </div>
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
            <div
              v-if="answer?.normative_result.compliance_state === 'REVIEW_REQUIRED'"
              class="notice"
            >
              部分规则缺少分层信息，需要人工复核（不猜测）。
            </div>
          </section>

          <!-- 7. Staff / Facilities -->
          <section class="place-section" data-testid="coexistence">
            <h2 class="place-section__title">共处边界</h2>
            <div v-if="!extras?.coexistence.length" class="muted">暂无共处边界结构化记录</div>
            <div v-for="c in extras?.coexistence ?? []" :key="c.id" class="zone-row">
              <span>{{ coexistenceLabel(c.attribute) }}</span>
              <span class="muted">
                {{ coexistenceValueLabel(c.value)
                }}<span v-if="c.verified_at"> · {{ c.verified_at.slice(0, 10) }}</span>
              </span>
            </div>
            <div class="notice">共处边界是来自来源的空间事实，不对人作评价。</div>
          </section>

          <section class="place-section" data-testid="entrances">
            <h2 class="place-section__title">怎么进入</h2>
            <div v-if="!extras?.entrances.length && !extras?.access_paths.length" class="muted">
              暂无入口 / 路径信息
            </div>
            <div v-for="e in extras?.entrances ?? []" :key="e.id" class="zone-row">
              <span class="zone-row__name">
                {{ e.name
                }}<span class="tag" style="margin-left: 6px">{{
                  entranceLabel(e.entrance_type)
                }}</span>
              </span>
              <span class="muted">{{ e.access_notes ?? "" }}</span>
            </div>
            <div v-for="p in extras?.access_paths ?? []" :key="p.id" class="zone-row">
              <span>{{ p.from_node }} → {{ p.to_node }}</span>
              <span class="muted">{{ p.name }}</span>
            </div>
          </section>

          <section class="place-section" data-testid="amenities">
            <h2 class="place-section__title">设施</h2>
            <div v-if="!extras?.amenities.length" class="muted">暂无设施记录</div>
            <div class="row">
              <span v-for="a in extras?.amenities ?? []" :key="a.id" class="tag">
                {{ amenityLabel(a.amenity_type) }} · {{ facilityStateLabel(a.status) }}
              </span>
            </div>
          </section>
          <!-- 8. History / Correction (sank; disclosure on mobile) -->
          <section class="place-section" data-testid="history" data-ui="place-history">
            <h2 class="place-section__title">历史版本与纠错</h2>
            <div v-if="!historyRules.length" class="muted">暂无历史版本</div>
            <div v-else>
              <button
                type="button"
                class="disclosure-toggle"
                :aria-expanded="historyOpen"
                @click="historyOpen = !historyOpen"
              >
                {{ historyOpen ? "收起历史版本" : "查看全部历史版本" }}
                <span class="disclosure-toggle__count">{{ historyRules.length }}</span>
              </button>
              <div v-show="historyOpen || isDesktop" class="history-list">
                <div v-for="r in historyRules" :key="r.id" class="zone-row">
                  <span class="zone-row__name">{{
                    ruleSubjectLine(r.animal_scope, r.action)
                  }}</span>
                  <span class="muted">
                    <StatusBadge :effect="r.effect" />
                    <span class="tag" style="margin-left: 6px">{{
                      ruleStatusLabel(r.status)
                    }}</span>
                  </span>
                </div>
              </div>
            </div>
            <div class="row" style="margin-top: 12px">
              <RouterLink :to="`/contribute/${placeId}`" class="pill">报告规则 / 贡献</RouterLink>
              <button @click="disputeFirstRule">对此处规则提出异议</button>
              <button @click="claimOperator">我是管理方（认领）</button>
            </div>
            <div class="muted" style="margin-top: 8px">
              管理方声明与用户观察并存：认领后管理方规则标注来源，用户仍可提交现场记录。
            </div>
          </section>

          <!-- Quick confirm (secondary, kept below the dossier) -->
          <section class="place-section" data-testid="quick-confirm">
            <h2 class="place-section__title">快速确认</h2>
            <div class="muted">页面显示当前规则，目前仍然如此吗？</div>
            <div class="row" style="margin-top: 8px">
              <button @click="quickConfirm(currentRules[0]?.id ?? '', 'still_valid')">
                仍然如此
              </button>
              <button @click="quickConfirm(currentRules[0]?.id ?? '', 'changed')">已变化</button>
              <button @click="quickConfirm(currentRules[0]?.id ?? '', 'uncertain')">不确定</button>
            </div>
            <div v-if="quickMsg" class="notice" data-testid="quick-msg">{{ quickMsg }}</div>
          </section>

          <!-- 现场记录 (secondary fact block, ≠ policy) -->
          <section class="place-section" data-testid="observations">
            <h2 class="place-section__title">现场记录</h2>
            <div class="notice" data-testid="observation-disclaimer">
              现场记录 ≠ 场所正式政策。以下为用户/现场记录，不构成规则。
            </div>
            <div v-for="o in observations" :key="o.id" class="zone-row">
              <span class="zone-row__name">
                {{ o.occurred_at.slice(0, 10) }} · {{ animalScopeLabel(o.animal_scope) }} ·
                {{ observedActionLabel(o.observed_action) }}
              </span>
              <span class="muted">{{ staffActionLabel(o.staff_action) }}</span>
            </div>
            <div v-if="!observations.length" class="muted">
              暂无足够现场记录（暂无记录 ≠ 没有动物）。
            </div>
          </section>
        </template>
      </main>

      <!-- sticky decision inspector (desktop only) -->
      <aside
        v-if="isDesktop && place"
        class="place-inspector"
        data-ui="place-inspector"
        aria-label="当前决策"
      >
        <DecisionInspector
          variant="place"
          :place="{ ...place, canonical_address: place.canonical_address ?? null }"
          :answer="answer"
          :answer-error="!coexistenceLoaded && !answer"
          :reality="coexistence?.reality_answer ?? null"
          :reality-error="coexistenceLoaded && !coexistence?.reality_answer"
          :snapshot="coexistence"
          :species-label="speciesLabel"
        />
      </aside>
    </div>
  </div>
</template>

<style scoped>
.place-workspace {
  min-height: 100%;
}

.place-workspace__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-6);
  padding: var(--pa-space-4);
  max-width: var(--pa-layout-content-narrow);
  margin: 0 auto;
}

@media (min-width: 768px) {
  /* v0.2.3 §27：main dossier x≈100 w∈820–860 + inspector x≈1010–1040
   * w∈320–350 sticky。居中 max-width 会让 dossier 漂到中间，必须全出血
   * 左对齐；dossier 列宽 cap 860px。 */
  .place-workspace__body--split {
    flex-direction: row;
    align-items: flex-start;
    max-width: none;
    padding: var(--pa-space-4) var(--pa-space-6);
  }

  .place-dossier {
    flex: 1 1 auto;
    min-width: 0;
    max-width: 860px;
  }

  .place-inspector {
    flex: 0 0 var(--pa-layout-inspector);
    min-width: 0;
    position: sticky;
    top: var(--pa-space-4);
  }
}

.place-dossier__head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  padding-bottom: var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
  margin-bottom: var(--pa-space-5);
}

.place-dossier__name {
  margin: 0;
  /* v0.2.3 §28：identity name = page identity 28/36/650。 */
  font-size: var(--pa-font-size-28);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-36);
  color: var(--pa-color-text-primary);
}

.place-dossier__meta {
  margin: 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-muted);
}

.place-dossier__actions {
  margin-top: var(--pa-space-2);
}

/* Sections: divider-led rhythm, not a flat wall of equal-weight panels. */
.place-section {
  margin-bottom: var(--pa-space-5);
}

.place-section__title {
  margin: 0 0 var(--pa-space-3);
  /* v0.2.3 §31：section title 18/26/600。 */
  font-size: var(--pa-font-size-18);
  font-weight: var(--pa-font-weight-600);
  line-height: var(--pa-line-height-26);
  color: var(--pa-color-text-primary);
}

.place-section__subtitle {
  margin: var(--pa-space-4) 0 var(--pa-space-2);
  font-size: var(--pa-font-size-17);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-secondary);
}

/* Current query + decision: flat divider-led blocks (Freeze §5 — NOT cards). */
.sub-answer {
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.sub-answer:last-child {
  border-bottom: none;
}

.sub-answer--mine {
  border-left: var(--pa-border-width-strong) solid var(--pa-color-accent);
  background: var(--pa-color-surface-warm);
  border-radius: var(--pa-radius-md);
  padding: var(--pa-space-3) var(--pa-space-4);
}

/* v0.2.3 §29：primary decision 30/38/650（blueprint §18）。 */
.sub-answer .status {
  font-size: var(--pa-font-size-30);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-38);
  margin: var(--pa-space-1) 0;
}

.sub-answer__context {
  margin: 0 0 var(--pa-space-1);
}

/* v0.2.3 §32：zone rows —— consumer names only，height 48–56，divider rows。 */
.zone-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--pa-space-3);
  min-height: 48px;
  max-height: 56px;
  padding: var(--pa-space-2) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.zone-row:last-child {
  border-bottom: none;
}

.zone-row__name {
  display: inline-flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--pa-space-1);
  font-size: var(--pa-font-size-base);
}

.zone-row__control {
  display: inline-flex;
  align-items: center;
  gap: var(--pa-space-2);
  flex-shrink: 0;
}

.disclosure-toggle {
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-md);
  padding: var(--pa-space-2) 0;
  cursor: pointer;
}

.disclosure-toggle__count {
  margin-left: var(--pa-space-1);
  color: var(--pa-color-text-muted);
}

.history-list {
  margin-top: var(--pa-space-1);
}

.provenance {
  margin-top: var(--pa-space-3);
}

@media (max-width: 767px) {
  /* v0.2.3 §18 mobile：page identity 23/31/650 · primary decision 24/32/650。 */
  .place-dossier__name {
    font-size: var(--pa-font-size-23);
    font-weight: var(--pa-font-weight-650);
    line-height: var(--pa-line-height-31);
  }

  .sub-answer .status {
    font-size: var(--pa-font-size-24);
    font-weight: var(--pa-font-weight-650);
    line-height: var(--pa-line-height-32);
  }
}
</style>
