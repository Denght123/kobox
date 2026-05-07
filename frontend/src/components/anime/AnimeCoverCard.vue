<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { AnimeSummary, CollectionStatus } from '../../types'

const props = defineProps<{
  anime: AnimeSummary
  status?: CollectionStatus | null
}>()

const emit = defineEmits<{
  add: [anime: AnimeSummary]
  updateStatus: [anime: AnimeSummary, status: CollectionStatus]
}>()

const { t } = useI18n()

function onAdd() {
  emit('add', props.anime)
}

function onSetStatus(status: CollectionStatus) {
  emit('updateStatus', props.anime, status)
}
</script>

<template>
  <article class="card surface-card">
    <div class="cover-wrap">
      <img :src="anime.cover_url" :alt="anime.title" class="cover-image" />
      <span v-if="anime.season" class="season-tag">{{ anime.year }} {{ anime.season }}</span>
    </div>
    <div class="content">
      <h3>{{ anime.title }}</h3>
      <p>{{ anime.genres.join(' · ') }}</p>
      <button class="ghost-btn full" :class="{ active: status === 'completed' }" type="button" @click="onAdd">
        {{ status === 'completed' ? t('search.added') : t('search.addToCollection') }}
      </button>
      <div class="status-actions">
        <button
          class="status-btn"
          :class="{ active: status === 'watching' }"
          type="button"
          @click="onSetStatus('watching')"
        >
          {{ t('search.setWatching') }}
        </button>
        <button
          class="status-btn"
          :class="{ active: status === 'plan_to_watch' }"
          type="button"
          @click="onSetStatus('plan_to_watch')"
        >
          {{ t('search.setPlan') }}
        </button>
      </div>
    </div>
  </article>
</template>

<style scoped>
.card {
  overflow: hidden;
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translateY(-5px) rotate(0.5deg);
}

.cover-wrap {
  position: relative;
  aspect-ratio: 3 / 4;
  overflow: hidden;
}

.cover-wrap img {
  transition: transform 0.65s ease;
}

.card:hover .cover-wrap img {
  transform: scale(1.06);
}

.season-tag {
  position: absolute;
  top: 12px;
  right: 12px;
  background: rgba(255, 255, 255, 0.26);
  border-radius: 999px;
  padding: 6px 10px;
  color: white;
  font-size: 10px;
  letter-spacing: 0.08em;
  font-family: "Plus Jakarta Sans", sans-serif;
}

.content {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

h3 {
  margin: 0;
  font-family: "Epilogue", sans-serif;
  font-size: 20px;
  line-height: 1.2;
}

p {
  margin: 0;
  color: var(--on-surface-variant);
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.full {
  width: 100%;
  border-color: rgba(219, 106, 137, 0.28);
  background: rgba(254, 182, 196, 0.09);
  font-weight: 700;
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
}

.full:hover {
  transform: translateY(-1px);
  background: rgba(254, 182, 196, 0.2);
  box-shadow: 0 10px 22px rgba(219, 106, 137, 0.16);
}

.full:active {
  transform: translateY(0) scale(0.98);
}

.full.active {
  border-color: transparent;
  background: linear-gradient(135deg, #f9a8bd, #e9668c);
  color: white;
  box-shadow: 0 12px 24px rgba(219, 106, 137, 0.24);
}

.status-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.status-btn {
  border: 1px solid rgba(219, 106, 137, 0.22);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.68);
  padding: 10px 10px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  color: var(--on-surface);
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.status-btn:hover {
  border-color: rgba(219, 106, 137, 0.35);
  background: rgba(254, 182, 196, 0.16);
  transform: translateY(-1px);
}

.status-btn.active {
  border-color: transparent;
  background: linear-gradient(135deg, #f9a8bd, #e9668c);
  color: white;
  box-shadow: 0 12px 24px rgba(219, 106, 137, 0.24);
}
</style>
