<script setup lang="ts">
import { onMounted, ref } from "vue";
import { client, session } from "@petaccess/client-core";
import AppShell from "../components/AppShell.vue";
import SkeletonList from "../components/SkeletonList.vue";
import MineActivitySections from "../components/mine/MineActivitySections.vue";
import MinePetSection from "../components/mine/MinePetSection.vue";
import MinePublicState from "../components/mine/MinePublicState.vue";
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
    if (!signedIn.value) return;

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
    :show-query-context="false"
    data-ui-page="mine"
    :data-ui-state="loading ? 'loading' : error ? 'error' : signedIn ? 'signed-in' : 'public'"
  >
    <header class="mine-head" :class="{ 'mine-head--signed-in': signedIn }">
      <p class="mine-head__kicker">个人出行中心</p>
      <h1>我的</h1>
      <template v-if="signedIn">
        <strong class="mine-head__name">{{ session.user?.display_name }}</strong>
        <span class="muted mine-head__email">{{ session.user?.email }}</span>
        <div class="mine-head__summary" aria-label="个人记录摘要">
          <div>
            <strong>{{ pets.length }}</strong>
            <span>宠物档案</span>
          </div>
          <div>
            <strong>{{ watches.length }}</strong>
            <span>关注变化</span>
          </div>
          <div>
            <strong>{{ contributions.length }}</strong>
            <span>贡献记录</span>
          </div>
        </div>
      </template>
    </header>

    <SkeletonList v-if="loading" :rows="3" />
    <StateMessage v-else-if="error" kind="ERROR" :description="error" data-testid="mine-error">
      <template #action>
        <button class="primary" type="button" @click="load">重试</button>
      </template>
    </StateMessage>

    <MinePublicState v-else-if="!signedIn" />

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

<style scoped src="./MineView.css"></style>
