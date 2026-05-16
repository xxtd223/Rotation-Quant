<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({
  label: String,
  pctMin: Number,
  pctMax: Number,
  colorClass: { type: String, default: '' },
  detail: String,
  labelMin: String,
  labelMax: String,
})

const minEl = ref(null)
const maxEl = ref(null)

onMounted(() => {
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      if (maxEl.value) maxEl.value.style.width = props.pctMax + '%'
      if (minEl.value) minEl.value.style.width = props.pctMin + '%'
    })
  })
})
</script>

<template>
  <div class="progress-item">
    <div class="progress-header">
      <span class="progress-label">{{ label }}</span>
      <span class="progress-range" :class="colorClass">{{ labelMin }} – {{ labelMax }}</span>
    </div>
    <div class="progress-track">
      <div ref="maxEl" class="progress-fill-max" :class="colorClass" style="width:0%" />
      <div ref="minEl" class="progress-fill-min" :class="colorClass" style="width:0%" />
    </div>
    <div v-if="detail" class="progress-detail">{{ detail }}</div>
  </div>
</template>

<style scoped>
.progress-item { display: flex; flex-direction: column; gap: 6px; }
.progress-header { display: flex; justify-content: space-between; align-items: center; }
.progress-label { font-size: 13px; color: var(--text-primary); }
.progress-range {
  font-size: 13px;
  font-weight: 600;
  font-family: monospace;
  color: var(--primary);
}
.progress-range.orange { color: var(--terracotta); }
.progress-range.green  { color: var(--secondary); }
.progress-detail { font-size: 11px; color: var(--text-muted); }

.progress-track {
  position: relative;
  background: var(--bg-secondary);
  border-radius: 3px;
  height: 8px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}
/* lighter band — full range up to max */
.progress-fill-max {
  position: absolute;
  left: 0; top: 0; height: 100%;
  border-radius: 3px;
  width: 0%;
  transition: width 1.4s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--primary);
  opacity: 0.28;
}
.progress-fill-max.orange { background: var(--terracotta); }
.progress-fill-max.green  { background: var(--secondary); }

/* darker band — guaranteed minimum */
.progress-fill-min {
  position: absolute;
  left: 0; top: 0; height: 100%;
  border-radius: 3px;
  width: 0%;
  transition: width 1.4s cubic-bezier(0.4, 0, 0.2, 1);
  background: var(--primary);
  opacity: 0.85;
}
.progress-fill-min.orange { background: var(--terracotta); }
.progress-fill-min.green  { background: var(--secondary); }
</style>
