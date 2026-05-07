import { ref } from 'vue'

export type ToastTone = 'success' | 'danger' | 'info'

export interface ToastItem {
  id: number
  message: string
  tone: ToastTone
}

const toasts = ref<ToastItem[]>([])
const recentToastAt = new Map<string, number>()
let toastId = 0

export function useToast() {
  function showToast(message: string, tone: ToastTone = 'success') {
    const key = `${tone}:${message}`
    const now = Date.now()
    const lastShownAt = recentToastAt.get(key) ?? 0
    if (now - lastShownAt < 900) {
      return
    }
    recentToastAt.set(key, now)
    const id = ++toastId
    toasts.value = [...toasts.value, { id, message, tone }]
    window.setTimeout(() => {
      toasts.value = toasts.value.filter((toast) => toast.id !== id)
    }, 2200)
  }

  return {
    toasts,
    showToast,
  }
}
