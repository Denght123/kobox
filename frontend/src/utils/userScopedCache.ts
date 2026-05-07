const USER_KEY = 'kobox.user'
const LEGACY_SESSION_CACHE_KEYS = ['kobox.cache.collections', 'kobox.cache.favorites']

export function getStoredUserId(): string {
  try {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) {
      return 'guest'
    }
    const user = JSON.parse(raw) as { id?: number | string }
    return user.id ? String(user.id) : 'guest'
  } catch {
    return 'guest'
  }
}

export function userScopedStorageKey(baseKey: string, userId = getStoredUserId()): string {
  return `${baseKey}:${userId || 'guest'}`
}

export function clearUserScopedBrowserCache(): void {
  for (const key of LEGACY_SESSION_CACHE_KEYS) {
    sessionStorage.removeItem(key)
  }
}
