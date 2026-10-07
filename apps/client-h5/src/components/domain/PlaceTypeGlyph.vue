<script setup lang="ts">
/**
 * PlaceTypeGlyph — neutral spatial identity when no evidence-bearing place
 * media exists.
 *
 * The approved visual reference used thumbnails to make place lists spatial
 * and scannable. Production cannot invent decorative photos, so this glyph
 * supplies the same identity anchor using the fixed PetAccess icon family.
 * It carries no access/reality meaning.
 */
import { computed } from "vue";
import { type IconName } from "@petaccess/design-tokens";
import PaIcon from "../ui/PaIcon.vue";

const props = withDefaults(
  defineProps<{
    placeType?: string | null;
    size?: "sm" | "md";
  }>(),
  { placeType: null, size: "md" },
);

const icon = computed<IconName>(() => {
  const type = props.placeType ?? "";
  if (["park", "square", "greenway", "beach", "scenic_area"].includes(type)) return "map";
  if (["transport_hub"].includes(type)) return "location";
  return "building";
});
</script>

<template>
  <span
    class="place-type-glyph"
    :class="`place-type-glyph--${size}`"
    aria-hidden="true"
    data-ui="place-type-glyph"
  >
    <PaIcon :name="icon" :size="size === 'sm' ? 'sm' : 'md'" />
  </span>
</template>

<style scoped>
.place-type-glyph {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface-muted);
  color: var(--pa-color-accent);
}

.place-type-glyph--md {
  width: 40px;
  height: 40px;
}

.place-type-glyph--sm {
  width: 32px;
  height: 32px;
}
</style>
