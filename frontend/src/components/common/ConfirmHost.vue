<script setup lang="ts">
import { useConfirm } from '../../composables/useConfirm'

const { confirmState, settleConfirm } = useConfirm()
</script>

<template>
  <Teleport to="body">
    <Transition name="confirm">
      <div v-if="confirmState.open" class="confirm-backdrop" @click.self="settleConfirm(false)">
        <section class="confirm-card" :class="confirmState.tone" role="dialog" aria-modal="true">
          <div class="confirm-orb">
            <span class="material-symbols-outlined">
              {{ confirmState.tone === 'danger' ? 'delete' : 'auto_awesome' }}
            </span>
          </div>
          <div class="confirm-copy">
            <h2>{{ confirmState.title }}</h2>
            <p>{{ confirmState.message }}</p>
          </div>
          <div class="confirm-actions">
            <button class="ghost-btn" type="button" @click="settleConfirm(false)">
              {{ confirmState.cancelText }}
            </button>
            <button class="primary-btn" :class="{ danger: confirmState.tone === 'danger' }" type="button" @click="settleConfirm(true)">
              {{ confirmState.confirmText }}
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.confirm-backdrop {
  position: fixed;
  inset: 0;
  z-index: 110;
  display: grid;
  place-items: center;
  padding: 24px;
  background:
    radial-gradient(circle at 40% 20%, rgba(254, 182, 196, 0.28), transparent 32%),
    rgba(48, 46, 44, 0.28);
  backdrop-filter: blur(12px);
}

.confirm-card {
  width: min(440px, 100%);
  border: 1px solid rgba(255, 255, 255, 0.74);
  border-radius: 32px;
  padding: 24px;
  display: grid;
  gap: 16px;
  justify-items: center;
  text-align: center;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(255, 247, 250, 0.96)),
    radial-gradient(circle at top right, rgba(250, 211, 253, 0.28), transparent 40%);
  box-shadow: 0 28px 80px rgba(89, 35, 49, 0.24);
}

.confirm-orb {
  width: 58px;
  height: 58px;
  border-radius: 20px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #f9a8bd, #e9668c);
  color: white;
  box-shadow: 0 18px 36px rgba(219, 106, 137, 0.28);
}

.confirm-card.danger .confirm-orb {
  background: linear-gradient(135deg, #ff9ca6, #b31b25);
}

.confirm-copy h2,
.confirm-copy p {
  margin: 0;
}

.confirm-copy {
  display: grid;
  gap: 8px;
}

.confirm-copy h2 {
  font-family: "Epilogue", sans-serif;
  font-size: 24px;
}

.confirm-copy p {
  color: var(--on-surface-variant);
}

.confirm-actions {
  width: 100%;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.primary-btn.danger {
  background: #ffd9de;
  color: #7d111b;
}

.confirm-enter-active,
.confirm-leave-active {
  transition: opacity 0.2s ease;
}

.confirm-enter-active .confirm-card,
.confirm-leave-active .confirm-card {
  transition: transform 0.2s ease, opacity 0.2s ease;
}

.confirm-enter-from,
.confirm-leave-to {
  opacity: 0;
}

.confirm-enter-from .confirm-card,
.confirm-leave-to .confirm-card {
  opacity: 0;
  transform: translateY(10px) scale(0.96);
}
</style>
