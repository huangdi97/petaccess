<script setup lang="ts">
import { computed } from "vue";
import { session, type QueryMode } from "@petaccess/client-core";
import ModeBar from "../components/ModeBar.vue";

const who = computed(() =>
  session.activePet
    ? `本次：${session.activePet.display_name} · ${session.activePet.breed_text ?? session.activePet.species}` +
      (session.activePet.weight_kg ? ` · ${session.activePet.weight_kg}kg` : "")
    : "未设置宠物档案",
);

function setMode(m: QueryMode) {
  session.mode = m;
}
</script>

<template>
  <div class="page">
    <ModeBar :mode="session.mode" @change="setMode" />
    <div class="panel">
      <div class="row" style="justify-content: space-between">
        <strong>{{ who }}</strong>
        <RouterLink to="/pet/new" class="pill">换宠物 / 新建</RouterLink>
      </div>
    </div>
    <slot />
  </div>
</template>
