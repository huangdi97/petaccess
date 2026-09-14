<script setup lang="ts">
import { onMounted, ref } from "vue";
import { client, ApiError, type BoundaryProfile } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import StateMessage from "../components/StateMessage.vue";
import { useOnline } from "../composables/useOnline";

/**
 * 共处边界：用户对「与动物共处」的自有条件。
 *
 * 这些是使用者自己的要求，不是对场所的评分。判定逐项进行，永不汇总为总分
 * （ADR / brief §8）。文案保持中性：描述「我能否接受」，而非「这家店好不好」。
 */

interface AttributeOption {
  value: string;
  label: string;
  stances: string[];
}

/** Attributes + which stances are meaningful for each. Mirrors the branches in
 *  `app.rulespec.v05_boundary.match()`. */
const ATTRIBUTES: AttributeOption[] = [
  { value: "off_leash", label: "脱绳活动", stances: ["avoid", "accept"] },
  { value: "designated_area", label: "指定活动区", stances: ["prefer", "avoid"] },
  {
    value: "indoor_access",
    label: "室内进入",
    stances: ["require_prohibited", "accept", "prefer"],
  },
  { value: "carrier_required", label: "要求装载（笼/包/推车）", stances: ["accept", "avoid"] },
  { value: "muzzle_required", label: "要求嘴套", stances: ["accept", "avoid"] },
  { value: "size_limit", label: "体型限制", stances: ["avoid", "accept"] },
  { value: "breed_limit", label: "品种限制", stances: ["avoid", "accept"] },
  { value: "peak_hours_restriction", label: "高峰时段限制", stances: ["prefer", "accept"] },
  { value: "dining_together", label: "可与同桌就餐", stances: ["prefer", "avoid"] },
  { value: "waiting_area", label: "设有等候区", stances: ["prefer", "avoid"] },
];

const STANCE_LABELS: Record<string, string> = {
  accept: "可接受",
  avoid: "希望没有",
  require_prohibited: "必须禁止（硬性）",
  prefer: "希望提供",
};

const profileName = ref("我的共处边界");
const chosen = ref<Record<string, string>>({});
const error = ref("");
const msg = ref("");
const busy = ref(false);
const loaded = ref(false);
const loading = ref(true);
const { online } = useOnline();

async function load() {
  error.value = "";
  loading.value = true;
  try {
    const res = await client.defaultBoundaryProfile();
    apply(res.profile);
  } catch (e) {
    error.value = e instanceof ApiError ? e.message : String(e);
  } finally {
    loaded.value = true;
    loading.value = false;
  }
}

function apply(p: BoundaryProfile | null) {
  if (!p) {
    chosen.value = {};
    return;
  }
  profileName.value = p.name || "我的共处边界";
  const next: Record<string, string> = {};
  for (const pref of p.preferences) next[pref.attribute] = pref.stance;
  chosen.value = next;
}

/** Tapping the active stance clears it — an unset attribute stays UNKNOWN
 *  rather than being coerced into a default (UNKNOWN ≠ allowed/prohibited). */
function pick(attribute: string, stance: string) {
  if (chosen.value[attribute] === stance) {
    delete chosen.value[attribute];
    chosen.value = { ...chosen.value };
  } else {
    chosen.value = { ...chosen.value, [attribute]: stance };
  }
}

async function save() {
  error.value = "";
  msg.value = "";
  if (!online.value) {
    error.value = "当前无网络连接，边界保存需要联网。";
    return;
  }
  busy.value = true;
  try {
    const preferences = Object.entries(chosen.value).map(([attribute, stance]) => ({
      attribute,
      stance,
      note: null,
    }));
    const saved = await client.saveBoundaryProfile({
      name: profileName.value || "我的共处边界",
      is_default: true,
      preferences,
    });
    apply(saved);
    msg.value = `已保存 ${preferences.length} 项边界${preferences.length ? "" : "（未设置项保持未知）"}`;
  } catch (e) {
    error.value =
      e instanceof ApiError
        ? `${e.message}${e.message.includes("登录") ? "" : "（需登录后保存）"}`
        : String(e);
  } finally {
    busy.value = false;
  }
}

onMounted(load);
</script>

<template>
  <AppShell>
    <div v-if="!online" class="offline-banner" data-testid="offline-banner">
      <span aria-hidden="true">⊘</span>
      <span>当前无网络连接：可查看已加载内容，保存操作已暂停。</span>
    </div>
    <SkeletonList v-if="loading" :rows="4" />
    <StateMessage
      v-else-if="error && !loaded"
      kind="ERROR"
      :description="`未能取得共处边界：${error}`"
    >
      <template #action>
        <button class="primary" @click="load">重试</button>
      </template>
    </StateMessage>
    <template v-else>
      <div v-if="error" class="panel" data-testid="boundary-error">{{ error }}</div>
      <div v-if="msg" class="panel" data-testid="boundary-msg">{{ msg }}</div>

      <div class="panel">
        <h1>共处边界</h1>
        <p class="muted" style="margin-top: 4px">
          这些是<strong>你自己的</strong>出行偏好，用来逐项比对场所公开记录。
          没设置的项保持「未知」，不会被当成允许或禁止。
        </p>
        <label>方案名称</label>
        <input v-model="profileName" placeholder="我的共处边界" />
      </div>

      <div v-for="attr in ATTRIBUTES" :key="attr.value" class="panel" data-testid="boundary-attr">
        <div style="font-weight: 600">{{ attr.label }}</div>
        <div class="row" style="margin-top: 8px">
          <button
            v-for="s in attr.stances"
            :key="s"
            class="pill"
            :class="{ active: chosen[attr.value] === s }"
            :data-testid="`stance-${attr.value}-${s}`"
            @click="pick(attr.value, s)"
          >
            {{ STANCE_LABELS[s] }}
          </button>
        </div>
        <div v-if="chosen[attr.value]" class="muted" style="margin-top: 6px">
          已选：{{ STANCE_LABELS[chosen[attr.value]] }}（再次点击可清除）
        </div>
      </div>

      <button
        class="primary block"
        :disabled="busy || !loaded || !online"
        data-testid="boundary-save"
        @click="save"
      >
        {{ busy ? "保存中…" : "保存边界" }}
      </button>

      <div class="panel" style="margin-top: 12px">
        <div class="muted">
          说明：边界仅用于「你」的比对结果，不是对场所的评分，也不会改变规则收录内容。
          服务犬适用独立的通行规则，不在此边界内判断。
        </div>
      </div>
    </template>
  </AppShell>
</template>
