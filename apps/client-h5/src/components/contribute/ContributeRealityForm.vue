<script setup lang="ts">
/** ContributeRealityForm — M7 reality contribution on the parent-flow API (A2). */
import { computed, ref } from "vue";
import { client } from "@petaccess/client-core";
import { isoAt, realityPayload } from "./contributeSupport";
import { presentDescription } from "../../errors";
import {
  ANIMAL_FACILITY_LABELS,
  FACILITY_STATE_LABELS,
  OBSERVED_ACTION_LABELS,
  STAFF_ACTION_LABELS,
  STAFF_ROLE_LABELS,
} from "../../consumer/labels";
import ContributionStepShell from "./ContributionStepShell.vue";
defineOptions({ name: "ContributeRealityForm" });
const props = defineProps<{
  placeId: string;
  placeName: string;
  parentPlaceId?: string | null;
  zones: { id: string; name: string }[];
  online: boolean;
  signedIn: boolean;
  kind: "observed_presence" | "staff_response" | "animal_facility";
}>();
const emit = defineEmits<{ done: [msg: string]; back: [] }>();
const KIND_LABELS: Record<string, string> = {
  observed_presence: "我刚刚看到动物",
  staff_response: "我看到工作人员怎么处理",
  animal_facility: "我发现这里有动物相关设施",
};

type SourceMode = "on_site_now" | "on_site_past" | "external_online_content";

const sourceMode = ref<SourceMode>("on_site_now");
const occurredAt = ref(new Date().toISOString().slice(0, 10));
const externalUrl = ref("");
const externalPlatform = ref("web");
const externalPublishedAt = ref("");
const externalEventAt = ref("");
const externalPlaceMatch = ref<"exact_place" | "parent_place_only" | "area_only" | "unresolved">(
  "exact_place",
);
const mediaId = ref<string | null>(null);
const mediaMessage = ref("");
const uploading = ref(false);
const zone = ref("");
const animal = ref("dog");
const count = ref("");
const action = ref("present");
const staffRole = ref("unknown_staff");
const staffAction = ref("unknown");
const staffAwareness = ref("awareness_unknown");
const staffOutcome = ref("");
const staffPolicyStatement = ref("");
const facilityType = ref("");
const facilityOperational = ref("unknown");
const facilityPurpose = ref("purpose_unknown");
const facilityAccessMode = ref("unknown");
const facilityCapacity = ref("");
const facilitySizeLimit = ref("");
const facilityWeatherProtection = ref<boolean | null>(null);
const facilityShade = ref<boolean | null>(null);
const facilityVentilation = ref<boolean | null>(null);
const facilityWaterAvailable = ref<boolean | null>(null);
const facilitySupervisionState = ref("");
const facilitySecurityState = ref("");
const context = ref("");
const effortBucket = ref("unknown");

const EFFORT_LABELS: Record<string, string> = {
  lt_10_min: "不到 10 分钟",
  min_10_30: "10–30 分钟",
  min_30_120: "30 分钟 – 2 小时",
  gt_120_min: "超过 2 小时",
  unknown: "不确定",
};

const OBSERVED_ACTION_KEYS = [
  "present",
  "entered",
  "stayed",
  "dined_near_table",
  "leashed",
  "off_leash",
  "in_carrier",
  "in_stroller",
] as const;

const STAFF_RESPONSE_KEYS = [
  "proactive_accommodation",
  "provide_water",
  "provide_container_or_stroller",
  "direct_to_allowed_zone",
  "remind_leash",
  "require_carrier",
  "request_relocation",
  "request_wait_outside",
  "deny_entry",
  "request_exit",
  "policy_explanation",
  "escalate_to_manager",
  "no_intervention_observed",
  "unknown",
] as const;

const STAFF_ROLE_KEYS = [
  "owner",
  "manager",
  "frontline_staff",
  "server",
  "security",
  "cleaning_staff",
  "front_desk",
  "unknown_staff",
] as const;

const FACILITY_TYPE_KEYS = [
  "outdoor_holding_cage",
  "kennel",
  "tether_point",
  "pet_waiting_area",
  "pet_parking",
  "water_bowl",
  "pet_stroller",
  "carrier_storage",
  "pet_entrance",
  "pet_elevator",
  "dedicated_pet_zone",
  "waste_bag_station",
  "cleaning_station",
  "washing_point",
  "dedicated_pet_tableware",
  "other",
] as const;

const FACILITY_STATE_KEYS = ["active", "temporarily_unavailable", "removed", "unknown"] as const;

const STAFF_AWARENESS_OPTIONS = [
  { key: "awareness_confirmed", label: "明确看到工作人员注意到该情况" },
  { key: "awareness_likely", label: "工作人员可能注意到了" },
  { key: "awareness_unknown", label: "不确定工作人员是否注意到" },
] as const;

const FACILITY_PURPOSE_OPTIONS = [
  { key: "purpose_signage_supported", label: "现场标识明确说明用途" },
  { key: "purpose_staff_stated", label: "工作人员说明过用途" },
  { key: "purpose_confirmed", label: "有其他明确依据确认用途" },
  { key: "purpose_user_inferred", label: "我是根据外观判断" },
  { key: "purpose_unknown", label: "不确定用途" },
] as const;

const FACILITY_ACCESS_OPTIONS = [
  { key: "operator_provided", label: "由场所提供 / 管理" },
  { key: "self_service", label: "可以自助使用" },
  { key: "staff_assisted", label: "需要工作人员协助" },
  { key: "unknown", label: "使用方式不确定" },
] as const;

const FACILITY_BOOLEAN_OPTIONS: { value: boolean | null; label: string }[] = [
  { value: null, label: "未确认" },
  { value: true, label: "有" },
  { value: false, label: "没有" },
];

const FACILITY_SUPERVISION_OPTIONS = [
  { key: "", label: "未确认" },
  { key: "有工作人员看护", label: "有工作人员看护" },
  { key: "无人固定看护", label: "无人固定看护" },
] as const;

const FACILITY_SECURITY_OPTIONS = [
  { key: "", label: "未确认" },
  { key: "可锁闭 / 有安全门", label: "可锁闭 / 有安全门" },
  { key: "开放式 / 不可锁闭", label: "开放式 / 不可锁闭" },
] as const;

const busy = ref(false);
const error = ref("");
const isExternal = computed(() => sourceMode.value === "external_online_content");
const hasClaimablePlaceMatch = computed(
  () =>
    !isExternal.value ||
    externalPlaceMatch.value === "exact_place" ||
    externalPlaceMatch.value === "parent_place_only",
);
const canUseCurrentZones = computed(
  () => !isExternal.value || externalPlaceMatch.value === "exact_place",
);
const canSubmit = computed(
  () =>
    props.online &&
    props.signedIn &&
    !busy.value &&
    !uploading.value &&
    (!isExternal.value || Boolean(externalUrl.value.trim() && externalPublishedAt.value)) &&
    (props.kind !== "animal_facility" || Boolean(facilityType.value)),
);

async function uploadEvidence(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] ?? null;
  if (!file) return;
  error.value = "";
  mediaMessage.value = "";
  uploading.value = true;
  try {
    const media = await client.uploadMedia(file, "reality_evidence", {
      ownerType: "place",
      ownerId: props.placeId,
    });
    mediaId.value = media.id;
    mediaMessage.value = media.duplicate_of
      ? "这份证据此前已上传过；仍会作为本次报告的私有核验材料。"
      : "证据已上传，仅供审核使用，不会自动公开。";
  } catch (err) {
    error.value = presentDescription(err);
  } finally {
    uploading.value = false;
    input.value = "";
  }
}

async function submit() {
  if (!canSubmit.value || !props.placeId) return;
  error.value = "";
  busy.value = true;
  try {
    const kind = props.kind;
    const onsiteAt =
      sourceMode.value === "on_site_now"
        ? new Date().toISOString()
        : sourceMode.value === "on_site_past"
          ? isoAt(occurredAt.value)
          : null;
    const externalEventIso =
      isExternal.value && externalEventAt.value ? isoAt(externalEventAt.value) : null;
    const externalPublishedIso =
      isExternal.value && externalPublishedAt.value ? isoAt(externalPublishedAt.value) : null;
    const eventAt = onsiteAt ?? externalEventIso;
    const placeMatchState = isExternal.value ? externalPlaceMatch.value : "exact_place";
    const reportPlaceId =
      placeMatchState === "exact_place"
        ? props.placeId
        : placeMatchState === "parent_place_only" && props.parentPlaceId
          ? props.parentPlaceId
          : null;
    const candidatePlaceId =
      placeMatchState === "parent_place_only" && props.parentPlaceId
        ? props.parentPlaceId
        : undefined;
    const { payload, animalScope } = realityPayload(props.kind, {
      animal: animal.value,
      count: count.value,
      action: action.value,
      context: context.value,
      staffRole: staffRole.value,
      staffAction: staffAction.value,
      staffAwareness: staffAwareness.value,
      staffOutcome: staffOutcome.value,
      staffPolicyStatement: staffPolicyStatement.value,
      facilityType: facilityType.value,
      facilityOperational: facilityOperational.value,
      facilityPurpose: facilityPurpose.value,
      facilityAccessMode: facilityAccessMode.value,
      facilityCapacity: facilityCapacity.value,
      facilitySizeLimit: facilitySizeLimit.value,
      facilityWeatherProtection: facilityWeatherProtection.value,
      facilityShade: facilityShade.value,
      facilityVentilation: facilityVentilation.value,
      facilityWaterAvailable: facilityWaterAvailable.value,
      facilitySupervisionState: facilitySupervisionState.value,
      facilitySecurityState: facilitySecurityState.value,
    });
    const res = await client.createRealityReport(props.placeId, {
      report: {
        origin: sourceMode.value,
        place_id: reportPlaceId,
        container_place_id:
          placeMatchState === "parent_place_only" && props.parentPlaceId
            ? props.parentPlaceId
            : null,
        subject_place_id: placeMatchState === "exact_place" ? props.placeId : null,
        place_match_state: placeMatchState,
        place_match_evidence_types: isExternal.value
          ? ["source_url", ...(placeMatchState === "exact_place" ? ["user_confirmation"] : [])]
          : ["user_confirmation"],
        content_published_at: externalPublishedIso,
        claimed_event_at: externalEventIso,
        observed_at: onsiteAt,
        time_evidence_state: isExternal.value
          ? externalEventIso
            ? "exact_event_date"
            : "publication_time_only"
          : sourceMode.value === "on_site_now"
            ? "live_device_time"
            : "exact_event_date",
        time_certainty: isExternal.value ? (externalEventIso ? "exact" : "unknown") : "exact",
        fact_evidence_state: isExternal.value
          ? mediaId.value
            ? "external_media"
            : "text_only_external"
          : mediaId.value
            ? "direct_media"
            : "first_hand_no_media",
        privacy_state: "private",
        media_refs: mediaId.value ? [{ media_id: mediaId.value }] : null,
        source_url: isExternal.value ? externalUrl.value.trim() : null,
        source_platform: isExternal.value ? externalPlatform.value : null,
      },
      candidates: hasClaimablePlaceMatch.value
        ? [
            {
              candidate_type: kind,
              place_id: candidatePlaceId,
              zone_id: placeMatchState === "exact_place" ? zone.value || null : null,
              animal_scope: animalScope,
              observed_at: eventAt,
              payload,
            },
          ]
        : [],
      effort: isExternal.value
        ? null
        : {
            place_id: props.placeId,
            duration_bucket: effortBucket.value,
            observed_at: onsiteAt,
            animal_observed: kind === "observed_presence" ? true : undefined,
          },
      confirmation: null,
      external_content: isExternal.value
        ? {
            source_url: externalUrl.value.trim(),
            platform: externalPlatform.value,
            published_at: externalPublishedIso,
          }
        : null,
    });
    const pending = res.moderation_state === "pending" || res.moderation_state === "flagged";
    emit(
      "done",
      !hasClaimablePlaceMatch.value
        ? "外部内容线索已提交。地点尚未精确匹配，因此没有生成当前场所的事实候选；人工完成地点核验后才能继续形成可审核事实。"
        : pending
          ? "现场情况已提交，进入人工审核队列。AI 不会自动裁定 —— 审核通过后才作为现场事实展示。"
          : "现场情况已提交并记录。审核通过后才会作为现场事实展示。",
    );
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <ContributionStepShell
    :place-name="placeName"
    :step="2"
    :total="3"
    :title="KIND_LABELS[kind]"
    description="只回答结构化问题。现场亲历、公开内容与证据媒体会分开记录；提交进入人工审核队列，AI 不会自动裁定。"
    @back="emit('back')"
  >
    <!-- §33 question clusters：什么时候 / 在哪里 / 你看到了什么 -->
    <!-- §19 field groups：真实结构化表单包一层 contribution-form 供几何 gate
         测量 group rhythm（When / Where / What 三组，组距 20–28px）。 -->
    <div class="reality-form" data-ui="contribution-form">
      <fieldset class="cluster">
        <legend class="cluster__title">这条信息来自哪里？</legend>
        <label for="reality-source-mode">来源方式</label>
        <select id="reality-source-mode" v-model="sourceMode" data-testid="reality-source-mode">
          <option value="on_site_now">我现在就在这里</option>
          <option value="on_site_past">我之前在这里看到过</option>
          <option value="external_online_content">我在公开帖子 / 视频里看到</option>
        </select>

        <template v-if="isExternal">
          <label for="reality-source-url">公开内容链接</label>
          <input
            id="reality-source-url"
            v-model="externalUrl"
            type="url"
            placeholder="https://…"
            data-testid="reality-source-url"
          />
          <label for="reality-place-match">内容能定位到哪里？</label>
          <select
            id="reality-place-match"
            v-model="externalPlaceMatch"
            data-testid="reality-place-match"
          >
            <option value="exact_place">能确认就是当前场所</option>
            <option v-if="parentPlaceId" value="parent_place_only">
              只能确认到当前场所所在的上级场所
            </option>
            <option value="area_only">只能确认到附近区域</option>
            <option value="unresolved">无法可靠确认具体地点</option>
          </select>
          <p class="muted source-note">
            只有精确匹配到具体场所的记录，才可能在人工核验后成为该场所的公开现场事实。
          </p>

          <label for="reality-source-platform">来源平台</label>
          <select
            id="reality-source-platform"
            v-model="externalPlatform"
            data-testid="reality-source-platform"
          >
            <option value="xiaohongshu">小红书</option>
            <option value="douyin">抖音</option>
            <option value="dianping">大众点评</option>
            <option value="weibo">微博</option>
            <option value="bilibili">哔哩哔哩</option>
            <option value="web">网页</option>
            <option value="other">其他</option>
          </select>
          <label for="reality-published-date">内容发布时间</label>
          <input
            id="reality-published-date"
            v-model="externalPublishedAt"
            type="date"
            data-testid="reality-published-date"
          />
          <label for="reality-external-event-date">内容明确说明的发生日期（可选）</label>
          <input
            id="reality-external-event-date"
            v-model="externalEventAt"
            type="date"
            data-testid="reality-external-event-date"
          />
          <p class="muted source-note">
            只有发布时间时，平台只会写“某日发布的内容中观察到”，不会把发布时间当成现场发生时间。
          </p>
        </template>

        <label for="reality-media">证据图片（可选）</label>
        <input
          id="reality-media"
          type="file"
          accept="image/png,image/jpeg,image/webp"
          :disabled="uploading"
          data-testid="reality-media"
          @change="uploadEvidence"
        />
        <p v-if="uploading" class="muted source-note">上传中…</p>
        <p v-if="mediaMessage" class="muted source-note" data-testid="reality-media-message">
          {{ mediaMessage }}
        </p>
      </fieldset>

      <fieldset v-if="!isExternal" class="cluster">
        <legend class="cluster__title">什么时候？</legend>
        <template v-if="sourceMode === 'on_site_past'">
          <label for="reality-date">发生日期</label>
          <input id="reality-date" v-model="occurredAt" type="date" data-testid="reality-date" />
        </template>
        <p v-else class="muted source-note">将使用提交时的当前时间记录这次现场观察。</p>
        <label for="reality-effort">在场时长</label>
        <select v-model="effortBucket" id="reality-effort" data-testid="reality-effort">
          <option v-for="(label, key) in EFFORT_LABELS" :key="key" :value="key">{{ label }}</option>
        </select>
      </fieldset>

      <fieldset class="cluster">
        <legend class="cluster__title">在哪里？</legend>
        <template v-if="canUseCurrentZones">
          <label for="reality-zone">适用区域</label>
          <select v-model="zone" id="reality-zone">
            <option value="">全场 / 不确定</option>
            <option v-for="z in zones" :key="z.id" :value="z.id">{{ z.name }}</option>
          </select>
        </template>
        <p v-else class="muted source-note" data-testid="reality-imprecise-place-note">
          {{
            externalPlaceMatch === "parent_place_only"
              ? "当前只能确认到上级场所，因此不会使用这个具体场所的分区。"
              : "地点尚未精确匹配；本次先保存来源与事实线索，不会把它挂成当前场所的事实。"
          }}
        </p>
      </fieldset>

      <fieldset class="cluster">
        <legend class="cluster__title">你看到了什么？</legend>
        <template v-if="kind === 'observed_presence'">
          <label for="reality-animal">动物</label>
          <select v-model="animal" id="reality-animal">
            <option value="dog">犬</option>
            <option value="cat">猫</option>
            <option value="other">其他</option>
          </select>
          <label for="reality-count">大概几只</label>
          <input
            v-model="count"
            type="number"
            min="1"
            placeholder="1"
            id="reality-count"
            data-testid="reality-count"
          />
          <label for="reality-action">在做什么</label>
          <select v-model="action" id="reality-action">
            <option v-for="key in OBSERVED_ACTION_KEYS" :key="key" :value="key">
              {{ OBSERVED_ACTION_LABELS[key] }}
            </option>
          </select>
        </template>

        <template v-else-if="kind === 'staff_response'">
          <label for="reality-staff-role">是哪类工作人员（可选）</label>
          <select id="reality-staff-role" v-model="staffRole" data-testid="reality-staff-role">
            <option v-for="key in STAFF_ROLE_KEYS" :key="key" :value="key">
              {{ STAFF_ROLE_LABELS[key] }}
            </option>
          </select>
          <p class="muted source-note">只记录岗位角色，不收集工作人员姓名或身份。</p>
          <label for="reality-staff-action">工作人员做了什么</label>
          <select v-model="staffAction" id="reality-staff-action">
            <option v-for="key in STAFF_RESPONSE_KEYS" :key="key" :value="key">
              {{ STAFF_ACTION_LABELS[key] }}
            </option>
          </select>
          <label for="reality-staff-awareness">你能确认工作人员注意到这个情况吗？</label>
          <select
            id="reality-staff-awareness"
            v-model="staffAwareness"
            data-testid="reality-staff-awareness"
          >
            <option v-for="item in STAFF_AWARENESS_OPTIONS" :key="item.key" :value="item.key">
              {{ item.label }}
            </option>
          </select>
          <label for="reality-staff-outcome">结果（可选）</label>
          <input
            v-model="staffOutcome"
            placeholder="一两句话即可，不填也可以"
            id="reality-staff-outcome"
          />

          <label for="reality-staff-statement">工作人员明确原话（可选）</label>
          <textarea
            id="reality-staff-statement"
            v-model="staffPolicyStatement"
            rows="3"
            maxlength="500"
            placeholder="只填写你能确认的原话；不确定就留空"
            data-testid="reality-staff-statement"
          />
          <p class="muted source-note">
            原话会作为具体事件的核验材料；即使审核通过，也不会自动成为运营方正式政策。
          </p>
        </template>

        <template v-else>
          <label for="reality-facility-type">设施类型</label>
          <select v-model="facilityType" id="reality-facility-type">
            <option value="" disabled>请选择设施类型</option>
            <option v-for="key in FACILITY_TYPE_KEYS" :key="key" :value="key">
              {{ ANIMAL_FACILITY_LABELS[key] }}
            </option>
          </select>
          <label for="reality-facility-purpose">你怎么确认它是动物相关设施？</label>
          <select
            id="reality-facility-purpose"
            v-model="facilityPurpose"
            data-testid="reality-facility-purpose"
          >
            <option v-for="item in FACILITY_PURPOSE_OPTIONS" :key="item.key" :value="item.key">
              {{ item.label }}
            </option>
          </select>
          <label for="reality-facility-status">状态</label>
          <select v-model="facilityOperational" id="reality-facility-status">
            <option v-for="key in FACILITY_STATE_KEYS" :key="key" :value="key">
              {{ FACILITY_STATE_LABELS[key] }}
            </option>
          </select>
          <label for="reality-facility-access">使用方式（可选）</label>
          <select
            id="reality-facility-access"
            v-model="facilityAccessMode"
            data-testid="reality-facility-access"
          >
            <option v-for="item in FACILITY_ACCESS_OPTIONS" :key="item.key" :value="item.key">
              {{ item.label }}
            </option>
          </select>
          <label for="reality-facility-capacity">数量 / 容量（可选）</label>
          <input
            id="reality-facility-capacity"
            v-model="facilityCapacity"
            type="number"
            min="1"
            placeholder="例如 2"
            data-testid="reality-facility-capacity"
          />

          <details class="facility-more" data-testid="reality-facility-more">
            <summary>补充设施使用与安全信息（可选）</summary>
            <div class="facility-more__fields">
              <label for="reality-facility-size">体型限制</label>
              <input
                id="reality-facility-size"
                v-model="facilitySizeLimit"
                maxlength="80"
                placeholder="例如：仅小型犬；不确定可留空"
                data-testid="reality-facility-size"
              />

              <label for="reality-facility-weather">有遮雨</label>
              <select
                id="reality-facility-weather"
                v-model="facilityWeatherProtection"
                data-testid="reality-facility-weather"
              >
                <option
                  v-for="item in FACILITY_BOOLEAN_OPTIONS"
                  :key="String(item.value)"
                  :value="item.value"
                >
                  {{ item.label }}
                </option>
              </select>

              <label for="reality-facility-shade">有遮阳</label>
              <select
                id="reality-facility-shade"
                v-model="facilityShade"
                data-testid="reality-facility-shade"
              >
                <option
                  v-for="item in FACILITY_BOOLEAN_OPTIONS"
                  :key="String(item.value)"
                  :value="item.value"
                >
                  {{ item.label }}
                </option>
              </select>

              <label for="reality-facility-ventilation">有通风</label>
              <select
                id="reality-facility-ventilation"
                v-model="facilityVentilation"
                data-testid="reality-facility-ventilation"
              >
                <option
                  v-for="item in FACILITY_BOOLEAN_OPTIONS"
                  :key="String(item.value)"
                  :value="item.value"
                >
                  {{ item.label }}
                </option>
              </select>

              <label for="reality-facility-water">可获得饮水</label>
              <select
                id="reality-facility-water"
                v-model="facilityWaterAvailable"
                data-testid="reality-facility-water"
              >
                <option
                  v-for="item in FACILITY_BOOLEAN_OPTIONS"
                  :key="String(item.value)"
                  :value="item.value"
                >
                  {{ item.label }}
                </option>
              </select>

              <label for="reality-facility-supervision">看护情况</label>
              <select
                id="reality-facility-supervision"
                v-model="facilitySupervisionState"
                data-testid="reality-facility-supervision"
              >
                <option
                  v-for="item in FACILITY_SUPERVISION_OPTIONS"
                  :key="item.key"
                  :value="item.key"
                >
                  {{ item.label }}
                </option>
              </select>

              <label for="reality-facility-security">安全 / 锁闭情况</label>
              <select
                id="reality-facility-security"
                v-model="facilitySecurityState"
                data-testid="reality-facility-security"
              >
                <option v-for="item in FACILITY_SECURITY_OPTIONS" :key="item.key" :value="item.key">
                  {{ item.label }}
                </option>
              </select>
            </div>
            <p class="muted source-note">
              这些字段只描述你实际看到的设施属性；不表示设施“安全”，也不推导动物可以进入场所。
            </p>
          </details>
        </template>

        <label for="reality-context">补充（可选）</label>
        <input
          v-model="context"
          id="reality-context"
          data-testid="reality-context"
          placeholder="一两句话即可，不填也可以"
        />
      </fieldset>
    </div>

    <p v-if="error" class="notice" data-testid="reality-error" role="alert">{{ error }}</p>
    <template #primary>
      <button class="primary" :disabled="!canSubmit" data-testid="reality-submit" @click="submit">
        {{ busy ? "提交中…" : "提交现场情况" }}
      </button>
    </template>
  </ContributionStepShell>
</template>

<style scoped>
.cluster {
  margin: 0 0 var(--pa-space-5);
  padding: 0;
  border: none;
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
}

.cluster + .cluster {
  padding-top: var(--pa-space-5);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.cluster__title {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
  margin-bottom: var(--pa-space-2);
}
.cluster label {
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}
.source-note {
  margin: 0;
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}
.cluster input,
.cluster select,
.cluster textarea {
  min-height: var(--pa-size-control-md);
  border: var(--pa-border-width) solid var(--pa-color-border-strong);
  border-radius: var(--pa-radius-control);
  padding: var(--pa-space-1) var(--pa-space-2);
  font-size: var(--pa-font-size-base);
  background: var(--pa-color-surface);
  color: var(--pa-color-text-primary);
}

.facility-more {
  margin-top: var(--pa-space-3);
  padding-top: var(--pa-space-3);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.facility-more summary {
  min-height: var(--pa-size-control-md);
  display: flex;
  align-items: center;
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-md);
  cursor: pointer;
}

.facility-more__fields {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  padding: var(--pa-space-2) 0;
}
</style>
