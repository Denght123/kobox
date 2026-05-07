import type {
  AddCollectionPayload,
  CollectionItem,
  CollectionStatus,
  ListResponse,
  UpdateCollectionPayload,
} from '../types'

import { apiClient } from './client'
import { mockCollections, paginate } from './mockData'
import { withMockFallback } from './mockRuntime'

export async function getMyCollections(
  status?: CollectionStatus,
  options: { includeTotal?: boolean } = {},
): Promise<ListResponse<CollectionItem>> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.get<ListResponse<CollectionItem>>('/api/me/collections', {
        params: {
          ...(status ? { status } : {}),
          page_size: 100,
          include_total: options.includeTotal ?? true,
        },
      })
      return data
    },
    () => {
      const owned = mockCollections.filter((item) => item.user_id === 1)
      const filtered = status ? owned.filter((item) => item.collection_status === status) : owned
      return paginate(filtered, 1, 50)
    },
  )
}

export async function addCollection(
  payload: AddCollectionPayload,
): Promise<CollectionItem> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.post<CollectionItem>('/api/me/collections', payload)
      return data
    },
    () => {
      const target = mockCollections.find(
        (item) =>
          item.user_id === 1 &&
          ((payload.anime_id !== undefined && item.anime.id === payload.anime_id) ||
            (payload.source_id && item.anime.source_id === payload.source_id)),
      )
      if (target) {
        target.collection_status = payload.collection_status
        target.updated_at = new Date().toISOString()
        return target
      }
      const anime = mockCollections.find(
        (item) =>
          (payload.anime_id !== undefined && item.anime.id === payload.anime_id) ||
          (payload.source_id && item.anime.source_id === payload.source_id),
      )?.anime
      if (!anime) {
        throw new Error('anime not found in mock data')
      }
      const newItem: CollectionItem = {
        id: Date.now(),
        user_id: 1,
        anime,
        collection_status: payload.collection_status,
        added_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      mockCollections.push(newItem)
      return newItem
    },
  )
}

export async function updateCollection(
  collectionId: number,
  payload: UpdateCollectionPayload,
): Promise<CollectionItem> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.put<CollectionItem>(
        `/api/me/collections/${collectionId}`,
        payload,
      )
      return data
    },
    () => {
      const current = mockCollections.find((item) => item.id === collectionId && item.user_id === 1)
      if (!current) {
        throw new Error('collection not found')
      }
      current.collection_status = payload.collection_status
      current.updated_at = new Date().toISOString()
      return current
    },
  )
}

export async function deleteCollection(collectionId: number): Promise<void> {
  return withMockFallback(
    async () => {
      await apiClient.delete(`/api/me/collections/${collectionId}`)
    },
    () => {
      const index = mockCollections.findIndex((item) => item.id === collectionId && item.user_id === 1)
      if (index >= 0) {
        mockCollections.splice(index, 1)
      }
    },
  )
}
