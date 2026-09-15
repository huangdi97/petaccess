<script setup lang="ts">
/**
 * Data-quality dashboard (P4 "data quality metrics", design #37).
 *
 * Shows raw, decomposable operational numbers and no composite score — the same
 * discipline the product applies to places. Every block states what it counts so
 * a drop can be traced without guessing.
 */
import { onMounted, ref } from "vue";
import { get, ApiError } from "../api";
import StateMessage from "../components/StateMessage.vue";
import SourceBadge from "../components/SourceBadge.vue";

interface Quality {
  generated_at: string;
  rule_coverage: { places_total: number; places_with_rules: number; coverage_ratio: number };
  rules: {
    total: number;
    current: number;
    with_source: number;
    source_coverage: number;
    review_overdue: number;
    never_verified: number;
    by_effect: Record<string, number>;
    age_days: { median: number | null; oldest: number | null; newest: number | null };
  };
  candidates: {
    total: number;
    by_status: Record<string, number>;
    by_layer: Record<string, number>;
    without_evidence: number;
    evidence_coverage: number;
    published: number;
  };
  evidence: {
    artifacts_total: number;
    bundles_total: number;
    with_content_hash: number;
    hash_coverage: number;
    with_license_metadata: number;
    license_coverage: number;
    lead_only: number;
  };
  provenance: { sources_total: number; official_ratio: number };
  contributions: { observations: number; verifications: number };
  queues: { operator_claims_pending: number; disputes_open: number };
}

const q = ref<Quality | null>(null);
const error = ref("");
const loading = ref(true);

const pct = (v: number | null | undefined) =>
  v === null || v === undefined ? "—" : `${Math.round(v * 100)}%`;
const num = (v: number | null | undefined) => (v === null || v === undefined ? "—" : String(v));

/** Render a `{bucket: count}` map as stable, alphabetically sorted rows. */
function buckets(map: Record<string, number> | undefined): [string, number][] {
  return Object.entries(map ?? {}).sort(([a], [b]) => a.localeCompare(b));
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    q.value = await get<Quality>("/admin/quality");
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
    q.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <h1>数据质量看板</h1>

  <div v-if="loading" class="skeleton-table">
    <div v-for="i in 8" :key="i" class="skeleton" style="height: 20px"></div>
  </div>

  <StateMessage v-else-if="error" kind="ERROR" :description="`未能取得质量指标：${error}`">
    <template #action>
      <button class="primary" @click="load">重试</button>
    </template>
  </StateMessage>

  <template v-else-if="q">
    <p class="hint">
      指标生成时间：{{ q.generated_at }}。本页只展示可分解的原始比例，不提供综合质量分——
      与产品对场所的原则一致。
    </p>

    <h2>规则覆盖</h2>
    <div class="stat-grid">
      <div class="stat">
        <div class="num">
          {{ q.rule_coverage.places_with_rules }}/{{ q.rule_coverage.places_total }}
        </div>
        <div class="label">有规则的场所 / 场所总数</div>
      </div>
      <div class="stat">
        <div class="num">{{ pct(q.rule_coverage.coverage_ratio) }}</div>
        <div class="label">场所覆盖率</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.rules.current }}</div>
        <div class="label">生效中规则</div>
      </div>
      <div class="stat">
        <div class="num">{{ pct(q.rules.source_coverage) }}</div>
        <div class="label">规则携带来源比例</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.rules.review_overdue }}</div>
        <div class="label">复核逾期（仅生效中）</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.rules.never_verified }}</div>
        <div class="label">从未核验（生效中）</div>
      </div>
    </div>

    <h2>规则构成与时效</h2>
    <div class="two-col">
      <div class="panel">
        <table class="compact">
          <thead>
            <tr>
              <th>效果</th>
              <th>数量</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="[k, v] in buckets(q.rules.by_effect)" :key="k">
              <td class="mono">{{ k }}</td>
              <td>{{ v }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="panel">
        <dl class="kv">
          <dt>中位规则年龄</dt>
          <dd>{{ num(q.rules.age_days.median) }} 天</dd>
          <dt>最旧</dt>
          <dd>{{ num(q.rules.age_days.oldest) }} 天</dd>
          <dt>最新</dt>
          <dd>{{ num(q.rules.age_days.newest) }} 天</dd>
        </dl>
      </div>
    </div>

    <h2>候选管线</h2>
    <div class="stat-grid">
      <div class="stat">
        <div class="num">{{ q.candidates.total }}</div>
        <div class="label">候选总数</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.candidates.published }}</div>
        <div class="label">已发布</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.candidates.without_evidence }}</div>
        <div class="label">缺少证据包</div>
      </div>
      <div class="stat">
        <div class="num">{{ pct(q.candidates.evidence_coverage) }}</div>
        <div class="label">证据覆盖率</div>
      </div>
    </div>
    <div class="two-col">
      <div class="panel">
        <h3>按审核状态</h3>
        <table class="compact">
          <tbody>
            <tr v-for="[k, v] in buckets(q.candidates.by_status)" :key="k">
              <td class="mono">{{ k }}</td>
              <td>{{ v }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="panel">
        <h3>按规则层级</h3>
        <table class="compact">
          <tbody>
            <tr v-for="[k, v] in buckets(q.candidates.by_layer)" :key="k">
              <td class="mono">{{ k }}</td>
              <td>{{ v }}</td>
            </tr>
          </tbody>
        </table>
        <p class="hint">
          层级决定优先级：LEGAL 高于 OPERATOR_POLICY。若 LEGAL 计数异常偏低，说明来源层级
          在采集或回填环节丢失。
        </p>
      </div>
    </div>

    <h2>证据完整性</h2>
    <div class="stat-grid">
      <div class="stat">
        <div class="num">{{ q.evidence.artifacts_total }}</div>
        <div class="label">来源快照</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.evidence.bundles_total }}</div>
        <div class="label">证据包</div>
      </div>
      <div class="stat">
        <div class="num">{{ pct(q.evidence.hash_coverage) }}</div>
        <div class="label">内容哈希覆盖率</div>
      </div>
      <div class="stat">
        <div class="num">{{ pct(q.evidence.license_coverage) }}</div>
        <div class="label">许可元数据覆盖率</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.evidence.lead_only }}</div>
        <div class="label">仅线索类来源（不可直接发布）</div>
      </div>
    </div>

    <h2>来源与贡献</h2>
    <div class="stat-grid">
      <div class="stat">
        <div class="num">{{ q.provenance.sources_total }}</div>
        <div class="label">来源总数</div>
      </div>
      <div class="stat">
        <div class="num">{{ pct(q.provenance.official_ratio) }}</div>
        <div class="label">官方 / 管理方来源占比</div>
      </div>
      <div class="stat">
        <div class="num">{{ q.contributions.observations }}</div>
        <div class="label">观察记录（≠ 规则）</div>
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

    <h2>来源分级示例</h2>
    <div class="panel">
      <p class="hint">前台展示的来源徽标（与消费者端使用同一套语义）：</p>
      <div class="row" style="gap: 8px">
        <SourceBadge source-type="statute_or_regulation" />
        <SourceBadge source-type="government_service" />
        <SourceBadge source-type="official_operator_policy" />
        <SourceBadge source-type="onsite_verification" />
        <SourceBadge source-type="ordinary_user" />
        <SourceBadge :source-type="null" />
      </div>
    </div>

    <h2>说明</h2>
    <p class="muted">
      平台不做「可信度评分」，只展示可追溯的结构化指标（设计 #13 / #37）。 高影响规则必须携带
      Source；UNKNOWN 不会被当作允许或禁止。
    </p>
  </template>

  <StateMessage
    v-else
    kind="EMPTY"
    description="尚未取得任何质量指标数据。请确认已应用迁移且服务可访问数据库。"
  />
</template>
