import { ref } from 'vue'

interface ConfirmState {
  open: boolean
  title: string
  message: string
  confirmText: string
  cancelText: string
  tone: 'default' | 'danger'
  resolve?: (confirmed: boolean) => void
}

const confirmState = ref<ConfirmState>({
  open: false,
  title: '',
  message: '',
  confirmText: '',
  cancelText: '',
  tone: 'default',
})

let lastConfirmOpenedAt = 0

export function useConfirm() {
  function confirmAction(options: {
    title: string
    message: string
    confirmText: string
    cancelText: string
    tone?: 'default' | 'danger'
  }) {
    const now = Date.now()
    if (confirmState.value.open || now - lastConfirmOpenedAt < 500) {
      return Promise.resolve(false)
    }
    lastConfirmOpenedAt = now
    return new Promise<boolean>((resolve) => {
      confirmState.value = {
        open: true,
        title: options.title,
        message: options.message,
        confirmText: options.confirmText,
        cancelText: options.cancelText,
        tone: options.tone ?? 'default',
        resolve,
      }
    })
  }

  function settleConfirm(confirmed: boolean) {
    const resolve = confirmState.value.resolve
    confirmState.value = {
      ...confirmState.value,
      open: false,
      resolve: undefined,
    }
    resolve?.(confirmed)
  }

  return {
    confirmState,
    confirmAction,
    settleConfirm,
  }
}
