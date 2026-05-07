import type { AnimeSuggestion, AnimeSummary, ListResponse, SearchAnimeParams } from '../types'

import { apiClient } from './client'
import { mockAnimePool, paginate } from './mockData'
import { withMockFallback } from './mockRuntime'

export async function searchAnimes(
  params: SearchAnimeParams,
  signal?: AbortSignal,
): Promise<ListResponse<AnimeSummary>> {
  const page = params.page ?? 1
  const pageSize = params.page_size ?? 20
  return withMockFallback(
    async () => {
      const { data } = await apiClient.get<ListResponse<AnimeSummary>>('/api/anime/search', {
        signal,
        params: {
          q: params.q,
          page,
          page_size: pageSize,
        },
      })
      return data
    },
    () => {
      const normalized = params.q.trim().toLowerCase()
      const filtered = normalized
        ? mockAnimePool.filter((item) => item.title.toLowerCase().includes(normalized))
        : mockAnimePool
      return paginate(filtered, page, pageSize)
    },
  )
}

export async function searchAnimeSuggestions(
  params: SearchAnimeParams,
  signal?: AbortSignal,
): Promise<ListResponse<AnimeSuggestion>> {
  const page = params.page ?? 1
  const pageSize = params.page_size ?? 10
  return withMockFallback(
    async () => {
      const { data } = await apiClient.get<ListResponse<AnimeSuggestion>>(
        '/api/anime/search/suggestions',
        {
          signal,
          params: {
            q: params.q,
            page,
            page_size: pageSize,
          },
        },
      )
      return data
    },
    () => {
      const normalized = params.q.trim().toLowerCase()
      const filtered = normalized
        ? mockAnimePool
            .filter((item) => item.title.toLowerCase().includes(normalized))
            .map((item) => ({ id: item.id, title: item.title }))
        : []
      return paginate(filtered, page, pageSize)
    },
  )
}
