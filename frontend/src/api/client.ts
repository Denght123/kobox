import axios, { AxiosError } from 'axios'

import type { ApiErrorBody, AuthSession } from '../types'

const ACCESS_TOKEN_KEY = 'kobox.access_token'
const REFRESH_TOKEN_KEY = 'kobox.refresh_token'
const USER_KEY = 'kobox.user'
const LOCALE_KEY = 'kobox.locale'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000',
  timeout: 20_000,
})

let refreshPromise: Promise<string | null> | null = null

apiClient.interceptors.request.use((config) => {
  const accessToken = localStorage.getItem(ACCESS_TOKEN_KEY)
  const locale = localStorage.getItem(LOCALE_KEY) ?? 'zh-CN'

  config.headers = config.headers ?? {}
  config.headers['Accept-Language'] = locale

  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }

  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorBody>) => {
    const originalRequest = error.config
    const payload = error.response?.data
    const shouldTryRefresh =
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest.url?.includes('/api/auth/refresh') &&
      !originalRequest.url?.includes('/api/auth/login') &&
      !originalRequest.headers?.['x-kobox-retried']

    if (shouldTryRefresh) {
      const nextToken = await refreshAccessToken()
      if (nextToken) {
        originalRequest.headers = originalRequest.headers ?? {}
        originalRequest.headers.Authorization = `Bearer ${nextToken}`
        originalRequest.headers['x-kobox-retried'] = '1'
        return apiClient(originalRequest)
      }
    }

    if (error.code === AxiosError.ECONNABORTED || error.message.toLowerCase().includes('timeout')) {
      return Promise.reject(new Error(getTimeoutMessage()))
    }

    if (payload) {
      return Promise.reject(new Error(payload.message))
    }
    return Promise.reject(error)
  },
)

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
  if (!refreshToken) {
    clearStoredSession()
    return null
  }

  refreshPromise ??= apiClient
    .post<AuthSession>('/api/auth/refresh', {
      refresh_token: refreshToken,
    })
    .then(({ data }) => {
      localStorage.setItem(ACCESS_TOKEN_KEY, data.access_token)
      localStorage.setItem(REFRESH_TOKEN_KEY, data.refresh_token)
      localStorage.setItem(USER_KEY, JSON.stringify(data.user))
      return data.access_token
    })
    .catch(() => {
      clearStoredSession()
      return null
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

function clearStoredSession() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}

function getTimeoutMessage() {
  const locale = localStorage.getItem(LOCALE_KEY) ?? 'zh-CN'
  if (locale.startsWith('zh')) {
    return '请求超时，请稍后重试。如果刚启动服务，请刷新页面后再试。'
  }
  return 'Request timed out. Please try again, or refresh after the service finishes starting.'
}
