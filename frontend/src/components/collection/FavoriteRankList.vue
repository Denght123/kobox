<script setup lang="ts">
import type { FavoriteRankItem } from '../../types'

const props = defineProps<{
  items: FavoriteRankItem[]
  title?: string
}>()
</script>

<template>
  <section class="surface-card rank-list">
    <h3 v-if="props.title" class="rank-title">{{ props.title }}</h3>
    <div v-if="props.items.length === 0" class="empty-rank">
      <span class="material-symbols-outlined">favorite</span>
      <strong>来排一排你热爱的番吧</strong>
    </div>
    <article v-for="item in props.items" :key="item.id" class="row">
      <span class="index">{{ String(item.rank_order).padStart(2, '0') }}</span>
      <img :src="item.anime.cover_url" :alt="item.anime.title" />
      <div>
        <h4>{{ item.anime.title }}</h4>
        <p>{{ item.anime.genres.join(' · ') }}</p>
      </div>
    </article>
  </section>
</template>

<style scoped>
.rank-list {
  min-height: 180px;
  padding: 16px;
  display: grid;
  gap: 10px;
}

.rank-title {
  margin: 0 0 2px;
  font-family: "Epilogue", sans-serif;
  font-size: clamp(22px, 3vw, 34px);
  color: var(--on-surface);
}

.empty-rank {
  min-height: 148px;
  border-radius: 18px;
  display: grid;
  place-items: center;
  gap: 8px;
  padding: 20px;
  text-align: center;
  background:
    radial-gradient(circle at top, rgba(254, 182, 196, 0.28), transparent 44%),
    var(--surface-container-low);
  color: #a64d67;
}

.empty-rank span {
  width: 42px;
  height: 42px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: rgba(254, 182, 196, 0.38);
}

.empty-rank strong {
  font-size: 15px;
}

.row {
  display: grid;
  grid-template-columns: 40px 58px 1fr;
  gap: 10px;
  align-items: center;
  padding: 6px;
  border-radius: 12px;
  background: var(--surface-container-low);
}

.index {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: #e9658c;
  color: white;
  display: grid;
  place-content: center;
  font-family: "Epilogue", sans-serif;
  font-weight: 800;
  font-size: 12px;
}

img {
  width: 58px;
  height: 78px;
  object-fit: cover;
  border-radius: 10px;
}

h4 {
  margin: 0;
  font-family: "Epilogue", sans-serif;
  font-size: 16px;
}

p {
  margin: 0;
  color: var(--on-surface-variant);
  font-size: 12px;
}
</style>
