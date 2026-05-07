<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { useAppStore } from '../../stores/app'
import type { LocaleCode } from '../../types'

const appStore = useAppStore()
const { t } = useI18n()
const isOpen = ref(false)

const localeOptions: LocaleCode[] = ['zh-CN', 'zh-TW', 'en', 'ja', 'ko']
const currentLocaleLabel = computed(() => t(`language.${appStore.locale}`))

function toggleMenu() {
  isOpen.value = !isOpen.value
}

function selectLocale(nextLocale: LocaleCode) {
  appStore.setLocale(nextLocale)
  isOpen.value = false
}

function closeMenu() {
  window.setTimeout(() => {
    isOpen.value = false
  }, 120)
}
</script>

<template>
  <div class="language-menu" @focusout="closeMenu">
    <button
      class="language-globe"
      type="button"
      :aria-label="currentLocaleLabel"
      :title="currentLocaleLabel"
      @click="toggleMenu"
    >
      <span class="material-symbols-outlined">language</span>
    </button>
    <div v-if="isOpen" class="locale-panel">
      <button
        v-for="localeOption in localeOptions"
        :key="localeOption"
        class="locale-option"
        :class="{ active: appStore.locale === localeOption }"
        type="button"
        @click="selectLocale(localeOption)"
      >
        {{ t(`language.${localeOption}`) }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.language-menu {
  position: relative;
  display: inline-flex;
}

.language-globe {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 999px;
  display: inline-grid;
  place-items: center;
  background: rgba(254, 182, 196, 0.16);
  color: #a36979;
  cursor: pointer;
  transition: background 0.2s ease, transform 0.2s ease;
}

.language-globe:hover {
  background: rgba(254, 182, 196, 0.3);
  transform: translateY(-1px);
}

.material-symbols-outlined {
  font-size: 20px;
}

.locale-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  z-index: 45;
  min-width: 156px;
  display: grid;
  gap: 4px;
  padding: 8px;
  border: 1px solid rgba(177, 172, 169, 0.18);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.98);
  box-shadow: var(--shadow-soft);
}

.locale-panel::before {
  content: "";
  position: absolute;
  top: -6px;
  right: 12px;
  width: 12px;
  height: 12px;
  background: rgba(255, 255, 255, 0.98);
  transform: rotate(45deg);
  border-left: 1px solid rgba(177, 172, 169, 0.18);
  border-top: 1px solid rgba(177, 172, 169, 0.18);
}

.locale-option {
  border: none;
  border-radius: 12px;
  background: transparent;
  color: var(--on-surface);
  padding: 9px 11px;
  text-align: left;
  cursor: pointer;
  font-weight: 700;
}

.locale-option:hover,
.locale-option.active {
  background: rgba(254, 182, 196, 0.22);
  color: #a64d67;
}
</style>
