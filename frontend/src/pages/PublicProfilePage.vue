<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { getPublicCollections, getPublicFavorites, getPublicUser } from '../api/public'
import FavoriteRankList from '../components/collection/FavoriteRankList.vue'
import CollectionSection from '../components/collection/CollectionSection.vue'
import AppFooter from '../components/layout/AppFooter.vue'
import AppTopNav from '../components/layout/AppTopNav.vue'
import FloatingBackdrop from '../components/layout/FloatingBackdrop.vue'
import ProfileHeader from '../components/profile/ProfileHeader.vue'
import { queryKeys } from '../composables/useQueryKeys'
import { useAppStore } from '../stores/app'

const props = defineProps<{
  username: string
}>()

const { t } = useI18n()
const appStore = useAppStore()
const router = useRouter()

const profileQuery = useQuery({
  queryKey: computed(() => queryKeys.publicProfile(props.username)),
  queryFn: () => getPublicUser(props.username),
})

const collectionQuery = useQuery({
  queryKey: computed(() => queryKeys.publicCollections(props.username)),
  queryFn: () => getPublicCollections(props.username),
})

const favoriteQuery = useQuery({
  queryKey: computed(() => queryKeys.publicFavorites(props.username)),
  queryFn: () => getPublicFavorites(props.username),
})

const collections = computed(() => collectionQuery.data.value?.items ?? [])
const publicBackgroundImageUrl = computed(
  () => profileQuery.data.value?.background_image_url ?? null,
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
  () => appStore.locale,
  () => {
    void collectionQuery.refetch()
    void favoriteQuery.refetch()
  },
)

function goToAuth() {
  void router.push({
    path: '/auth',
    query: {
      publicEntry: '1',
    },
  })
}
</script>

<template>
  <div class="page-root">
    <FloatingBackdrop :background-image-url="publicBackgroundImageUrl" />
    <AppTopNav active="public" :show-share="false" :public-only="true" />
    <main class="container public-page">
      <ProfileHeader
        v-if="profileQuery.data.value"
        :profile="profileQuery.data.value"
        :subtitle="t('publicProfile.heroBadge')"
        :show-share-button="false"
      />
      <section class="stack">
        <CollectionSection
          :title="t('publicProfile.archiveTitle')"
          :items="completedItems"
          status="completed"
          :readonly="true"
        />
        <CollectionSection
          :title="t('publicProfile.watchingTitle')"
          :items="watchingItems"
          status="watching"
          :readonly="true"
        />
        <CollectionSection
          :title="t('publicProfile.planTitle')"
          :items="planItems"
          status="plan_to_watch"
          :readonly="true"
        />
      </section>

      <FavoriteRankList :items="favoriteQuery.data.value?.items ?? []" title="Ta的最爱" />

      <section class="cta glass-card">
        <h2>{{ t('publicProfile.ctaTitle') }}</h2>
        <p>{{ t('publicProfile.ctaSubtitle') }}</p>
        <button class="primary-btn" type="button" @click="goToAuth">
          {{ t('publicProfile.ctaButton') }}
        </button>
      </section>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.public-page {
  display: grid;
  gap: 16px;
}

.stack {
  display: grid;
  gap: 14px;
}

.cta {
  margin-top: 8px;
  border-radius: 36px;
  padding: 30px 24px;
  text-align: center;
  display: grid;
  gap: 10px;
}

.cta h2,
.cta p {
  margin: 0;
}

.cta h2 {
  font-family: "Epilogue", sans-serif;
  font-size: clamp(26px, 4vw, 44px);
}

.cta p {
  color: var(--on-surface-variant);
}

.cta button {
  justify-self: center;
}
</style>
