<script setup lang="ts">
/**
 * ContributeEntry — the first question of the Contribution transaction flow
 * (v0.2.4 §41): 你刚刚知道了什么？ with focused choice rows.
 *
 * Each choice is a real transaction launcher: icon + title + one-line
 * description + chevron + divider, row height 64–72px — never bare text rows.
 * Options map onto the existing step machine keys; testids asserted by the
 * e2e wizard (entry-quick, entry-reality-observed_presence) are preserved.
 */
import { type IconName } from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";
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
      description: string;
      icon: IconName;
    }
  | {
      kind: "reality";
      key: "observed_presence" | "staff_response" | "animal_facility";
      testid: string;
      label: string;
      description: string;
      icon: IconName;
    };

const OPTIONS: EntryOption[] = [
  {
    kind: "select",
    key: "rule",
    testid: "entry-rule",
    label: "我看到了新的规则",
    description: "规则牌、公告或正式说明",
    icon: "document",
  },
  {
    kind: "reality",
    key: "observed_presence",
    testid: "entry-reality-observed_presence",
    label: "我在现场看到动物",
    description: "是什么动物，在哪里，什么时间",
    icon: "eye",
  },
  {
    kind: "reality",
    key: "staff_response",
    testid: "entry-reality-staff_response",
    label: "工作人员进行了处理",
    description: "如何引导、提示或允许进入",
    icon: "info",
  },
  {
    kind: "reality",
    key: "animal_facility",
    testid: "entry-reality-animal_facility",
    label: "我发现了相关设施",
    description: "宠物区、饮水点、临时安置等",
    icon: "building",
  },
  {
    kind: "select",
    key: "quick",
    testid: "entry-quick",
    label: "场所信息有误",
    description: "名称、地址或当前结论需要纠正",
    icon: "flag",
  },
];

function choose(opt: EntryOption) {
  if (opt.kind === "reality") emit("reality", opt.key);
  else emit("select", opt.key);
}
</script>

<template>
  <div data-ui="contribution-flow">
    <h2 class="entry-question" data-testid="contribute-question">你刚刚知道了什么？</h2>
    <p class="muted entry-hint">选择最接近的一项。</p>
    <ul class="entry-options" role="list">
      <li v-for="opt in OPTIONS" :key="opt.testid" class="entry-option">
        <button
          type="button"
          class="entry-option__button"
          :data-testid="opt.testid"
          @click="choose(opt)"
        >
          <span class="entry-option__icon" aria-hidden="true">
            <PaIcon :name="opt.icon" size="lg" />
          </span>
          <span class="entry-option__text">
            <span class="entry-option__label">{{ opt.label }}</span>
            <span class="muted entry-option__description">{{ opt.description }}</span>
          </span>
          <span class="entry-option__chevron" aria-hidden="true">→</span>
        </button>
      </li>
    </ul>
    <p class="muted entry-note">提交内容会进入人工核验，AI 不会自动裁定。</p>
  </div>
</template>

<style scoped>
.entry-question {
  margin: 0;
  /* §44 mobile：24/32/650；desktop 保持页级标题。 */
  font-size: var(--pa-font-size-2xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-32);
  color: var(--pa-color-text-primary);
}
.entry-hint {
  margin: var(--pa-space-1) 0 0;
}
.entry-options {
  margin: var(--pa-space-5) 0 0;
  padding: 0;
  list-style: none;
}
/* §41：choice row 64–72px，icon + title + one-line desc + chevron + divider。 */
.entry-option {
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}
.entry-option:last-child {
  border-bottom: none;
}
.entry-option__button {
  display: flex;
  align-items: center;
  width: 100%;
  min-height: 64px;
  max-height: 72px;
  padding: var(--pa-space-2) var(--pa-space-1);
  border: none;
  border-radius: 0;
  background: transparent;
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-base);
  text-align: left;
  cursor: pointer;
  gap: var(--pa-space-3);
}
.entry-option__button:hover {
  color: var(--pa-color-accent);
}
.entry-option__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--pa-color-accent);
}
.entry-option__text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.entry-option__label {
  font-size: var(--pa-font-size-base);
  font-weight: var(--pa-font-weight-medium);
  color: var(--pa-color-text-primary);
}
.entry-option__description {
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.entry-option__chevron {
  margin-left: auto;
  flex-shrink: 0;
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-lg);
}
.entry-note {
  margin: var(--pa-space-4) 0 0;
}
</style>
