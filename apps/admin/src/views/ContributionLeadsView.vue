<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { errText, page, shortId, ts } from "../api";

interface VerificationLead {
  id: string;
  place_id: string;
  zone_id: string | null;
  user_id: string | null;
  event_type: string;
  note: string | null;
  evidence_refs: unknown[] | null;
  proximity_verified: boolean;
  created_at: string;
}

interface RuleCandidateLead {
  id: string;
  place_id: string | null;
  zone_id: string | null;
  animal_scope: string | null;
  effect: string | null;
  raw_text: string | null;
  media_id: string | null;
  review_status: string;
  supersedes_rule_id: string | null;
  created_at: string | null;
}

const ruleCandidates = ref<RuleCandidateLead[]>([]);
const corrections = ref<VerificationLead[]>([]);
const error = ref("");
const loading = ref(true);

const total = computed(() => ruleCandidates.value.length + corrections.value.length);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const [rules, places] = await Promise.all([
      page<RuleCandidateLead>("/admin/candidates", {
        limit: 100,
        review_status: "REVIEW_PENDING",
      }),
      page<VerificationLead>("/admin/place-corrections", { limit: 100 }),
    ]);
    ruleCandidates.value = rules.items;
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
        <h1>贡献与待核验输入</h1>
        <p class="muted">
          这里只汇总还没有成为正式事实的输入。规则线索已经进入 RuleCandidate 人工审核路径；场所纠错仍保持独立，避免误写 Rule 或 Reality。
        </p>
      </div>
      <button @click="load">刷新</button>
    </div>

    <div class="governance-note">
      <strong>处理边界</strong>
      <span>规则线索 → RuleCandidate → Human Review → Publish</span>
      <span>场所纠错 → 人工核对 → 在 Place 数据路径中修订</span>
      <span>任何用户提交都不会自动变成正式规则或现场事实。</span>
    </div>

    <div v-if="error" class="error-banner">{{ error }}</div>
    <p v-if="loading" class="muted">正在读取待核验输入…</p>
    <p v-else class="muted">当前列表共 {{ total }} 条。</p>

    <section class="queue-section">
      <div class="queue-head">
        <h2>待审核规则候选</h2>
        <RouterLink to="/rule-candidates">进入完整规则候选队列 →</RouterLink>
      </div>
      <table class="compact">
        <thead>
          <tr>
            <th>候选</th>
            <th>场所</th>
            <th>作用域</th>
            <th>效果</th>
            <th>线索类型</th>
            <th>线索摘要</th>
            <th>证据</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in ruleCandidates" :key="item.id">
            <td class="mono">{{ shortId(item.id) }}</td>
            <td>
              <RouterLink v-if="item.place_id" :to="`/places/${item.place_id}`">
                {{ shortId(item.place_id) }}
              </RouterLink>
              <span v-else>属地 / 未绑定场所</span>
            </td>
            <td>{{ item.animal_scope || "待审核" }}</td>
            <td>{{ item.effect || "待审核" }}</td>
            <td>
              <span v-if="item.supersedes_rule_id">
                报告现行规则变化 · {{ shortId(item.supersedes_rule_id) }}
              </span>
              <span v-else>新增 / 未指定替换对象</span>
            </td>
            <td class="lead-note">{{ item.raw_text || "未补充文字说明" }}</td>
            <td>{{ item.media_id ? "含媒体证据" : "无媒体" }}</td>
            <td>{{ ts(item.created_at) }}</td>
          </tr>
          <tr v-if="!loading && !ruleCandidates.length">
            <td colspan="8" class="muted">当前没有待审核规则候选。</td>
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
            <th>证据</th>
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
            <td>{{ item.evidence_refs?.length ? `${item.evidence_refs.length} 项` : "无附件" }}</td>
            <td>{{ ts(item.created_at) }}</td>
          </tr>
          <tr v-if="!loading && !corrections.length">
            <td colspan="5" class="muted">当前没有场所纠错线索。</td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>

<style scoped src="./ContributionLeadsView.css"></style>
