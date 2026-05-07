<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { getMyCollections } from '../api/collections'
import { getMyFavorites, updateFavoriteRank } from '../api/favorites'
import AppFooter from '../components/layout/AppFooter.vue'
import AppTopNav from '../components/layout/AppTopNav.vue'
import FloatingBackdrop from '../components/layout/FloatingBackdrop.vue'
import { useConfirm } from '../composables/useConfirm'
import { queryKeys } from '../composables/useQueryKeys'
import { useToast } from '../composables/useToast'
import { useAppStore } from '../stores/app'
import type { CollectionItem, FavoriteRankItem, ListResponse, UserDashboard } from '../types'

const { t } = useI18n()
const queryClient = useQueryClient()
const appStore = useAppStore()
const { confirmAction } = useConfirm()
const { showToast } = useToast()
const MAX_RANK_ITEMS = 10

const favoriteQuery = useQuery({
  queryKey: queryKeys.favorites(),
  queryFn: getMyFavorites,
  initialData: getInitialFavorites,
  placeholderData: getInitialFavorites,
  staleTime: 5 * 60 * 1000,
  gcTime: 30 * 60 * 1000,
})

const collectionQuery = useQuery({
  queryKey: queryKeys.collections('completed'),
  queryFn: () => getMyCollections('completed', { includeTotal: false }),
  initialData: getInitialCompletedCollections,
  placeholderData: getInitialCompletedCollections,
  staleTime: 30 * 1000,
  gcTime: 30 * 60 * 1000,
})

const localList = ref<FavoriteRankItem[]>([])
const isEditing = ref(false)
const isAddModalOpen = ref(false)
let persistTimer: number | undefined
let persistRevision = 0
let persistInFlight = false
let pendingRankPayload: { items: Array<{ anime_id: number; rank_order: number }> } | null = null

watch(
  () => favoriteQuery.data.value?.items,
  (items) => {
    localList.value = normalizeRank([...(items ?? [])].sort((a, b) => a.rank_order - b.rank_order))
  },
  { immediate: true },
)

const updateMutation = useMutation({
  mutationFn: updateFavoriteRank,
})

onBeforeUnmount(() => {
  window.clearTimeout(persistTimer)
  void flushRankPersist()
})

const previewList = computed(() => localList.value.slice(0, 5))
const completedItems = computed(() => getSyncedCompletedCollections().items)
const rankedAnimeIds = computed(() => new Set(localList.value.map((item) => item.anime.id)))
const availableItems = computed(() => {
  const seen = new Set<number>()
  return completedItems.value.filter((item) => {
    if (item.anime.id <= 0 || rankedAnimeIds.value.has(item.anime.id) || seen.has(item.anime.id)) {
      return false
    }
    seen.add(item.anime.id)
    return true
  })
})

function persistRank(list: FavoriteRankItem[]) {
  const deduped = dedupeRankItems(list)
  const nextFavorites = {
    items: deduped,
    total: deduped.length,
    page: 1,
    page_size: deduped.length || 10,
  }
  persistRevision += 1
  queryClient.setQueryData<ListResponse<FavoriteRankItem>>(queryKeys.favorites(), nextFavorites)
  syncDashboardFavorites(nextFavorites)
  pendingRankPayload = {
    items: deduped.map((item, index) => ({
      anime_id: item.anime.id,
      rank_order: index + 1,
    })),
  }
  window.clearTimeout(persistTimer)
  persistTimer = window.setTimeout(() => {
    persistTimer = undefined
    void flushRankPersist()
  }, 120)
}

async function flushRankPersist() {
  if (persistInFlight || !pendingRankPayload) {
    return
  }

  const payload = pendingRankPayload
  const revision = persistRevision
  pendingRankPayload = null
  persistInFlight = true

  try {
    const data = await updateMutation.mutateAsync(payload)
    if (!pendingRankPayload && revision === persistRevision) {
      localList.value = normalizeRank([...data.items].sort((a, b) => a.rank_order - b.rank_order))
      queryClient.setQueryData(queryKeys.favorites(), data)
      syncDashboardFavorites(data)
      void queryClient.invalidateQueries({ queryKey: queryKeys.favorites() })
    }
  } catch {
    showToast(t('common.saveFailed'), 'danger')
  } finally {
    persistInFlight = false
    if (pendingRankPayload) {
      void flushRankPersist()
    }
  }
}

async function moveItem(index: number, direction: -1 | 1) {
  const targetIndex = index + direction
  if (targetIndex < 0 || targetIndex >= localList.value.length) {
    return
  }
  const list = [...localList.value]
  ;[list[index], list[targetIndex]] = [list[targetIndex], list[index]]
  localList.value = normalizeRank(list)
  persistRank(localList.value)
  showToast(t('favoriteRank.editSuccess'), 'info')
}

function setRank(index: number, rankOrder: number) {
  const targetIndex = rankOrder - 1
  if (targetIndex < 0 || targetIndex >= localList.value.length || targetIndex === index) {
    return
  }
  const list = [...localList.value]
  const [item] = list.splice(index, 1)
  list.splice(targetIndex, 0, item)
  localList.value = normalizeRank(list)
  persistRank(localList.value)
  showToast(t('favoriteRank.editSuccess'), 'info')
}

function normalizeRank(list: FavoriteRankItem[]) {
  return dedupeRankItems(list).slice(0, MAX_RANK_ITEMS).map((item, index) => ({
    ...item,
    rank_order: index + 1,
  }))
}

function dedupeRankItems(list: FavoriteRankItem[]) {
  const seen = new Set<number>()
  const deduped: FavoriteRankItem[] = []
  for (const item of list) {
    if (seen.has(item.anime.id) || item.anime.id <= 0) {
      continue
    }
    seen.add(item.anime.id)
    deduped.push(item)
  }
  return deduped
}

async function removeItem(index: number) {
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
  localList.value = normalizeRank(localList.value.filter((_, itemIndex) => itemIndex !== index))
  persistRank(localList.value)
  showToast(t('favoriteRank.editSuccess'), 'info')
}

async function addItem(collectionItem: CollectionItem) {
  if (localList.value.length >= MAX_RANK_ITEMS) {
    showToast(t('favoriteRank.maxLimit', { count: MAX_RANK_ITEMS }), 'info')
    return
  }
  if (rankedAnimeIds.value.has(collectionItem.anime.id)) {
    return
  }
  const confirmed = await confirmAction({
    title: t('common.confirmTitle'),
    message: t('common.confirmMessage'),
    confirmText: t('common.confirm'),
    cancelText: t('common.cancel'),
  })
  if (!confirmed) {
    return
  }
  const nextItem: FavoriteRankItem = {
    id: -Date.now(),
    user_id: collectionItem.user_id,
    anime: collectionItem.anime,
    rank_order: localList.value.length + 1,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
  localList.value = normalizeRank([...localList.value, nextItem])
  persistRank(localList.value)
  showToast(t('favoriteRank.editSuccess'))
}

function getInitialFavorites() {
  return (
    queryClient.getQueryData<ListResponse<FavoriteRankItem>>(queryKeys.favorites()) ??
    queryClient.getQueryData<UserDashboard>(queryKeys.dashboard)?.favorites
  )
}

function getInitialCompletedCollections() {
  return getSyncedCompletedCollections()
}

function getSyncedCompletedCollections() {
  const dashboardCollections = queryClient.getQueryData<UserDashboard>(queryKeys.dashboard)?.collections
  const allCollections = queryClient.getQueryData<ListResponse<CollectionItem>>(queryKeys.collections())
  const cached = queryClient.getQueryData<ListResponse<CollectionItem>>(queryKeys.collections('completed'))

  const items = uniqueCollectionsByAnime(
    [
      ...(dashboardCollections?.items ?? []),
      ...(allCollections?.items ?? []),
      ...(cached?.items ?? []),
    ].filter((item) => item.collection_status === 'completed'),
  )
  const source = allCollections ?? dashboardCollections ?? cached
  return {
    ...(source ?? { page: 1, page_size: 100 }),
    items,
    total: items.length,
    page_size: items.length || source?.page_size || 100,
  }
}

function syncCompletedCollectionCache() {
  queryClient.setQueryData(queryKeys.collections('completed'), getSyncedCompletedCollections())
}

function syncDashboardFavorites(favorites: ListResponse<FavoriteRankItem>) {
  queryClient.setQueryData<UserDashboard>(queryKeys.dashboard, (current) => {
    if (!current) {
      return current
    }
    return {
      ...current,
      favorites,
    }
  })
}

function uniqueCollectionsByAnime(items: CollectionItem[]) {
  const seen = new Set<string>()
  const result: CollectionItem[] = []
  for (const item of items) {
    const key = getCollectionUniqueKey(item)
    if (seen.has(key)) {
      continue
    }
    seen.add(key)
    result.push(item)
  }
  return result
}

function getCollectionUniqueKey(item: CollectionItem) {
  if (item.anime.id > 0) {
    return `id:${item.anime.id}`
  }
  if (item.anime.source_id) {
    return `source:${item.anime.source_id}`
  }
  return `collection:${item.id}`
}

watch(
  () => appStore.locale,
  () => {
    void favoriteQuery.refetch()
    void collectionQuery.refetch()
  },
)

watch(
  () => [
    queryClient.getQueryData<UserDashboard>(queryKeys.dashboard)?.collections.items,
    queryClient.getQueryData<ListResponse<CollectionItem>>(queryKeys.collections())?.items,
  ],
  () => {
    syncCompletedCollectionCache()
  },
  { immediate: true },
)

watch(
  () => isAddModalOpen.value,
  (isOpen) => {
    if (!isOpen) {
      return
    }
    syncCompletedCollectionCache()
    void queryClient.prefetchQuery({
      queryKey: queryKeys.collections('completed'),
      queryFn: () => getMyCollections('completed', { includeTotal: false }),
      staleTime: 30 * 1000,
    })
  },
)
</script>

<template>
  <div class="page-root">
    <FloatingBackdrop />
    <AppTopNav active="favorite-rank" />
    <main class="container rank-page">
      <header class="header">
        <div>
          <h1 class="section-title">{{ t('favoriteRank.title') }}</h1>
          <p class="subtitle">{{ t('favoriteRank.subtitle') }}</p>
        </div>
        <div class="header-actions">
          <button class="edit-toggle" :class="{ active: isEditing }" type="button" @click="isEditing = !isEditing">
            <span class="material-symbols-outlined">edit</span>
            {{ t('favoriteRank.editMode') }}
          </button>
          <button class="edit-toggle add" type="button" @click="isAddModalOpen = true">
            <span class="material-symbols-outlined">add</span>
            {{ t('favoriteRank.addFavorite') }}
          </button>
        </div>
      </header>

      <section class="content-grid">
        <div class="main-list">
          <article v-for="(item, index) in localList" :key="item.id" class="surface-card row">
            <span class="rank-index">{{ String(item.rank_order).padStart(2, '0') }}</span>
            <img :src="item.anime.cover_url" :alt="item.anime.title" />
            <div class="info">
              <h3>{{ item.anime.title }}</h3>
              <p>{{ item.anime.summary }}</p>
            </div>
            <div v-if="isEditing" class="ops">
              <select
                class="rank-select"
                :value="item.rank_order"
                :aria-label="t('favoriteRank.adjust')"
                @change="setRank(index, Number(($event.target as HTMLSelectElement).value))"
              >
                <option v-for="rank in localList.length" :key="rank" :value="rank">
                  {{ String(rank).padStart(2, '0') }}
                </option>
              </select>
              <button class="icon-btn" type="button" :aria-label="t('favoriteRank.moveUp')" @click="void moveItem(index, -1)">
                <span class="material-symbols-outlined">arrow_upward</span>
              </button>
              <button class="icon-btn" type="button" :aria-label="t('favoriteRank.moveDown')" @click="void moveItem(index, 1)">
                <span class="material-symbols-outlined">arrow_downward</span>
              </button>
              <button class="icon-btn danger" type="button" :aria-label="t('favoriteRank.remove')" @click="void removeItem(index)">
                <span class="material-symbols-outlined">close</span>
              </button>
            </div>
          </article>
        </div>
        <aside class="surface-card preview">
          <h2>{{ t('favoriteRank.previewTitle') }}</h2>
          <p class="subtitle">{{ t('favoriteRank.previewDescription') }}</p>
          <ul>
            <li v-for="item in previewList" :key="item.id">
              <span>{{ String(item.rank_order).padStart(2, '0') }}</span>
              <strong>{{ item.anime.title }}</strong>
            </li>
          </ul>
        </aside>
      </section>
      <Teleport to="body">
        <div v-if="isAddModalOpen" class="rank-modal-backdrop" @click.self="isAddModalOpen = false">
          <section class="rank-modal" role="dialog" aria-modal="true">
            <button class="modal-close" type="button" :aria-label="t('common.cancel')" @click="isAddModalOpen = false">
              <span class="material-symbols-outlined">close</span>
            </button>
            <div class="modal-copy">
              <span class="modal-kicker">{{ t('favoriteRank.editMode') }}</span>
              <h2>{{ t('favoriteRank.addFromCompleted') }}</h2>
              <p>{{ t('favoriteRank.previewDescription') }}</p>
            </div>
            <div class="modal-grid">
              <button
                v-for="item in availableItems"
                :key="item.id"
                class="modal-anime"
                type="button"
                @click="void addItem(item)"
              >
                <img :src="item.anime.cover_url" :alt="item.anime.title" />
                <span>{{ item.anime.title }}</span>
              <strong>{{ t('favoriteRank.addFavorite') }}</strong>
            </button>
              <p v-if="availableItems.length === 0" class="modal-empty">
                {{ t('showcase.emptySection') }}
              </p>
            </div>
          </section>
        </div>
      </Teleport>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.rank-page {
  display: grid;
  gap: 18px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: end;
  gap: 12px;
}

.header-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.edit-toggle {
  border: 1px solid rgba(219, 106, 137, 0.2);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.62);
  color: var(--on-surface-variant);
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.18s ease, background 0.18s ease, color 0.18s ease;
}

.edit-toggle:hover,
.edit-toggle.active {
  transform: translateY(-1px);
  background: rgba(254, 182, 196, 0.22);
  color: #a64d67;
}

.edit-toggle.add {
  background: linear-gradient(135deg, rgba(249, 168, 189, 0.9), rgba(233, 102, 140, 0.9));
  color: white;
  border-color: transparent;
  box-shadow: 0 14px 28px rgba(219, 106, 137, 0.2);
}

.edit-toggle .material-symbols-outlined {
  color: #e9668c;
  font-size: 18px;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 16px;
}

.main-list {
  display: grid;
  gap: 12px;
}

.row {
  display: grid;
  grid-template-columns: 44px 92px 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 12px;
}

.rank-index {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: #e9668c;
  color: white;
  display: grid;
  place-content: center;
  font-family: "Epilogue", sans-serif;
  font-weight: 800;
  font-size: 12px;
}

img {
  width: 92px;
  height: 128px;
  object-fit: cover;
  border-radius: 12px;
}

.info {
  display: grid;
  gap: 6px;
}

.info h3 {
  margin: 0;
  font-family: "Epilogue", sans-serif;
}

.info p {
  margin: 0;
  color: var(--on-surface-variant);
  font-size: 13px;
}

.ops {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: end;
}

.rank-select {
  width: 64px;
  height: 34px;
  border: 1px solid rgba(219, 106, 137, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--on-surface);
  padding: 0 10px;
  font-weight: 800;
  cursor: pointer;
}

.icon-btn {
  border: 1px solid rgba(219, 106, 137, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.82);
  color: var(--on-surface);
  display: inline-flex;
  align-items: center;
  gap: 4px;
  width: 34px;
  height: 34px;
  justify-content: center;
  padding: 0;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.icon-btn:hover {
  transform: translateY(-1px);
  border-color: rgba(219, 106, 137, 0.36);
  background: rgba(254, 182, 196, 0.16);
}

.icon-btn .material-symbols-outlined {
  font-size: 16px;
}

.icon-btn.danger {
  color: #b31b25;
  border-color: rgba(179, 27, 37, 0.22);
}

.icon-btn.danger:hover {
  background: rgba(179, 27, 37, 0.08);
}

.preview {
  padding: 14px;
  align-self: start;
}

.preview h2 {
  margin: 0 0 6px;
  font-family: "Epilogue", sans-serif;
}

.preview ul {
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
  display: grid;
  gap: 8px;
}

.preview li {
  display: grid;
  grid-template-columns: 32px 1fr;
  align-items: center;
  gap: 8px;
  background: var(--surface-container-low);
  border-radius: 10px;
  padding: 8px;
}

@media (max-width: 1000px) {
  .content-grid {
    grid-template-columns: 1fr;
  }

  .row {
    grid-template-columns: 44px 78px 1fr;
  }

  .ops {
    grid-column: 1 / -1;
    justify-content: start;
  }
}
</style>

<style>
.rank-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 30% 20%, rgba(254, 182, 196, 0.24), transparent 34%),
    rgba(42, 35, 39, 0.28);
  backdrop-filter: blur(10px);
}

.rank-modal {
  position: relative;
  width: min(760px, 100%);
  max-height: min(720px, 86vh);
  overflow: auto;
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 34px;
  padding: 26px;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(255, 247, 250, 0.96)),
    radial-gradient(circle at top right, rgba(254, 182, 196, 0.22), transparent 40%);
  box-shadow: 0 28px 80px rgba(89, 35, 49, 0.28);
}

.modal-close {
  position: absolute;
  top: 18px;
  right: 18px;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 999px;
  background: rgba(254, 182, 196, 0.18);
  color: #a64d67;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.modal-copy {
  display: grid;
  gap: 8px;
  padding-right: 48px;
}

.modal-kicker {
  width: max-content;
  border-radius: 999px;
  padding: 6px 10px;
  background: rgba(254, 182, 196, 0.24);
  color: #a64d67;
  font-size: 12px;
  font-weight: 900;
}

.modal-copy h2 {
  margin: 0;
  font-family: "Epilogue", sans-serif;
  font-size: clamp(26px, 4vw, 42px);
}

.modal-copy p {
  margin: 0;
  color: var(--on-surface-variant);
}

.modal-grid {
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.modal-anime {
  border: 1px solid rgba(219, 106, 137, 0.16);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.74);
  padding: 10px;
  display: grid;
  gap: 9px;
  text-align: left;
  color: var(--on-surface);
  cursor: pointer;
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.modal-anime:hover {
  transform: translateY(-3px);
  border-color: rgba(219, 106, 137, 0.34);
  box-shadow: 0 18px 36px rgba(89, 35, 49, 0.13);
}

.modal-anime img {
  width: 100%;
  aspect-ratio: 3 / 4;
  border-radius: 16px;
  object-fit: cover;
}

.modal-anime span {
  font-weight: 900;
  line-height: 1.25;
}

.modal-anime strong {
  width: max-content;
  border-radius: 999px;
  padding: 6px 10px;
  background: linear-gradient(135deg, #f9a8bd, #e9668c);
  color: white;
  font-size: 12px;
}

.modal-empty {
  grid-column: 1 / -1;
  margin: 0;
  padding: 30px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.7);
  color: var(--on-surface-variant);
  text-align: center;
}
</style>
