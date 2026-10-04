<script setup lang="ts">
import { onMounted, ref } from "vue";
import { client, session } from "@petaccess/client-core";
import { EMPTY_STATE_COPY } from "@petaccess/design-tokens";
import AppShell from "../components/AppShell.vue";
import StateMessage from "../components/StateMessage.vue";
import { animalScopeLabel } from "../consumer/labels";
import { CANDIDATE_TYPE_LABELS, contributionStatusLabel } from "../reality";
import { presentDescription } from "../errors";

const pets = ref<Awaited<ReturnType<typeof client.myPets>>>([]);
const watches = ref<Awaited<ReturnType<typeof client.myWatches>>>([]);
const contributions = ref<Awaited<ReturnType<typeof client.myRealityContributions>>>([]);
const error = ref("");

const WATCH_LABELS: Record<string, string> = {
  place: "场所规则变化",
  zone: "区域规则变化",
  rule: "规则变化",
  regulation: "法规变化",
};

onMounted(async () => {
  await session.restore();
  if (!session.signedIn) return;
  try {
    pets.value = await client.myPets();
    watches.value = await client.myWatches();
    contributions.value = await client.myRealityContributions();
  } catch (e) {
    error.value = presentDescription(e);
  }
});

function petMeta(p: (typeof pets.value)[number]): string {
  const parts = [animalScopeLabel(p.species), p.breed_text ?? ""].filter(Boolean);
  if (p.weight_kg) parts.push(`${p.weight_kg} kg`);
  if (p.service_role !== "none") parts.push("服务犬（用户声明）");
  return parts.join(" · ");
}

function setActivePet(p: (typeof pets.value)[number]) {
  session.activePet = p;
  session.mode = "with_pet";
}
</script>

<template>
  <AppShell>
    <header class="mine-head">
      <h1>我的</h1>
      <template v-if="session.signedIn">
        <strong class="mine-head__name">{{ session.user?.display_name }}</strong>
        <span class="muted">{{ session.user?.email }}</span>
      </template>
    </header>

    <StateMessage v-if="error" kind="ERROR" :description="error" data-testid="mine-error" />

    <StateMessage
      v-if="!session.signedIn"
      kind="EMPTY"
      title="登录后管理你的出行设置"
      description="宠物档案、规则关注和贡献记录只在登录后显示。公开场所信息仍可免登录浏览。"
    >
      <template #action>
        <RouterLink class="btn primary" to="/onboarding">登录 / 注册</RouterLink>
      </template>
    </StateMessage>

    <template v-else>
      <section class="mine-section">
        <div class="mine-section__head">
          <div>
            <h2>宠物档案</h2>
            <p class="muted">用于当前查询中真正需要的物种、体重或角色条件。</p>
          </div>
          <RouterLink class="btn-inline" to="/pets" data-testid="open-pet-profile">
            管理档案 →
          </RouterLink>
        </div>

        <div v-for="p in pets" :key="p.id" class="mine-row">
          <div class="mine-row__body">
            <strong>{{ p.display_name }}</strong>
            <span class="muted">{{ petMeta(p) }}</span>
          </div>
          <button
            type="button"
            class="mine-row__action"
            :aria-pressed="session.activePet?.id === p.id"
            @click="setActivePet(p)"
          >
            {{ session.activePet?.id === p.id ? "本次使用中" : "设为本次对象" }}
          </button>
        </div>
        <p v-if="!pets.length" class="mine-empty">
          还没有宠物档案。没有必要为了浏览公开规则先建立档案。
        </p>
      </section>

      <section class="mine-section">
        <div class="mine-section__head">
          <div>
            <h2>关注的规则变化</h2>
            <p class="muted">只显示你主动关注的变化，不把它们解释成新的准入结论。</p>
          </div>
          <RouterLink class="btn-inline" to="/notifications" data-testid="open-notifications">
            通知中心 →
          </RouterLink>
        </div>

        <div v-for="w in watches" :key="w.id" class="mine-row">
          <div class="mine-row__body">
            <strong>{{ WATCH_LABELS[w.target_type] ?? "已关注的规则变化" }}</strong>
            <span class="muted">等待后续规则版本更新</span>
          </div>
        </div>
        <p v-if="!watches.length" class="mine-empty">暂无关注。</p>
      </section>

      <section class="mine-section">
        <div class="mine-section__head">
          <div>
            <h2>我的贡献</h2>
            <p class="muted">提交内容与正式规则分开保存，只有经过核验后才进入相应记录。</p>
          </div>
        </div>

        <div
          v-for="c in contributions"
          :key="c.report_id"
          class="mine-contribution"
          data-testid="contribution-row"
        >
          <time class="mine-contribution__date">{{
            new Date(c.created_at ?? 0).toLocaleDateString("zh-CN")
          }}</time>
          <div class="mine-contribution__facts">
            <span v-for="cand in c.candidates" :key="cand.candidate_type + (cand.observed_at ?? '')">
              {{ CANDIDATE_TYPE_LABELS[cand.candidate_type] ?? "现场信息" }}
              · {{ contributionStatusLabel(cand) }}
            </span>
          </div>
        </div>
        <p v-if="!contributions.length" class="mine-empty" data-testid="contributions-empty">
          {{ EMPTY_STATE_COPY.CONTRIBUTION_HISTORY.title }} —
          {{ EMPTY_STATE_COPY.CONTRIBUTION_HISTORY.description }}
        </p>
      </section>

      <section class="mine-section">
        <div class="mine-section__head">
          <div>
            <h2>共处边界</h2>
            <p class="muted">
              这是你自己的出行偏好，只用于逐项比对公开事实，不形成场所总分。
            </p>
          </div>
          <RouterLink class="btn-inline" to="/boundary" data-testid="open-boundary">
            设置边界 →
          </RouterLink>
        </div>
      </section>

      <section class="mine-section">
        <div class="mine-section__head">
          <div>
            <h2>隐私与设置</h2>
            <p class="muted">
              位置仅用于附近查询或现场核验；不建立连续位置轨迹，不根据照片认定服务犬身份。
            </p>
          </div>
        </div>
        <nav class="mine-links" aria-label="隐私与设置">
          <RouterLink class="btn-inline" to="/privacy" data-testid="open-privacy">
            隐私与数据 →
          </RouterLink>
          <RouterLink class="btn-inline" to="/settings" data-testid="open-settings">
            设置与说明 →
          </RouterLink>
        </nav>
      </section>

      <button class="mine-logout" type="button" @click="session.logout()">退出登录</button>
    </template>
  </AppShell>
</template>

<style scoped>
.mine-head {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.mine-head__name {
  margin-top: var(--pa-space-2);
  font-size: var(--pa-font-size-lg);
}

.mine-section {
  padding: var(--pa-space-5) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.mine-section__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--pa-space-4);
  margin-bottom: var(--pa-space-3);
}

.mine-section h2 {
  margin: 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}

.mine-section__head p {
  margin: var(--pa-space-1) 0 0;
  max-width: 560px;
}

.mine-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-4);
  min-height: 56px;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.mine-row:last-of-type {
  border-bottom: none;
}

.mine-row__body {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
  min-width: 0;
}

.mine-row__action {
  flex: 0 0 auto;
  border: none;
  background: transparent;
  color: var(--pa-color-accent);
  min-height: var(--pa-size-control-md);
  padding: var(--pa-space-1) var(--pa-space-2);
  cursor: pointer;
}

.mine-row__action:hover,
.mine-row__action:focus-visible {
  background: var(--pa-color-accent-weak);
}

.mine-empty {
  margin: 0;
  color: var(--pa-color-text-secondary);
}

.mine-contribution {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: var(--pa-space-4);
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.mine-contribution__date {
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-md);
}

.mine-contribution__facts {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-1);
}

.mine-links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-4);
}

.mine-logout {
  margin-top: var(--pa-space-6);
  border: none;
  background: transparent;
  color: var(--pa-color-text-secondary);
  min-height: var(--pa-size-control-md);
  padding: 0;
  cursor: pointer;
}

.mine-logout:hover,
.mine-logout:focus-visible {
  color: var(--pa-color-text-primary);
  text-decoration: underline;
  text-underline-offset: 3px;
}

@media (max-width: 767px) {
  .mine-section__head,
  .mine-row {
    align-items: flex-start;
  }

  .mine-section__head {
    flex-direction: column;
    gap: var(--pa-space-2);
  }

  .mine-row {
    flex-direction: column;
  }

  .mine-row__action {
    padding-left: 0;
  }

  .mine-contribution {
    grid-template-columns: 1fr;
    gap: var(--pa-space-1);
  }
}
</style>
