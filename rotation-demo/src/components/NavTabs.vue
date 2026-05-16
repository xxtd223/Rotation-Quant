<script setup>
const props = defineProps({ active: String })
const emit = defineEmits(['update:active'])

const tabs = [
  { id: 'dist',    label: 'Distribution' },
  { id: 'heatmap', label: 'Quant. Error' },
  { id: 'metrics', label: 'Performance' },
  { id: 'hw',      label: 'Hardware' },
]
</script>

<template>
  <nav class="nav-tabs">
    <div class="nav-brand">LQH Quantization Research</div>
    <div class="tab-list">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: active === tab.id }"
        @click="emit('update:active', tab.id)"
      >
        {{ tab.label }}
      </button>
    </div>
  </nav>
</template>

<style scoped>
.nav-tabs {
  display: flex;
  align-items: center;
  gap: 32px;
  padding: 0 24px;
  background: var(--bg-card);
  border-bottom: 1px solid var(--border-color);
  height: 52px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}
.nav-brand {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-primary);
  flex-shrink: 0;
  letter-spacing: -0.2px;
}
.tab-list {
  display: flex;
  gap: 2px;
  height: 100%;
}
.tab-btn {
  display: flex;
  align-items: center;
  padding: 0 14px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  font-size: 14px;
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s;
  white-space: nowrap;
}
.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}
</style>
