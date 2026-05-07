import type { CollectionStatus } from '../types'

export function formatDateText(value: string | null): string {
  if (!value) {
    return '--'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return value
  }
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(
    date.getDate(),
  ).padStart(2, '0')}`
}

export function statusToI18nKey(status: CollectionStatus): string {
  return `status.${status}`
}
