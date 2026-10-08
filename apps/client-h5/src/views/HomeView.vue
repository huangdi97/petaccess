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
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
import HomeEntries from "../components/domain/HomeEntries.vue";
import HomeNearbySection from "../components/domain/HomeNearbySection.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import { CONDITION_ZH, HOME_ENTRIES, useHomeLauncher } from "../composables/useHomeLauncher";

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
  submitSearch,
  goEntry,
  open,
  why,
  clearRecent,
  load,
} = useHomeLauncher();
</script>

<template>
  <div class="home-workspace">
    <QueryContextBar />
    <DesktopContentContainer mode="wide">
      <div
        class="page page--home"
        data-ui="home"
        data-ui-page="home"
        data-ui-state="ready"
        data-ui-fixture="home-ready-v1"
      >
        <!-- location + map link -->
        <div class="home-topline">
          <strong data-testid="coverage-area">上海 · 试点</strong>
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
          :list-stale="listStale"
          :nearby-fetched-at-ms="nearbyFetchedAtMs"
          :online="online"
          :species-label="speciesLabel"
          :conditions-label="CONDITION_ZH"
          :interest="interest"
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
          没有足够信息时，PetAccess 会直接显示“信息不足”，不会替你猜；不同携带方式可能得到不同结果。
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
/* Home 是 task launcher，不是 dashboard：全局 Query Context 独立成顶栏，
   主内容保持一条清晰的阅读/操作轴。 */
.home-workspace {
  min-height: 100%;
}

.page--home {
  max-width: 920px;
  margin: 0 auto;
  padding-top: var(--pa-space-6);
}

.home-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--pa-space-2);
  margin: 0 0 var(--pa-space-5);
  color: var(--pa-color-text-secondary);
}

.home-intro {
  max-width: 720px;
  margin-bottom: var(--pa-space-5);
}

.home-intro h1 {
  font-size: var(--pa-font-size-28);
  font-weight: var(--pa-font-weight-650);
  line-height: var(--pa-line-height-36);
  letter-spacing: -0.01em;
}

.home-subtitle {
  margin: var(--pa-space-2) 0 0;
  font-size: var(--pa-font-size-base);
  line-height: var(--pa-line-height-23);
}

/* Primary search: a flat input row, not a card. */
.home-search {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  margin-bottom: var(--pa-space-6);
}

.home-search input {
  min-height: 52px;
  margin: 0;
  border-color: var(--pa-color-border-strong);
  background: var(--pa-color-surface-raised);
}

.home-search__submit {
  min-height: 52px;
  padding-inline: var(--pa-space-5);
  font-weight: var(--pa-font-weight-600);
}

.home-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--pa-space-3);
  padding: var(--pa-space-2) 0;
}

.home-section-title {
  margin: 0;
  font-size: var(--pa-font-size-2xl);
  font-weight: var(--pa-font-weight-medium);
  line-height: var(--pa-line-height-tight);
  color: var(--pa-color-text-primary);
}

/* Recent rows — divider-based, radius 0. */
.home-recent {
  margin-top: var(--pa-space-6);
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.home-recent__item {
  display: block;
  width: 100%;
  text-align: left;
  border: none;
  background: transparent;
  font: inherit;
  color: inherit;
  cursor: pointer;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.home-recent__item:last-child {
  border-bottom: none;
}

.home-recent__item:focus-visible {
  outline: 2px solid var(--pa-color-border-focus);
  outline-offset: -2px;
}

.home-lenses {
  margin: 0 0 var(--pa-space-6);
  padding-bottom: var(--pa-space-5);
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.home-section-header--lenses {
  padding-top: 0;
}

.home-section-hint {
  margin: var(--pa-space-1) 0 0;
  font-size: var(--pa-font-size-md);
  line-height: var(--pa-line-height-20);
}

.home-semantics {
  margin: var(--pa-space-6) 0 0;
  padding-top: var(--pa-space-4);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
  font-size: var(--pa-font-size-sm);
  color: var(--pa-color-text-secondary);
}

.home-footer {
  margin-top: var(--pa-space-7);
  padding-top: var(--pa-space-5);
  border-top: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.home-footer p {
  margin-bottom: 0;
}

@media (max-width: 767px) {
  .page--home {
    padding-top: var(--pa-space-4);
  }

  .home-intro h1 {
    font-size: var(--pa-font-size-24);
    line-height: var(--pa-line-height-32);
  }
}

@media (min-width: 768px) {
  .home-search {
    flex-direction: row;
    align-items: center;
  }

  .home-search input {
    flex: 1;
    min-width: 0;
  }

  .home-search__submit {
    flex-shrink: 0;
    margin-top: var(--pa-space-1);
  }
}
</style>
