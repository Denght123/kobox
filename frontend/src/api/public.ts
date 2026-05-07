import type { CollectionItem, CollectionStatus, FavoriteRankItem, ListResponse, UserProfile } from '../types'

import { apiClient } from './client'
import { mockCollections, mockFavorites, mockPublicUser, paginate } from './mockData'
import { withMockFallback } from './mockRuntime'

export async function getPublicUser(username: string): Promise<UserProfile> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.get<UserProfile>(`/api/public/users/${username}`)
      return data
    },
    () => ({
      ...mockPublicUser,
      username,
    }),
  )
}

export async function getPublicCollections(
  username: string,
  status?: CollectionStatus,
): Promise<ListResponse<CollectionItem>> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.get<ListResponse<CollectionItem>>(
        `/api/public/users/${username}/collections`,
        {
          params: status ? { status } : undefined,
        },
      )
      return data
    },
    () => {
      const userId = username === mockPublicUser.username ? 2 : 1
      const owned = mockCollections.filter((item) => item.user_id === userId)
      const filtered = status ? owned.filter((item) => item.collection_status === status) : owned
      return paginate(filtered, 1, 50)
    },
  )
}

export async function getPublicFavorites(
  username: string,
): Promise<ListResponse<FavoriteRankItem>> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.get<ListResponse<FavoriteRankItem>>(
        `/api/public/users/${username}/favorites`,
      )
      return data
    },
    () => {
      const userId = username === mockPublicUser.username ? 2 : 1
      const list = mockFavorites
        .filter((item) => item.user_id === userId)
        .sort((a, b) => a.rank_order - b.rank_order)
      return paginate(list, 1, 50)
    },
  )
}
