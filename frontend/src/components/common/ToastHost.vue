<script setup lang="ts">
import { useToast } from '../../composables/useToast'

const { toasts } = useToast()
</script>

<template>
  <Teleport to="body">
    <TransitionGroup name="toast" tag="div" class="toast-host">
      <div v-for="toast in toasts" :key="toast.id" class="kobox-toast" :class="toast.tone">
        <span class="material-symbols-outlined">
          {{ toast.tone === 'danger' ? 'close' : toast.tone === 'info' ? 'info' : 'check' }}
        </span>
        <strong>{{ toast.message }}</strong>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<style scoped>
.toast-host {
  position: fixed;
  right: 28px;
  bottom: 28px;
  z-index: 120;
  display: grid;
  gap: 10px;
  pointer-events: none;
}

.kobox-toast {
  min-width: 220px;
  max-width: min(360px, calc(100vw - 48px));
  border: 1px solid rgba(255, 255, 255, 0.74);
  border-radius: 999px;
  padding: 12px 16px 12px 12px;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255, 255, 255, 0.9);
  color: var(--on-surface);
  box-shadow: 0 18px 48px rgba(89, 35, 49, 0.18);
  backdrop-filter: blur(18px);
}

.kobox-toast span {
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #f9a8bd, #e9668c);
  color: white;
  font-size: 17px;
}

.kobox-toast.danger span {
  background: linear-gradient(135deg, #ff9ca6, #b31b25);
}

.kobox-toast.info span {
  background: linear-gradient(135deg, #a3e3fd, #1a6379);
}

.kobox-toast strong {
  font-size: 13px;
  font-weight: 900;
}

.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.28s ease, transform 0.28s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.96);
}

@media (max-width: 680px) {
  .toast-host {
    left: 16px;
    right: 16px;
    bottom: 18px;
  }
}
</style>
