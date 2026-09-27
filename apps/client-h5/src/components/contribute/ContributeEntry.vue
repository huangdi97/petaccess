<script setup lang="ts">
/**
 * ContributeEntry — the first question of the Contribution transaction flow
 * (freeze §9): 你刚刚知道了什么？ with consumer-language options only.
 * Options map onto the existing step machine keys; testids asserted by the
 * e2e wizard (entry-quick, entry-reality-observed_presence) are preserved.
 */
defineOptions({ name: "ContributeEntry" });

const emit = defineEmits<{
  select: [step: "quick" | "signage" | "rule" | "experience"];
  reality: [kind: "observed_presence" | "staff_response" | "animal_facility"];
}>();

type EntryOption =
  | {
      kind: "select";
      key: "quick" | "signage" | "rule" | "experience";
      testid: string;
      label: string;
    }
  | {
      kind: "reality";
      key: "observed_presence" | "staff_response" | "animal_facility";
      testid: string;
      label: string;
    };

const OPTIONS: EntryOption[] = [
  { kind: "select", key: "rule", testid: "entry-rule", label: "我看到了新的规则" },
  {
    kind: "reality",
    key: "observed_presence",
    testid: "entry-reality-observed_presence",
    label: "我在现场看到动物",
  },
  {
    kind: "reality",
    key: "staff_response",
    testid: "entry-reality-staff_response",
    label: "工作人员进行了处理",
  },
  {
    kind: "reality",
    key: "animal_facility",
    testid: "entry-reality-animal_facility",
    label: "我发现了相关设施",
  },
  { kind: "select", key: "quick", testid: "entry-quick", label: "场所信息有误" },
];

function choose(opt: EntryOption) {
  if (opt.kind === "reality") emit("reality", opt.key);
  else emit("select", opt.key);
}
</script>

<template>
  <div>
    <h2 class="entry-question">你刚刚知道了什么？</h2>
    <p class="muted entry-hint">只提供结构化选项，不设自由评论区，以避免未经核实的评价影响判断。</p>
    <ul class="entry-options" role="list">
      <li v-for="opt in OPTIONS" :key="opt.testid" class="entry-option">
        <button
          type="button"
          class="entry-option__button"
          :data-testid="opt.testid"
          @click="choose(opt)"
        >
          {{ opt.label }}
        </button>
      </li>
    </ul>
    <p class="muted entry-note">提交进入人工审核队列，AI 不会自动裁定。</p>
  </div>
</template>

<style scoped>
.entry-question {
  margin: 0;
  font-size: var(--pa-font-size-xl);
  color: var(--pa-color-text-primary);
}
.entry-hint {
  margin: var(--pa-space-2) 0 0;
}
.entry-options {
  margin: var(--pa-space-4) 0 0;
  padding: 0;
  list-style: none;
}
.entry-option {
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.entry-option:last-child {
  border-bottom: none;
}
.entry-option__button {
  display: block;
  width: 100%;
  min-height: var(--pa-layout-touch-target);
  padding: var(--pa-space-3) 0;
  border: none;
  border-radius: 0;
  background: transparent;
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-base);
  text-align: left;
  cursor: pointer;
}
.entry-option__button:hover {
  color: var(--pa-color-accent);
}
.entry-note {
  margin: var(--pa-space-4) 0 0;
}
</style>
