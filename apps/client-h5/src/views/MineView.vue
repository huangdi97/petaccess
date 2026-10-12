<script setup lang="ts">
import { onMounted, ref } from "vue";
import { client, session } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import MineActivitySections from "../components/mine/MineActivitySections.vue";
import MinePetSection from "../components/mine/MinePetSection.vue";
import StateMessage from "../components/StateMessage.vue";
import { presentDescription } from "../errors";

const pets = ref<Awaited<ReturnType<typeof client.myPets>>>([]);
const watches = ref<Awaited<ReturnType<typeof client.myWatches>>>([]);
const contributions = ref<Awaited<ReturnType<typeof client.myContributionActivity>>>([]);
const error = ref("");
const loading = ref(true);
const signedIn = ref(false);

async function load() {
  loading.value = true;
  error.value = "";
  pets.value = [];
  watches.value = [];
  contributions.value = [];
  try {
    await session.restore();
    signedIn.value = session.signedIn;
    if (!signedIn.value) {
      pets.value = [];
      watches.value = [];
      contributions.value = [];
      return;
    }
    // Only show an account's data when all three scoped API calls succeed.
    // A partial failure must not look like an empty contribution history.
    const [nextPets, nextWatches, nextContributions] = await Promise.all([
      client.myPets(),
      client.myWatches(),
      client.myContributionActivity(),
    ]);
    pets.value = nextPets;
    watches.value = nextWatches;
    contributions.value = nextContributions;
  } catch (e) {
    error.value = presentDescription(e);
  } finally {
    loading.value = false;
  }
}

onMounted(load);

function logout() {
  session.logout();
  signedIn.value = false;
  pets.value = [];
  watches.value = [];
  contributions.value = [];
  error.value = "";
}

function setActivePet(pet: (typeof pets.value)[number]) {
  session.setActivePet(pet);
  session.setDeclaredRole(null);
  session.mode = pet.service_role === "working" ? "service_dog" : "with_pet";
}
</script>

<template>
  <AppShell
    data-ui-page="mine"
    :data-ui-state="loading ? 'loading' : error ? 'error' : signedIn ? 'signed-in' : 'public'"
  >
    <header class="mine-head">
      <h1>我的</h1>
      <template v-if="signedIn">
        <strong class="mine-head__name">{{ session.user?.display_name }}</strong>
        <span class="muted">{{ session.user?.email }}</span>
      </template>
    </header>

    <SkeletonList v-if="loading" :rows="3" />
    <StateMessage v-else-if="error" kind="ERROR" :description="error" data-testid="mine-error">
      <template #action>
        <button class="primary" type="button" @click="load">重试</button>
      </template>
    </StateMessage>

    <section v-else-if="!signedIn" class="mine-public" data-testid="mine-public">
      <div class="mine-public__hero">
        <p class="mine-public__kicker">个人出行档案</p>
        <h2>登录后管理你的出行设置</h2>
        <p class="muted">
          宠物档案、共处边界、变化关注和贡献记录只在登录后显示；公开场所信息仍可免登录浏览。
        </p>
        <div class="mine-public__actions">
          <RouterLink class="btn primary" :to="{ name: 'onboarding', query: { next: '/mine' } }">
            登录 / 注册
          </RouterLink>
          <RouterLink class="btn" to="/map">继续浏览地图</RouterLink>
        </div>
      </div>

      <div class="mine-public__grid">
        <section>
          <h3>登录后</h3>
          <ul>
            <li>保存宠物档案与当前查询对象</li>
            <li>设置自己的共处边界，不形成场所总分</li>
            <li>查看关注变化与贡献核验进度</li>
          </ul>
        </section>
        <section>
          <h3>无需登录也可以</h3>
          <ul>
            <li>搜索和查看地图上的公开场所</li>
            <li>查看规则、现场事实与证据来源</li>
            <li>判断信息是否充分，而不是被迫注册</li>
          </ul>
        </section>
      </div>
    </section>

    <template v-else>
      <MinePetSection :pets="pets" @activate="setActivePet" />
      <MineActivitySections :watches="watches" :contributions="contributions" />

      <section class="mine-section">
        <div class="mine-section__head">
          <div>
            <h2>共处边界</h2>
            <p class="muted">这是你自己的出行偏好，只用于逐项比对公开事实，不形成场所总分。</p>
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
          <nav class="mine-links" aria-label="隐私与设置">
            <RouterLink class="btn-inline" to="/privacy" data-testid="open-privacy">
              隐私与数据 →
            </RouterLink>
            <RouterLink class="btn-inline" to="/settings" data-testid="open-settings">
              设置与说明 →
            </RouterLink>
          </nav>
        </div>
      </section>

      <button class="mine-logout" type="button" @click="logout">退出登录</button>
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

.mine-public {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-5);
  padding-top: var(--pa-space-5);
}

.mine-public__hero {
  padding: var(--pa-space-5);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: calc(var(--pa-radius-md) + 2px);
  background:
    linear-gradient(
      145deg,
      color-mix(in srgb, var(--pa-color-accent-weak) 76%, var(--pa-color-surface)) 0%,
      var(--pa-color-surface-raised) 74%
    );
}

.mine-public__kicker {
  margin: 0 0 var(--pa-space-2);
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-650);
  letter-spacing: var(--pa-letter-spacing-wide);
}

.mine-public__hero h2 {
  margin: 0;
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-xl);
  line-height: var(--pa-line-height-26);
  text-wrap: balance;
}

.mine-public__hero p {
  max-width: 620px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.mine-public__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-4);
}

.mine-public__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--pa-space-3);
}

.mine-public__grid section {
  padding: var(--pa-space-4);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface-raised);
}

.mine-public__grid h3 {
  margin: 0;
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-base);
}

.mine-public__grid ul {
  display: grid;
  gap: var(--pa-space-2);
  margin: var(--pa-space-3) 0 0;
  padding-left: 1.15rem;
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
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
}
.mine-section h2 {
  margin: 0;
  font-size: var(--pa-font-size-lg);
  font-weight: var(--pa-font-weight-650);
}
.mine-section__head p {
  max-width: 560px;
  margin: var(--pa-space-1) 0 0;
}
.mine-links {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-4);
}
.mine-logout {
  margin-top: var(--pa-space-6);
  min-height: var(--pa-size-control-md);
  border: none;
  background: transparent;
  color: var(--pa-color-text-secondary);
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
  .mine-section__head {
    flex-direction: column;
    gap: var(--pa-space-2);
  }

  .mine-public {
    gap: var(--pa-space-4);
  }

  .mine-public__hero {
    padding: var(--pa-space-4);
  }

  .mine-public__grid {
    grid-template-columns: 1fr;
  }
}
</style>
