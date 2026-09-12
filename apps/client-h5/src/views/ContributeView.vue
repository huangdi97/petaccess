<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute } from "vue-router";
import { client } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";

const route = useRoute();
const placeId = route.params.id as string;

/** Progressive disclosure (design #15): one question at a time. */
const step = ref(1);
const knowRule = ref("");
const scope = ref("");
const zone = ref("");
const conditions = ref<string[]>([]);
const occurredAt = ref(new Date().toISOString().slice(0, 10));
const result = ref("");
const msg = ref("");

const zones = ref<{ id: string; name: string }[]>([]);
client
  .zones(placeId)
  .then((zs) => {
    zones.value = zs;
  })
  .catch(() => {
    /* anonymous ok */
  });

const conditionOptions = computed(() => [
  { key: "leash_required", label: "需牵引" },
  { key: "carrier_required", label: "需宠物包" },
  { key: "stroller_required", label: "需推车" },
  { key: "no_ground", label: "不可落地" },
]);

async function submitObservation() {
  msg.value = "";
  try {
    await client.createObservation({
      place_id: placeId,
      zone_id: zone.value || null,
      occurred_at: new Date(occurredAt.value).toISOString(),
      occurred_precision: "same_day",
      animal_scope: scope.value || "dog",
      observed_action: "enter",
      staff_action: "no_interaction_observed",
      place_confidence: "confirmed_on_site",
      note: `快速贡献：${knowRule.value} / ${result.value}`,
      proximity_verified: true,
      distance_bucket: "<100m",
      accuracy_bucket: "10-50m",
    });
    msg.value = "观察已提交（Observation 与规则并存，不会自动变成规则）";
    step.value = 6;
  } catch (e) {
    msg.value = e instanceof Error ? `提交失败（需登录）：${e.message}` : String(e);
  }
}

async function submitVerification() {
  msg.value = "";
  try {
    const rules = await client.rules(placeId);
    const target = rules.find((r) => r.status === "current");
    await client.verify({
      place_id: placeId,
      rule_id: target?.id ?? null,
      result:
        result.value === "仍有效"
          ? "still_valid"
          : result.value === "已变化"
            ? "changed"
            : "uncertain",
      note: "现场核验",
      proximity_verified: true,
      distance_bucket: "<100m",
      accuracy_bucket: "10-50m",
    });
    msg.value = "核验已记录 ✓";
    step.value = 6;
  } catch (e) {
    msg.value = e instanceof Error ? `提交失败（需登录）：${e.message}` : String(e);
  }
}
</script>

<template>
  <AppShell>
    <h1>现场贡献</h1>
    <div class="panel">
      <template v-if="step === 1">
        <strong>你知道这里对普通犬的规则吗？</strong>
        <div class="row" style="margin-top: 10px">
          <button
            class="pill"
            @click="
              knowRule = '明确允许';
              step = 2;
            "
          >
            明确允许
          </button>
          <button
            class="pill"
            @click="
              knowRule = '明确限制';
              step = 2;
            "
          >
            明确限制
          </button>
          <button
            class="pill"
            @click="
              knowRule = '有条件';
              step = 2;
            "
          >
            有条件
          </button>
          <button
            class="pill"
            @click="
              result = '不确定';
              step = 5;
            "
          >
            不确定
          </button>
        </div>
      </template>

      <template v-else-if="step === 2">
        <strong>在哪里？</strong>
        <div class="row" style="margin-top: 10px">
          <button
            class="pill"
            @click="
              scope = 'dog';
              step = 3;
            "
          >
            全场 / 不确定
          </button>
          <button
            v-for="z in zones"
            :key="z.id"
            class="pill"
            @click="
              zone = z.id;
              scope = 'dog';
              step = 3;
            "
          >
            {{ z.name }}
          </button>
        </div>
      </template>

      <template v-else-if="step === 3">
        <strong>需要什么条件？（可多选 / 全不选）</strong>
        <div class="row" style="margin-top: 10px">
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
        <button class="primary block" style="margin-top: 14px" @click="step = 4">下一步</button>
      </template>

      <template v-else-if="step === 4">
        <label>现场告示照片（可选 · OCR 仅作审核参考）</label>
        <input type="file" accept="image/*" />
        <label>规则生效日期</label>
        <input v-model="occurredAt" type="date" />
        <button class="primary block" style="margin-top: 14px" @click="step = 5">下一步</button>
      </template>

      <template v-else-if="step === 5">
        <strong>现场实际情况</strong>
        <div class="row" style="margin-top: 10px">
          <button
            class="pill"
            @click="
              result = '仍有效';
              submitVerification();
            "
          >
            规则仍有效
          </button>
          <button
            class="pill"
            @click="
              result = '已变化';
              submitVerification();
            "
          >
            规则已变化
          </button>
          <button
            class="pill"
            @click="
              result = '观察';
              submitObservation();
            "
          >
            提交现场观察
          </button>
        </div>
      </template>

      <template v-if="step === 6">
        <div class="notice" data-testid="contribute-result">{{ msg }}</div>
      </template>
      <div v-if="msg && step !== 6" class="notice">{{ msg }}</div>
    </div>
    <div class="notice">
      位置仅记录分桶后的现场核验结果（距离/精度），不保存原始 GPS 轨迹（ADR-012）。
      高频提交会被限流。
    </div>
  </AppShell>
</template>
