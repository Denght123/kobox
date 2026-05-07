<script setup lang="ts">
import QRCode from 'qrcode'
import { useQueryClient } from '@tanstack/vue-query'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'

import LanguageSwitcher from '../common/LanguageSwitcher.vue'
import { useConfirm } from '../../composables/useConfirm'
import { warmupRouteChunk } from '../../composables/useRouteWarmup'
import { useAuthStore } from '../../stores/auth'
import { clearUserScopedBrowserCache } from '../../utils/userScopedCache'

const props = withDefaults(
  defineProps<{
    active?: 'showcase' | 'search' | 'favorite-rank' | 'settings' | 'public'
    showShare?: boolean
    publicOnly?: boolean
  }>(),
  {
    active: 'showcase',
    showShare: true,
    publicOnly: false,
  },
)

const authStore = useAuthStore()
const router = useRouter()
const queryClient = useQueryClient()
const { t } = useI18n()
const { confirmAction } = useConfirm()
const isLoggingOut = ref(false)
const shareCopied = ref(false)
const qrDataUrl = ref('')
const qrVisible = ref(false)

const avatarUrl = computed(
  () =>
    authStore.user?.avatar_url ??
    'https://lh3.googleusercontent.com/aida-public/AB6AXuANBi_bq6GIix1NKreGJV2a4S5yj2VPKcMjaMTWlt8RZoKOymjVQLiZQaIdyZFDYe3QzpWiOgD4OVeW5fWAxlqyELD4GAFSDmuXSSFzhoFLLl2w0i58IAyP8RviAVUecvPfnxxCoM7dyizqVmzZ1o745ki0rDNCswKDEUM4V9eznQnhVqWpI-1KvETPmM9Tea-OcMVl4F1inYeK_Ae-1ORqsQ0k6xyx-RcxDDSFUSDAF6WsMX-xe6XrsJQAWLR5xiZqjEOBBv5N1JQ',
)

const shareUrl = computed(() => {
  const publicSlug = authStore.user?.public_slug ?? authStore.user?.username
  const siteUrl = (import.meta.env.VITE_PUBLIC_SITE_URL || window.location.origin).replace(/\/$/, '')
  if (!publicSlug) {
    return siteUrl
  }
  return `${siteUrl}/u/${publicSlug}`
})

async function onLogout() {
  if (isLoggingOut.value) {
    return
  }

  const confirmed = await confirmAction({
    title: '退出登录',
    message: '确认退出当前账号吗？退出后需要重新登录才能继续管理你的展柜。',
    confirmText: '确认退出',
    cancelText: t('common.cancel'),
    tone: 'danger',
  })
  if (!confirmed) {
    return
  }

  isLoggingOut.value = true
  try {
    await authStore.logout()
    queryClient.clear()
    clearUserScopedBrowserCache()
    await router.replace('/auth')
  } finally {
    isLoggingOut.value = false
  }
}

async function onShare() {
  await navigator.clipboard.writeText(shareUrl.value)
  shareCopied.value = true
  setTimeout(() => {
    shareCopied.value = false
  }, 1200)
}

async function showQrPreview() {
  qrVisible.value = true
  if (qrDataUrl.value) {
    return
  }
  qrDataUrl.value = await QRCode.toDataURL(shareUrl.value, {
    width: 150,
    margin: 1,
    color: {
      dark: '#65323e',
      light: '#ffffff',
    },
  })
}

function hideQrPreview() {
  qrVisible.value = false
}

function onQrIconClick() {
  void showQrPreview()
}

function preloadShowcase() {
  warmupRouteChunk('showcase')
}

function preloadSearch() {
  warmupRouteChunk('search')
}

function preloadFavorites() {
  warmupRouteChunk('favoriteRank')
}

function preloadSettings() {
  warmupRouteChunk('settings')
}
</script>

<template>
  <header class="glass-nav">
    <div class="top-nav">
      <RouterLink
        :to="props.publicOnly ? { path: '/auth', query: { publicEntry: '1' } } : '/showcase'"
        @focus="preloadShowcase"
        @mouseenter="preloadShowcase"
      >
        <h1 class="brand-title">{{ t('app.name') }}</h1>
      </RouterLink>
      <nav v-if="!props.publicOnly" class="main-menu">
        <RouterLink
          :class="{ active: props.active === 'showcase' }"
          to="/showcase"
          @focus="preloadShowcase"
          @mouseenter="preloadShowcase"
        >
          {{ t('nav.showcase') }}
        </RouterLink>
        <RouterLink
          :class="{ active: props.active === 'search' }"
          to="/search"
          @focus="preloadSearch"
          @mouseenter="preloadSearch"
        >
          {{ t('nav.search') }}
        </RouterLink>
        <RouterLink
          :class="{ active: props.active === 'favorite-rank' }"
          to="/favorite-rank"
          @focus="preloadFavorites"
          @mouseenter="preloadFavorites"
        >
          {{ t('nav.favoriteRank') }}
        </RouterLink>
        <RouterLink
          :class="{ active: props.active === 'settings' }"
          to="/settings"
          @focus="preloadSettings"
          @mouseenter="preloadSettings"
        >
          {{ t('nav.settings') }}
        </RouterLink>
      </nav>
      <div class="actions">
        <div
          v-if="props.showShare"
          class="share-action"
          @focusin="showQrPreview"
          @mouseenter="showQrPreview"
          @focusout="hideQrPreview"
          @mouseleave="hideQrPreview"
        >
          <button class="icon-btn" type="button" @click="onQrIconClick">
            <span class="material-symbols-outlined">qr_code_2</span>
          </button>
          <div v-if="qrVisible" class="qr-popover">
            <strong>{{ t('showcase.shareCollection') }}</strong>
            <img v-if="qrDataUrl" :src="qrDataUrl" :alt="t('common.qrCode')" />
            <small>{{ shareUrl }}</small>
            <button class="copy-link-btn" type="button" @click="onShare">{{ t('common.copyLink') }}</button>
          </div>
        </div>
        <LanguageSwitcher />
        <span v-if="shareCopied" class="share-hint">{{ t('common.copied') }}</span>
        <button
          v-if="!props.publicOnly && authStore.isAuthenticated"
          class="logout-btn"
          type="button"
          :disabled="isLoggingOut"
          @click="onLogout"
        >
          {{ isLoggingOut ? t('common.loading') : t('auth.logout') }}
        </button>
        <img v-if="!props.publicOnly" :src="avatarUrl" alt="avatar" class="avatar" />
      </div>
    </div>
    <nav v-if="!props.publicOnly" class="mobile-menu">
      <RouterLink :class="{ active: props.active === 'showcase' }" to="/showcase">
        {{ t('nav.showcase') }}
      </RouterLink>
      <RouterLink :class="{ active: props.active === 'search' }" to="/search">
        {{ t('nav.search') }}
      </RouterLink>
      <RouterLink :class="{ active: props.active === 'favorite-rank' }" to="/favorite-rank">
        {{ t('nav.favoriteRank') }}
      </RouterLink>
      <RouterLink :class="{ active: props.active === 'settings' }" to="/settings">
        {{ t('nav.settings') }}
      </RouterLink>
    </nav>
  </header>
</template>

<style scoped>
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.top-nav > a,
.top-nav .brand-title {
  cursor: pointer;
}

.main-menu {
  display: flex;
  align-items: center;
  gap: 28px;
  font-family: "Epilogue", sans-serif;
  font-size: 14px;
  color: #7e7b79;
}

.main-menu a {
  transition: color 0.25s ease;
}

.main-menu a:hover {
  color: #d35f7f;
}

.main-menu a.active {
  color: #ba4c6b;
  border-bottom: 2px solid #e96d8d;
  padding-bottom: 4px;
}

.actions {
  position: relative;
  display: flex;
  gap: 12px;
  align-items: center;
}

.share-action {
  position: relative;
  display: inline-flex;
}

.logout-btn {
  border: 1px solid rgba(122, 118, 115, 0.24);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.7);
  color: var(--on-surface-variant);
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
}

.logout-btn:hover {
  border-color: rgba(131, 75, 88, 0.42);
  color: var(--primary);
}

.icon-btn {
  border: none;
  background: transparent;
  width: 34px;
  height: 34px;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: #a36979;
  cursor: pointer;
}

.icon-btn:hover {
  background: rgba(254, 182, 196, 0.25);
}

.qr-popover {
  position: absolute;
  top: calc(100% + 10px);
  right: -52px;
  width: 190px;
  z-index: 40;
  border-radius: 22px;
  padding: 14px;
  display: grid;
  gap: 8px;
  justify-items: center;
  text-align: center;
  color: var(--on-surface);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: var(--shadow-soft);
  border: 1px solid rgba(177, 172, 169, 0.18);
}

.qr-popover::before {
  content: "";
  position: absolute;
  top: -8px;
  right: 64px;
  width: 16px;
  height: 16px;
  background: rgba(255, 255, 255, 0.96);
  transform: rotate(45deg);
  border-left: 1px solid rgba(177, 172, 169, 0.18);
  border-top: 1px solid rgba(177, 172, 169, 0.18);
}

.qr-popover strong {
  font-family: "Epilogue", sans-serif;
  font-size: 13px;
}

.qr-popover img {
  width: 118px;
  height: 118px;
  border-radius: 14px;
}

.qr-popover small {
  max-width: 100%;
  color: var(--on-surface-variant);
  overflow-wrap: anywhere;
  font-size: 10px;
}

.copy-link-btn {
  border: none;
  border-radius: 999px;
  padding: 6px 12px;
  background: rgba(254, 182, 196, 0.25);
  color: var(--primary);
  font-size: 11px;
  font-weight: 700;
  cursor: pointer;
}

.copy-link-btn:hover {
  background: rgba(254, 182, 196, 0.38);
}

.share-hint {
  font-size: 11px;
  color: #2f7d54;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 999px;
  border: 2px solid white;
  object-fit: cover;
}

@media (max-width: 960px) {
  .main-menu {
    display: none;
  }

  .glass-nav {
    border-radius: 28px;
  }

  .top-nav {
    align-items: center;
  }

  .actions {
    gap: 8px;
  }

  .logout-btn {
    padding: 6px 10px;
  }

  .mobile-menu {
    margin-top: 10px;
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 6px;
  }

  .mobile-menu a {
    border-radius: 999px;
    padding: 8px 6px;
    text-align: center;
    font-size: 12px;
    color: var(--on-surface-variant);
    background: rgba(255, 255, 255, 0.48);
  }

  .mobile-menu a.active {
    color: #ba4c6b;
    background: rgba(254, 182, 196, 0.24);
    font-weight: 800;
  }
}

@media (min-width: 961px) {
  .mobile-menu {
    display: none;
  }
}

@media (max-width: 520px) {
  .avatar {
    display: none;
  }

  .qr-popover {
    right: -86px;
  }
}
</style>
