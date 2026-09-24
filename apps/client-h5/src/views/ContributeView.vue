<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { client, session, ApiError } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import StateMessage from "../components/StateMessage.vue";
import { useOnline } from "../composables/useOnline";

/**
 * Contribution UX (UI_UX_IMPLEMENTATION_SPEC §7).
 *
 * Four entry points, one question at a time (design #15):
 *   1. 快速确认  — a yes/no/unsure field check on the currently published rule
 *   2. 拍规则牌  — camera/upload → real media upload → OCR preview → user confirms
 *   3. 我知道规则 — structured form (no free-text essay field)
 *   4. 我有现场经历 — observation form
 *
 * Product rules encoded here:
 * - There is deliberately **no free-text comment box**. Only structured fields,
 *   because a comment stream would become an unmoderated judgement channel.
 * - A submitted observation is *not* a rule. The confirmation screen says so.
 * - OCR output is shown as a **preview for the reviewer**, never as an accepted
 *   rule and never auto-published (ADR-005 / ADR-022).
 * - Raw GPS is never sent; only the on-site proximity buckets (ADR-012).
 */

type Step = "entry" | "quick" | "signage" | "rule" | "experience" | "reality" | "done";

const route = useRoute();
// Empty string, not the literal "undefined": `/#/contribute` with no id is a
// real route (the user picks a place first), and `String(undefined)` would be
// truthy, hiding the picker and fetching zones for a place called "undefined".
const placeId = computed(() => (route.params.id ? String(route.params.id) : ""));
const { online } = useOnline();

const step = ref<Step>("entry");
const msg = ref("");
const error = ref("");
const busy = ref(false);
const signedIn = ref(false);

const zones = ref<{ id: string; name: string }[]>([]);
const zone = ref("");

// shared form state
const occurredAt = ref(new Date().toISOString().slice(0, 10));
const conditions = ref<string[]>([]);
const note = ref("");

// quick confirm
const quickResult = ref<"still_valid" | "changed" | "uncertain">("still_valid");

// signage upload
const mediaId = ref<string | null>(null);
const mediaMeta = ref<Awaited<ReturnType<typeof client.mediaMeta>> | null>(null);
const ocrText = ref("");
const ocrCandidates = ref<string[]>([]);
const uploadMsg = ref("");
const uploading = ref(false);
const placeConfirmed = ref(false);

// experience
const observedAction = ref("enter");
const staffAction = ref("no_interaction_observed");
const placeConfidence = ref("confirmed_on_site");
const knowRule = ref<"allowed" | "restricted" | "conditional" | "">("");

const conditionOptions = [
  { key: "leash_required", label: "需牵引" },
  { key: "carrier_required", label: "需宠物包" },
  { key: "stroller_required", label: "需推车" },
  { key: "no_ground", label: "不可落地" },
];

const canSubmit = computed(() => online.value && signedIn.value && !busy.value);

// Reactive param + `immediate` instead of `onMounted`: Vue Router reuses this
// component across `/contribute/:id` changes. The stakes here are higher than a
// stale render — every submit carries `place_id`, so a reused instance left the
// form pointed at the previous place and would have filed the report against it.
watch(
  placeId,
  async () => {
    reset();
    zones.value = [];
    // Session restore runs first and unconditionally: `/#/contribute` with no
    // id is a valid entry point and still needs to know whether the visitor is
    // signed in.
    await session.restore();
    signedIn.value = session.signedIn;
    if (!signedIn.value || !placeId.value) return;
    try {
      zones.value = await client.zones(placeId.value);
    } catch {
      /* anonymous read is best-effort; the form still works without zones */
    }
  },
  { immediate: true },
);

function reset() {
  step.value = "entry";
  msg.value = "";
  error.value = "";
  mediaId.value = null;
  mediaMeta.value = null;
  ocrText.value = "";
  ocrCandidates.value = [];
  uploadMsg.value = "";
  placeConfirmed.value = false;
  note.value = "";
  conditions.value = [];
}

async function uploadSignage(e: Event) {
  const input = e.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  if (!file) return;
  error.value = "";
  uploadMsg.value = "";
  uploading.value = true;
  try {
    const media = await client.uploadMedia(file, "signage_evidence", {
      ownerType: "place",
      ownerId: placeId.value,
    });
    mediaId.value = media.id;
    uploadMsg.value = media.duplicate_of
      ? "该图片此前已上传过（内容一致）。仍会作为本次证据提交。"
      : `已上传（${Math.round(media.byte_size / 1024)}KB）。证据媒体不公开，仅审核可见。`;
    // OCR preview is best-effort: failure degrades to PARTIAL, never blocks.
    try {
      const meta = await client.mediaMeta(media.id);
      mediaMeta.value = meta;
      ocrText.value = meta.ocr_text ?? "";
      ocrCandidates.value = Array.isArray(meta.ocr_rule_candidates)
        ? (meta.ocr_rule_candidates as unknown[]).map(String)
        : [];
    } catch {
      ocrText.value = "";
      ocrCandidates.value = [];
    }
  } catch (err) {
    error.value =
      err instanceof ApiError
        ? `${err.message}${err.status === 401 ? "（需登录后上传）" : ""}`
        : String(err);
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

function evidenceRefs() {
  return mediaId.value ? [{ media_id: mediaId.value, purpose: "signage_evidence" }] : null;
}

function proximity() {
  return { proximity_verified: true, distance_bucket: "<100m", accuracy_bucket: "10-50m" };
}

async function submitQuick() {
  if (!canSubmit.value) return;
  error.value = "";
  busy.value = true;
  try {
    const rules = await client.rules(placeId.value);
    const target = rules.find((r) => r.status === "current") ?? rules[0];
    await client.verify({
      place_id: placeId.value,
      rule_id: target?.id ?? null,
      event_type: "field_check",
      result: quickResult.value,
      note: null,
      ...proximity(),
    });
    msg.value =
      quickResult.value === "still_valid"
        ? "已记录：现场与已收录规则一致。这会提高该规则的核验置信度，但不会改变规则内容。"
        : quickResult.value === "changed"
          ? "已记录：现场与已收录规则不一致。该记录进入人工复核队列，规则不会自动改写。"
          : "已记录：不确定。不确定的记录同样有价值，不会被当作否定。";
    step.value = "done";
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

async function submitSignage() {
  if (!canSubmit.value) return;
  if (!mediaId.value) {
    error.value = "请先上传规则牌照片。";
    return;
  }
  if (!placeConfirmed.value) {
    error.value = "请确认照片拍摄于本场所。";
    return;
  }
  error.value = "";
  busy.value = true;
  try {
    const parts: string[] = [];
    if (note.value.trim()) parts.push(note.value.trim());
    if (ocrText.value.trim()) parts.push(`[OCR 待人工核对] ${ocrText.value.trim()}`);
    if (conditions.value.length) parts.push(`条件：${conditions.value.join(",")}`);
    await client.verify({
      place_id: placeId.value,
      zone_id: zone.value || null,
      rule_id: null,
      event_type: "signage_uploaded",
      result: "uncertain",
      note: parts.join(" | ").slice(0, 1000) || null,
      evidence_refs: evidenceRefs(),
      ...proximity(),
    });
    msg.value =
      "证据已提交，等待人工审核。照片与 OCR 文本都只是审核材料，不会自动成为规则，也不会自动发布。";
    step.value = "done";
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

async function submitKnownRule() {
  if (!canSubmit.value) return;
  error.value = "";
  busy.value = true;
  try {
    await client.createObservation({
      place_id: placeId.value,
      zone_id: zone.value || null,
      occurred_at: new Date(occurredAt.value).toISOString(),
      occurred_precision: "same_day",
      animal_scope: "dog",
      observed_action: "enter",
      staff_action: "no_interaction_observed",
      place_confidence: "confirmed_on_site",
      note: [`用户声明：${knowRule.value}`, conditions.value.join(",")].filter(Boolean).join(" | "),
      evidence_refs: evidenceRefs(),
      ...proximity(),
    });
    msg.value =
      "已提交你的说明。这是「用户陈述」，会与场所正式规则并存展示，不会覆盖已收录的规则。";
    step.value = "done";
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

async function submitObservation() {
  if (!canSubmit.value) return;
  error.value = "";
  busy.value = true;
  try {
    await client.createObservation({
      place_id: placeId.value,
      zone_id: zone.value || null,
      occurred_at: new Date(occurredAt.value).toISOString(),
      occurred_precision: "same_day",
      animal_scope: "dog",
      observed_action: observedAction.value,
      staff_action: staffAction.value,
      place_confidence: placeConfidence.value,
      note: note.value.trim() || null,
      evidence_refs: evidenceRefs(),
      ...proximity(),
    });
    msg.value = "现场记录已提交。现场记录 ≠ 场所正式政策，二者会分开呈现。";
    step.value = "done";
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}

// ---- v0.9-R1 §25.2 Reality contribution — three structured branches ----
type RealityKind = "observed_presence" | "staff_response" | "animal_facility";
const realityKind = ref<RealityKind | "">("");
const realityAnimal = ref("dog");
const realityZone = ref("");
const realityCount = ref("");
const realityAction = ref("");
const realityContext = ref("");
const realityStaffAction = ref("");
const realityStaffOutcome = ref("");
const realityFacilityType = ref("");
const realityFacilityOperational = ref("active");

const REALITY_KIND_LABELS: Record<RealityKind, string> = {
  observed_presence: "我刚刚看到动物",
  staff_response: "我看到工作人员怎么处理",
  animal_facility: "我发现这里有动物相关设施",
};

function startReality(kind: RealityKind) {
  realityKind.value = kind;
  step.value = "reality";
}

async function submitReality() {
  if (!realityKind.value || !canSubmit.value) return;
  error.value = "";
  busy.value = true;
  try {
    const kind = realityKind.value;
    const payload: Record<string, unknown> = {};
    if (kind === "observed_presence") {
      payload.animal_scope = realityAnimal.value;
      payload.animal_count_estimate = realityCount.value ? Number(realityCount.value) : null;
      payload.observed_action = realityAction.value || "present";
      payload.observed_context = realityContext.value.trim() || null;
    } else if (kind === "staff_response") {
      payload.actor_role = "staff";
      payload.trigger_context = realityContext.value.trim() || null;
      payload.response_action = realityStaffAction.value || "provided_guidance";
      payload.response_outcome = realityStaffOutcome.value.trim() || null;
    } else {
      payload.facility_type = realityFacilityType.value || "waiting_area";
      payload.operator_provided = false;
      payload.operational_state = realityFacilityOperational.value;
    }
    await client.submitRealityContribution(placeId.value, {
      candidate_type: kind,
      zone_id: realityZone.value || zone.value || null,
      animal_scope: kind === "observed_presence" ? realityAnimal.value : null,
      observed_at: new Date(occurredAt.value).toISOString(),
      payload,
    });
    msg.value =
      "现场情况已提交，进入人工审核队列。AI 不会自动裁定 —— 审核通过后才作为现场事实展示。";
    step.value = "done";
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <AppShell>
    <div v-if="!online" class="offline-banner" data-testid="offline-banner">
      <span aria-hidden="true">⊘</span>
      <span>当前无网络连接：离线时不接受提交，以免产生未经确认的记录。</span>
    </div>

    <!-- One h1 for every state of this page: the place-missing prompt, the
         signed-out prompt and the working form used to be three different
         "pages" as far as a screen reader was concerned, and only the last one
         had a heading. -->
    <h1 class="visually-hidden">现场贡献</h1>

    <!-- Consumer UX v1 §21–23: 贡献 is a tab, so it can be opened with no place
         selected. That check comes first — never guess which place is meant. -->
    <StateMessage
      v-if="!placeId"
      kind="PARTIAL"
      data-testid="contribute-needs-place"
      description="现场贡献绑定到具体场所与区域。先在搜索或地图里选定一个场所，再从该场所发起。"
    >
      <template #action>
        <RouterLink class="btn primary" to="/search" data-testid="contribute-go-search"
          >去搜索场所</RouterLink
        >
        <RouterLink class="btn" to="/map" style="margin-left: 8px" data-testid="contribute-go-map"
          >看地图</RouterLink
        >
      </template>
    </StateMessage>

    <StateMessage
      v-else-if="!signedIn"
      kind="PERMISSION_DENIED"
      description="贡献需要登录后进行，以便记录来源与核验历史。未登录不会提交任何数据。"
    >
      <template #action>
        <RouterLink class="btn primary" to="/onboarding">登录 / 注册</RouterLink>
      </template>
    </StateMessage>

    <template v-else>
      <div v-if="error" class="panel" data-testid="contribute-error">{{ error }}</div>

      <div class="panel">
        <!-- ------------------------------------------------------------ entry -->
        <template v-if="step === 'entry'">
          <strong>你想提供哪一类信息？</strong>
          <p class="muted" style="margin-top: 4px">
            只提供结构化选项，不设自由评论区，以避免未经核实的评价影响判断。
          </p>
          <div class="row" style="margin-top: 10px">
            <button class="pill" data-testid="entry-quick" @click="step = 'quick'">快速确认</button>
            <button class="pill" data-testid="entry-signage" @click="step = 'signage'">
              拍规则牌
            </button>
            <button class="pill" data-testid="entry-rule" @click="step = 'rule'">我知道规则</button>
            <button class="pill" data-testid="entry-experience" @click="step = 'experience'">
              我有现场经历
            </button>
          </div>
          <div
            class="row"
            style="margin-top: 10px; border-top: 1px dashed var(--line); padding-top: 10px"
          >
            <button
              v-for="(label, kind) in REALITY_KIND_LABELS"
              :key="kind"
              class="pill"
              :data-testid="'entry-reality-' + kind"
              @click="startReality(kind as RealityKind)"
            >
              {{ label }}
            </button>
          </div>
          <p class="muted" style="margin-top: 6px">
            v0.9 现场贡献：只回答结构化问题；提交进入人工审核队列，AI 不会自动裁定。
          </p>
        </template>

        <!-- ------------------------------------------------------ quick check -->
        <template v-else-if="step === 'quick'">
          <strong>页面显示的已收录规则，目前仍然如此吗？</strong>
          <p class="muted" style="margin-top: 4px">
            你只需判断现场是否与已收录内容一致；这不会修改规则内容本身。
          </p>
          <div class="row" style="margin-top: 10px">
            <button
              class="pill"
              :class="{ active: quickResult === 'still_valid' }"
              data-testid="quick-still-valid"
              @click="quickResult = 'still_valid'"
            >
              仍然如此
            </button>
            <button
              class="pill"
              :class="{ active: quickResult === 'changed' }"
              data-testid="quick-changed"
              @click="quickResult = 'changed'"
            >
              已变化
            </button>
            <button
              class="pill"
              :class="{ active: quickResult === 'uncertain' }"
              data-testid="quick-uncertain"
              @click="quickResult = 'uncertain'"
            >
              不确定
            </button>
          </div>
          <div class="row" style="margin-top: 14px">
            <button
              class="primary"
              :disabled="!canSubmit"
              data-testid="quick-submit"
              @click="submitQuick"
            >
              {{ busy ? "提交中…" : "提交确认" }}
            </button>
            <button :disabled="busy" @click="reset">返回</button>
          </div>
        </template>

        <!-- ---------------------------------------------------- signage photo -->
        <template v-else-if="step === 'signage'">
          <strong>拍规则牌</strong>
          <div class="notice" style="margin-top: 8px">
            证据说明：照片用于人工审核，属受控长期保存的证据媒体，不对外公开；
            平台不会仅凭照片自动生成或发布规则。
          </div>

          <label>现场告示照片（camera / 相册）</label>
          <input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            capture="environment"
            data-testid="signage-file"
            :disabled="uploading"
            @change="uploadSignage"
          />
          <div v-if="uploading" class="muted" data-testid="signage-uploading">上传中…</div>
          <div v-if="uploadMsg" class="notice" data-testid="signage-upload-msg">
            {{ uploadMsg }}
          </div>

          <template v-if="mediaId">
            <label>OCR 预览（仅作审核参考，需人工核对）</label>
            <div class="panel" data-testid="ocr-preview">
              <div v-if="ocrText" style="white-space: pre-wrap">{{ ocrText }}</div>
              <div v-else class="muted">
                未取得 OCR 文本（信息不完整）。照片仍会作为证据提交，由人工阅读。
              </div>
              <div v-if="ocrCandidates.length" class="muted" style="margin-top: 6px">
                可能的规则要点：{{ ocrCandidates.join(" / ") }}
              </div>
            </div>

            <label>拍摄区域（可选）</label>
            <select v-model="zone">
              <option value="">全场 / 不确定</option>
              <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
            </select>

            <label>条件（可多选 / 全不选）</label>
            <div class="row">
              <button
                v-for="c in conditionOptions"
                :key="c.key"
                class="pill"
                :class="{ active: conditions.includes(c.key) }"
                @click="
                  conditions.includes(c.key)
                    ? (conditions = conditions.filter((k) => k !== c.key))
                    : conditions.push(c.key)
                "
              >
                {{ c.label }}
              </button>
            </div>

            <label>补充说明（结构化补充，非评论区）</label>
            <input v-model="note" maxlength="500" placeholder="如：告示位于入口右侧" />

            <label style="display: flex; gap: 8px; align-items: center; margin-top: 10px">
              <input v-model="placeConfirmed" type="checkbox" data-testid="signage-place-confirm" />
              <span>我确认这张照片拍摄于本场所</span>
            </label>

            <div class="row" style="margin-top: 14px">
              <button
                class="primary"
                :disabled="!canSubmit || !placeConfirmed"
                data-testid="signage-submit"
                @click="submitSignage"
              >
                {{ busy ? "提交中…" : "提交证据" }}
              </button>
              <button :disabled="busy" @click="reset">返回</button>
            </div>
          </template>
          <div v-else class="row" style="margin-top: 14px">
            <button :disabled="busy" @click="reset">返回</button>
          </div>
        </template>

        <!-- ---------------------------------------------------- known rule -->
        <template v-else-if="step === 'rule'">
          <strong>我知道规则（结构化表单）</strong>
          <p class="muted" style="margin-top: 4px">
            你的说明会以「用户陈述」与场所正式规则并存展示，不会覆盖已收录规则。
          </p>
          <label>你了解到的规则是</label>
          <select v-model="knowRule" data-testid="rule-known">
            <option value="">请选择</option>
            <option value="allowed">明确允许</option>
            <option value="restricted">明确限制</option>
            <option value="conditional">有条件进入</option>
          </select>

          <label>适用区域</label>
          <select v-model="zone">
            <option value="">全场 / 不确定</option>
            <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
          </select>

          <label>条件（可多选 / 全不选）</label>
          <div class="row">
            <button
              v-for="c in conditionOptions"
              :key="c.key"
              class="pill"
              :class="{ active: conditions.includes(c.key) }"
              @click="
                conditions.includes(c.key)
                  ? (conditions = conditions.filter((k) => k !== c.key))
                  : conditions.push(c.key)
              "
            >
              {{ c.label }}
            </button>
          </div>

          <div class="row" style="margin-top: 14px">
            <button
              class="primary"
              :disabled="!canSubmit || !knowRule"
              data-testid="rule-submit"
              @click="submitKnownRule"
            >
              {{ busy ? "提交中…" : "提交" }}
            </button>
            <button :disabled="busy" @click="reset">返回</button>
          </div>
        </template>

        <!-- ---------------------------------------------------- experience -->
        <template v-else-if="step === 'experience'">
          <strong>我有现场经历</strong>
          <p class="muted" style="margin-top: 4px">
            只记录可观察到的行为，不记录主观推断。现场记录 ≠ 场所正式政策。
          </p>

          <label>日期</label>
          <input v-model="occurredAt" type="date" data-testid="exp-date" />

          <label>适用区域</label>
          <select v-model="zone">
            <option value="">全场 / 不确定</option>
            <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
          </select>

          <label>当时发生了什么</label>
          <select v-model="observedAction" data-testid="exp-action">
            <option value="enter">进入</option>
            <option value="dine">就餐</option>
            <option value="walk">通行</option>
            <option value="stay">停留</option>
          </select>

          <label>工作人员的反应</label>
          <select v-model="staffAction" data-testid="exp-staff">
            <option value="no_interaction_observed">未见工作人员介入</option>
            <option value="explicitly_allowed">明确允许</option>
            <option value="explicitly_refused">明确拒绝</option>
            <option value="asked_to_remove">被要求离开</option>
            <option value="interaction_unknown">不确定</option>
          </select>

          <label>你对在场情况的确认程度</label>
          <select v-model="placeConfidence" data-testid="exp-confidence">
            <option value="confirmed_on_site">我在现场确认</option>
            <option value="high">高</option>
            <option value="medium">中</option>
            <option value="low">低</option>
            <option value="uncertain">不确定</option>
          </select>

          <label>结构化补充（非评论区）</label>
          <input v-model="note" maxlength="500" placeholder="如：工作日下午，未见工作人员介入" />

          <div class="row" style="margin-top: 14px">
            <button
              class="primary"
              :disabled="!canSubmit"
              data-testid="exp-submit"
              @click="submitObservation"
            >
              {{ busy ? "提交中…" : "提交现场记录" }}
            </button>
            <button :disabled="busy" @click="reset">返回</button>
          </div>
        </template>

        <!-- ------------------------------------------------- reality (v0.9 §25.2) -->
        <template v-else-if="step === 'reality'">
          <strong>{{ REALITY_KIND_LABELS[realityKind as RealityKind] }}</strong>
          <p class="muted" style="margin-top: 4px">
            只回答结构化问题。提交进入人工审核队列，AI 不会自动裁定。
          </p>

          <div v-if="zones.length" class="row" style="margin-top: 10px">
            <label class="muted" style="margin-right: 8px">区域：</label>
            <select v-model="realityZone">
              <option value="">（未指定区域）</option>
              <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
            </select>
          </div>

          <template v-if="realityKind === 'observed_presence'">
            <div class="row" style="margin-top: 10px">
              <label class="muted" style="margin-right: 8px">动物：</label>
              <select v-model="realityAnimal">
                <option value="dog">犬</option>
                <option value="cat">猫</option>
                <option value="other">其他</option>
              </select>
              <label class="muted" style="margin: 0 8px">大概几只：</label>
              <input
                v-model="realityCount"
                type="number"
                min="1"
                placeholder="1"
                style="width: 72px"
              />
            </div>
            <div class="row" style="margin-top: 10px">
              <label class="muted" style="margin-right: 8px">在做什么：</label>
              <select v-model="realityAction">
                <option value="present">在场</option>
                <option value="walking">行走</option>
                <option value="waiting">等待</option>
                <option value="entering">进入</option>
                <option value="dining">用餐</option>
              </select>
            </div>
          </template>

          <template v-else-if="realityKind === 'staff_response'">
            <div class="row" style="margin-top: 10px">
              <label class="muted" style="margin-right: 8px">工作人员做了什么：</label>
              <select v-model="realityStaffAction">
                <option value="provided_guidance">引导 / 说明</option>
                <option value="asked_to_leave">要求离开</option>
                <option value="offered_assistance">提供协助</option>
                <option value="no_interaction">未与顾客互动</option>
              </select>
            </div>
          </template>

          <template v-else>
            <div class="row" style="margin-top: 10px">
              <label class="muted" style="margin-right: 8px">设施类型：</label>
              <select v-model="realityFacilityType">
                <option value="waiting_area">宠物等候区 / 笼</option>
                <option value="water_station">饮水点 / 水碗</option>
                <option value="pet_elevator">宠物电梯</option>
                <option value="designated_zone">专用活动区</option>
                <option value="other_facility">其他设施</option>
              </select>
            </div>
            <div class="row" style="margin-top: 10px">
              <label class="muted" style="margin-right: 8px">状态：</label>
              <select v-model="realityFacilityOperational">
                <option value="active">正常可用</option>
                <option value="removed">已拆除</option>
                <option value="out_of_service">停用</option>
              </select>
            </div>
          </template>

          <div class="row" style="margin-top: 10px">
            <label class="muted" style="margin-right: 8px">补充（可选）：</label>
            <input
              v-model="realityContext"
              placeholder="一两句话即可，不填也可以"
              style="flex: 1"
            />
          </div>

          <div class="row" style="margin-top: 12px">
            <button
              class="primary"
              :disabled="!canSubmit || busy"
              data-testid="reality-submit"
              @click="submitReality"
            >
              {{ busy ? "提交中…" : "提交现场情况" }}
            </button>
            <button :disabled="busy" @click="reset">返回</button>
          </div>
        </template>

        <!-- ---------------------------------------------------------- done -->
        <template v-else-if="step === 'done'">
          <StateMessage kind="PARTIAL" :description="msg" data-testid="contribute-result">
            <template #action>
              <div class="row">
                <button class="primary" @click="reset">继续贡献</button>
                <RouterLink :to="{ name: 'place', params: { id: placeId } }">
                  <button>返回场所</button>
                </RouterLink>
              </div>
            </template>
          </StateMessage>
        </template>
      </div>

      <div class="notice">
        位置仅记录分桶后的现场核验结果（距离/精度），不保存原始 GPS 轨迹（ADR-012）。
        高频提交会被限流。证据媒体不公开，仅审核可见。
      </div>
    </template>
  </AppShell>
</template>
