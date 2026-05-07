import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import { i18n } from './i18n'
import { router } from './router'
import { warmupAuthedQueries, warmupRouteChunk } from './composables/useRouteWarmup'
import { useAuthStore } from './stores/auth'
import './style.css'

const app = createApp(App)
const pinia = createPinia()
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60_000,
      gcTime: 30 * 60_000,
      retry: 1,
      refetchOnWindowFocus: false,
      refetchOnMount: false,
    },
  },
})

app.use(pinia)
app.use(i18n)
app.use(router)
app.use(VueQueryPlugin, { queryClient })

const authStore = useAuthStore(pinia)
if (authStore.isAuthenticated) {
  warmupRouteChunk('showcase')
  void warmupAuthedQueries(queryClient)
}

app.mount('#app')
