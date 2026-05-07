<script setup lang="ts">
const props = defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <div class="empty-wrap surface-card">
    <span class="material-symbols-outlined">stacks</span>
    <h3>{{ props.title }}</h3>
    <p v-if="props.description">{{ props.description }}</p>
  </div>
</template>

<style scoped>
.empty-wrap {
  min-height: 180px;
  display: grid;
  place-content: center;
  gap: 10px;
  text-align: center;
  padding: 18px;
}

span {
  color: #c08ea0;
}

h3 {
  margin: 0;
  font-family: "Epilogue", sans-serif;
}

p {
  margin: 0;
  color: var(--on-surface-variant);
  font-size: 14px;
}
</style>
