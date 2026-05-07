import { createI18n } from 'vue-i18n'

import en from './locales/en.json'
import ja from './locales/ja.json'
import ko from './locales/ko.json'
import zhCN from './locales/zh-CN.json'
import zhTW from './locales/zh-TW.json'

const STORAGE_KEY = 'kobox.locale'
const storedLocale = localStorage.getItem(STORAGE_KEY)
const locale = storedLocale ?? 'zh-CN'

export const i18n = createI18n({
  legacy: false,
  locale,
  fallbackLocale: 'zh-CN',
  messages: {
    'zh-CN': zhCN,
    'zh-TW': zhTW,
    en,
    ja,
    ko,
  },
})

export function persistLocale(nextLocale: string): void {
  localStorage.setItem(STORAGE_KEY, nextLocale)
}
