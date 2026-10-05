<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { errText, page, shortId, ts } from "../api";

interface VerificationLead {
  id: string;
  place_id: string;
  zone_id: string | null;
  rule_id: string | null;
  user_id: string | null;
  event_type: string;
  result: string;
  note: string | null;
  evidence_refs: unknown[] | null;
  proximity_verified: boolean;
  occurred_at: string;
  created_at: string;
}

const ruleLeads = ref<VerificationLead[]>([]);
const corrections = ref<VerificationLead[]>([]);
const error = ref("");
const loading = ref(true);

const RULE_LEAD_LABELS: Record<string, string> = {
  rule_lead_submitted: "规则线索",
  signage_uploaded: "规则牌证据",
};

const total = computed(() => ruleLeads.value.length + corrections.value.length);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [rules, places] = await Promise.all([
      page<VerificationLead>("/admin/rule-leads", { limit: 100 }),
      page<VerificationLead>("/admin/place-corrections", { limit: 100 }),
    ]);
    ruleLeads.value = rules.items;
    corrections.value = places.items;
  } catch (e) {
    error.value = errText(e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <section>
    <div class="page-head">
      <div>
        <h1>用户贡献线索</h1>
        <p class="muted">
          这里收拢尚未成为正式事实的用户输入。规则线索不会自动成为 Rule，场所纠错也不会直接覆盖 Place。
        </p>
      </div>
      <button @click="load">刷新</button>
    </div>

    <div class="governance-note">
      <strong>处理边界</strong>
      <span>规则线索 → 建立来源/证据 → RuleCandidate → Human Review → Publish</span>
      <span>场所纠错 → 人工核对 → 在正确的 Place 数据路径中修订</span>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <p v-if="loading" class="muted">正在读取待核验线索…</p>
    <p v-else class="muted">当前共 {{ total }} 条待人工查看的线索。</p>

    <section class="queue-section">
      <div class="queue-head">
        <h2>规则 / 规则牌线索</h2>
        <RouterLink to="/rule-candidates">查看规则候选 →</RouterLink>
      </div>
      <table class="compact">
        <thead>
          <tr>
            <th>类型</th>
            <th>场所</th>
            <th>区域</th>
            <th>提交内容</th>
            <th>证据</th>
            <th>提交时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in ruleLeads" :key="item.id">
            <td>{{ RULE_LEAD_LABELS[item.event_type] ?? "规则线索" }}</td>
            <td>
              <RouterLink :to="`/places/${item.place_id}`">
                {{ shortId(item.place_id) }}
              </RouterLink>
            </td>
            <td class="mono">{{ item.zone_id ? shortId(item.zone_id) : "全场 / 未确认" }}</td>
            <td class="lead-note">{{ item.note || "未补充文字说明" }}</td>
            <td>{{ item.evidence_refs?.length ? `${item.evidence_refs.length} 项` : "无附件" }}</td>
            <td>{{ ts(item.created_at) }}</td>
          </tr>
          <tr v-if="!loading && !ruleLeads.length">
            <td colspan="6" class="muted">当前没有规则线索。</td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="queue-section">
      <div class="queue-head">
        <h2>场所纠错线索</h2>
        <RouterLink to="/places">查看场所 →</RouterLink>
      </div>
      <table class="compact">
        <thead>
          <tr>
            <th>场所</th>
            <th>提交内容</th>
            <th>现场接近信息</th>
            <th>提交时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in corrections" :key="item.id">
            <td>
              <RouterLink :to="`/places/${item.place_id}`">
                {{ shortId(item.place_id) }}
              </RouterLink>
            </td>
            <td class="lead-note">{{ item.note || "未补充文字说明" }}</td>
            <td>{{ item.proximity_verified ? "有现场接近证据" : "未使用现场接近证据" }}</td>
            <td>{{ ts(item.created_at) }}</td>
          </tr>
          <tr v-if="!loading && !corrections.length">
            <td colspan="4" class="muted">当前没有场所纠错线索。</td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<style scoped>
.page-head,
.queue-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-head p {
  max-width: 760px;
}

.governance-note {
  display: grid;
  gap: 6px;
  margin: 16px 0 20px;
  padding: 12px 14px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--pa-color-bg-app);
  font-size: 13px;
}

.governance-note span {
  color: var(--muted);
}

.queue-section {
  margin-top: 28px;
}

.queue-head {
  align-items: baseline;
  margin-bottom: 10px;
}

.queue-head h2 {
  margin: 0;
}

.lead-note {
  max-width: 520px;
  white-space: normal;
  overflow-wrap: anywhere;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
</style>
