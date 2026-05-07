<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { CollectionItem, CollectionStatus } from '../../types'
import { formatDateText } from '../../utils/format'

const props = defineProps<{
  title: string
  items: CollectionItem[]
  status: CollectionStatus
  readonly?: boolean
  isLoading?: boolean
}>()

const emit = defineEmits<{
  add: [status: CollectionStatus]
  remove: [collectionId: number]
}>()

const { t } = useI18n()
const isManaging = ref(false)

function onAdd() {
  emit('add', props.status)
}

function onRemove(collectionId: number) {
  emit('remove', collectionId)
}
</script>

<template>
  <section class="collection-block">
    <div class="heading">
      <h2>{{ props.title }}</h2>
      <span class="pill">{{ props.items.length }}</span>
      <div v-if="!props.readonly" class="section-actions">
        <button class="mini-btn add" type="button" @click="onAdd">
          <span class="material-symbols-outlined">add</span>
          {{ t('showcase.addItem') }}
        </button>
        <button class="mini-btn" type="button" @click="isManaging = !isManaging">
          <span class="material-symbols-outlined">edit</span>
          {{ isManaging ? t('showcase.doneManage') : t('showcase.manageItems') }}
        </button>
      </div>
    </div>
    <div v-if="props.isLoading && props.items.length === 0" class="loading-card surface-card">
      {{ t('common.loading') }}
    </div>
    <div v-else-if="props.items.length === 0" class="empty-card surface-card">
      {{ t('showcase.emptyCollectionPrompt') }}
    </div>
    <div class="grid">
      <article v-for="item in props.items" :key="item.id" class="surface-card anime-item">
        <button
          v-if="isManaging && !props.readonly"
          class="card-remove"
          type="button"
          :aria-label="t('favoriteRank.remove')"
          @click="onRemove(item.id)"
        >
          <span class="material-symbols-outlined">close</span>
        </button>
        <div class="image-wrap">
          <img :src="item.anime.cover_url" :alt="item.anime.title" class="cover-image" />
        </div>
        <div class="meta">
          <h3>{{ item.anime.title }}</h3>
          <p>{{ formatDateText(item.added_at) }}</p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.collection-block {
  display: grid;
  gap: 16px;
}

.heading {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

h2 {
  margin: 0;
  font-size: 30px;
  font-family: "Epilogue", sans-serif;
}

.grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.anime-item {
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
}

.anime-item:hover {
  transform: translateY(-5px) rotate(0.5deg);
  border-color: rgba(219, 106, 137, 0.24);
  box-shadow: 0 18px 40px rgba(89, 35, 49, 0.16);
}

.image-wrap {
  aspect-ratio: 3 / 4;
  overflow: hidden;
}

.image-wrap img {
  transition: transform 0.65s ease, filter 0.65s ease;
}

.anime-item:hover .image-wrap img {
  transform: scale(1.06);
  filter: saturate(1.06) contrast(1.03);
}

.meta {
  padding: 12px;
  display: grid;
  gap: 6px;
}

h3 {
  margin: 0;
  font-size: 17px;
  font-family: "Epilogue", sans-serif;
  line-height: 1.25;
}

p,
small {
  margin: 0;
  color: var(--on-surface-variant);
}

.section-actions {
  margin-left: auto;
  display: flex;
  gap: 8px;
}

.mini-btn {
  border: 1px solid rgba(219, 106, 137, 0.18);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.56);
  color: var(--on-surface);
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 8px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease;
}

.mini-btn:hover {
  transform: translateY(-1px);
  border-color: rgba(219, 106, 137, 0.34);
  background: rgba(254, 182, 196, 0.16);
}

.mini-btn.add {
  background: rgba(254, 182, 196, 0.18);
  font-weight: 700;
}

.mini-btn .material-symbols-outlined {
  font-size: 16px;
}

.card-remove {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 3;
  width: 30px;
  height: 30px;
  border: 1px solid rgba(255, 255, 255, 0.68);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.86);
  color: #b31b25;
  display: grid;
  place-items: center;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(89, 35, 49, 0.18);
  transition: transform 0.16s ease, background 0.16s ease;
}

.card-remove:hover {
  transform: scale(1.08) rotate(5deg);
  background: #fff5f7;
}

.card-remove .material-symbols-outlined {
  font-size: 16px;
}

.empty-edit {
  color: var(--on-surface-variant);
  font-size: 13px;
}

.loading-card {
  min-height: 140px;
  display: grid;
  place-items: center;
  color: var(--on-surface-variant);
  font-weight: 800;
  letter-spacing: 0.08em;
}

.empty-card {
  min-height: 180px;
  display: grid;
  place-items: center;
  border: 1px dashed rgba(219, 106, 137, 0.22);
  background: rgba(255, 255, 255, 0.36);
  color: var(--on-surface-variant);
  font-weight: 800;
}

@media (max-width: 1180px) {
  .grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 780px) {
  .grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .section-actions {
    width: 100%;
    margin-left: 0;
  }
}

@media (max-width: 520px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
