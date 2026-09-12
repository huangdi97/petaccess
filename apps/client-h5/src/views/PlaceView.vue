<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  client, evaluatePlace, provenanceSummary, session, STATUS_GLYPHS,
  type Answer, type ObservationView, type PlaceSummary, type RuleView,
  type SourceView, type Zone,
} from "@petaccess/client-core";
import Shell from "../components/Shell.vue";

const route = useRoute();
const placeId = route.params.id as string;

const place = ref<{ id: string; canonical_name: string; place_type: string;
  canonical_address: string | null } | null>(null);
const zones = ref<Zone[]>([]);
const rules = ref<RuleView[]>([]);
const observations = ref<ObservationView[]>([]);
const verifications = ref<{ occurred_at: string; result: string; note: string | null }[]>([]);
const sources = ref<SourceView[]>([]);
const answer = ref<Answer | null>(null);
const error = ref("");
const watching = ref(false);
const quickMsg = ref("");

const sourceMap = computed(() => {
  const m = new Map<string, SourceView>();
  for (const s of sources.value) m.set(s.id, s);
  return m;
});
const prov = computed(() => provenanceSummary(rules.value, verifications.value));

async function evaluate() {
  const animal = session.activePet
    ? { species: session.activePet.species,
        service_role: session.activePet.service_role,
        weight_kg: session.activePet.weight_kg }
    : null;
  answer.value = await evaluatePlace(
    session.mode, animal, placeId, zones.value,
    (body) => client.evaluate(body as Parameters<typeof client.evaluate>[0]),
  );
}

// mode / pet switches re-run the deterministic evaluation immediately
watch(() => [session.mode, session.activePet], () => { void evaluate(); });

onMounted(async () => {
  try {
    place.value = await client.place(placeId);
    zones.value = await client.zones(placeId);
    rules.value = await client.rules(placeId);
    observations.value = await client.observations(placeId);
    verifications.value = await client.verifications(placeId);
    sources.value = (await client.allSources()).filter((s) =>
      rules.value.some((r) => r.source_id === s.id));
    await evaluate();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
});

async function quickConfirm(ruleId: string, result: "still_valid" | "changed" | "uncertain") {
  quickMsg.value = "";
  try {
    await client.verify({
      place_id: placeId, rule_id: ruleId, result,
      note: "Quick Confirm（现场快捷确认）",
      proximity_verified: true, distance_bucket: "<100m", accuracy_bucket: "10-50m",
    });
    quickMsg.value = result === "still_valid" ? "已记录：规则仍有效 ✓"
      : result === "changed" ? "已记录：规则已变化，进入复核" : "已记录：不确定";
    verifications.value = await client.verifications(placeId);
  } catch (e) {
    quickMsg.value = e instanceof Error ? `需要登录后才能核验：${e.message}` : String(e);
  }
}

async function toggleWatch() {
  try {
    const mine = await client.myWatches();
    const existing = mine.find((w) => w.target_type === "place" && w.target_id === placeId);
    if (existing) {
      await client.unwatch(existing.id);
      watching.value = false;
    } else {
      await client.watch("place", placeId);
      watching.value = true;
    }
  } catch (e) {
    quickMsg.value = e instanceof Error ? `关注失败（需登录）：${e.message}` : String(e);
  }
}

async function disputeFirstRule() {
  const target = rules.value.find((r) => r.status === "current");
  if (!target) return;
  quickMsg.value = "";
  try {
    await client.submitDispute({
      target_type: "access_rule", target_id: target.id,
      reason_code: "rule_inaccurate",
      notice_text: "用户报告：现场规则与收录内容不一致（请补充现场情况）",
    });
    quickMsg.value = "异议已提交，进入人工复核流程";
  } catch (e) {
    quickMsg.value = e instanceof Error ? `提交失败（需登录）：${e.message}` : String(e);
  }
}

const STATUS_TEXT: Record<string, string> = {
  MATCH: "可进入", CONDITIONAL: "有条件", RESTRICTED: "限制",
  UNKNOWN: "信息不足", CONFLICT: "冲突",
};
</script>

<template>
  <Shell>
    <div v-if="error" class="panel">{{ error }}</div>
    <template v-if="place">
      <div class="panel">
        <h1>{{ place.canonical_name }}</h1>
        <div class="muted" style="margin-top: 4px">
          {{ place.place_type }} · {{ place.canonical_address ?? "地址未收录" }}
          · 生效规则 {{ prov.ruleCount }} 条
        </div>
        <button style="margin-top: 10px" @click="toggleWatch">
          {{ watching ? "已关注规则变化 ✓（点击取消）" : "关注此场所规则变化" }}
        </button>
        <RouterLink :to="`/place/${placeId}/why`">
          <button style="margin-top: 10px; margin-left: 6px" class="primary" data-testid="open-why">
            为什么是这个结果
          </button>
        </RouterLink>
      </div>

      <div v-if="answer" class="answer panel" :class="'s-' + answer.status" data-testid="answer">
        <div class="muted">
          {{ session.activePet ? `对于：${session.activePet.display_name}` : "未选择宠物档案" }}
          · 模式：{{ session.mode === "with_pet" ? "带宠出行" :
                     session.mode === "restrictions" ? "普通宠物限制" :
                     session.mode === "service_dog" ? "服务犬通行" : "规则地图" }}
        </div>
        <div class="status" data-testid="answer-status">{{ answer.headline }}</div>
        <div v-if="answer.obligations.length" class="muted">
          条件：{{ answer.obligations.join(" · ") }}
        </div>
        <div v-if="answer.unknownInputs.length" class="muted">
          需要补充：{{ answer.unknownInputs.join("、") }}（不猜测）
        </div>
        <div class="notice">
          来源：{{ rules[0] ? (sourceMap.get(rules[0].source_id)?.issuer ?? "待收录") : "待收录" }}
          · 最近核验：{{ prov.latestVerified ? prov.latestVerified.slice(0, 10) : "暂无" }}
        </div>
      </div>

      <h2>分区域规则</h2>
      <div class="panel" data-testid="zones">
        <div v-if="!answer || (!answer.zones.length && !rules.length)" class="muted">
          暂无已收录规则（信息不足 ≠ 允许）
        </div>
        <div v-for="z in answer?.zones ?? []" :key="z.zone.id" class="zone-row">
          <span>{{ z.zone.name }}<span class="tag" v-if="z.zone.floor_ref" style="margin-left:6px">{{ z.zone.floor_ref }}</span></span>
          <span>
            <span class="tag" :class="'s-' + z.status" style="color:#fff; border:none">{{ STATUS_TEXT[z.status] ?? z.status }}</span>
            <span class="muted" v-if="z.obligations.length">{{ z.obligations.join(" · ") }}</span>
          </span>
        </div>
        <div v-for="r in rules.filter(r => !r.zone_id && r.status === 'current')" :key="r.id" class="zone-row">
          <span>全场 · {{ r.animal_scope }} · {{ r.action }}</span>
          <span>
            <span class="tag" :class="'s-' + r.effect.toUpperCase()" style="color:#fff; border:none">
              {{ r.effect === "allowed" ? "允许" : r.effect === "prohibited" ? "限制" : "有条件" }}
            </span>
          </span>
        </div>
      </div>

      <h2>规则来源与核验</h2>
      <div class="panel">
        <div v-for="r in rules.filter(r => r.status === 'current')" :key="r.id" class="zone-row">
          <span>
            {{ sourceMap.get(r.source_id)?.issuer ?? "来源 " + r.source_id.slice(0, 8) }}
            <span class="tag">{{ sourceMap.get(r.source_id)?.source_type ?? "?" }}</span>
          </span>
          <span class="muted">
            核验：{{ r.last_verified_at?.slice(0, 10) ?? "暂无" }}
            <button style="margin-left: 8px; padding: 4px 8px" @click="quickConfirm(r.id, 'still_valid')">仍有效</button>
            <button style="margin-left: 4px; padding: 4px 8px" @click="quickConfirm(r.id, 'changed')">已变化</button>
            <button style="margin-left: 4px; padding: 4px 8px" @click="quickConfirm(r.id, 'uncertain')">不确定</button>
          </span>
        </div>
        <div v-if="quickMsg" class="notice" data-testid="quick-msg">{{ quickMsg }}</div>
      </div>

      <h2>现场观察（与规则并存，不构成规则）</h2>
      <div class="panel">
        <div v-for="o in observations" :key="o.id" class="zone-row">
          <span>{{ o.occurred_at.slice(0, 10) }} · {{ o.animal_scope }} {{ o.observed_action }}</span>
          <span class="muted">{{ o.staff_action }}</span>
        </div>
        <div v-if="!observations.length" class="muted">暂无观察记录</div>
        <div class="notice">
          本页展示已收录的规则和历史现场记录，不构成场所实际无动物的保证。
        </div>
      </div>

      <h2>操作</h2>
      <div class="row">
        <RouterLink :to="`/contribute/${placeId}`" class="pill">报告规则 / 贡献</RouterLink>
        <button @click="disputeFirstRule">对此处规则提出异议</button>
      </div>
    </template>
  </Shell>
</template>
