<script setup lang="ts">
import { onMounted, ref } from "vue";
import { client, ApiError, session, type BoundaryProfile } from "@petaccess/client-core";
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
    // Signed out there is no profile to fetch and the endpoint answers 401;
    // explain that in plain language instead of surfacing the transport error.
    if (!session.signedIn) {
      apply(null);
      error.value = "共处边界保存在你的账号下：登录后即可设置并同步到各页面。";
      return;
    }
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
      <header class="boundary-head">
        <h1>共处边界</h1>
        <p class="muted">
          这些是你自己的出行偏好，只用于逐项比对场所公开记录，不形成场所总分。
          没有设置的项目会保持信息不足。
        </p>
      </header>

      <p v-if="error" class="boundary-feedback" data-testid="boundary-error">{{ error }}</p>
      <p v-if="msg" class="boundary-feedback" data-testid="boundary-msg">{{ msg }}</p>

      <label class="boundary-name">
        <span>方案名称</span>
        <input v-model="profileName" aria-label="共处边界名称" placeholder="我的共处边界" />
      </label>

      <section class="boundary-list" aria-label="共处偏好">
        <div
          v-for="attr in ATTRIBUTES"
          :key="attr.value"
          class="boundary-row"
          data-testid="boundary-attr"
        >
          <div class="boundary-row__body">
            <strong>{{ attr.label }}</strong>
            <span v-if="chosen[attr.value]" class="muted">
              当前：{{ STANCE_LABELS[chosen[attr.value]] }}
            </span>
            <span v-else class="muted">未设置</span>
          </div>

          <div class="boundary-choices" :aria-label="attr.label">
            <button
              v-for="s in attr.stances"
              :key="s"
              type="button"
              class="boundary-choice"
              :class="{ 'boundary-choice--active': chosen[attr.value] === s }"
              :aria-pressed="chosen[attr.value] === s"
              :data-testid="`stance-${attr.value}-${s}`"
              @click="pick(attr.value, s)"
            >
              {{ STANCE_LABELS[s] }}
            </button>
          </div>
        </div>
      </section>

      <div class="boundary-actions">
        <button
          class="primary"
          :disabled="busy || !loaded || !online"
          data-testid="boundary-save"
          @click="save"
        >
          {{ busy ? "保存中…" : "保存边界" }}
        </button>
      </div>

      <p class="boundary-note muted">
        共处边界只改变“是否符合你的偏好”的逐项展示，不改变场所规则、现场事实或服务犬通行规则。
      </p>
    </template>
  </AppShell>
</template>

<style scoped>
.boundary-head {
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.boundary-head p {
  max-width: 680px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.boundary-feedback {
  margin: var(--pa-space-3) 0 0;
  color: var(--pa-color-text-secondary);
}

.boundary-name {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  max-width: 420px;
  padding: var(--pa-space-5) 0;
  font-size: var(--pa-font-size-md);
}

.boundary-name input {
  margin: 0;
}

.boundary-list {
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.boundary-row {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) auto;
  align-items: center;
  gap: var(--pa-space-5);
  min-height: 72px;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.boundary-row__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.boundary-choices {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--pa-space-1);
}

.boundary-choice {
  min-height: 36px;
  padding: 0 var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface);
  color: var(--pa-color-text-secondary);
  cursor: pointer;
}

.boundary-choice:hover,
.boundary-choice:focus-visible {
  border-color: var(--pa-color-accent);
}

.boundary-choice--active {
  border-color: var(--pa-color-accent);
  background: var(--pa-color-accent-weak);
  color: var(--pa-color-accent);
  font-weight: var(--pa-font-weight-600);
}

.boundary-actions {
  padding-top: var(--pa-space-5);
}

.boundary-note {
  margin: var(--pa-space-5) 0 0;
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
  line-height: var(--pa-line-height-20);
}

@media (max-width: 767px) {
  .boundary-row {
    grid-template-columns: 1fr;
    gap: var(--pa-space-2);
    align-items: flex-start;
  }

  .boundary-choices {
    justify-content: flex-start;
  }
}
</style>
