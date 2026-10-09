<script setup lang="ts">
/**
 * Stable venue-scene frame for Search / Place identity.
 *
 * A photo is shown only when the caller already obtained it through the
 * reviewed public-media gate. Missing media is a first-class honest state,
 * never replaced by evidence/signage/import imagery or synthetic venue art.
 */
import PaIcon from "../ui/PaIcon.vue";

withDefaults(
  defineProps<{
    src?: string | null;
    alt?: string;
    variant?: "hero" | "compact";
    eager?: boolean;
  }>(),
  {
    src: null,
    alt: "经审核允许公开展示的场所场景照片",
    variant: "hero",
    eager: false,
  },
);
</script>

<template>
  <figure class="scene-frame" :class="`scene-frame--${variant}`" data-ui="place-scene-frame">
    <img
      v-if="src"
      class="scene-frame__image"
      :src="src"
      :alt="alt"
      :loading="eager ? 'eager' : 'lazy'"
      decoding="async"
      referrerpolicy="no-referrer"
    />
    <div v-else class="scene-frame__empty" data-testid="scene-media-empty">
      <span class="scene-frame__camera" aria-hidden="true"><PaIcon name="camera" size="lg" /></span>
      <span class="scene-frame__empty-copy">
        <strong>暂无可公开场景图片</strong>
        <small>仅展示经审核允许公开的场景媒体</small>
      </span>
    </div>
    <figcaption v-if="src" class="scene-frame__caption">经审核允许公开展示的场所场景</figcaption>
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

.scene-frame__camera {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  flex: 0 0 auto;
  border: var(--pa-border-width) solid var(--pa-color-border);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface);
  color: var(--pa-color-accent);
}

.scene-frame__empty-copy {
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

.scene-frame--hero .scene-frame__image,
.scene-frame--hero .scene-frame__empty {
  aspect-ratio: 16 / 6;
}

.scene-frame--compact {
  flex: 0 0 152px;
  width: 152px;
  height: 96px;
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
    flex-basis: 96px;
    width: 96px;
    height: 64px;
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
