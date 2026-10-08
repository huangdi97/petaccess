<script setup lang="ts">
import { computed } from "vue";
import type { RealityEventView } from "@petaccess/client-core";
import { evidenceMaterialLabel, factEvidenceLabel, realityOriginLabel } from "../../consumer/realityEvent";

const props = defineProps<{
  events: RealityEventView[];
  ruleFirstPartyPending: boolean;
}>();

const humanAccepted = computed(
  () =>
    props.events.filter((event) =>
      ["human_verified", "human_verified_with_note"].includes(event.verification_status),
    ).length,
);

const openDisputes = computed(() => props.events.filter((event) => event.dispute_open).length);

const independentlyConfirmed = computed(
  () => props.events.filter((event) => (event.confirmation_count ?? 0) > 0).length,
);
const confirmationTotal = computed(() =>
  props.events.reduce((total, event) => total + (event.confirmation_count ?? 0), 0),
);

const origins = computed(() =>
  [...new Set(props.events.map((event) => realityOriginLabel(event.origin)))].filter(Boolean),
);

const evidencePostures = computed(() =>
  [...new Set(props.events.map((event) => factEvidenceLabel(event.fact_evidence_state)))].filter(
    Boolean,
  ),
);

const materialPostures = computed(() =>
  [
    ...new Set(
      props.events
        .filter((event) => Boolean(event.evidence_bundle_id))
        .map((event) => evidenceMaterialLabel(event)),
    ),
  ].filter(Boolean),
);

const bundleCount = computed(
  () =>
    new Set(
      props.events
        .map((event) => event.evidence_bundle_id)
        .filter((id): id is string => Boolean(id)),
    ).size,
);
</script>

<template>
  <section class="evidence-governance" data-ui="evidence-governance">
    <h2 class="evidence-governance__title">证据状态摘要</h2>
    <dl class="evidence-governance__list">
      <div class="evidence-governance__row">
        <dt>人工接受</dt>
        <dd>{{ humanAccepted }} / {{ events.length }} 条现场事实</dd>
      </div>
      <div class="evidence-governance__row">
        <dt>来源方式</dt>
        <dd>{{ origins.length ? origins.join(" · ") : "未记录" }}</dd>
      </div>
      <div class="evidence-governance__row">
        <dt>证据形态</dt>
        <dd>{{ evidencePostures.length ? evidencePostures.join(" · ") : "未记录" }}</dd>
      </div>
      <div class="evidence-governance__row">
        <dt>原始材料 / 许可</dt>
        <dd>
          <template v-if="materialPostures.length">
            <span v-for="(item, index) in materialPostures" :key="item">
              {{ item }}<template v-if="index < materialPostures.length - 1">；</template>
            </span>
          </template>
          <template v-else>暂无可公开确认的原始材料元数据</template>
        </dd>
      </div>
      <div class="evidence-governance__row">
        <dt>证据包</dt>
        <dd>
          {{ bundleCount ? `${bundleCount} 个可追溯证据包` : "暂无证据包锚点" }}
          <span class="muted">· 当前公开接口不推断包内材料数量</span>
        </dd>
      </div>
      <div class="evidence-governance__row">
        <dt>独立确认</dt>
        <dd>
          <template v-if="confirmationTotal">
            {{ independentlyConfirmed }} 条事实另有 {{ confirmationTotal }} 条独立确认
          </template>
          <template v-else> 当前已发布事实尚无额外独立确认；这不影响其既有人工核验状态 </template>
        </dd>
      </div>
      <div class="evidence-governance__row">
        <dt>规则来源升级</dt>
        <dd>{{ ruleFirstPartyPending ? "仍待一手 / 管理方来源补强" : "当前无待升级标记" }}</dd>
      </div>
      <div class="evidence-governance__row">
        <dt>争议 / 纠错</dt>
        <dd>{{ openDisputes ? `${openDisputes} 条事实存在进行中的异议` : "暂无进行中的异议" }}</dd>
      </div>
    </dl>
    <p class="muted evidence-governance__note">
      人工核验、地点匹配、时间依据、来源类型和争议状态分别记录；其中任何一项都不会自动替代其他项。
    </p>
  </section>
</template>

<style scoped>
.evidence-governance {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
}

.evidence-governance__title {
  margin: var(--pa-space-4) 0 var(--pa-space-1);
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
  color: var(--pa-color-text-primary);
}

.evidence-governance__list {
  margin: 0;
}

.evidence-governance__row {
  display: grid;
  grid-template-columns: 8rem minmax(0, 1fr);
  gap: var(--pa-space-4);
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.evidence-governance__row dt {
  color: var(--pa-color-text-muted);
  font-size: var(--pa-font-size-sm);
}

.evidence-governance__row dd {
  margin: 0;
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
}

.evidence-governance__note {
  margin: var(--pa-space-2) 0 0;
  max-width: 680px;
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}

@media (max-width: 767px) {
  .evidence-governance__row {
    grid-template-columns: 1fr;
    gap: var(--pa-space-1);
  }
}
</style>
