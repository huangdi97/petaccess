<script setup lang="ts">
import { onMounted, ref } from "vue";
import { client, session } from "@petaccess/client-core";

const pets = ref<Awaited<ReturnType<typeof client.myPets>>>([]);
const watches = ref<Awaited<ReturnType<typeof client.myWatches>>>([]);
const error = ref("");

onMounted(async () => {
  await session.restore();
  if (!session.signedIn) return;
  try {
    pets.value = await client.myPets();
    watches.value = await client.myWatches();
  } catch (e) {
    error.value = e instanceof Error ? e.message : String(e);
  }
});
</script>

<template>
  <div class="page">
    <h1>我的</h1>
    <div v-if="error" class="panel">{{ error }}</div>
    <div v-if="!session.signedIn" class="panel">
      <p>未登录 — 登录后可管理宠物档案、关注规则变化。</p>
      <RouterLink to="/onboarding"><button class="primary block">登录 / 注册</button></RouterLink>
    </div>
    <template v-else>
      <div class="panel">
        <strong>{{ session.user?.display_name }}</strong>
        <div class="muted">{{ session.user?.email }}</div>
      </div>
      <h2>宠物档案</h2>
      <div class="panel" v-for="p in pets" :key="p.id">
        <strong>{{ p.display_name }}</strong>
        <div class="muted">
          {{ p.species }} {{ p.breed_text ?? "" }}
          {{ p.weight_kg ? `· ${p.weight_kg}kg` : "" }}
          {{ p.service_role !== "none" ? "· 服务犬（用户声明）" : "" }}
        </div>
        <button
          style="margin-top: 8px"
          @click="
            session.activePet = p;
            session.mode = 'with_pet';
          "
        >
          设为本次对象
        </button>
      </div>
      <h2>关注的规则变化</h2>
      <div class="panel" v-for="w in watches" :key="w.id">
        <span class="muted">{{ w.target_type }} · {{ w.target_id.slice(0, 8) }}…</span>
      </div>
      <div class="panel" v-if="!watches.length"><span class="muted">暂无关注</span></div>
      <h2>我的共处边界</h2>
      <div class="panel">
        <div class="muted">
          设定你自己的出行偏好，用于逐项比对场所公开记录。逐项判定，无总分； 未设置的项保持未知。
        </div>
        <RouterLink to="/boundary">
          <button class="primary block" style="margin-top: 8px" data-testid="open-boundary">
            设置 / 修改共处边界
          </button>
        </RouterLink>
      </div>
      <h2>隐私</h2>
      <div class="panel">
        <div class="notice">
          · 位置仅用于附近查询/现场核验，不建立连续轨迹<br />
          · 小区只展示公共空间规则，无住户信息<br />
          · 服务犬身份仅由用户声明，平台不凭照片认定
        </div>
      </div>
      <button class="block" @click="session.logout()">退出登录</button>
    </template>
  </div>
</template>
