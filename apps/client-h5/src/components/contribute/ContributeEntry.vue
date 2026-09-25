<script setup lang="ts">
/** ContributeEntry — M7 wizard type picker (结构化入口，无自由评论区). */
defineOptions({ name: "ContributeEntry" });

defineEmits<{
  select: [step: "quick" | "signage" | "rule" | "experience"];
  reality: [kind: "observed_presence" | "staff_response" | "animal_facility"];
}>();

const REALITY_KINDS = [
  { key: "observed_presence", label: "我刚刚看到动物" },
  { key: "staff_response", label: "我看到工作人员怎么处理" },
  { key: "animal_facility", label: "我发现这里有动物相关设施" },
] as const;
</script>

<template>
  <div>
    <strong>你想提供哪一类信息？</strong>
    <p class="muted" style="margin-top: 4px">
      只提供结构化选项，不设自由评论区，以避免未经核实的评价影响判断。
    </p>
    <div class="row" style="margin-top: 10px">
      <button class="pill" data-testid="entry-quick" @click="$emit('select', 'quick')">
        快速确认
      </button>
      <button class="pill" data-testid="entry-signage" @click="$emit('select', 'signage')">
        拍规则牌
      </button>
      <button class="pill" data-testid="entry-rule" @click="$emit('select', 'rule')">
        我知道规则
      </button>
      <button class="pill" data-testid="entry-experience" @click="$emit('select', 'experience')">
        我有现场经历
      </button>
    </div>
    <div
      class="row"
      style="margin-top: 10px; border-top: 1px dashed var(--line); padding-top: 10px"
    >
      <button
        v-for="k in REALITY_KINDS"
        :key="k.key"
        class="pill"
        :data-testid="'entry-reality-' + k.key"
        @click="$emit('reality', k.key)"
      >
        {{ k.label }}
      </button>
    </div>
    <p class="muted" style="margin-top: 6px">
      v0.9 现场贡献：只回答结构化问题；提交进入人工审核队列，AI 不会自动裁定。
    </p>
  </div>
</template>
