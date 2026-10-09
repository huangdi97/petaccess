<script setup lang="ts">
/**
 * Stable venue-scene frame for Search / Place identity.
 *
 * A photo is shown only when the caller already obtained it through the
 * reviewed public-media gate. Missing media is a first-class honest state,
 * never replaced by evidence/signage/import imagery or synthetic venue art.
 */
import { computed, ref, watch } from "vue";
import PlaceTypeGlyph from "./PlaceTypeGlyph.vue";

const props = withDefaults(
  defineProps<{
    src?: string | null;
    alt?: string;
    variant?: "hero" | "compact";
    eager?: boolean;
    placeType?: string | null;
  }>(),
  {
    src: null,
    alt: "经审核允许公开展示的场所场景照片",
    variant: "hero",
    eager: false,
    placeType: null,
  },
);

const imageFailed = ref(false);
watch(
  () => props.src,
  () => {
    imageFailed.value = false;
  },
);

const showImage = computed(() => Boolean(props.src) && !imageFailed.value);
</script>

<template>
  <figure
    class="scene-frame"
    :class="[`scene-frame--${variant}`, { 'scene-frame--empty': !showImage }]"
    data-ui="place-scene-frame"
  >
    <img
      v-if="showImage"
      class="scene-frame__image"
      :src="src ?? undefined"
      :alt="alt"
      :loading="eager ? 'eager' : 'lazy'"
      decoding="async"
      referrerpolicy="no-referrer"
      @error="imageFailed = true"
    />
    <div v-else class="scene-frame__empty" data-testid="scene-media-empty">
      <span class="scene-frame__abstract" aria-hidden="true">
        <span class="scene-frame__abstract-block scene-frame__abstract-block--a"></span>
        <span class="scene-frame__abstract-block scene-frame__abstract-block--b"></span>
        <span class="scene-frame__abstract-path"></span>
      </span>
      <PlaceTypeGlyph
        class="scene-frame__identity-glyph"
        :place-type="placeType"
        :size="variant === 'hero' ? 'xl' : 'lg'"
      />
      <span class="scene-frame__empty-copy">
        <strong>暂无可公开场景图片</strong>
        <small>这里是抽象身份占位，不代表真实建筑或现场；仅展示经审核允许公开的场景媒体。</small>
      </span>
    </div>
    <figcaption v-if="showImage" class="scene-frame__caption">
      经审核允许公开展示的场所场景
    </figcaption>
  </figure>
</template>

<style scoped>
.scene-frame {
  margin: 0;
  min-width: 0;
  overflow: hidden;
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  background: var(--pa-color-surface-muted);
}

.scene-frame__image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.scene-frame__empty {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  gap: var(--pa-space-3);
  padding: var(--pa-space-4);
  color: var(--pa-color-text-secondary);
  background:
    linear-gradient(120deg, var(--pa-color-accent-weak), transparent 48%),
    var(--pa-color-surface-muted);
}

.scene-frame__identity-glyph {
  position: relative;
  z-index: 2;
}

.scene-frame__abstract {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.scene-frame__abstract::before,
.scene-frame__abstract::after,
.scene-frame__abstract-block,
.scene-frame__abstract-path {
  content: "";
  position: absolute;
  display: block;
}

.scene-frame__abstract::before {
  width: 54%;
  height: 72%;
  right: -8%;
  bottom: -28%;
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  transform: rotate(-9deg);
  background: color-mix(in srgb, var(--pa-color-surface) 72%, transparent);
}

.scene-frame__abstract::after {
  width: 38%;
  height: 52%;
  right: 18%;
  top: -22%;
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  transform: rotate(13deg);
}

.scene-frame__abstract-block--a {
  width: 84px;
  height: 42px;
  left: 46%;
  top: 48%;
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  background: color-mix(in srgb, var(--pa-color-surface) 82%, transparent);
}

.scene-frame__abstract-block--b {
  width: 56px;
  height: 32px;
  left: 66%;
  top: 32%;
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  background: color-mix(in srgb, var(--pa-color-surface) 76%, transparent);
}

.scene-frame__abstract-path {
  width: 74%;
  height: 1px;
  left: 33%;
  top: 62%;
  background: var(--pa-color-border);
  transform: rotate(-8deg);
  opacity: 0.65;
}

.scene-frame__empty-copy {
  position: relative;
  z-index: 2;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.scene-frame__empty-copy strong {
  font-size: var(--pa-font-size-md);
  font-weight: var(--pa-font-weight-600);
  color: var(--pa-color-text-primary);
}

.scene-frame__empty-copy small,
.scene-frame__caption {
  font-size: var(--pa-font-size-xs);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-muted);
}

.scene-frame__caption {
  display: block;
  padding: var(--pa-space-1) var(--pa-space-2);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.scene-frame--hero {
  width: 100%;
  max-width: 620px;
  min-height: 132px;
  border-radius: var(--pa-radius-control);
}

.scene-frame--hero .scene-frame__image {
  aspect-ratio: 16 / 6;
}

.scene-frame--hero.scene-frame--empty {
  max-width: 520px;
  min-height: 0;
}

.scene-frame--hero.scene-frame--empty .scene-frame__empty {
  aspect-ratio: 16 / 4.5;
}

.scene-frame--compact {
  flex: 0 0 var(--scene-frame-compact-width, 152px);
  width: var(--scene-frame-compact-width, 152px);
  height: var(--scene-frame-compact-height, 96px);
  border-radius: var(--pa-radius-control);
}

.scene-frame--compact .scene-frame__empty {
  padding: var(--pa-space-2);
  gap: var(--pa-space-2);
}

.scene-frame--compact .scene-frame__empty-copy small {
  display: none;
}

.scene-frame--compact .scene-frame__empty-copy strong {
  font-size: var(--pa-font-size-xs);
  line-height: var(--pa-line-height-20);
}

.scene-frame--compact .scene-frame__caption {
  display: none;
}

@media (max-width: 767px) {
  .scene-frame--compact {
    flex-basis: var(--scene-frame-compact-mobile-width, 96px);
    width: var(--scene-frame-compact-mobile-width, 96px);
    height: var(--scene-frame-compact-mobile-height, 64px);
  }

  .scene-frame--compact .scene-frame__empty {
    justify-content: center;
    padding: var(--pa-space-1);
  }

  .scene-frame--compact .scene-frame__empty-copy {
    display: none;
  }
}
</style>
