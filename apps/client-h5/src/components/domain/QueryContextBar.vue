<script setup lang="ts">
/**
 * QueryContextBar — the unified Consumer query primitive (Design Freeze §8).
 *
 * Shown on Home / Search / Map / Place as a toolbar line (desktop) or a light
 * sticky strip (mobile). Displays the CURRENT query derived from the API
 * contract (animal · action · scope). Editing opens a popover/panel (desktop)
 * or bottom sheet (mobile) and changes the session query mode — which changes
 * the consumer cache key (currentQueryContext in repository.ts) so snapshots
 * are refetched for the new question. It never invents query fields the API
 * does not accept.
 */
import { computed, ref } from "vue";
import { session, type QueryMode } from "@petaccess/client-core";
import PaDialog from "../ui/PaDialog.vue";

defineOptions({ name: "QueryContextBar" });

const open = ref(false);

const MODES: { key: QueryMode; label: string }[] = [
  { key: "with_pet", label: "普通携带" },
  { key: "service_dog", label: "服务犬通行" },
  { key: "rules_only", label: "规则视角" },
];

const speciesLabel = computed(() => {
  const s = session.activePet?.species ?? "dog";
  if (session.mode === "service_dog") return "服务犬";
  return s === "dog" ? "普通犬" : s === "cat" ? "猫" : "其他宠物";
});

/** 当前查询：动物 / 动作 / 范围 —— 全部来自 currentQueryContext 同源字段。 */
const summary = computed(() => `${speciesLabel.value} · 进入 · 公共区域`);

function selectMode(m: QueryMode) {
  session.mode = m;
  open.value = false;
}
</script>

<template>
  <div class="query-context" data-testid="query-context" data-ui="query-context">
    <span class="query-context__label" aria-hidden="true">当前查询</span>
    <span class="query-context__value" data-testid="query-context-summary">{{ summary }}</span>
    <button
      type="button"
      class="query-context__edit"
      data-testid="query-context-edit"
      aria-label="修改当前查询"
      @click="open = true"
    >
      修改
    </button>

    <PaDialog :open="open" :title="'当前查询：' + summary" @close="open = false">
      <div class="query-context__form">
        <p class="query-context__hint">
          你带哪类动物、以什么身份进入，会影响页面显示的准入结论。修改后会按新的问题重新查询。
        </p>
        <div class="query-context__modes" role="group" aria-label="查询视角">
          <button
            v-for="m in MODES"
            :key="m.key"
            type="button"
            class="query-context__mode"
            :class="{ 'query-context__mode--active': session.mode === m.key }"
            :aria-pressed="session.mode === m.key"
            @click="selectMode(m.key)"
          >
            {{ m.label }}
          </button>
        </div>
        <p class="query-context__note muted">
          当前问题是「进入公共区域」。选择服务犬通行时，会按服务犬对应的规则条件查询。
        </p>
      </div>
    </PaDialog>
  </div>
</template>

<style scoped src="./QueryContextBar.css"></style>
