<script setup lang="ts">
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { addCollection, deleteCollection, getMyCollections, updateCollection } from '../api/collections'
import { searchAnimes, searchAnimeSuggestions } from '../api/anime'
import AnimeCoverCard from '../components/anime/AnimeCoverCard.vue'
import EmptyState from '../components/common/EmptyState.vue'
import SearchBar from '../components/common/SearchBar.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import AppTopNav from '../components/layout/AppTopNav.vue'
import FloatingBackdrop from '../components/layout/FloatingBackdrop.vue'
import { useConfirm } from '../composables/useConfirm'
import { queryKeys } from '../composables/useQueryKeys'
import { useToast } from '../composables/useToast'
import { useAppStore } from '../stores/app'
import type { AnimeSuggestion, AnimeSummary, CollectionItem, CollectionStatus, ListResponse, UserDashboard } from '../types'
import { statusToI18nKey } from '../utils/format'

const { t } = useI18n()
const route = useRoute()
const queryClient = useQueryClient()
const appStore = useAppStore()
const { confirmAction } = useConfirm()
const { showToast } = useToast()
const SEARCH_MEMORY_KEY = 'kobox.search.last'
const searchMemory = readSearchMemory()
const keyword = ref(searchMemory?.keyword ?? '')
const debouncedKeyword = ref('')
const hasSearched = ref(Boolean(searchMemory?.data?.items.length))
const localStatusByKey = ref(new Map<string, CollectionStatus>())
const pendingCreatedByKey = ref(new Map<string, number>())
const tempCollectionByKey = ref(new Map<string, number>())
let debounceTimer = 0

watch(
  () => keyword.value.trim(),
  (value) => {
    if (debounceTimer) {
      window.clearTimeout(debounceTimer)
    }
    debounceTimer = window.setTimeout(() => {
      debouncedKeyword.value = value
      debounceTimer = 0
    }, 60)
  },
  { immediate: true },
)

const searchQuery = useQuery({
  queryKey: computed(() => queryKeys.search(keyword.value.trim(), appStore.locale)),
  queryFn: ({ signal }) => searchAnimes({ q: keyword.value.trim(), page: 1, page_size: 16 }, signal),
  enabled: false,
  initialData: () =>
    searchMemory?.locale === appStore.locale && searchMemory.keyword === keyword.value.trim()
      ? searchMemory.data
      : undefined,
  placeholderData: keepPreviousData,
  staleTime: 10 * 60 * 1000,
  gcTime: 30 * 60 * 1000,
})

const suggestionQuery = useQuery({
  queryKey: computed(() => queryKeys.searchSuggestions(debouncedKeyword.value, appStore.locale)),
  queryFn: ({ signal }) =>
    searchAnimeSuggestions({
      q: debouncedKeyword.value,
      page: 1,
      page_size: 8,
    }, signal),
  enabled: computed(() => debouncedKeyword.value.length > 0),
  placeholderData: keepPreviousData,
  staleTime: 10 * 60 * 1000,
  gcTime: 30 * 60 * 1000,
})

const collectionQuery = useQuery({
  queryKey: queryKeys.collections(),
  queryFn: () => getMyCollections(),
  staleTime: 5 * 60 * 1000,
  gcTime: 30 * 60 * 1000,
})

const addMutation = useMutation({
  mutationFn: addCollection,
  onSuccess: (item) => {
    rememberCreatedCollection(item)
    upsertCollectionCache(item)
    void queryClient.invalidateQueries({ queryKey: queryKeys.collections() })
    void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard })
  },
  onError: (_error, payload) => {
    const anime = animeList.value.find(
      (item) =>
        (payload.anime_id !== undefined && item.id === payload.anime_id) ||
        (payload.source_id !== undefined && item.source_id === payload.source_id),
    )
    if (!anime) {
      return
    }
    const tempId = tempCollectionByKey.value.get(getAnimeKey(anime))
    if (tempId) {
      removeCollectionCache(tempId)
    }
    clearLocalStatus(anime)
  },
})

const updateMutation = useMutation({
  mutationFn: ({ collectionId, status }: { collectionId: number; status: CollectionStatus }) =>
    updateCollection(collectionId, { collection_status: status }),
  onSuccess: (item) => {
    upsertCollectionCache(item)
    void queryClient.invalidateQueries({ queryKey: queryKeys.collections() })
    void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard })
  },
})

const deleteMutation = useMutation({
  mutationFn: deleteCollection,
  onSuccess: (_, collectionId) => {
    removeCollectionCache(collectionId)
    void queryClient.invalidateQueries({ queryKey: queryKeys.collections() })
    void queryClient.invalidateQueries({ queryKey: queryKeys.favorites() })
    void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard })
  },
})

const collectionMap = computed(() => {
  const map = new Map<number, { id: number; status: CollectionStatus }>()
  const sourceMap = new Map<string, { id: number; status: CollectionStatus }>()
  collectionQuery.data.value?.items.forEach((item) => {
    map.set(item.anime.id, { id: item.id, status: item.collection_status })
    if (item.anime.source_id) {
      sourceMap.set(item.anime.source_id, { id: item.id, status: item.collection_status })
    }
  })
  return { byId: map, bySourceId: sourceMap }
})

const animeList = computed(() => searchQuery.data.value?.items ?? [])
const suggestions = computed(() => suggestionQuery.data.value?.items ?? [])
const shouldShowFullLoading = computed(() => searchQuery.isFetching.value && hasSearched.value && animeList.value.length === 0)
const shouldShowInlineLoading = computed(() => searchQuery.isFetching.value && hasSearched.value && animeList.value.length > 0)

function onSubmitSearch() {
  hasSearched.value = true
  if (!keyword.value.trim()) {
    return
  }
  void searchQuery.refetch()
}

function onSelectSuggestion(item: AnimeSuggestion) {
  keyword.value = item.title
  onSubmitSearch()
}

function getCollectionEntry(anime: AnimeSummary) {
  if (anime.source_id) {
    return collectionMap.value.bySourceId.get(anime.source_id)
  }
  return collectionMap.value.byId.get(anime.id)
}

function getAnimeKey(anime: AnimeSummary) {
  return anime.source_id ?? `anime:${anime.id}`
}

function getVisibleStatus(anime: AnimeSummary) {
  return localStatusByKey.value.get(getAnimeKey(anime)) ?? getCollectionEntry(anime)?.status ?? null
}

function getTargetStatus(fallback: CollectionStatus) {
  const routeStatus = route.query.status
  if (
    routeStatus === 'completed' ||
    routeStatus === 'watching' ||
    routeStatus === 'plan_to_watch' ||
    routeStatus === 'on_hold' ||
    routeStatus === 'dropped'
  ) {
    return routeStatus
  }
  return fallback
}

function markLocalStatus(anime: AnimeSummary, status: CollectionStatus) {
  const next = new Map(localStatusByKey.value)
  next.set(getAnimeKey(anime), status)
  localStatusByKey.value = next
}

function clearLocalStatus(anime: AnimeSummary) {
  const next = new Map(localStatusByKey.value)
  next.delete(getAnimeKey(anime))
  localStatusByKey.value = next
}

async function toggleStatus(anime: AnimeSummary, targetStatus: CollectionStatus) {
  const confirmed = await confirmAction({
    title: t('common.confirmTitle'),
    message: t('common.confirmMessage'),
    confirmText: t('common.confirm'),
    cancelText: t('common.cancel'),
    tone: getVisibleStatus(anime) === targetStatus ? 'danger' : 'default',
  })
  if (!confirmed) {
    return
  }

  const animeKey = getAnimeKey(anime)
  const found = getCollectionEntry(anime)
  if (getVisibleStatus(anime) === targetStatus) {
    const collectionId =
      found?.id ?? pendingCreatedByKey.value.get(animeKey) ?? tempCollectionByKey.value.get(animeKey)
    if (collectionId) {
      removeCollectionCache(collectionId)
      if (collectionId > 0) {
        deleteMutation.mutate(collectionId)
      }
    }
    clearLocalStatus(anime)
    showToast(t('common.deleteSuccess'), 'danger')
    return
  }

  if (found) {
    removeCollectionCache(found.id)
    upsertCollectionCache({
      ...buildCollectionItem(anime, found.id, targetStatus),
      added_at: new Date().toISOString(),
    })
    updateMutation.mutate({
      collectionId: found.id,
      status: targetStatus,
    })
    markLocalStatus(anime, targetStatus)
    showToast(t('common.updateSuccess', { status: t(statusToI18nKey(targetStatus)) }), 'info')
    return
  }
  const tempId = -Date.now()
  const tempItem = buildCollectionItem(anime, tempId, targetStatus)
  const nextTemps = new Map(tempCollectionByKey.value)
  nextTemps.set(animeKey, tempId)
  tempCollectionByKey.value = nextTemps
  upsertCollectionCache(tempItem)
  addMutation.mutate({
    anime_id: anime.id > 0 ? anime.id : undefined,
    source_id: anime.source_id ?? undefined,
    collection_status: targetStatus,
  })
  markLocalStatus(anime, targetStatus)
  showToast(t('common.addStatusSuccess', { status: t(statusToI18nKey(targetStatus)) }))
}

function onAdd(anime: AnimeSummary) {
  void toggleStatus(anime, getTargetStatus('completed'))
}

function onUpdateStatus(anime: AnimeSummary, status: CollectionStatus) {
  void toggleStatus(anime, status)
}

function rememberCreatedCollection(item: CollectionItem) {
  const next = new Map(pendingCreatedByKey.value)
  next.set(getAnimeKey(item.anime), item.id)
  pendingCreatedByKey.value = next
  const tempId = tempCollectionByKey.value.get(getAnimeKey(item.anime))
  if (tempId) {
    removeCollectionCache(tempId)
    const nextTemps = new Map(tempCollectionByKey.value)
    nextTemps.delete(getAnimeKey(item.anime))
    tempCollectionByKey.value = nextTemps
  }
}

function buildCollectionItem(anime: AnimeSummary, id: number, status: CollectionStatus): CollectionItem {
  const now = new Date().toISOString()
  return {
    id,
    user_id: 0,
    anime,
    collection_status: status,
    added_at: now,
    updated_at: now,
  }
}

function upsertCollectionCache(item: CollectionItem) {
  upsertDashboardCollection(item)
  queryClient.setQueryData<ListResponse<CollectionItem>>(queryKeys.collections(), (current) => {
    for (const status of ['completed', 'watching', 'plan_to_watch', 'on_hold', 'dropped'] as const) {
      if (status !== item.collection_status) {
        removeCollectionFromStatusCache(item, status)
      }
    }

    const existingStatusKey = queryKeys.collections(item.collection_status)
    queryClient.setQueryData<ListResponse<CollectionItem>>(existingStatusKey, (statusCurrent) => {
      if (!statusCurrent) {
        return { items: [item], total: 1, page: 1, page_size: 100 }
      }
      const statusIndex = statusCurrent.items.findIndex((entry) => isSameCollection(entry, item))
      const statusItems =
        statusIndex >= 0 ? [...statusCurrent.items] : [item, ...statusCurrent.items]
      if (statusIndex >= 0) {
        statusItems[statusIndex] = item
      }
      const items = uniqueCollections(statusItems)
      return { ...statusCurrent, items, total: items.length }
    })

    if (!current) {
      return { items: [item], total: 1, page: 1, page_size: 100 }
    }
    const index = current.items.findIndex((entry) => isSameCollection(entry, item))
    const items = index >= 0 ? [...current.items] : [item, ...current.items]
    if (index >= 0) {
      items[index] = item
    }
    const uniqueItems = uniqueCollections(items)
    return { ...current, items: uniqueItems, total: uniqueItems.length }
  })
}

function removeCollectionCache(collectionId: number) {
  removeDashboardCollection(collectionId)
  queryClient.setQueryData<ListResponse<CollectionItem>>(queryKeys.collections(), (current) => {
    if (!current) {
      return current
    }
    const items = current.items.filter((item) => item.id !== collectionId)
    return { ...current, items, total: Math.max(0, current.total - (items.length === current.items.length ? 0 : 1)) }
  })
  for (const status of ['completed', 'watching', 'plan_to_watch', 'on_hold', 'dropped'] as const) {
    queryClient.setQueryData<ListResponse<CollectionItem>>(queryKeys.collections(status), (current) => {
      if (!current) {
        return current
      }
      const items = current.items.filter((item) => item.id !== collectionId)
      return {
        ...current,
        items,
        total: Math.max(0, current.total - (items.length === current.items.length ? 0 : 1)),
      }
    })
  }
}

function upsertDashboardCollection(item: CollectionItem) {
  queryClient.setQueryData<UserDashboard>(queryKeys.dashboard, (current) => {
    if (!current) {
      return current
    }
    const index = current.collections.items.findIndex((entry) => isSameCollection(entry, item))
    const items = index >= 0 ? [...current.collections.items] : [item, ...current.collections.items]
    if (index >= 0) {
      items[index] = item
    }
    const uniqueItems = uniqueCollections(items)
    return {
      ...current,
      collections: {
        ...current.collections,
        items: uniqueItems,
        total: uniqueItems.length,
      },
    }
  })
}

function removeDashboardCollection(collectionId: number) {
  queryClient.setQueryData<UserDashboard>(queryKeys.dashboard, (current) => {
    if (!current) {
      return current
    }
    const removed = current.collections.items.find((item) => item.id === collectionId)
    const items = current.collections.items.filter((item) => item.id !== collectionId)
    const favorites = removed
      ? current.favorites.items
          .filter((item) => item.anime.id !== removed.anime.id)
          .map((item, index) => ({ ...item, rank_order: index + 1 }))
      : current.favorites.items
    return {
      ...current,
      collections: {
        ...current.collections,
        items,
        total: items.length,
      },
      favorites: {
        ...current.favorites,
        items: favorites,
        total: favorites.length,
        page_size: favorites.length || 10,
      },
    }
  })
}

function removeCollectionFromStatusCache(item: CollectionItem, status: CollectionStatus) {
  queryClient.setQueryData<ListResponse<CollectionItem>>(queryKeys.collections(status), (current) => {
    if (!current) {
      return current
    }
    const items = current.items.filter((entry) => !isSameCollection(entry, item))
    return { ...current, items, total: items.length }
  })
}

function isSameCollection(left: CollectionItem, right: CollectionItem) {
  if (left.id === right.id) {
    return true
  }
  if (left.anime.id > 0 && right.anime.id > 0 && left.anime.id === right.anime.id) {
    return true
  }
  return Boolean(left.anime.source_id && right.anime.source_id && left.anime.source_id === right.anime.source_id)
}

function uniqueCollections(items: CollectionItem[]) {
  const seen = new Set<string>()
  const result: CollectionItem[] = []
  for (const item of items) {
    const key = item.anime.id > 0
      ? `id:${item.anime.id}`
      : item.anime.source_id
        ? `source:${item.anime.source_id}`
        : `collection:${item.id}`
    if (seen.has(key)) {
      continue
    }
    seen.add(key)
    result.push(item)
  }
  return result
}

watch(
  () => searchQuery.data.value,
  (data) => {
    const nextKeyword = keyword.value.trim()
    if (!data || !nextKeyword) {
      return
    }
    localStorage.setItem(
      SEARCH_MEMORY_KEY,
      JSON.stringify({
        keyword: nextKeyword,
        locale: appStore.locale,
        data,
      }),
    )
  },
)

watch(
  () => appStore.locale,
  () => {
    if (hasSearched.value && keyword.value.trim()) {
      void searchQuery.refetch()
      void collectionQuery.refetch()
    }
  },
)

function readSearchMemory():
  | { keyword: string; locale: string; data: ListResponse<AnimeSummary> }
  | null {
  try {
    const raw = localStorage.getItem(SEARCH_MEMORY_KEY)
    return raw ? (JSON.parse(raw) as { keyword: string; locale: string; data: ListResponse<AnimeSummary> }) : null
  } catch {
    return null
  }
}
</script>

<template>
  <div class="page-root">
    <FloatingBackdrop />
    <AppTopNav active="search" />
    <main class="container search-page">
      <section class="hero">
        <div class="sticker">
          <span class="material-symbols-outlined">auto_awesome</span>
          <span>{{ t('search.newArrival') }}</span>
        </div>
        <h1 class="section-title">{{ t('search.heroTitle') }}</h1>
        <p class="subtitle">{{ t('search.heroSubtitle') }}</p>
        <SearchBar
          v-model="keyword"
          :button-text="t('search.searchButton')"
          :placeholder="t('search.searchPlaceholder')"
          :suggestions="suggestions"
          :suggestions-loading="suggestionQuery.isFetching.value && !searchQuery.isFetching.value"
          @select-suggestion="onSelectSuggestion"
          @submit="onSubmitSearch"
        />
      </section>

      <section class="results">
        <div v-if="shouldShowFullLoading" class="loading">
          {{ t('common.loading') }}
        </div>
        <EmptyState
          v-else-if="hasSearched && animeList.length === 0"
          :title="t('search.empty')"
          :description="t('search.heroSubtitle')"
        />
        <div v-else class="results-body">
          <div v-if="shouldShowInlineLoading" class="loading-pill">
            {{ t('common.loading') }}
          </div>
          <div class="anime-grid">
            <AnimeCoverCard
              v-for="anime in animeList"
              :key="anime.id"
              :anime="anime"
              :status="getVisibleStatus(anime)"
              @add="onAdd"
              @update-status="onUpdateStatus"
            />
          </div>
        </div>
      </section>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.search-page {
  display: grid;
  gap: 34px;
}

.hero {
  position: relative;
  text-align: center;
  padding: 50px 0 22px;
  display: grid;
  justify-items: center;
  gap: 16px;
}

.hero .subtitle {
  max-width: 620px;
}

.sticker {
  position: absolute;
  left: 12px;
  top: 8px;
  background: rgba(250, 211, 253, 0.5);
  border-radius: 12px;
  padding: 8px 12px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--on-secondary-container);
  transform: rotate(-8deg);
}

.results {
  display: grid;
  gap: 14px;
}

.loading {
  color: var(--on-surface-variant);
}

.results-body {
  position: relative;
}

.loading-pill {
  position: sticky;
  top: 82px;
  justify-self: start;
  z-index: 4;
  width: max-content;
  margin-bottom: 12px;
  border-radius: 999px;
  padding: 8px 12px;
  color: var(--on-surface-variant);
  background: rgba(255, 255, 255, 0.86);
  box-shadow: var(--shadow-soft);
  backdrop-filter: blur(12px);
}

.anime-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(245px, 1fr));
  gap: 16px;
}
</style>
