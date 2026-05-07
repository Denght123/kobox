<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { getMe, getMySettings, updateMyProfile, updateMySettings } from '../api/me'
import { clearBackground, uploadAvatar, uploadBackground } from '../api/upload'
import AppFooter from '../components/layout/AppFooter.vue'
import AppTopNav from '../components/layout/AppTopNav.vue'
import FloatingBackdrop from '../components/layout/FloatingBackdrop.vue'
import { useConfirm } from '../composables/useConfirm'
import { queryKeys } from '../composables/useQueryKeys'
import { useToast } from '../composables/useToast'
import { useAppStore } from '../stores/app'
import { useAuthStore } from '../stores/auth'
import type { UserDashboard, UserProfile } from '../types'

const FALLBACK_AVATAR_URL =
  'https://lh3.googleusercontent.com/aida-public/AB6AXuANBi_bq6GIix1NKreGJV2a4S5yj2VPKcMjaMTWlt8RZoKOymjVQLiZQaIdyZFDYe3QzpWiOgD4OVeW5fWAxlqyELD4GAFSDmuXSSFzhoFLLl2w0i58IAyP8RviAVUecvPfnxxCoM7dyizqVmzZ1o745ki0rDNCswKDEUM4V9eznQnhVqWpI-1KvETPmM9Tea-OcMVl4F1inYeK_Ae-1ORqsQ0k6xyx-RcxDDSFUSDAF6WsMX-xe6XrsJQAWLR5xiZqjEOBBv5N1JQ'

const { t } = useI18n()
const appStore = useAppStore()
const authStore = useAuthStore()
const queryClient = useQueryClient()
const { confirmAction } = useConfirm()
const { showToast } = useToast()

const meQuery = useQuery({
  queryKey: queryKeys.me,
  queryFn: getMe,
})

const settingsQuery = useQuery({
  queryKey: queryKeys.settings,
  queryFn: getMySettings,
})

const displayName = ref('')
const birthday = ref('')
const bio = ref('')
const avatarPreviewUrl = ref(FALLBACK_AVATAR_URL)
const uploadedAvatarUrl = ref<string | null>(null)
const uploadedAvatarSource = ref<'remote' | 'local' | null>(null)
const avatarHint = ref('')
const backgroundPreviewUrl = ref('')
const uploadedBackgroundUrl = ref<string | null>(null)
const uploadedBackgroundSource = ref<'remote' | 'local' | null>(null)
const backgroundHint = ref('')
const profileSaveMessage = ref('')
const settingsSaveMessage = ref('')
const showDynamicBackground = ref(true)
const showPublicRank = ref(true)
let localPreviewObjectUrl: string | null = null
let localBackgroundPreviewObjectUrl: string | null = null

watch(
  () => meQuery.data.value,
  (profile) => {
    if (!profile) {
      return
    }
    displayName.value = profile.display_name
    birthday.value = profile.birthday ?? ''
    bio.value = profile.bio ?? ''
    avatarPreviewUrl.value = uploadedAvatarUrl.value ?? profile.avatar_url ?? FALLBACK_AVATAR_URL
    backgroundPreviewUrl.value = uploadedBackgroundUrl.value ?? profile.background_image_url ?? ''
    authStore.setUser(profile)
  },
  { immediate: true },
)

watch(
  () => settingsQuery.data.value,
  (settings) => {
    if (!settings) {
      return
    }
    showDynamicBackground.value = settings.show_dynamic_background
    showPublicRank.value = settings.show_public_rank
  },
  { immediate: true },
)

const saveProfileMutation = useMutation({
  mutationFn: updateMyProfile,
  onSuccess: (profile) => {
    applyProfileCache(profile)
    profileSaveMessage.value = t('settings.profileSaved')
    showToast(t('settings.profileSaved'))
    if (uploadedAvatarSource.value === 'remote') {
      avatarHint.value = t('settings.avatarSynced')
    }
    if (uploadedBackgroundSource.value === 'remote') {
      backgroundHint.value = '背景图片已同步到服务器。'
    }
    uploadedAvatarUrl.value = null
    uploadedAvatarSource.value = null
    uploadedBackgroundUrl.value = null
    uploadedBackgroundSource.value = null
    avatarPreviewUrl.value = profile.avatar_url ?? FALLBACK_AVATAR_URL
    backgroundPreviewUrl.value = profile.background_image_url ?? ''
  },
})

const saveSettingsMutation = useMutation({
  mutationFn: updateMySettings,
  onSuccess: (settings) => {
    queryClient.setQueryData(queryKeys.settings, settings)
    queryClient.setQueryData<UserDashboard>(queryKeys.dashboard, (current) => {
      if (!current) {
        return current
      }
      return {
        ...current,
        settings,
      }
    })
    settingsSaveMessage.value = t('settings.settingsSaved')
    showToast(t('settings.settingsSaved'))
  },
})

const uploadAvatarMutation = useMutation({
  mutationFn: uploadAvatar,
  onSuccess: (result) => {
    profileSaveMessage.value = ''
    uploadedAvatarUrl.value = result.avatar_url
    uploadedAvatarSource.value = result.source
    avatarPreviewUrl.value = result.avatar_url

    if (result.source === 'remote') {
      if (result.profile) {
        applyProfileCache(result.profile)
      } else if (authStore.user) {
        applyProfileCache({ ...authStore.user, avatar_url: result.avatar_url })
      }
      uploadedAvatarUrl.value = null
      uploadedAvatarSource.value = null
      avatarHint.value = '头像已保存'
      showToast('头像已保存', 'success')
      clearLocalPreviewUrl()
      return
    }

    localPreviewObjectUrl = result.avatar_url
    avatarHint.value = t('settings.avatarLocalPreviewHint')
    showToast(t('settings.avatarLocalPreviewHint'), 'info')
  },
  onError: (error) => {
    clearLocalPreviewUrl()
    avatarPreviewUrl.value = authStore.user?.avatar_url ?? FALLBACK_AVATAR_URL
    uploadedAvatarUrl.value = null
    uploadedAvatarSource.value = null
    avatarHint.value = error instanceof Error ? error.message : '头像上传失败，请稍后重试'
    showToast('头像上传失败，请稍后重试', 'danger')
  },
})

const uploadBackgroundMutation = useMutation({
  mutationFn: uploadBackground,
  onSuccess: (result) => {
    profileSaveMessage.value = ''
    uploadedBackgroundUrl.value = result.background_image_url
    uploadedBackgroundSource.value = result.source
    backgroundPreviewUrl.value = result.background_image_url

    if (result.source === 'remote') {
      if (result.profile) {
        applyProfileCache(result.profile)
      } else if (authStore.user) {
        applyProfileCache({
          ...authStore.user,
          background_image_url: result.background_image_url,
        })
      }
      uploadedBackgroundUrl.value = null
      uploadedBackgroundSource.value = null
      backgroundHint.value = '背景图片已保存'
      showToast('背景图片已保存', 'success')
      clearLocalBackgroundPreviewUrl()
      return
    }

    localBackgroundPreviewObjectUrl = result.background_image_url
    backgroundHint.value = '未检测到背景上传接口，已切换为本地预览。'
    showToast('未检测到背景上传接口，已切换为本地预览。', 'info')
  },
  onError: (error) => {
    clearLocalBackgroundPreviewUrl()
    backgroundPreviewUrl.value = authStore.user?.background_image_url ?? ''
    uploadedBackgroundUrl.value = null
    uploadedBackgroundSource.value = null
    backgroundHint.value = error instanceof Error ? error.message : '背景图片上传失败，请稍后重试'
    showToast('背景图片上传失败，请稍后重试', 'danger')
  },
})

const clearBackgroundMutation = useMutation({
  mutationFn: clearBackground,
  onSuccess: (result) => {
    clearLocalBackgroundPreviewUrl()
    const profile =
      result.profile ??
      (authStore.user
        ? {
            ...authStore.user,
            background_image_url: null,
          }
        : null)
    if (profile) {
      applyProfileCache(profile)
    }
    backgroundPreviewUrl.value = ''
    uploadedBackgroundUrl.value = null
    uploadedBackgroundSource.value = null
    showDynamicBackground.value = true
    queryClient.setQueryData<UserDashboard>(queryKeys.dashboard, (current) => {
      if (!current) {
        return current
      }
      return {
        ...current,
        settings: {
          ...current.settings,
          show_dynamic_background: true,
        },
      }
    })
    backgroundHint.value = '已恢复默认背景'
    showToast('已恢复默认背景', 'success')
  },
  onError: (error) => {
    backgroundHint.value = error instanceof Error ? error.message : '恢复默认背景失败，请稍后重试'
    showToast('恢复默认背景失败，请稍后重试', 'danger')
  },
})

const profileCompletion = computed(() => {
  let score = 0
  if (avatarPreviewUrl.value !== FALLBACK_AVATAR_URL) {
    score += 25
  }
  if (displayName.value.trim()) {
    score += 25
  }
  if (birthday.value) {
    score += 25
  }
  if (bio.value.trim()) {
    score += 25
  }
  return Math.min(score, 100)
})

const profileCompletionText = computed(() =>
  t('settings.completionSubtitle', { progress: profileCompletion.value }),
)

function saveProfile() {
  profileSaveMessage.value = ''
  saveProfileMutation.mutate({
    display_name: displayName.value.trim(),
    birthday: birthday.value || null,
    bio: bio.value.trim(),
    avatar_url:
      uploadedAvatarSource.value === 'remote' ? uploadedAvatarUrl.value ?? undefined : undefined,
    background_image_url:
      uploadedBackgroundSource.value === 'remote' ? uploadedBackgroundUrl.value ?? undefined : undefined,
  })
}

function saveSettings() {
  settingsSaveMessage.value = ''
  saveSettingsMutation.mutate({
    language: appStore.locale,
    show_dynamic_background: showDynamicBackground.value,
    show_public_rank: showPublicRank.value,
  })
}

async function saveAll() {
  const confirmed = await confirmAction({
    title: t('common.saveConfirmTitle'),
    message: t('common.saveConfirmMessage'),
    confirmText: t('common.confirm'),
    cancelText: t('common.cancel'),
  })
  if (!confirmed) {
    return
  }
  saveProfile()
  saveSettings()
}

async function onAvatarInputChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) {
    return
  }
  const confirmed = await confirmAction({
    title: t('common.confirmTitle'),
    message: t('common.confirmMessage'),
    confirmText: t('common.confirm'),
    cancelText: t('common.cancel'),
  })
  if (!confirmed) {
    target.value = ''
    return
  }

  clearLocalPreviewUrl()
  localPreviewObjectUrl = URL.createObjectURL(file)
  avatarPreviewUrl.value = localPreviewObjectUrl
  avatarHint.value = ''
  uploadAvatarMutation.mutate(file)
  target.value = ''
}

async function onBackgroundInputChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) {
    return
  }
  const confirmed = await confirmAction({
    title: t('common.confirmTitle'),
    message: t('common.confirmMessage'),
    confirmText: t('common.confirm'),
    cancelText: t('common.cancel'),
  })
  if (!confirmed) {
    target.value = ''
    return
  }

  clearLocalBackgroundPreviewUrl()
  localBackgroundPreviewObjectUrl = URL.createObjectURL(file)
  backgroundPreviewUrl.value = localBackgroundPreviewObjectUrl
  backgroundHint.value = ''
  uploadBackgroundMutation.mutate(file)
  target.value = ''
}

async function restoreDefaultBackground() {
  const confirmed = await confirmAction({
    title: '恢复默认背景',
    message: '确认恢复默认背景和页面主题吗？',
    confirmText: t('common.confirm'),
    cancelText: t('common.cancel'),
  })
  if (!confirmed) {
    return
  }
  clearBackgroundMutation.mutate()
}

onBeforeUnmount(() => {
  clearLocalPreviewUrl()
  clearLocalBackgroundPreviewUrl()
})

function clearLocalPreviewUrl() {
  if (!localPreviewObjectUrl) {
    return
  }
  URL.revokeObjectURL(localPreviewObjectUrl)
  localPreviewObjectUrl = null
}

function clearLocalBackgroundPreviewUrl() {
  if (!localBackgroundPreviewObjectUrl) {
    return
  }
  URL.revokeObjectURL(localBackgroundPreviewObjectUrl)
  localBackgroundPreviewObjectUrl = null
}

function applyProfileCache(profile: UserProfile) {
  authStore.setUser(profile)
  queryClient.setQueryData(queryKeys.me, profile)
  queryClient.setQueryData<UserDashboard>(queryKeys.dashboard, (current) => {
    if (!current) {
      return current
    }
    return {
      ...current,
      profile,
    }
  })
}
</script>

<template>
  <div class="page-root">
    <FloatingBackdrop />
    <AppTopNav active="settings" />
    <main class="container settings-page">
      <header>
        <h1 class="section-title">{{ t('settings.title') }}</h1>
        <p class="subtitle">{{ t('settings.subtitle') }}</p>
      </header>

      <section class="grid">
        <article class="surface-card profile-card">
          <div class="avatar-editor">
            <div class="avatar-frame">
              <img :src="avatarPreviewUrl" :alt="t('common.avatarPreview')" />
            </div>
            <div class="avatar-control">
              <h2>{{ t('settings.uploadAvatar') }}</h2>
              <label class="ghost-btn upload-trigger">
                <input
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  type="file"
                  @change="onAvatarInputChange"
                />
                {{ uploadAvatarMutation.isPending.value ? t('common.loading') : t('settings.uploadAvatar') }}
              </label>
              <p v-if="avatarHint" class="hint">{{ avatarHint }}</p>
            </div>
          </div>
          <h2>{{ t('settings.profileSection') }}</h2>
          <div class="background-editor">
            <div class="background-preview" :class="{ empty: !backgroundPreviewUrl }">
              <img v-if="backgroundPreviewUrl" :src="backgroundPreviewUrl" alt="background preview" />
              <span v-else>页面背景预览</span>
            </div>
            <div class="background-control">
              <h2>更换页面背景</h2>
              <label class="ghost-btn upload-trigger">
                <input
                  accept="image/png,image/jpeg,image/webp,image/gif"
                  type="file"
                  @change="onBackgroundInputChange"
                />
                {{ uploadBackgroundMutation.isPending.value ? t('common.loading') : '上传背景图片' }}
              </label>
              <button
                class="restore-background-btn"
                :disabled="clearBackgroundMutation.isPending.value"
                type="button"
                @click="restoreDefaultBackground"
              >
                {{ clearBackgroundMutation.isPending.value ? t('common.loading') : '恢复默认' }}
              </button>
              <p v-if="backgroundHint" class="hint">{{ backgroundHint }}</p>
            </div>
          </div>
          <label>
            <span>{{ t('settings.nickname') }}</span>
            <input v-model="displayName" type="text" />
          </label>
          <label>
            <span>{{ t('settings.birthday') }}</span>
            <input v-model="birthday" type="date" />
          </label>
          <label>
            <span>{{ t('settings.bio') }}</span>
            <textarea v-model="bio" rows="4" />
          </label>
          <button class="primary-btn" type="button" @click="saveAll">
            {{
              saveProfileMutation.isPending.value || saveSettingsMutation.isPending.value
                ? t('common.loading')
                : t('settings.save')
            }}
          </button>
          <p v-if="saveProfileMutation.error.value" class="error">
            {{
              saveProfileMutation.error.value instanceof Error
                ? saveProfileMutation.error.value.message
                : t('common.saveFailed')
            }}
          </p>
          <p v-if="profileSaveMessage" class="hint success">{{ profileSaveMessage }}</p>
        </article>

        <article class="surface-card side-card display-card">
          <h2>{{ t('settings.displaySection') }}</h2>
          <p class="display-copy">{{ t('settings.displayDescription') }}</p>
          <label class="switch">
            <input v-model="showDynamicBackground" type="checkbox" />
            <span>{{ t('settings.displayDynamicBackground') }}</span>
          </label>
          <label class="switch">
            <input v-model="showPublicRank" type="checkbox" />
            <span>{{ t('settings.displayPublicRank') }}</span>
          </label>
          <p v-if="saveSettingsMutation.error.value" class="error">
            {{
              saveSettingsMutation.error.value instanceof Error
                ? saveSettingsMutation.error.value.message
                : t('common.saveFailed')
            }}
          </p>
          <p v-if="settingsSaveMessage" class="hint success">{{ settingsSaveMessage }}</p>
        </article>
      </section>

      <section class="progress surface-card">
        <div>
          <h3>{{ t('settings.completionTitle') }}</h3>
          <p>{{ profileCompletionText }}</p>
        </div>
        <div class="bar">
          <div class="fill" :style="{ width: `${profileCompletion}%` }" />
        </div>
      </section>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.settings-page {
  display: grid;
  gap: 16px;
}

.grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 14px;
}

.profile-card,
.side-card {
  padding: 18px;
  display: grid;
  gap: 10px;
}

.display-card {
  align-content: start;
  min-height: 260px;
  padding: 24px;
}

.display-copy {
  margin: 0 0 10px;
  color: var(--on-surface-variant);
}

.avatar-editor {
  margin-bottom: 6px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(177, 172, 169, 0.2);
  padding: 14px;
  display: flex;
  gap: 16px;
  align-items: center;
}

.background-editor {
  margin-bottom: 6px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(177, 172, 169, 0.2);
  padding: 14px;
  display: grid;
  grid-template-columns: minmax(180px, 260px) 1fr;
  gap: 16px;
  align-items: center;
}

.background-preview {
  min-height: 126px;
  border-radius: 18px;
  overflow: hidden;
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at top, rgba(254, 182, 196, 0.28), transparent 48%),
    var(--surface-container-low);
  color: var(--on-surface-variant);
  font-weight: 800;
}

.background-preview img {
  width: 100%;
  height: 100%;
  min-height: 126px;
  object-fit: cover;
}

.background-control {
  display: grid;
  gap: 8px;
}

.restore-background-btn {
  width: fit-content;
  border: 1px solid rgba(219, 106, 137, 0.24);
  border-radius: 999px;
  padding: 9px 18px;
  background: rgba(255, 255, 255, 0.64);
  color: #a64d67;
  font-weight: 800;
  cursor: pointer;
  box-shadow: 0 10px 22px rgba(131, 75, 88, 0.08);
  transition:
    transform 0.18s ease,
    background 0.18s ease,
    box-shadow 0.18s ease;
}

.restore-background-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  background: rgba(254, 230, 235, 0.86);
  box-shadow: 0 14px 26px rgba(131, 75, 88, 0.12);
}

.restore-background-btn:disabled {
  cursor: not-allowed;
  opacity: 0.58;
}

.avatar-frame {
  width: 108px;
  height: 108px;
  border-radius: 18px;
  overflow: hidden;
  box-shadow: var(--shadow-soft);
  flex-shrink: 0;
}

.avatar-frame img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-control {
  display: grid;
  gap: 8px;
}

.upload-trigger {
  width: fit-content;
  position: relative;
  overflow: hidden;
}

.upload-trigger input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: pointer;
}

h2 {
  margin: 0;
  font-family: "Epilogue", sans-serif;
}

label {
  display: grid;
  gap: 6px;
}

label span {
  color: var(--on-surface-variant);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

input,
textarea,
select {
  border: 1px solid rgba(122, 118, 115, 0.25);
  border-radius: 12px;
  padding: 10px;
  background: #fff;
}

textarea {
  resize: none;
}

.switch {
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 10px;
}

.switch input {
  width: 18px;
  height: 18px;
  margin: 0;
}

.progress {
  padding: 16px;
  display: grid;
  gap: 10px;
}

.progress h3,
.progress p {
  margin: 0;
}

.hint {
  margin: 0;
  color: var(--on-surface-variant);
  font-size: 12px;
}

.success {
  color: #2f7d54;
}

.error {
  margin: 0;
  color: #b31b25;
  font-size: 12px;
}

.bar {
  height: 10px;
  background: #f5dce4;
  border-radius: 999px;
  overflow: hidden;
}

.fill {
  height: 100%;
  background: #db6a89;
  transition: width 0.3s ease;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .avatar-editor {
    flex-direction: column;
    align-items: flex-start;
  }

  .background-editor {
    grid-template-columns: 1fr;
  }
}
</style>
