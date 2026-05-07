import { apiClient } from './client'
import { mockCurrentUser } from './mockData'
import { withMockFallback } from './mockRuntime'

import type {
  AuthSession,
  LoginPayload,
  PasswordResetConfirmPayload,
  PasswordResetRequestPayload,
  PasswordResetRequestResponse,
  RegisterPayload,
} from '../types'

export async function loginAuth(payload: LoginPayload): Promise<AuthSession> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.post<AuthSession>('/api/auth/login', payload)
      return data
    },
    () => ({
      access_token: `mock-access-token-${Date.now()}`,
      refresh_token: `mock-refresh-token-${Date.now()}`,
      token_type: 'bearer',
      user: mockCurrentUser,
    }),
  )
}

export async function registerAuth(payload: RegisterPayload): Promise<AuthSession> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.post<AuthSession>('/api/auth/register', payload)
      return data
    },
    () => ({
      access_token: `mock-access-token-${Date.now()}`,
      refresh_token: `mock-refresh-token-${Date.now()}`,
      token_type: 'bearer',
      user: {
        ...mockCurrentUser,
        username: payload.username,
        public_slug: payload.username,
        display_name: payload.display_name ?? payload.username,
      },
    }),
  )
}

export async function refreshAuthToken(token: string): Promise<AuthSession> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.post<AuthSession>('/api/auth/refresh', {
        refresh_token: token,
      })
      return data
    },
    () => ({
      access_token: `mock-access-token-${Date.now()}`,
      refresh_token: token,
      token_type: 'bearer',
      user: mockCurrentUser,
    }),
  )
}

export async function logoutAuth(refreshToken?: string | null): Promise<void> {
  if (!refreshToken) {
    return
  }

  return withMockFallback(
    async () => {
      await apiClient.post('/api/auth/logout', {
        refresh_token: refreshToken,
      })
    },
    () => undefined,
  )
}

export async function requestPasswordReset(
  payload: PasswordResetRequestPayload,
): Promise<PasswordResetRequestResponse> {
  const { data } = await apiClient.post<PasswordResetRequestResponse>(
    '/api/auth/password-reset/request',
    payload,
  )
  return data
}

export async function confirmPasswordReset(payload: PasswordResetConfirmPayload): Promise<void> {
  await apiClient.post('/api/auth/password-reset/confirm', payload)
}
