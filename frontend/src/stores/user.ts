import { defineStore } from 'pinia'

import type { UserProfile, UserSettings } from '../types'

export const useUserStore = defineStore('user', {
  state: () => ({
    profile: null as UserProfile | null,
    settings: null as UserSettings | null,
  }),
  actions: {
    setProfile(profile: UserProfile) {
      this.profile = profile
    },
    setSettings(settings: UserSettings) {
      this.settings = settings
    },
  },
})
