<script setup lang="ts">
import { computed } from 'vue'

import { useAuthStore } from '../../stores/auth'

const props = defineProps<{
  backgroundImageUrl?: string | null
}>()

const authStore = useAuthStore()
const backgroundImageUrl = computed(() => {
  if (props.backgroundImageUrl !== undefined) {
    return props.backgroundImageUrl || ''
  }
  return authStore.user?.background_image_url || ''
})
</script>

<template>
  <div class="floating-bg" :class="{ custom: backgroundImageUrl }">
    <div
      v-if="backgroundImageUrl"
      class="custom-background"
      :style="{ backgroundImage: `url(${backgroundImageUrl})` }"
    />
    <div class="floating-orb primary orb-a" />
    <div class="floating-orb tertiary orb-b" />
    <div class="floating-orb secondary orb-c" />
  </div>
</template>

<style scoped>
.orb-a {
  width: 420px;
  height: 420px;
  top: -120px;
  left: -90px;
}

.orb-b {
  width: 520px;
  height: 520px;
  right: -150px;
  bottom: -160px;
}

.orb-c {
  width: 260px;
  height: 260px;
  left: 34%;
  top: 34%;
}

.custom-background {
  position: absolute;
  inset: 0;
  background-position: center;
  background-size: cover;
  opacity: 1;
}
</style>
