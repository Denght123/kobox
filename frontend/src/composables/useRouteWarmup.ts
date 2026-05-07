import type { QueryClient } from '@tanstack/vue-query'

import { getMyDashboard } from '../api/me'
import { queryKeys } from './useQueryKeys'
import type { RoutePrefetchTarget } from '../router'
import { preloadRouteChunk } from '../router'
import type { UserDashboard } from '../types'
import { getStoredUserId } from '../utils/userScopedCache'

const warmupTargets = new Map<string, Promise<void>>()

export function warmupRouteChunk(target: RoutePrefetchTarget): void {
  preloadRouteChunk(target)
}

export function warmupAuthedQueries(queryClient: QueryClient): Promise<void> {
  const key = `authed-shell:${getStoredUserId()}`
  const cached = warmupTargets.get(key)
  if (cached) {
    return cached
  }

  const promise = queryClient
    .fetchQuery({
      queryKey: queryKeys.dashboard,
      queryFn: () => getMyDashboard(),
      staleTime: 0,
    })
    .then((dashboard) => {
      seedDashboardQuery(queryClient, dashboard)
    })
    .then(() => undefined)
    .finally(() => {
      warmupTargets.delete(key)
    })

  warmupTargets.set(key, promise)
  return promise
}

export function seedDashboardQuery(queryClient: QueryClient, dashboard: UserDashboard): void {
  queryClient.setQueryData(queryKeys.dashboard, dashboard)
  queryClient.setQueryData(queryKeys.me, dashboard.profile)
  queryClient.setQueryData(queryKeys.settings, dashboard.settings)
  queryClient.setQueryData(queryKeys.collections(), dashboard.collections)
  queryClient.setQueryData(queryKeys.favorites(), dashboard.favorites)
}
