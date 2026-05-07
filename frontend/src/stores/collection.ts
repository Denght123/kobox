import { defineStore } from 'pinia'

import type { CollectionStatus } from '../types'

export const useCollectionStore = defineStore('collection', {
  state: () => ({
    activeStatusFilter: 'completed' as CollectionStatus,
  }),
  actions: {
    setActiveStatusFilter(status: CollectionStatus) {
      this.activeStatusFilter = status
    },
  },
})
