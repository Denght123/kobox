import { defineStore } from 'pinia'

import { i18n, persistLocale } from '../i18n'
import type { LocaleCode } from '../types'

export const useAppStore = defineStore('app', {
  state: () => ({
    locale: i18n.global.locale.value as LocaleCode,
  }),
  actions: {
    setLocale(nextLocale: LocaleCode) {
      this.locale = nextLocale
      i18n.global.locale.value = nextLocale
      persistLocale(nextLocale)
    },
  },
})
