<script setup>
const props = defineProps({
  active: String,
})
const emit = defineEmits(['update:active'])

const tabs = [
  { id: 'dist',    icon: '📊', label: 'Distribution Comparison' },
  { id: 'heatmap', icon: '🌡️', label: 'Quantization Error' },
  { id: 'metrics', icon: '⚡', label: 'Performance Metrics' },
  { id: 'hw',      icon: '🖥️', label: 'Hardware Dashboard' },
]
</script>

<template>
  <nav class="nav-tabs">
    <div class="nav-brand">
      <span class="brand-icon">⚛</span>
      <span class="brand-text">LQH Quant Research</span>
    </div>
    <div class="tab-list">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ active: active === tab.id }"
        @click="emit('update:active', tab.id)"
      >
        <span class="tab-icon">{{ tab.icon }}</span>
        <span class="tab-label">{{ tab.label }}</span>
      </button>
    </div>
  </nav>
</template>

<style scoped>
.nav-tabs {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 0 24px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  height: 56px;
  position: sticky;
  top: 0;
  z-index: 100;
}
.nav-brand {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}
.brand-icon {
  font-size: 20px;
  animation: pulse-text 3s ease-in-out infinite;
}
.brand-text {
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: var(--accent-cyan);
}
.tab-list {
  display: flex;
  gap: 4px;
  height: 100%;
}
.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 16px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-muted);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}
.tab-btn:hover {
  color: var(--text-primary);
  border-bottom-color: var(--border-color);
}
.tab-btn.active {
  color: var(--accent-cyan);
  border-bottom-color: var(--accent-cyan);
  text-shadow: 0 0 8px rgba(0, 229, 255, 0.4);
}
.tab-icon { font-size: 15px; }
</style>
