import type { AxiosError } from 'axios'

import type { UserProfile } from '../types'

import { apiClient } from './client'
import { shouldUseMock } from './mockRuntime'

const DEFAULT_AVATAR_UPLOAD_ENDPOINTS = ['/api/me/avatar', '/api/me/avatar/upload']
const DEFAULT_BACKGROUND_UPLOAD_ENDPOINTS = ['/api/me/background', '/api/me/background/upload']

export interface AvatarUploadResult {
  avatar_url: string
  source: 'remote' | 'local'
  profile?: UserProfile
}

export interface BackgroundUploadResult {
  background_image_url: string
  source: 'remote' | 'local'
  profile?: UserProfile
}

export async function uploadAvatar(file: File): Promise<AvatarUploadResult> {
  const result = await uploadImage({
    file,
    endpoints: getUploadEndpoints('VITE_AVATAR_UPLOAD_URL', DEFAULT_AVATAR_UPLOAD_ENDPOINTS),
    fields: ['avatar_url', 'url', 'location'],
  })
  return {
    avatar_url: result.url,
    source: result.source,
    profile: result.profile,
  }
}

export async function uploadBackground(file: File): Promise<BackgroundUploadResult> {
  const result = await uploadImage({
    file,
    endpoints: getUploadEndpoints('VITE_BACKGROUND_UPLOAD_URL', DEFAULT_BACKGROUND_UPLOAD_ENDPOINTS),
    fields: ['background_image_url', 'url', 'location'],
  })
  return {
    background_image_url: result.url,
    source: result.source,
    profile: result.profile,
  }
}

export async function clearBackground(): Promise<BackgroundUploadResult> {
  const { data } = await apiClient.delete('/api/me/background')
  return {
    background_image_url: extractImageUrl(data, ['background_image_url', 'url', 'location']) ?? '',
    source: 'remote',
    profile: extractProfile(data),
  }
}

async function uploadImage({
  file,
  endpoints,
  fields,
}: {
  file: File
  endpoints: string[]
  fields: string[]
}): Promise<{ url: string; source: 'remote' | 'local'; profile?: UserProfile }> {
  for (const endpoint of endpoints) {
    try {
      const formData = new FormData()
      formData.append('file', file)

      const { data } = await apiClient.post(endpoint, formData)

      const imageUrl = extractImageUrl(data, fields)
      if (imageUrl) {
        return {
          url: imageUrl,
          source: 'remote',
          profile: extractProfile(data),
        }
      }
    } catch (error) {
      if (!shouldFallbackToLocalPreview(error)) {
        throw error
      }
    }
  }

  return {
    url: URL.createObjectURL(file),
    source: 'local',
  }
}

function getUploadEndpoints(envKey: string, defaults: string[]): string[] {
  const configured = import.meta.env[envKey]
  const endpoints = configured ? [configured, ...defaults] : defaults
  return [...new Set(endpoints)]
}

function extractImageUrl(payload: unknown, fields: string[]): string | null {
  if (typeof payload === 'string' && payload.trim()) {
    return payload
  }

  if (!payload || typeof payload !== 'object') {
    return null
  }

  const data = payload as Record<string, unknown>
  const directUrl = getStringField(data, fields)
  if (directUrl) {
    return directUrl
  }

  const nestedData = data.data
  if (!nestedData || typeof nestedData !== 'object') {
    return null
  }

  return getStringField(nestedData as Record<string, unknown>, fields)
}

function shouldFallbackToLocalPreview(error: unknown): boolean {
  if (!shouldUseMock()) {
    return false
  }

  const axiosError = error as AxiosError | undefined
  if (!axiosError?.isAxiosError) {
    return true
  }

  const statusCode = axiosError.response?.status
  if (typeof statusCode !== 'number') {
    return true
  }

  return statusCode >= 500 || statusCode === 404 || statusCode === 405
}

function extractProfile(payload: unknown): UserProfile | undefined {
  if (!payload || typeof payload !== 'object') {
    return undefined
  }

  const data = payload as Record<string, unknown>
  if (isUserProfile(data.profile)) {
    return data.profile
  }

  const nestedData = data.data
  if (nestedData && typeof nestedData === 'object') {
    const nested = nestedData as Record<string, unknown>
    if (isUserProfile(nested.profile)) {
      return nested.profile
    }
  }

  return undefined
}

function isUserProfile(value: unknown): value is UserProfile {
  if (!value || typeof value !== 'object') {
    return false
  }
  const profile = value as Record<string, unknown>
  return typeof profile.id === 'number' && typeof profile.username === 'string'
}

function getStringField(
  source: Record<string, unknown>,
  keys: string[],
): string | null {
  for (const key of keys) {
    const value = source[key]
    if (typeof value === 'string' && value.trim()) {
      return value
    }
  }
  return null
}
