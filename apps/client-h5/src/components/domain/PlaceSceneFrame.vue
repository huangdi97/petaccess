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
        <strong>场景图片待补充</strong>
        <small>仅展示经审核允许公开的场景媒体；不以证据图或合成图冒充真实场所。</small>
      </span>
    </div>
    <figcaption v-if="showImage" class="scene-frame__caption">
      经审核允许公开展示的场所场景
    </figcaption>
  </figure>
</template>

<style scoped src="./PlaceSceneFrame.css"></style>
