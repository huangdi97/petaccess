<script setup lang="ts">
import { onMounted, ref } from "vue";
import { get, ApiError } from "../api";

interface Quality {
  rule_coverage: { places_total: number; places_with_rules: number; coverage_ratio: number };
  rules: {
    total: number;
    current: number;
    with_source: number;
    source_coverage: number;
    review_overdue: number;
  };
  provenance: { sources_total: number; official_ratio: number };
  contributions: { observations: number; verifications: number };
  queues: { operator_claims_pending: number; disputes_open: number };
}

const q = ref<Quality | null>(null);
const error = ref("");

onMounted(async () => {
  try {
    q.value = await get<Quality>("/admin/quality");
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  }
});
</script>

<template>
  <h1>数据质量看板</h1>
  <div v-if="error" class="error-banner">{{ error }}</div>
  <template v-if="q">
    <div class="stat-grid">
      <div class="stat">
        <div class="num">
          {{ q.rule_coverage.places_with_rules }}/{{ q.rule_coverage.places_total }}
        </div>
        <div class="label">规则覆盖率（场所）</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.rules.current }}</div>
        <div class="label">生效中规则</div>
      </div>
      <div class="stat">
        <div class="num">{{ Math.round(q.rules.source_coverage * 100) }}%</div>
        <div class="label">规则来源覆盖率</div>
      </div>
      <div class="stat">
        <div class="num">{{ Math.round(q.provenance.official_ratio * 100) }}%</div>
        <div class="label">官方/管理方来源占比</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.rules.review_overdue }}</div>
        <div class="label">复核逾期规则</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.contributions.observations }}</div>
        <div class="label">观察记录</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.contributions.verifications }}</div>
        <div class="label">现场核验</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.queues.operator_claims_pending }}</div>
        <div class="label">待审认领</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.queues.disputes_open }}</div>
        <div class="label">未结异议</div>
      </div>
    </div>
    <h2>说明</h2>
    <p class="muted">
      平台不做"可信度评分"，只展示可追溯的结构化指标（设计 #13 / #37）。 高影响规则必须携带
      Source；UNKNOWN 不会被当作允许或禁止。
    </p>
  </template>
</template>
