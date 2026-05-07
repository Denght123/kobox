import type { UserDashboard, UserProfile, UserSettings, UpdateProfilePayload } from '../types'

import { apiClient } from './client'
import { mockCurrentUser, mockUserSettings } from './mockData'
import { withMockFallback } from './mockRuntime'

export async function getMe(): Promise<UserProfile> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.get<UserProfile>('/api/me')
      return data
    },
    () => mockCurrentUser,
  )
}

export async function getMyDashboard(): Promise<UserDashboard> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.get<UserDashboard>('/api/me/dashboard')
      return data
    },
    () => ({
      profile: mockCurrentUser,
      settings: mockUserSettings,
      collections: {
        items: [],
        total: 0,
        page: 1,
        page_size: 100,
      },
      favorites: {
        items: [],
        total: 0,
        page: 1,
        page_size: 10,
      },
    }),
  )
}

export async function updateMyProfile(payload: UpdateProfilePayload): Promise<UserProfile> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.put<UserProfile>('/api/me/profile', payload)
      return data
    },
    () => {
      mockCurrentUser.display_name = payload.display_name
      mockCurrentUser.birthday = payload.birthday
      mockCurrentUser.bio = payload.bio
      if (payload.avatar_url) {
        mockCurrentUser.avatar_url = payload.avatar_url
      }
      if (payload.background_image_url) {
        mockCurrentUser.background_image_url = payload.background_image_url
      }
      return mockCurrentUser
    },
  )
}

export async function getMySettings(): Promise<UserSettings> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.get<UserSettings>('/api/me/settings')
      return data
    },
    () => mockUserSettings,
  )
}

export async function updateMySettings(
  payload: Partial<UserSettings>,
): Promise<UserSettings> {
  return withMockFallback(
    async () => {
      const { data } = await apiClient.put<UserSettings>('/api/me/settings', payload)
      return data
    },
    () => {
      Object.assign(mockUserSettings, payload)
      return mockUserSettings
    },
  )
}
