<script setup lang="ts">
/** Contribution entry: five focused transaction launchers, not a generic form. */
import { type IconName } from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";
defineOptions({ name: "ContributeEntry" });

const emit = defineEmits<{
  select: [step: "quick" | "rule"];
  reality: [kind: "observed_presence" | "staff_response" | "animal_facility"];
}>();

type EntryOption =
  | {
      kind: "select";
      key: "quick" | "rule";
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
    label: "我看到或了解到一条规则",
    description: "规则牌、公告、工作人员说明或其他线索",
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
    label: "我看到工作人员怎么处理",
    description: "如何引导、提示、要求，或本次没有观察到进一步处理",
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
    description: "名称、地址或场所状态需要纠正",
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

<style scoped src="./ContributeEntry.css"></style>
