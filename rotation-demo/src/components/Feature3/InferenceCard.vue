<script setup>
defineProps({
  label: String,
  format: String,
  method: String,
  text: String,
  quality: { type: String, default: 'good' },
})
</script>

<template>
  <div class="infer-card panel-card" :class="[`quality-${quality}`, { 'lqh-highlight': method && method.includes('LQH') }]">
    <div class="card-header">
      <span class="format-badge">{{ format }}</span>
      <span class="method-tag">{{ method }}</span>
      <span v-if="quality === 'reference'" class="ref-badge">Reference</span>
      <span v-if="method && method.includes('LQH')" class="ours-badge">Ours</span>
    </div>
    <div class="card-label">{{ label }}</div>
    <div class="card-text">{{ text }}</div>
  </div>
</template>

<style scoped>
.infer-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 180px;
}
.quality-reference { border-color: var(--primary); }
.quality-good      { border-color: var(--mist-blue); }
.quality-degraded  { border-color: var(--terracotta); }

.card-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.format-badge {
  font-size: 12px;
  padding: 2px 7px;
  border-radius: 3px;
  background: rgba(107, 142, 155, 0.12);
  border: 1px solid rgba(107, 142, 155, 0.35);
  color: var(--mist-blue);
  font-weight: 600;
}
.method-tag {
  font-size: 12px;
  padding: 2px 7px;
  border-radius: 3px;
  background: rgba(74, 124, 89, 0.1);
  border: 1px solid rgba(74, 124, 89, 0.28);
  color: var(--primary);
}
.ref-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 3px;
  background: rgba(74, 124, 89, 0.08);
  border: 1px solid rgba(74, 124, 89, 0.25);
  color: var(--primary);
}
.card-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}
.card-text {
  font-size: 14px;
  color: var(--text-primary);
  line-height: 1.7;
  flex: 1;
  padding: 10px 12px;
  background: var(--bg-secondary);
  border-radius: 4px;
  border: 1px solid var(--border-color);
}
</style>
