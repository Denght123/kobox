import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '../stores/auth'

const routeChunks = {
  auth: () => import('../pages/AuthPage.vue'),
  search: () => import('../pages/SearchPage.vue'),
  showcase: () => import('../pages/ShowcasePage.vue'),
  favoriteRank: () => import('../pages/FavoriteRankPage.vue'),
  settings: () => import('../pages/SettingsPage.vue'),
  publicProfile: () => import('../pages/PublicProfilePage.vue'),
} as const

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      redirect: () => {
        const authStore = useAuthStore()
        return authStore.isAuthenticated ? '/showcase' : '/auth'
      },
    },
    { path: '/auth', name: 'auth', component: routeChunks.auth },
    { path: '/search', name: 'search', component: routeChunks.search, meta: { requiresAuth: true } },
    { path: '/showcase', name: 'showcase', component: routeChunks.showcase, meta: { requiresAuth: true } },
    {
      path: '/favorite-rank',
      name: 'favorite-rank',
      component: routeChunks.favoriteRank,
      meta: { requiresAuth: true },
    },
    { path: '/settings', name: 'settings', component: routeChunks.settings, meta: { requiresAuth: true } },
    { path: '/u/:username', name: 'public-profile', component: routeChunks.publicProfile, props: true },
    {
      path: '/:pathMatch(.*)*',
      redirect: () => {
        const authStore = useAuthStore()
        return authStore.isAuthenticated ? '/showcase' : '/auth'
      },
    },
  ],
})

router.beforeEach((to) => {
  const authStore = useAuthStore()

  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return {
      path: '/auth',
      query: {
        redirect: to.fullPath,
      },
    }
  }

  const forceAuthEntry = to.query.publicEntry === '1'
  if (to.path === '/auth' && authStore.isAuthenticated && !forceAuthEntry) {
    const redirectPath =
      typeof to.query.redirect === 'string' && to.query.redirect !== '/auth'
        ? to.query.redirect
        : '/showcase'
    return redirectPath
  }

  return true
})

export type RoutePrefetchTarget =
  | 'auth'
  | 'search'
  | 'showcase'
  | 'favoriteRank'
  | 'settings'
  | 'publicProfile'

export function preloadRouteChunk(target: RoutePrefetchTarget): void {
  void routeChunks[target]()
}
