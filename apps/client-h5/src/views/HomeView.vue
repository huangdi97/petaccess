<script setup lang="ts">
/**
 * Home — Task Launcher (UI_RECONSTRUCTION_DESIGN_FREEZE §9).
 *
 * Composition: data/actions live in useHomeLauncher; the verified/pending
 * nearby list and the secondary lens entries are their own components. This
 * view keeps the page skeleton: QueryContextBar → location → primary search →
 * recent → nearby section → lens entries → semantics footer. No hero photo,
 * no feature-card wall, no category chips — lists are divider-led rows.
 *
 * 产品方向（frozen，未变）：search-first；「去之前，查清规则」；UNKNOWN ≠ ALLOWED；
 * 已核验范围写明（动物 · 区域）；贡献为低优先级 footer。
 */
import DesktopContentContainer from "../components/layout/DesktopContentContainer.vue";
import HomeEntries from "../components/domain/HomeEntries.vue";
import HomeNearbySection from "../components/domain/HomeNearbySection.vue";
import QueryContextBar from "../components/domain/QueryContextBar.vue";
import { CONDITION_ZH, HOME_ENTRIES, useHomeLauncher } from "../composables/useHomeLauncher";

const {
  query,
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
  <DesktopContentContainer mode="wide">
    <div
      class="page"
      data-ui="home"
      data-ui-page="home"
      data-ui-state="ready"
      data-ui-fixture="home-ready-v1"
    >
      <QueryContextBar />

      <!-- coverage header — survives an API failure -->
      <div class="home-topline">
        <strong data-testid="coverage-area">上海 · 试点</strong>
        <span class="row home-topline__actions">
          <RouterLink class="btn-inline" to="/map" data-testid="go-map">看地图 &gt;</RouterLink>
          <RouterLink to="/settings" class="pill" data-testid="coverage-scope">覆盖范围</RouterLink>
        </span>
      </div>

      <h1 data-testid="home-title">去之前，先看看这里的规则和现场。</h1>
      <p class="muted home-subtitle" data-testid="home-subtitle">
        了解场所规则，也参考经核验的现场记录。
      </p>

      <!-- search-first -->
      <form class="home-search" data-testid="home-search" @submit.prevent="submitSearch">
        <label class="visually-hidden" for="home-q">搜索场所、商圈或地址</label>
        <input
          id="home-q"
          v-model="query"
          data-testid="home-search-input"
          placeholder="搜索场所、商圈或地址"
          autocomplete="off"
        />
        <button class="primary home-search__submit" type="submit" data-testid="home-search-submit">
          查询
        </button>
      </form>

      <!-- 最近查看：divider 行，非卡片 -->
      <section v-if="recent.length" data-testid="recent-section">
        <div class="home-section-header">
          <h2 class="home-section-title">最近查看</h2>
          <button class="pill" data-testid="clear-recent" @click="clearRecent">清空</button>
        </div>
        <p class="muted">打开时重新求值 —— 规则更新后会以最新结果呈现，不复用旧答案。</p>
        <div
          v-for="r in recent"
          :key="r.id"
          class="home-recent__item"
          :data-testid="'recent-' + r.id"
          @click="open(r.id)"
        >
          <strong>{{ r.name }}</strong>
        </div>
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
        @open="open"
        @why="why"
        @retry="load"
      />

      <!-- 次级镜头入口：安静的 divider 列表，不是彩色卡片 -->
      <HomeEntries :entries="HOME_ENTRIES" @select="goEntry" />

      <p class="notice home-semantics" data-testid="home-semantics">
        「规则待核实」＝ 尚未核验，<strong>不等于允许或禁止</strong>。已核验的结论会写明范围（动物 ·
        区域），不对整个场所下结论。
      </p>

      <footer class="home-footer">
        <RouterLink class="btn" to="/contribute" data-testid="contribute-link"
          >拍规则牌 / 现场核验</RouterLink
        >
        <p class="muted">现场记录与官方规则分开保存；AI/OCR 只生成待审候选，不会自动成为规则。</p>
      </footer>
    </div>
  </DesktopContentContainer>
</template>

<style scoped>
.home-topline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--pa-space-2);
  margin: var(--pa-space-4) 0;
}

.home-subtitle {
  margin: var(--pa-space-1) 0 var(--pa-space-4);
}

/* Primary search: a flat input row, not a card. */
.home-search {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-2);
  margin-bottom: var(--pa-space-4);
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
.home-recent__item {
  cursor: pointer;
  padding: var(--pa-space-3) 0;
  border-bottom: var(--pa-border-width) solid var(--pa-color-border-subtle);
}

.home-recent__item:last-child {
  border-bottom: none;
}

.home-semantics {
  margin-top: var(--pa-space-5);
}

.home-footer {
  margin-top: var(--pa-space-5);
}

.home-footer p {
  margin-bottom: 0;
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
