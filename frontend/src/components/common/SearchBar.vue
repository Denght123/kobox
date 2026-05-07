<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { AnimeSuggestion } from '../../types'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    modelValue: string
    placeholder?: string
    buttonText?: string
    suggestions?: AnimeSuggestion[]
    suggestionsLoading?: boolean
  }>(),
  {
    placeholder: '',
    suggestions: () => [],
    suggestionsLoading: false,
  },
)

const buttonText = computed(() => props.buttonText ?? t('submit'))

const emit = defineEmits<{
  'update:modelValue': [value: string]
  submit: []
  selectSuggestion: [value: AnimeSuggestion]
}>()

const isFocused = ref(false)
let blurTimer = 0

function onInput(event: Event) {
  const target = event.target as HTMLInputElement
  emit('update:modelValue', target.value)
}

function onSubmit() {
  emit('submit')
}

function onFocus() {
  if (blurTimer) {
    window.clearTimeout(blurTimer)
    blurTimer = 0
  }
  isFocused.value = true
}

function onBlur() {
  blurTimer = window.setTimeout(() => {
    isFocused.value = false
    blurTimer = 0
  }, 120)
}

function onSelectSuggestion(item: AnimeSuggestion) {
  emit('update:modelValue', item.title)
  emit('selectSuggestion', item)
  isFocused.value = false
}

const shouldShowSuggestions = computed(
  () =>
    isFocused.value &&
    props.modelValue.trim().length > 0 &&
    (props.suggestionsLoading || props.suggestions.length > 0),
)

onBeforeUnmount(() => {
  if (blurTimer) {
    window.clearTimeout(blurTimer)
  }
})
</script>

<template>
  <div class="search-shell">
    <div class="search-box">
      <div class="search-input-row">
        <span class="material-symbols-outlined icon">search</span>
        <input
          :value="props.modelValue"
          :placeholder="props.placeholder"
          type="text"
          @blur="onBlur"
          @focus="onFocus"
          @input="onInput"
          @keyup.enter="onSubmit"
        />
        <button class="primary-btn" type="button" @click="onSubmit">
          {{ buttonText }}
        </button>
      </div>
      <div v-if="shouldShowSuggestions" class="suggestions-panel">
        <div v-if="props.suggestionsLoading && props.suggestions.length === 0" class="suggestion loading">
          {{ t('common.loading') }}
        </div>
        <button
          v-for="item in props.suggestions"
          v-else
          :key="item.id"
          class="suggestion"
          type="button"
          @mousedown.prevent="onSelectSuggestion(item)"
        >
          <span class="material-symbols-outlined">search</span>
          <span>{{ item.title }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.search-shell {
  width: 100%;
}

.search-box {
  position: relative;
  width: 100%;
}

.search-input-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  border-radius: 999px;
  padding: 8px 10px 8px 14px;
  border: 1px solid rgba(177, 172, 169, 0.2);
  background: var(--surface-container-lowest);
  box-shadow: var(--shadow-soft);
}

.icon {
  color: var(--outline);
}

input {
  border: none;
  background: transparent;
  flex: 1;
  min-width: 40px;
  outline: none;
  color: var(--on-surface);
}

.suggestions-panel {
  position: absolute;
  inset: calc(100% + 10px) 0 auto;
  display: grid;
  gap: 6px;
  padding: 10px;
  border-radius: 20px;
  border: 1px solid rgba(177, 172, 169, 0.2);
  background: rgba(255, 255, 255, 0.97);
  box-shadow: var(--shadow-soft);
  z-index: 20;
}

.suggestion {
  border: none;
  background: rgba(245, 242, 239, 0.9);
  border-radius: 14px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-align: left;
  color: var(--on-surface);
}

.suggestion:hover {
  background: rgba(250, 211, 253, 0.35);
}

.suggestion.loading {
  color: var(--on-surface-variant);
}
</style>
