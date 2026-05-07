<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { UserProfile } from '../../types'

const props = defineProps<{
  profile: UserProfile
  subtitle?: string
  showShareButton?: boolean
}>()

const emit = defineEmits<{
  share: []
}>()

const { t } = useI18n()

const avatarUrl = computed(
  () =>
    props.profile.avatar_url ??
    'https://lh3.googleusercontent.com/aida-public/AB6AXuANBi_bq6GIix1NKreGJV2a4S5yj2VPKcMjaMTWlt8RZoKOymjVQLiZQaIdyZFDYe3QzpWiOgD4OVeW5fWAxlqyELD4GAFSDmuXSSFzhoFLLl2w0i58IAyP8RviAVUecvPfnxxCoM7dyizqVmzZ1o745ki0rDNCswKDEUM4V9eznQnhVqWpI-1KvETPmM9Tea-OcMVl4F1inYeK_Ae-1ORqsQ0k6xyx-RcxDDSFUSDAF6WsMX-xe6XrsJQAWLR5xiZqjEOBBv5N1JQ',
)

const profileBio = computed(() => props.profile.bio ?? t('common.empty'))

function onShare() {
  emit('share')
}
</script>

<template>
  <header class="profile-header">
    <div class="avatar-wrap">
      <img :src="avatarUrl" :alt="props.profile.display_name" class="cover-image" />
    </div>
    <div class="content">
      <h1>{{ props.profile.display_name }}</h1>
      <p>{{ props.subtitle ?? profileBio }}</p>
      <div class="meta-row">
        <span class="pill">@{{ props.profile.username }}</span>
        <span v-if="props.profile.birthday" class="pill">{{ props.profile.birthday }}</span>
      </div>
    </div>
    <button v-if="props.showShareButton" class="primary-btn share-btn" type="button" @click="onShare">
      {{ t('showcase.shareCollection') }}
    </button>
  </header>
</template>

<style scoped>
.profile-header {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 18px;
  align-items: end;
}

.avatar-wrap {
  width: 120px;
  height: 120px;
  border-radius: 24px;
  overflow: hidden;
  box-shadow: var(--shadow-soft);
}

.content {
  display: grid;
  gap: 8px;
}

h1 {
  margin: 0;
  font-size: clamp(30px, 5vw, 52px);
  font-family: "Epilogue", sans-serif;
  line-height: 1;
}

p {
  margin: 0;
  color: var(--on-surface-variant);
}

.meta-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.share-btn {
  align-self: center;
}

@media (max-width: 860px) {
  .profile-header {
    grid-template-columns: 1fr;
    justify-items: start;
  }
}
</style>
