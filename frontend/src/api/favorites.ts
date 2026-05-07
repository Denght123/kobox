import type { FavoriteRankItem, ListResponse, UpdateFavoriteRankPayload } from '../types'

import { apiClient } from './client'
import { mockFavorites, paginate } from './mockData'
import { withMockFallback } from './mockRuntime'

export async function getMyFavorites(): Promise<ListResponse<FavoriteRankItem>> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.get<ListResponse<FavoriteRankItem>>('/api/me/favorites')
      return data
    },
    () => {
      const items = mockFavorites
        .filter((item) => item.user_id === 1)
        .sort((a, b) => a.rank_order - b.rank_order)
      return paginate(items, 1, 50)
    },
  )
}

export async function updateFavoriteRank(
  payload: UpdateFavoriteRankPayload,
): Promise<ListResponse<FavoriteRankItem>> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.put<ListResponse<FavoriteRankItem>>(
        '/api/me/favorites/rank',
        payload,
      )
      return data
    },
    () => {
      payload.items.forEach((target) => {
        const current = mockFavorites.find(
          (item) => item.user_id === 1 && item.anime.id === target.anime_id,
        )
        if (current) {
          current.rank_order = target.rank_order
          current.updated_at = new Date().toISOString()
        }
      })
      const list = mockFavorites
        .filter((item) => item.user_id === 1)
        .sort((a, b) => a.rank_order - b.rank_order)
      return paginate(list, 1, 50)
    },
  )
}
