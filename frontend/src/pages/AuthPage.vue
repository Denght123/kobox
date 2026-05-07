<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useQueryClient } from '@tanstack/vue-query'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { confirmPasswordReset, requestPasswordReset } from '../api/auth'
import AppFooter from '../components/layout/AppFooter.vue'
import FloatingBackdrop from '../components/layout/FloatingBackdrop.vue'
import { seedDashboardQuery, warmupAuthedQueries } from '../composables/useRouteWarmup'
import { useToast } from '../composables/useToast'
import { useAuthStore } from '../stores/auth'
import { clearUserScopedBrowserCache } from '../utils/userScopedCache'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const queryClient = useQueryClient()
const { showToast } = useToast()

const mode = ref<'login' | 'register'>('login')
const pending = ref(false)
const errorText = ref('')
const successText = ref('')

const account = ref('')
const password = ref('')

const registerEmail = ref('')
const registerUsername = ref('')
const registerDisplayName = ref('')
const registerPassword = ref('')
const registerPasswordConfirm = ref('')
const isPasswordResetOpen = ref(false)
const passwordResetEmail = ref('')
const passwordResetToken = ref('')
const passwordResetNewPassword = ref('')
const passwordResetConfirmPassword = ref('')
const passwordResetPending = ref(false)
const passwordResetMessage = ref('')
const passwordResetError = ref('')

const redirectPath = computed(() =>
  typeof route.query.redirect === 'string' && route.query.redirect !== '/auth'
    ? route.query.redirect
    : '/showcase',
)

watch(mode, () => {
  errorText.value = ''
  successText.value = ''
})

watch(
  () => route.query.reset_token,
  (token) => {
    if (typeof token !== 'string' || !token) {
      return
    }
    passwordResetToken.value = token
    openPasswordReset()
  },
  { immediate: true },
)

async function onLogin() {
  pending.value = true
  errorText.value = ''
  successText.value = ''
  try {
    const session = await authStore.login({
      account: account.value.trim(),
      password: password.value,
    })
    resetUserScopedCache()
    if (session.dashboard) {
      seedDashboardQuery(queryClient, session.dashboard)
    } else {
      void warmupAuthedQueries(queryClient).catch(() => undefined)
    }
    showToast('登录成功', 'success')
    await sleep(1000)
    await router.replace(redirectPath.value)
  } catch (error) {
    errorText.value = ''
    showToast('账户或密码错误', 'danger')
  } finally {
    pending.value = false
  }
}

async function onRegister() {
  const email = registerEmail.value.trim()
  const username = registerUsername.value.trim()
  const displayName = registerDisplayName.value.trim()

  if (!email || !username || !registerPassword.value) {
    errorText.value = t('auth.completeRequired')
    return
  }

  if (registerPassword.value !== registerPasswordConfirm.value) {
    errorText.value = t('auth.passwordMismatch')
    return
  }

  pending.value = true
  errorText.value = ''
  successText.value = ''
  try {
    await authStore.register({
      email,
      username,
      password: registerPassword.value,
      display_name: displayName || undefined,
    })
    resetUserScopedCache()
    authStore.clearSession()
    account.value = email
    password.value = ''
    registerPassword.value = ''
    registerPasswordConfirm.value = ''
    successText.value = '注册成功，请登录'
    showToast('注册成功，请登录', 'success')
    await sleep(1000)
    mode.value = 'login'
  } catch (error) {
    errorText.value = error instanceof Error ? error.message : t('auth.registerFailed')
  } finally {
    pending.value = false
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, ms)
  })
}

function resetUserScopedCache() {
  queryClient.clear()
  clearUserScopedBrowserCache()
}

function openPasswordReset() {
  passwordResetError.value = ''
  passwordResetMessage.value = ''
  passwordResetEmail.value = registerEmail.value || account.value
  isPasswordResetOpen.value = true
}

async function onRequestPasswordReset() {
  const email = passwordResetEmail.value.trim()
  if (!email) {
    passwordResetError.value = t('auth.resetEmailRequired')
    return
  }

  passwordResetPending.value = true
  passwordResetError.value = ''
  passwordResetMessage.value = ''
  try {
    const result = await requestPasswordReset({ email })
    passwordResetMessage.value = result.dev_reset_token
      ? t('auth.resetDevTokenReady')
      : t('auth.resetEmailSent')
    if (result.dev_reset_token) {
      passwordResetToken.value = result.dev_reset_token
    }
  } catch (error) {
    passwordResetError.value = error instanceof Error ? error.message : t('auth.resetRequestFailed')
  } finally {
    passwordResetPending.value = false
  }
}

async function onConfirmPasswordReset() {
  if (!passwordResetToken.value.trim() || !passwordResetNewPassword.value) {
    passwordResetError.value = t('auth.resetTokenRequired')
    return
  }
  if (passwordResetNewPassword.value !== passwordResetConfirmPassword.value) {
    passwordResetError.value = t('auth.passwordMismatch')
    return
  }

  passwordResetPending.value = true
  passwordResetError.value = ''
  passwordResetMessage.value = ''
  try {
    await confirmPasswordReset({
      token: passwordResetToken.value.trim(),
      password: passwordResetNewPassword.value,
    })
    passwordResetMessage.value = t('auth.resetSuccess')
    passwordResetNewPassword.value = ''
    passwordResetConfirmPassword.value = ''
    await router.replace({ path: '/auth', query: {} })
  } catch (error) {
    passwordResetError.value = error instanceof Error ? error.message : t('auth.resetConfirmFailed')
  } finally {
    passwordResetPending.value = false
  }
}
</script>

<template>
  <div class="page-root auth-root">
    <FloatingBackdrop />
    <main class="auth-main">
      <div class="brand-block">
        <button class="brand-home" type="button" @click="router.push('/showcase')">
          <h1 class="brand-title huge">Kobox</h1>
        </button>
        <p class="label-mini">{{ t('app.slogan') }}</p>
      </div>
      <section class="glass-card login-card">
        <header>
          <h2>{{ t('auth.welcome') }}</h2>
          <p class="subtitle">{{ t('auth.subtitle') }}</p>
          <div class="mode-switch">
            <button :class="{ active: mode === 'login' }" type="button" @click="mode = 'login'">
              {{ t('auth.login') }}
            </button>
            <button
              :class="{ active: mode === 'register' }"
              type="button"
              @click="mode = 'register'"
            >
              {{ t('auth.register') }}
            </button>
          </div>
        </header>
        <form v-if="mode === 'login'" class="form" @submit.prevent="onLogin">
          <label>
            <span>{{ t('auth.accountLabel') }}</span>
            <input v-model="account" :placeholder="t('auth.accountPlaceholder')" type="text" />
          </label>
          <label>
            <span>{{ t('auth.passwordLabel') }}</span>
            <input v-model="password" :placeholder="t('auth.passwordPlaceholder')" type="password" />
          </label>
          <p v-if="errorText" class="error">{{ errorText }}</p>
          <button class="primary-btn enter-btn" :disabled="pending" type="submit">
            {{ pending ? t('common.loading') : t('auth.enter') }}
          </button>
        </form>
        <form v-else class="form" @submit.prevent="onRegister">
          <label>
            <span>{{ t('auth.emailLabel') }} *</span>
            <input v-model="registerEmail" :placeholder="t('auth.emailPlaceholder')" type="email" />
          </label>
          <label>
            <span>{{ t('auth.usernameLabel') }} *</span>
            <input
              v-model="registerUsername"
              :placeholder="t('auth.usernamePlaceholder')"
              type="text"
            />
          </label>
          <label>
            <span>{{ t('auth.displayNameLabel') }}</span>
            <input
              v-model="registerDisplayName"
              :placeholder="t('auth.displayNamePlaceholder')"
              type="text"
            />
          </label>
          <label>
            <span>{{ t('auth.passwordLabel') }} *</span>
            <input
              v-model="registerPassword"
              :placeholder="t('auth.passwordHint')"
              type="password"
            />
          </label>
          <label>
            <span>{{ t('auth.confirmPasswordLabel') }} *</span>
            <input
              v-model="registerPasswordConfirm"
              :placeholder="t('auth.confirmPasswordPlaceholder')"
              type="password"
            />
          </label>
          <p v-if="errorText" class="error">{{ errorText }}</p>
          <p v-if="successText" class="success">{{ successText }}</p>
          <button class="primary-btn enter-btn" :disabled="pending" type="submit">
            {{ pending ? t('common.loading') : t('auth.createAccount') }}
          </button>
        </form>
        <footer class="actions">
          <button v-if="mode === 'login'" class="inline-link" type="button" @click="openPasswordReset">
            {{ t('auth.forgotPassword') }}
          </button>
          <span v-if="mode === 'login'">
            {{ t('auth.firstVisit') }}
            <button class="inline-link" type="button" @click="mode = 'register'">
              {{ t('auth.registerNow') }}
            </button>
          </span>
          <span v-else>
            {{ t('auth.haveAccount') }}
            <button class="inline-link" type="button" @click="mode = 'login'">
              {{ t('auth.backToLogin') }}
            </button>
          </span>
        </footer>
      </section>
      <Teleport to="body">
        <div v-if="isPasswordResetOpen" class="reset-backdrop" @click.self="isPasswordResetOpen = false">
          <section class="reset-card glass-card" role="dialog" aria-modal="true">
            <button class="reset-close" type="button" :aria-label="t('common.cancel')" @click="isPasswordResetOpen = false">
              <span class="material-symbols-outlined">close</span>
            </button>
            <h2>{{ t('auth.resetTitle') }}</h2>
            <p class="subtitle">{{ t('auth.resetSubtitle') }}</p>
            <label>
              <span>{{ t('auth.emailLabel') }}</span>
              <input v-model="passwordResetEmail" :placeholder="t('auth.emailPlaceholder')" type="email" />
            </label>
            <button class="primary-btn" :disabled="passwordResetPending" type="button" @click="onRequestPasswordReset">
              {{ passwordResetPending ? t('common.loading') : t('auth.sendResetEmail') }}
            </button>
            <label>
              <span>{{ t('auth.resetTokenLabel') }}</span>
              <input v-model="passwordResetToken" :placeholder="t('auth.resetTokenPlaceholder')" type="text" />
            </label>
            <label>
              <span>{{ t('auth.newPasswordLabel') }}</span>
              <input v-model="passwordResetNewPassword" :placeholder="t('auth.passwordHint')" type="password" />
            </label>
            <label>
              <span>{{ t('auth.confirmPasswordLabel') }}</span>
              <input
                v-model="passwordResetConfirmPassword"
                :placeholder="t('auth.confirmPasswordPlaceholder')"
                type="password"
              />
            </label>
            <button class="ghost-btn reset-submit" :disabled="passwordResetPending" type="button" @click="onConfirmPasswordReset">
              {{ t('auth.resetPassword') }}
            </button>
            <p v-if="passwordResetError" class="error">{{ passwordResetError }}</p>
            <p v-if="passwordResetMessage" class="success">{{ passwordResetMessage }}</p>
          </section>
        </div>
      </Teleport>
    </main>
    <AppFooter />
  </div>
</template>

<style scoped>
.auth-root {
  background: linear-gradient(180deg, #fbf5f1 0%, #eef6ff 100%);
}

.auth-main {
  min-height: calc(100vh - 150px);
  display: grid;
  place-content: center;
  gap: 28px;
}

.brand-block {
  text-align: center;
}

.brand-home {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
}

.brand-home .brand-title {
  cursor: pointer;
}

.huge {
  font-size: clamp(48px, 10vw, 96px);
  margin-bottom: 8px;
}

.login-card {
  width: min(460px, 95vw);
  padding: 28px;
  border-radius: 26px;
}

.mode-switch {
  margin-top: 14px;
  border-radius: 999px;
  background: rgba(250, 211, 253, 0.4);
  padding: 4px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}

.mode-switch button {
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--on-surface-variant);
  padding: 8px 10px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.mode-switch button.active {
  background: #fff;
  color: var(--primary);
  box-shadow: 0 6px 16px rgba(131, 75, 88, 0.15);
}

header h2 {
  margin: 0;
  font-size: 32px;
  font-family: "Epilogue", sans-serif;
}

.form {
  margin-top: 18px;
  display: grid;
  gap: 14px;
}

label {
  display: grid;
  gap: 7px;
}

label span {
  font-size: 11px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--on-surface-variant);
}

input {
  border: none;
  border-bottom: 1px solid rgba(122, 118, 115, 0.3);
  padding: 11px 2px;
  background: transparent;
  outline: none;
}

.enter-btn {
  width: 100%;
  margin-top: 8px;
}

.actions {
  margin-top: 16px;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  font-size: 12px;
  color: var(--on-surface-variant);
}

.actions a {
  color: #c04f71;
}

.inline-link {
  border: none;
  background: transparent;
  color: #c04f71;
  cursor: pointer;
  padding: 0;
}

.error {
  margin: 0;
  color: #b31b25;
  font-size: 12px;
}

.success {
  margin: 0;
  color: #2f7d54;
  font-size: 12px;
}

.reset-backdrop {
  position: fixed;
  inset: 0;
  z-index: 80;
  display: grid;
  place-items: center;
  padding: 24px;
  background: rgba(42, 35, 39, 0.28);
  backdrop-filter: blur(10px);
}

.reset-card {
  position: relative;
  width: min(460px, 94vw);
  padding: 26px;
  border-radius: 28px;
  display: grid;
  gap: 14px;
}

.reset-card h2 {
  margin: 0;
  font-family: "Epilogue", sans-serif;
  font-size: 28px;
}

.reset-close {
  position: absolute;
  top: 16px;
  right: 16px;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 999px;
  background: rgba(254, 182, 196, 0.22);
  color: #a64d67;
  display: grid;
  place-items: center;
  cursor: pointer;
}

.reset-submit {
  width: 100%;
}
</style>
