<script setup lang="ts">
import ToastHost from './components/common/ToastHost.vue'
import ConfirmHost from './components/common/ConfirmHost.vue'
</script>

<template>
  <RouterView />
  <ConfirmHost />
  <ToastHost />
</template>
