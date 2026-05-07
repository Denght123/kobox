<script setup lang="ts">
import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { deleteCollection, getMyCollections } from '../api/collections'
import { getMyFavorites } from '../api/favorites'
import { getMyDashboard } from '../api/me'
import FavoriteRankList from '../components/collection/FavoriteRankList.vue'
import CollectionSection from '../components/collection/CollectionSection.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import AppTopNav from '../components/layout/AppTopNav.vue'
import FloatingBackdrop from '../components/layout/FloatingBackdrop.vue'
import ProfileHeader from '../components/profile/ProfileHeader.vue'
import { useConfirm } from '../composables/useConfirm'
import { queryKeys } from '../composables/useQueryKeys'
import { useToast } from '../composables/useToast'
import { useAppStore } from '../stores/app'
import { useAuthStore } from '../stores/auth'
import type { CollectionItem, CollectionStatus, FavoriteRankItem, ListResponse, UserDashboard } from '../types'
import { userScopedStorageKey } from '../utils/userScopedCache'

const { t } = useI18n()
const router = useRouter()
const authStore = useAuthStore()
const queryClient = useQueryClient()
const appStore = useAppStore()
const { confirmAction } = useConfirm()
const { showToast } = useToast()
const COLLECTION_CACHE_BASE_KEY = 'kobox.cache.collections'
const FAVORITE_CACHE_BASE_KEY = 'kobox.cache.favorites'

const meQuery = useQuery({
  queryKey: queryKeys.me,
  queryFn: () => Promise.resolve(authStore.user),
  enabled: false,
  initialData: () => authStore.user ?? undefined,
  staleTime: 5 * 60 * 1000,
  gcTime: 30 * 60 * 1000,
})

const dashboardQuery = useQuery({
  queryKey: queryKeys.dashboard,
  queryFn: getMyDashboard,
  staleTime: 5 * 60 * 1000,
  gcTime: 30 * 60 * 1000,
  placeholderData: keepPreviousData,
})

const collectionQuery = useQuery({
  queryKey: queryKeys.collections(),
  queryFn: () => getMyCollections(undefined, { includeTotal: false }),
  enabled: false,
  staleTime: 5 * 60 * 1000,
  gcTime: 30 * 60 * 1000,
  initialData: () => readSessionCache<ListResponse<CollectionItem>>(collectionCacheKey()),
  placeholderData: () => queryClient.getQueryData(queryKeys.collections()),
})

const favoriteQuery = useQuery({
  queryKey: queryKeys.favorites(),
  queryFn: getMyFavorites,
  enabled: false,
  staleTime: 5 * 60 * 1000,
  gcTime: 30 * 60 * 1000,
  initialData: () => readSessionCache<ListResponse<FavoriteRankItem>>(favoriteCacheKey()),
  placeholderData: () => queryClient.getQueryData(queryKeys.favorites()),
})

const deleteMutation = useMutation({
  mutationFn: deleteCollection,
  onMutate: async (collectionId) => {
    await Promise.all([
      queryClient.cancelQueries({ queryKey: queryKeys.collections() }),
      queryClient.cancelQueries({ queryKey: queryKeys.favorites() }),
      queryClient.cancelQueries({ queryKey: queryKeys.dashboard }),
    ])
    const previousCollections = queryClient.getQueryData<ListResponse<CollectionItem>>(queryKeys.collections())
    const previousFavorites = queryClient.getQueryData<ListResponse<FavoriteRankItem>>(queryKeys.favorites())
    const previousDashboard = queryClient.getQueryData<UserDashboard>(queryKeys.dashboard)
    const removedCollection = (previousCollections?.items ?? previousDashboard?.collections.items ?? []).find(
      (item) => item.id === collectionId,
    )

    queryClient.setQueryData<ListResponse<CollectionItem>>(queryKeys.collections(), (current) => {
      return removeCollectionFromResponse(current, collectionId)
    })
    removeCollectionFromStatusCaches(collectionId)
    if (removedCollection) {
      queryClient.setQueryData<ListResponse<FavoriteRankItem>>(queryKeys.favorites(), (current) => {
        return removeFavoriteByAnimeFromResponse(current, removedCollection.anime.id)
      })
      const nextFavorites = queryClient.getQueryData<ListResponse<FavoriteRankItem>>(queryKeys.favorites())
      writeSessionCache(favoriteCacheKey(), nextFavorites)
    }
    queryClient.setQueryData<UserDashboard>(queryKeys.dashboard, (current) => {
      return removeCollectionFromDashboard(current, collectionId, removedCollection?.anime.id)
    })
    const nextCollections = queryClient.getQueryData<ListResponse<CollectionItem>>(queryKeys.collections())
    writeSessionCache(collectionCacheKey(), nextCollections)
    showToast(t('common.deleteSuccess'), 'danger')

    return { previousCollections, previousFavorites, previousDashboard }
  },
  onError: (_error, _collectionId, context) => {
    if (context?.previousCollections) {
      queryClient.setQueryData(queryKeys.collections(), context.previousCollections)
      writeSessionCache(collectionCacheKey(), context.previousCollections)
    }
    if (context?.previousFavorites) {
      queryClient.setQueryData(queryKeys.favorites(), context.previousFavorites)
    }
    if (context?.previousDashboard) {
      queryClient.setQueryData(queryKeys.dashboard, context.previousDashboard)
      writeSessionCache(collectionCacheKey(), context.previousDashboard.collections)
      writeSessionCache(favoriteCacheKey(), context.previousDashboard.favorites)
    }
  },
  onSuccess: () => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.collections() })
    void queryClient.invalidateQueries({ queryKey: queryKeys.favorites() })
    void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard })
  },
})

const profile = computed(() => dashboardQuery.data.value?.profile ?? meQuery.data.value ?? authStore.user)
const collections = computed(() => uniqueCollections(collectionQuery.data.value?.items ?? dashboardQuery.data.value?.collections?.items ?? []))
const favorites = computed(() => uniqueFavorites(favoriteQuery.data.value?.items ?? dashboardQuery.data.value?.favorites?.items ?? []))
const isHydratingShowcase = computed(
  () => dashboardQuery.isFetching.value && collections.value.length === 0,
)

const completedItems = computed(() =>
  collections.value.filter((item) => item.collection_status === 'completed'),
)
const watchingItems = computed(() =>
  collections.value.filter((item) => item.collection_status === 'watching'),
)
const planItems = computed(() =>
  collections.value.filter((item) => item.collection_status === 'plan_to_watch'),
)

watch(
  () => collectionQuery.data.value,
  (data) => writeSessionCache(collectionCacheKey(), data),
)

watch(
  () => favoriteQuery.data.value,
  (data) => writeSessionCache(favoriteCacheKey(), data),
)

watch(
  () => dashboardQuery.data.value,
  (data) => {
    if (!data) {
      return
    }
    if (data.profile) {
      queryClient.setQueryData(queryKeys.me, data.profile)
      authStore.setUser(data.profile)
    }
    if (data.collections) {
      queryClient.setQueryData(queryKeys.collections(), data.collections)
      writeSessionCache(collectionCacheKey(), data.collections)
    }
    if (data.favorites) {
      queryClient.setQueryData(queryKeys.favorites(), data.favorites)
      writeSessionCache(favoriteCacheKey(), data.favorites)
    }
    if (data.settings) {
      queryClient.setQueryData(queryKeys.settings, data.settings)
    }
  },
  { immediate: true },
)

watch(
  () => appStore.locale,
  () => {
    void dashboardQuery.refetch()
  },
)

function onAddStatus(status: CollectionStatus) {
  void router.push({ name: 'search', query: { status } })
}

async function onRemoveCollection(collectionId: number) {
  const confirmed = await confirmAction({
    title: t('common.deleteConfirmTitle'),
    message: t('common.deleteConfirmMessage'),
    confirmText: t('common.confirm'),
    cancelText: t('common.cancel'),
    tone: 'danger',
  })
  if (!confirmed) {
    return
  }
  deleteMutation.mutate(collectionId)
}

function readSessionCache<T>(key: string): T | undefined {
  try {
    const raw = sessionStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : undefined
  } catch {
    return undefined
  }
}

function writeSessionCache(key: string, value: unknown) {
  if (!value) {
    return
  }
  sessionStorage.setItem(key, JSON.stringify(value))
}

function removeCollectionFromResponse(
  current: ListResponse<CollectionItem> | undefined,
  collectionId: number,
) {
  if (!current) {
    return current
  }
  const items = current.items.filter((item) => item.id !== collectionId)
  return {
    ...current,
    items,
    total: Math.max(0, current.total - (items.length === current.items.length ? 0 : 1)),
  }
}

function removeFavoriteByAnimeFromResponse(
  current: ListResponse<FavoriteRankItem> | undefined,
  animeId: number,
) {
  if (!current) {
    return current
  }
  const items = current.items
    .filter((item) => item.anime.id !== animeId)
    .map((item, index) => ({ ...item, rank_order: index + 1 }))
  return {
    ...current,
    items,
    total: items.length,
    page_size: items.length || 10,
  }
}

function removeCollectionFromDashboard(
  current: UserDashboard | undefined,
  collectionId: number,
  animeId?: number,
) {
  if (!current) {
    return current
  }
  return {
    ...current,
    collections: removeCollectionFromResponse(current.collections, collectionId) ?? current.collections,
    favorites:
      animeId === undefined
        ? current.favorites
        : removeFavoriteByAnimeFromResponse(current.favorites, animeId) ?? current.favorites,
  }
}

function removeCollectionFromStatusCaches(collectionId: number) {
  for (const status of ['completed', 'watching', 'plan_to_watch', 'on_hold', 'dropped'] as const) {
    queryClient.setQueryData<ListResponse<CollectionItem>>(queryKeys.collections(status), (current) => {
      return removeCollectionFromResponse(current, collectionId)
    })
  }
}

function collectionCacheKey() {
  return userScopedStorageKey(COLLECTION_CACHE_BASE_KEY, authStore.user?.id ? String(authStore.user.id) : undefined)
}

function favoriteCacheKey() {
  return userScopedStorageKey(FAVORITE_CACHE_BASE_KEY, authStore.user?.id ? String(authStore.user.id) : undefined)
}

function uniqueCollections(items: CollectionItem[]) {
  const seen = new Set<number>()
  return items.filter((item) => {
    if (seen.has(item.anime.id)) {
      return false
    }
    seen.add(item.anime.id)
    return true
  })
}

function uniqueFavorites(items: FavoriteRankItem[]) {
  const seen = new Set<number>()
  return items
    .filter((item) => {
      if (seen.has(item.anime.id)) {
        return false
      }
      seen.add(item.anime.id)
      return true
    })
    .map((item, index) => ({ ...item, rank_order: index + 1 }))
}

</script>

<template>
  <div class="page-root">
    <FloatingBackdrop />
    <AppTopNav active="showcase" />
    <main class="container showcase">
      <ProfileHeader
        v-if="profile"
        :profile="profile"
        :subtitle="t('showcase.profileBio')"
        :show-share-button="false"
      />
      <div v-if="isHydratingShowcase" class="loaded-pill">
        {{ t('common.loading') }}
      </div>
      <section class="layout-grid">
        <div class="main-column">
          <CollectionSection
            :title="t('showcase.completedTitle')"
            :items="completedItems"
            status="completed"
            :is-loading="isHydratingShowcase"
            @add="onAddStatus"
            @remove="onRemoveCollection"
          />
          <CollectionSection
            :title="t('showcase.watchingTitle')"
            :items="watchingItems"
            status="watching"
            :is-loading="isHydratingShowcase"
            @add="onAddStatus"
            @remove="onRemoveCollection"
          />
          <CollectionSection
            :title="t('showcase.planTitle')"
            :items="planItems"
            status="plan_to_watch"
            :is-loading="isHydratingShowcase"
            @add="onAddStatus"
            @remove="onRemoveCollection"
          />
        </div>
        <aside class="side-column">
          <FavoriteRankList :items="favorites" />
        </aside>
      </section>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.showcase {
  display: grid;
  gap: 26px;
}

.layout-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 20px;
  position: relative;
}

.main-column {
  display: grid;
  gap: 18px;
}

.loaded-pill {
  width: max-content;
  border-radius: 999px;
  padding: 8px 14px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--on-surface-variant);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  box-shadow: var(--shadow-soft);
}

.side-column {
  position: absolute;
  left: calc(100% + 18px);
  top: 0;
  width: 320px;
  display: grid;
  align-content: start;
  gap: 12px;
}

@media (max-width: 1720px) {
  .side-column {
    position: static;
    width: auto;
  }
}
</style>
