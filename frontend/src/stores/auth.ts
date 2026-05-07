import { defineStore } from 'pinia'

import { loginAuth, logoutAuth, registerAuth } from '../api/auth'
import type { AuthSession, LoginPayload, RegisterPayload, UserProfile } from '../types'

const ACCESS_TOKEN_KEY = 'kobox.access_token'
const REFRESH_TOKEN_KEY = 'kobox.refresh_token'
const USER_KEY = 'kobox.user'

interface AuthState {
  accessToken: string | null
  refreshToken: string | null
  user: UserProfile | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    accessToken: localStorage.getItem(ACCESS_TOKEN_KEY),
    refreshToken: localStorage.getItem(REFRESH_TOKEN_KEY),
    user: safeParseUser(localStorage.getItem(USER_KEY)),
  }),
  getters: {
    isAuthenticated: (state) => Boolean(state.accessToken && state.user),
  },
  actions: {
    async login(payload: LoginPayload) {
      const session = await loginAuth(payload)
      this.applySession(session)
      return session
    },
    async register(payload: RegisterPayload) {
      const session = await registerAuth(payload)
      this.applySession(session)
      return session
    },
    async logout() {
      try {
        await logoutAuth(this.refreshToken)
      } finally {
        this.clearSession()
      }
    },
    setUser(user: UserProfile) {
      this.user = user
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },
    applySession(session: AuthSession) {
      this.accessToken = session.access_token
      this.refreshToken = session.refresh_token
      this.user = session.user
      localStorage.setItem(ACCESS_TOKEN_KEY, session.access_token)
      localStorage.setItem(REFRESH_TOKEN_KEY, session.refresh_token)
      localStorage.setItem(USER_KEY, JSON.stringify(session.user))
    },
    clearSession() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      localStorage.removeItem(ACCESS_TOKEN_KEY)
      localStorage.removeItem(REFRESH_TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    },
  },
})

function safeParseUser(value: string | null): UserProfile | null {
  if (!value) {
    return null
  }
  try {
    return JSON.parse(value) as UserProfile
  } catch {
    return null
  }
}
