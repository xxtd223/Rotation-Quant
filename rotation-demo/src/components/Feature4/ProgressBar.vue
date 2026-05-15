<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  label: String,
  percent: Number,
  colorClass: { type: String, default: '' },
  detail: String,
})

const fillEl = ref(null)

onMounted(() => {
  // Trigger CSS transition after mount
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      if (fillEl.value) fillEl.value.style.width = props.percent + '%'
    })
  })
})
</script>

<template>
  <div class="progress-item">
    <div class="progress-header">
      <span class="progress-label">{{ label }}</span>
      <span class="progress-pct">{{ percent }}%</span>
    </div>
    <div class="progress-track">
      <div ref="fillEl" class="progress-fill" :class="colorClass" style="width:0%" />
    </div>
    <div v-if="detail" class="progress-detail">{{ detail }}</div>
  </div>
</template>

<style scoped>
.progress-item { display: flex; flex-direction: column; gap: 6px; }
.progress-header { display: flex; justify-content: space-between; align-items: center; }
.progress-label { font-size: 13px; color: var(--text-primary); }
.progress-pct { font-size: 13px; font-weight: 700; color: var(--accent-cyan); font-family: monospace; }
.progress-detail { font-size: 11px; color: var(--text-muted); }
</style>
