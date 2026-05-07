import type { CollectionStatus } from '../types'

export const queryKeys = {
  me: ['me'] as const,
  settings: ['settings'] as const,
  dashboard: ['me', 'dashboard'] as const,
  search: (keyword: string, locale = 'zh-CN') => ['anime', 'search', locale, keyword] as const,
  searchSuggestions: (keyword: string, locale = 'zh-CN') =>
    ['anime', 'search', 'suggestions', locale, keyword] as const,
  collections: (status?: CollectionStatus) =>
    ['collections', status ?? 'all'] as const,
  favorites: () => ['favorites'] as const,
  publicProfile: (username: string) => ['public', username, 'profile'] as const,
  publicCollections: (username: string, status?: CollectionStatus) =>
    ['public', username, 'collections', status ?? 'all'] as const,
  publicFavorites: (username: string) => ['public', username, 'favorites'] as const,
}
