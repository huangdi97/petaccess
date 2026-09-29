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
          查询对象与视角决定「进入 / 限制」结论的求值上下文；切换后结果会按新上下文重新获取。
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
          动作：进入（当前仅支持进入查询）；范围：公共区域。服务犬模式按「工作犬」求值。
        </p>
      </div>
    </PaDialog>
  </div>
</template>

<style scoped>
.query-context {
  display: flex;
  align-items: center;
  gap: var(--pa-space-2);
  padding: var(--pa-space-2) var(--pa-space-4);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border);
  background: var(--pa-color-surface);
  font-size: var(--pa-font-size-md);
}

.query-context__label {
  color: var(--pa-color-text-muted);
}

.query-context__value {
  color: var(--pa-color-text-primary);
  font-weight: var(--pa-font-weight-medium);
}

.query-context__edit {
  margin-left: auto;
  padding: var(--pa-space-1) var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
  color: var(--pa-color-accent);
  font: inherit;
  font-size: var(--pa-font-size-md);
  cursor: pointer;
}

.query-context__edit:hover {
  border-color: var(--pa-color-accent);
}

.query-context__form {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-4);
}

.query-context__hint,
.query-context__note {
  margin: 0;
}

.query-context__modes {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
}

.query-context__mode {
  min-height: var(--pa-layout-touch-target);
  padding: 0 var(--pa-space-4);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
  color: var(--pa-color-text-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.query-context__mode:hover {
  border-color: var(--pa-color-accent);
}

.query-context__mode--active {
  border-color: var(--pa-color-accent);
  background: var(--pa-color-accent-weak);
  color: var(--pa-color-accent);
  font-weight: var(--pa-font-weight-medium);
}
</style>
