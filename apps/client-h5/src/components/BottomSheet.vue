<script setup lang="ts">
/**
 * Bottom sheet for the selected map item (spec §2.1). Accessible: it is a
 * labelled dialog region with an explicit close control and Escape handling, so
 * it works with a keyboard and a screen reader, not just a thumb.
 */
import { onBeforeUnmount, onMounted } from "vue";

const props = defineProps<{ open: boolean; title?: string | null }>();
const emit = defineEmits<{ close: [] }>();

function onKey(e: KeyboardEvent) {
  if (props.open && e.key === "Escape") emit("close");
}

onMounted(() => window.addEventListener("keydown", onKey));
onBeforeUnmount(() => window.removeEventListener("keydown", onKey));
</script>

<template>
  <div v-if="open" class="sheet-backdrop" data-testid="sheet-backdrop" @click.self="emit('close')">
    <section class="sheet" role="dialog" aria-modal="false" :aria-label="title ?? '场所详情'">
      <header class="sheet__head">
        <strong class="sheet__title">{{ title }}</strong>
        <button class="sheet__close" data-testid="sheet-close" @click="emit('close')">关闭</button>
      </header>
      <div class="sheet__body">
        <slot />
      </div>
    </section>
  </div>
</template>
