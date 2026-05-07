<script setup lang="ts">
import QRCode from 'qrcode'
import { onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const props = defineProps<{
  shareUrl: string
}>()

const { t } = useI18n()
const qrDataUrl = ref('')
const hintText = ref('')
let pendingFrame = 0

watch(
  () => props.shareUrl,
  (value) => {
    if (pendingFrame) {
      cancelAnimationFrame(pendingFrame)
    }
    pendingFrame = requestAnimationFrame(async () => {
      qrDataUrl.value = await QRCode.toDataURL(value, {
        width: 220,
        margin: 1,
        color: {
          dark: '#65323e',
          light: '#ffffff',
        },
      })
      pendingFrame = 0
    })
  },
  { immediate: true },
)

async function copyLink() {
  await navigator.clipboard.writeText(props.shareUrl)
  hintText.value = t('common.copied')
  setTimeout(() => {
    hintText.value = ''
  }, 1200)
}

onBeforeUnmount(() => {
  if (pendingFrame) {
    cancelAnimationFrame(pendingFrame)
    pendingFrame = 0
  }
})
</script>

<template>
  <aside class="surface-card share-card">
    <h3>{{ t('showcase.shareCollection') }}</h3>
    <img :src="qrDataUrl" :alt="t('common.qrCode')" />
    <p>{{ props.shareUrl }}</p>
    <p v-if="hintText" class="copy-hint">{{ hintText }}</p>
    <button class="ghost-btn" type="button" @click="copyLink">
      {{ t('common.copyLink') }}
    </button>
  </aside>
</template>

<style scoped>
.share-card {
  padding: 14px;
  display: grid;
  gap: 10px;
  justify-items: center;
  text-align: center;
}

h3 {
  margin: 0;
  font-family: "Epilogue", sans-serif;
}

img {
  width: 180px;
  height: 180px;
  border-radius: 16px;
}

p {
  margin: 0;
  width: 100%;
  color: var(--on-surface-variant);
  font-size: 12px;
  overflow-wrap: anywhere;
}

.copy-hint {
  color: #2f7d54;
  font-size: 11px;
}
</style>
