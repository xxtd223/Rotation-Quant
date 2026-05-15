<script setup>
defineProps({
  label: String,
  format: String,
  method: String,
  text: String,
  quality: { type: String, default: 'good' }, // 'reference' | 'good' | 'degraded'
})
</script>

<template>
  <div class="infer-card panel-card" :class="`quality-${quality}`">
    <div class="card-header">
      <span class="format-badge">{{ format }}</span>
      <span class="method-tag">{{ method }}</span>
      <span v-if="quality === 'reference'" class="ref-badge">Reference</span>
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
.quality-reference { border-color: var(--accent-cyan); }
.quality-good { border-color: var(--accent-green); }
.quality-degraded { border-color: #ff6b6b; }

.card-header { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.format-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(79, 195, 247, 0.15);
  border: 1px solid rgba(79, 195, 247, 0.4);
  color: var(--accent-blue);
  font-weight: 600;
}
.method-tag {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(105, 219, 124, 0.12);
  border: 1px solid rgba(105, 219, 124, 0.3);
  color: var(--accent-green);
}
.ref-badge {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(0, 229, 255, 0.12);
  border: 1px solid rgba(0, 229, 255, 0.4);
  color: var(--accent-cyan);
}
.card-label {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.card-text {
  font-size: 13px;
  color: var(--text-primary);
  line-height: 1.7;
  font-family: 'Segoe UI', system-ui, sans-serif;
  flex: 1;
  padding: 10px 12px;
  background: rgba(13, 17, 23, 0.5);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}
</style>
