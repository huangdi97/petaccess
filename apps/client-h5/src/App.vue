<script setup lang="ts">
/**
 * App root — mounts the one ConsumerAppShell (V020_APP_SHELL_SPEC §14).
 * The old bare `<nav class="tabbar">` in this file is gone; navigation is
 * shell-owned now (mobile bottom tabs / desktop rail).
 */
import ConsumerAppShell from "./components/shell/ConsumerAppShell.vue";
</script>

<template>
  <ConsumerAppShell />
</template>