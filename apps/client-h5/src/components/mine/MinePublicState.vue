<template>
  <section class="mine-public" data-testid="mine-public">
    <div class="mine-public__hero">
      <p class="mine-public__kicker">个人出行档案</p>
      <h2>登录后管理你的出行设置</h2>
      <p class="muted">
        宠物档案、共处边界、变化关注和贡献记录只在登录后显示；公开场所信息仍可免登录浏览。
      </p>
      <div class="mine-public__actions">
        <RouterLink class="btn primary" :to="{ name: 'onboarding', query: { next: '/mine' } }">
          登录 / 注册
        </RouterLink>
        <RouterLink class="btn" to="/map">继续浏览地图</RouterLink>
      </div>
    </div>

    <div class="mine-public__grid">
      <section>
        <h3>登录后</h3>
        <ul>
          <li>保存宠物档案与当前查询对象</li>
          <li>设置自己的共处边界，不形成场所总分</li>
          <li>查看关注变化与贡献核验进度</li>
        </ul>
      </section>
      <section>
        <h3>无需登录也可以</h3>
        <ul>
          <li>搜索和查看地图上的公开场所</li>
          <li>查看规则、现场事实与证据来源</li>
          <li>判断信息是否充分，而不是被迫注册</li>
        </ul>
      </section>
    </div>
  </section>
</template>

<style scoped>
.mine-public {
  display: flex;
  flex-direction: column;
  gap: var(--pa-space-5);
  padding-top: var(--pa-space-5);
}

.mine-public__hero {
  padding: var(--pa-space-5);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: calc(var(--pa-radius-md) + 2px);
  background: linear-gradient(
    145deg,
    color-mix(in srgb, var(--pa-color-accent-weak) 76%, var(--pa-color-surface)) 0%,
    var(--pa-color-surface-raised) 74%
  );
}

.mine-public__kicker {
  margin: 0 0 var(--pa-space-2);
  color: var(--pa-color-accent);
  font-size: var(--pa-font-size-sm);
  font-weight: var(--pa-font-weight-650);
  letter-spacing: var(--pa-letter-spacing-wide);
}

.mine-public__hero h2 {
  margin: 0;
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-xl);
  line-height: var(--pa-line-height-26);
  text-wrap: balance;
}

.mine-public__hero p {
  max-width: 620px;
  margin: var(--pa-space-2) 0 0;
  line-height: var(--pa-line-height-23);
}

.mine-public__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--pa-space-2);
  margin-top: var(--pa-space-4);
}

.mine-public__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--pa-space-3);
}

.mine-public__grid section {
  padding: var(--pa-space-4);
  border: var(--pa-border-width) solid var(--pa-color-border-subtle);
  border-radius: var(--pa-radius-md);
  background: var(--pa-color-surface-raised);
}

.mine-public__grid h3 {
  margin: 0;
  color: var(--pa-color-text-primary);
  font-size: var(--pa-font-size-base);
}

.mine-public__grid ul {
  display: grid;
  gap: var(--pa-space-2);
  margin: var(--pa-space-3) 0 0;
  padding-left: 1.15rem;
  color: var(--pa-color-text-secondary);
  font-size: var(--pa-font-size-sm);
  line-height: var(--pa-line-height-20);
}

@media (max-width: 767px) {
  .mine-public {
    gap: var(--pa-space-4);
  }

  .mine-public__hero {
    padding: var(--pa-space-4);
  }

  .mine-public__grid {
    grid-template-columns: 1fr;
  }
}
</style>
