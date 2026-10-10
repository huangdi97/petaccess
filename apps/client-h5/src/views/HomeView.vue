<script setup lang="ts">
/**
 * Home — Task Launcher (v0.2.4 §29–31).
 *
 * Desktop main max 960px. Structure is a flat list, not a portal:
 * Location + map link → Headline → Search → 最近/附近 divider rows →
 * 待核实 divider rows → Quick lenses (4 text links). No big white card,
 * no pending card rows, no 「为什么？」pill — anything explanatory is a
 * text link（为什么这个结论？ →）.
 */
import { computed } from "vue";
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
import HomeEntries from "../components/domain/HomeEntries.vue";
import HomeNearbySection from "../components/domain/HomeNearbySection.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import { CONDITION_ZH, HOME_ENTRIES, useHomeLauncher } from "../composables/useHomeLauncher";
import { usePlaceSceneMedia } from "../composables/usePlaceSceneMedia";

const {
  query,
  interest,
  recent,
  loading,
  error,
  places,
  listStale,
  nearbyFetchedAtMs,
  online,
  speciesLabel,
  verified,
  pending,
  unavailable,
  submitSearch,
  goEntry,
  open,
  why,
  clearRecent,
  load,
} = useHomeLauncher();

const featuredSceneMedia = usePlaceSceneMedia(computed(() => verified.value[0]?.place.id ?? null));
const homeState = computed(() => {
  if (loading.value) return "loading";
  if (error.value) return "error";
  if (!places.value.length) return "empty";
  return "ready";
});
const homeFixture = computed(() => `home-${homeState.value}-v1`);
</script>

<template>
  <div class="home-workspace">
    <QueryContextBar />
    <DesktopContentContainer mode="wide">
      <div
        class="page page--home"
        data-ui="home"
        data-ui-page="home"
        :data-ui-state="homeState"
        :data-ui-fixture="homeFixture"
      >
        <!-- location + map link -->
        <div class="home-topline">
          <strong data-testid="coverage-area"
            ><span class="home-brand">PetAccess</span> · 上海 · 试点</strong
          >
          <RouterLink class="btn-inline" to="/map" data-testid="go-map">看地图 →</RouterLink>
        </div>

        <div class="home-intro">
          <h1 data-testid="home-title">去之前，先看看这里的规则和现场。</h1>
          <p class="muted home-subtitle" data-testid="home-subtitle">
            了解规则，也参考真实的现场情况。
          </p>
        </div>

        <!-- search-first -->
        <form class="home-search" data-testid="home-search" @submit.prevent="submitSearch">
          <label class="visually-hidden" for="home-q">搜索场所、商圈或地址</label>
          <input
            id="home-q"
            v-model="query"
            data-testid="home-search-input"
            placeholder="搜索附近场所 / 场所名 / 商圈 / 地址"
            autocomplete="off"
          />
          <button
            class="primary home-search__submit"
            type="submit"
            data-testid="home-search-submit"
          >
            查询
          </button>
        </form>

        <section class="home-lenses" aria-label="你更想先看什么">
          <div class="home-section-header home-section-header--lenses">
            <div>
              <h2 class="home-section-title">你更想先看什么？</h2>
              <p class="muted home-section-hint">
                从同一组规则、现场与证据事实中，先看你最关心的一层。
              </p>
            </div>
          </div>
          <HomeEntries :entries="HOME_ENTRIES" @select="goEntry" />
        </section>

        <HomeNearbySection
          :loading="loading"
          :error="error"
          :places="places"
          :verified="verified"
          :pending="pending"
          :unavailable="unavailable"
          :list-stale="listStale"
          :nearby-fetched-at-ms="nearbyFetchedAtMs"
          :online="online"
          :species-label="speciesLabel"
          :conditions-label="CONDITION_ZH"
          :interest="interest"
          :featured-scene-media-url="featuredSceneMedia?.url ?? null"
          @open="open"
          @why="why"
          @retry="load"
        />

        <!-- Canonical v0.10-R1: recent history comes after recommendations,
             overview and divergence so it never competes with the current task. -->
        <section v-if="recent.length" class="home-recent" data-testid="recent-section">
          <div class="home-section-header">
            <h2 class="home-section-title">最近查看</h2>
            <button class="btn-inline" data-testid="clear-recent" @click="clearRecent">清空</button>
          </div>
          <button
            v-for="r in recent"
            :key="r.id"
            type="button"
            class="home-recent__item"
            :data-testid="'recent-' + r.id"
            :aria-label="`查看最近场所 ${r.name}`"
            @click="open(r.id)"
          >
            <strong>{{ r.name }}</strong>
          </button>
        </section>

        <p class="home-semantics" data-testid="home-semantics">
          附近待补充的场所会标明“信息不足”；信息不足不等于允许或禁止，不同携带方式也可能得到不同结果。
          <RouterLink class="btn-inline" to="/settings">了解判断方式 →</RouterLink>
        </p>

        <footer class="home-footer">
          <RouterLink class="btn" to="/contribute" data-testid="contribute-link">
            补充规则或现场
          </RouterLink>
          <p class="muted">
            现场记录与正式规则分开保存；提交内容会先进入人工核验，不会自动改变规则结论。
          </p>
        </footer>
      </div>
    </DesktopContentContainer>
  </div>
</template>

<style scoped>
.home-workspace {
  min-height: 100%;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--pa-color-accent-weak) 45%, transparent) 0, transparent 360px),
    var(--pa-color-surface);
}

.page--home {
  position: relative;
  max-width: 1120px;
  margin: 0 auto;
  padding-top: var(--pa-space-6);
  isolation: isolate;
}

.page--home::before,
.page--home::after {
  content: "";
  position: absolute;
  z-index: -1;
  pointer-events: none;
  border-radius: 999px;
  filter: blur(1px);
}

.page--home::before {
  top: 20px;
  right: 2%;
  width: 280px;
  height: 180px;
  background:
    radial-gradient(circle at 30% 35%, color-mix(in srgb, var(--pa-color-accent) 15%, transparent) 0 6%, transparent 6.5%),
    radial-gradient(circle at 70% 58%, color-mix(in srgb, var(--pa-color-accent) 9%, transparent) 0 9%, transparent 9.5%),
    linear-gradient(145deg, transparent 0 38%, var(--pa-color-border-subtle) 38% 39%, transparent 39% 100%);
  opacity: 0.9;
}

.page--home::after {
  top: 126px;
  right: 14%;
  width: 170px;
  height: 80px;
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  opacity: 0.55;
}

.home-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--pa-space-3);
  margin: 0 0 var(--pa-space-6);
  color: var(--pa-color-text-secondary);
}

.home-brand {
  color: var(--pa-color-text-primary);
  font-weight: var(--pa-font-weight-650);
}

.home-intro {
  max-width: 760px;
  margin-bottom: var(--pa-space-5);
}

.home-intro h1 {
  max-width: 690px;
  margin: 0;
  font-size: clamp(2rem, 3vw, 3.25rem);
  font-weight: var(--pa-font-weight-650);
  line-height: 1.08;
  letter-spacing: -0.035em;
  color: var(--pa-color-text-primary);
}

.home-subtitle {
  max-width: 560px;
  margin: var(--pa-space-3) 0 0;
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-23);
}

.home-search {
  display: flex;
  gap: var(--pa-space-2);
  max-width: 820px;
  margin-bottom: var(--pa-space-7);
  padding: var(--pa-space-2);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: calc(var(--pa-radius-md) + 4px);
  background: var(--pa-color-surface-raised);
  box-shadow: var(--pa-elevation-1);
}

.home-search input {
  flex: 1 1 auto;
  min-width: 0;
  min-height: 52px;
  margin: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.home-search input:focus-visible {
  outline: none;
}

.home-search:focus-within {
  border-color: var(--pa-color-border-focus);
  box-shadow: 0 0 0 2px color-mix(in srgb, var(--pa-color-border-focus) 18%, transparent);
}

.home-search__submit {
  flex: 0 0 auto;
  min-height: 52px;
  padding-inline: var(--pa-space-5);
  border-radius: var(--pa-radius-control);
  font-weight: var(--pa-font-weight-650);
}

.home-section-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: var(--pa-space-3);
  padding: 0;
}

.home-section-title {
  margin: 0;
  font-size: var(--pa-font-size-2xl);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

.home-section-hint {
  max-width: 640px;
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
}

.home-lenses {
  margin: 0 0 var(--pa-space-8);
}

.home-section-header--lenses {
  margin-bottom: var(--pa-space-1);
}

.home-recent {
  margin-top: var(--pa-space-7);
  padding-top: var(--pa-space-5);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.home-recent__item {
  display: inline-flex;
  width: auto;
  margin: var(--pa-space-2) var(--pa-space-2) 0 0;
  padding: var(--pa-space-2) var(--pa-space-3);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-control);
  background: var(--pa-color-surface-raised);
  color: inherit;
  cursor: pointer;
  font: inherit;
  text-align: left;
}

.home-recent__item:hover {
  border-color: var(--pa-color-border-strong);
}

.home-recent__item:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: 2px;
}

.home-semantics {
  max-width: 760px;
  margin: var(--pa-space-7) 0 0;
  padding: var(--pa-space-4);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface-muted);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
  color: var(--pa-color-text-secondary);
}

.home-footer {
  display: flex;
  align-items: center;
  gap: var(--pa-space-4);
  margin-top: var(--pa-space-7);
  padding: var(--pa-space-5) 0 var(--pa-space-7);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.home-footer p {
  max-width: 660px;
  margin: 0;
}

@media (max-width: 767px) {
  .page--home {
    padding-top: var(--pa-space-4);
  }

  .page--home::before {
    width: 180px;
    height: 120px;
    opacity: 0.55;
  }

  .page--home::after {
    display: none;
  }

  .home-topline {
    margin-bottom: var(--pa-space-5);
  }

  .home-intro {
    margin-bottom: var(--pa-space-4);
  }

  .home-intro h1 {
    max-width: 92%;
    font-size: 2rem;
    line-height: 1.12;
  }

  .home-search {
    flex-direction: column;
    margin-bottom: var(--pa-space-6);
    padding: var(--pa-space-2);
  }

  .home-search__submit {
    width: 100%;
  }

  .home-lenses {
    margin-bottom: var(--pa-space-6);
  }

  .home-footer {
    align-items: flex-start;
    flex-direction: column;
  }
}

@media (min-width: 768px) {
  .page--home {
    margin-left: 0;
    margin-right: auto;
  }
}
</style>