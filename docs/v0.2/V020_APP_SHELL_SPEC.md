# V020 App Shell Spec

Status: M2 Product Experience Foundation — app shell
Last updated: 2026-09-24
Owner: PetAccess v0.2.0 M2

## 1. Purpose

The consumer app now boots into one stable **ConsumerAppShell** instead of a
bare `App.vue` + hand-rolled tabbar. The shell owns chrome only; pages own data.

Files:
- `apps/client-h5/src/components/shell/ConsumerAppShell.vue` — root chrome.
- `apps/client-h5/src/components/shell/AppBoundary.vue` — global loading/error boundary.
- `apps/client-h5/src/components/shell/GlobalOfflineBanner.vue` — one offline affordance.
- `apps/client-h5/src/components/shell/ToastHost.vue` / `DialogHost.vue` — global toast/dialog.
- `apps/client-h5/src/components/nav/MobileTabbar.vue` — < 768px bottom navigation.
- `apps/client-h5/src/components/nav/DesktopRail.vue` — ≥ 768px navigation rail.
- `apps/client-h5/src/components/layout/DesktopContentContainer.vue` — desktop content modes.
- `apps/client-h5/src/composables/useBreakpoint.ts` — reactive viewport bucket.
- `apps/client-h5/src/composables/useUi.ts` — global toast/dialog state.

## 2. Shell responsibilities (and nothing more)

1. **Navigation**: mobile bottom tabs (`首页 / 地图 / 贡献 / 我的`) below 768px;
   desktop rail (`首页 / 搜索 / 地图 / 贡献` + divider + `我的 / 设置 / 关于`) at
   ≥ 768px. Search is a Home-level feature on mobile, a first-class rail item on
   desktop (spec §15/§16).
2. **Route frame**: `<RouterView>` hosted inside the shell main; desktop main is
   offset by the rail width (`--pa-layout-rail-width`) and no longer reserves
   tabbar space.
3. **Safe area**: the mobile tabbar applies `--pa-safe-bottom`; the shell main
   reserves `--pa-safe-total-bottom`; the rail applies safe-bottom padding.
4. **Network state**: `GlobalOfflineBanner` renders when offline
   (「当前离线，部分内容可能不是最新状态。」+ 重连).
5. **Global toast + dialog**: exactly one `ToastHost` / `DialogHost`; pages use
   `useUi()`.
6. **Theme**: the shell sets `data-theme="light"` on `<html>` (light is the
   shipped theme; tokens are defined once so a dark theme can be added by
   overriding `:root` under `[data-theme="dark"]`).
7. **Global loading + error boundary**: `AppBoundary` shows an app-level loading
   state until the router is ready and captures uncaught render errors into a
   unified error state (presentation via `presentError` in `src/errors.ts`).
8. **Version info**: desktop rail footer shows `PetAccess v<version>`
   (`VITE_APP_VERSION`, fallback `0.2.0-dev`) + environment label.

The shell contains **no** Rule/Reality calculations, no API queries, no place
matching — verified by review of the six shell components (they import only
`vue`, `vue-router`, `@petaccess/design-tokens`, `useBreakpoint`, `useOnline`,
`useUi`, `PaIcon`).

## 3. Navigation contract

| Viewport | Element | Items | Active state |
|---|---|---|---|
| < 768px | `MobileTabbar` (fixed bottom, `--pa-z-tabbar`) | 首页 / 地图 / 贡献 / 我的 | `aria-current="page"` + accent color |
| ≥ 768px | `DesktopRail` (fixed left, `--pa-z-sticky`, width `--pa-layout-rail-width`) | 首页 / 搜索 / 地图 / 贡献 · 我的 / 设置 / 关于 | `aria-current="page"` + tinted bg |

Every nav item is ≥ `--pa-layout-touch-target` (44px). Active detection: exact
path match (`/` special-cased) or prefix match (`/place/...` highlights 首页
nowhere — only exact tab targets highlight, so sub-pages never fake a tab).

Tap targets: `MobileTabbar__item` uses `min-height: var(--pa-layout-tabbar-height)`
(56px) with an icon+label column; desktop items use `min-height: 44px`.

Safe area: mobile tabbar `padding-bottom: var(--pa-safe-bottom)`; desktop rail
`padding-bottom: var(--pa-safe-bottom)`; shell main mobile
`padding-bottom: calc(var(--pa-safe-bottom) + var(--pa-layout-tabbar-height))`.

## 4. Desktop layout (DesktopContentContainer)

Three content modes (V020_DESIGN_SYSTEM_SPEC §8/§17):

| Mode | CSS | Use |
|---|---|---|
| `single-column` | `max-width: var(--pa-layout-content-narrow)` (640px) | detail pages |
| `wide` | `max-width: var(--pa-layout-content-max)` (1200px) | home / search results |
| `split` | grid 1fr/1fr + gap | search list + preview, map + detail (future) |

All modes keep `padding-inline: var(--pa-layout-content-gutter)` and
`margin: 0 auto`; the rail offset is applied by the shell main. The old
480px-centered `#app { max-width: 480px }` was removed from `styles.css`.

## 5. Breakpoint behavior

`useBreakpoint()` resolves `BREAKPOINTS` (sm/md/lg/xl) and exposes
`mobile` (sm+md) and `desktop` (lg+xl). The shell renders tabbar iff mobile,
rail iff desktop. Verified at 320/360/390/430/768/1024/1280/1440/1920 by the
responsive e2e suite.

## 6. Global overlay contract

- **Toast**: `useUi().toast(kind, message, duration?)` — kinds
  success/info/warning/error; icons from the fixed family
  (`check-circle`/`info`/`warning`/`x-circle`); auto-dismiss default 3500ms,
  error 6000ms; `role="alert"` for error, `role="status"` otherwise.
- **Dialog**: `useUi().confirm({title, message?, confirmLabel?, cancelLabel?,
  danger?})` → Promise<boolean>; one `DialogHost` at `--pa-z-modal`.
- No page-level `alert()` and no random toast library remain in consumer pages.

## 7. Verification notes

- vue-tsc PASS on the whole client-h5 src (the pre-existing `client.ts` syntax
  breakage was fixed this round — methods now live inside the `client` object).
- Playwright e2e `h5-shell.spec.ts` (structure views offline) + `responsive.spec.ts`
  (7 viewports × 5 pages, no horizontal overflow) gate the shell.
