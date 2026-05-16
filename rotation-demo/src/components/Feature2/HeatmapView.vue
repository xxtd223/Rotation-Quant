<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import HeatmapPanel from './HeatmapPanel.vue'
import HeatmapColorbar from './HeatmapColorbar.vue'
import { generateData, DIST_OPTIONS } from '../../composables/useDataGenerator.js'
import { METHOD_OPTIONS, applyTransformFull } from '../../composables/useTransformer.js'
import { nvfp4QuantError, flatTo2D } from '../../composables/useQuantization.js'

const props = defineProps({ visible: Boolean })

const distKey     = ref('one_extreme')
const methodMid   = ref('hadamard')
const methodRight = ref('LQH')

const D = 16, N = 64, M = 64, gs = 16

const rawData = ref(null)

function regenerate() {
  const X = generateData(distKey.value, D * N)
  const W = generateData('Llama_WQ', D * M)
  rawData.value = { X, W, D, N, M, gs }
}

const sharedAbsMax = computed(() => {
  if (!rawData.value) return 0
  const { X, W, D, N, M, gs } = rawData.value
  let globalMax = 1e-10
  for (const method of ['None', methodMid.value, methodRight.value]) {
    const { X_prime, W_prime } = applyTransformFull(X, W, D, N, M, gs, method)
    const scale = (method === 'LQ' || method === 'LQH') ? 0.7 : 1.0
    const { error } = nvfp4QuantError(W, D, M, X, N, X_prime, W_prime, scale)
    for (const row of flatTo2D(error, Math.min(M, 64), Math.min(N, 64)))
      for (const v of row) if (Math.abs(v) > globalMax) globalMax = Math.abs(v)
  }
  return globalMax
})

const panelMid   = ref(null)
const panelRight = ref(null)

watch(() => props.visible, (v) => {
  if (v) setTimeout(() => { panelMid.value?.resize(); panelRight.value?.resize() }, 50)
})
watch(distKey, regenerate)
onMounted(regenerate)

const midLabel   = () => METHOD_OPTIONS.find(m => m.value === methodMid.value)?.label ?? methodMid.value
const rightLabel = () => METHOD_OPTIONS.find(m => m.value === methodRight.value)?.label ?? methodRight.value
</script>

<template>
  <div class="heatmap-view">
    <div class="view-header">
      <div>
        <div class="section-title">Quantization Error Heatmap</div>
        <p class="view-desc">
          NVFP4 absolute output error |Ŷ − Y| &nbsp;|&nbsp;
          D={{ D }}, N={{ N }}, M={{ M }}, gs={{ gs }} &nbsp;|&nbsp;
          W ~ Llama_WQ
        </p>
      </div>
    </div>

    <div class="controls-row">
      <div class="ctrl-group">
        <label class="ctrl-label">Activation Distribution (X)</label>
        <select v-model="distKey" class="ctrl-select">
          <option v-for="d in DIST_OPTIONS" :key="d.value" :value="d.value">{{ d.label }}</option>
        </select>
      </div>
      <div class="ctrl-group">
        <label class="ctrl-label">Middle Panel Method</label>
        <select v-model="methodMid" class="ctrl-select">
          <option v-for="m in METHOD_OPTIONS.filter(x => x.value !== 'None')" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
      </div>
      <div class="ctrl-group">
        <label class="ctrl-label">Right Panel Method</label>
        <select v-model="methodRight" class="ctrl-select">
          <option v-for="m in METHOD_OPTIONS.filter(x => x.value !== 'None')" :key="m.value" :value="m.value">{{ m.label }}</option>
        </select>
      </div>
      <button class="btn btn-primary" @click="regenerate">↺ Regenerate</button>
    </div>

    <!-- Three equal panels + standalone colorbar column -->
    <div class="panels-row">
      <div class="panels-grid">
        <HeatmapPanel
          :rawData="rawData"
          title="None"
          :isBaseline="true"
          method="None"
          :sharedAbsMax="sharedAbsMax"
        />
        <HeatmapPanel
          ref="panelMid"
          :rawData="rawData"
          :title="midLabel()"
          :method="methodMid"
          :sharedAbsMax="sharedAbsMax"
        />
        <HeatmapPanel
          ref="panelRight"
          :rawData="rawData"
          :title="rightLabel()"
          :method="methodRight"
          :sharedAbsMax="sharedAbsMax"
        />
      </div>
      <HeatmapColorbar :absMax="sharedAbsMax" />
    </div>

    <div class="legend-row">
      <div class="legend-item">
        <div class="legend-dot" style="background:#8b4a3a"></div>
        <span>Large absolute error</span>
      </div>
      <div class="legend-item">
        <div class="legend-dot" style="background:#d4a853"></div>
        <span>Medium absolute error</span>
      </div>
      <div class="legend-item">
        <div class="legend-dot" style="background:#e4f1e6; border:1px solid #b8d4ba"></div>
        <span>Near-zero error (ideal)</span>
      </div>
      <div class="legend-note">Block size = 16 (NVFP4)</div>
    </div>
  </div>
</template>

<style scoped>
.heatmap-view { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.view-header { display: flex; align-items: flex-start; }
.view-desc { font-size: 14px; color: var(--text-muted); margin-top: 4px; }

.controls-row {
  display: flex;
  align-items: flex-end;
  gap: 16px;
  flex-wrap: wrap;
  padding: 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
}
.ctrl-group { display: flex; flex-direction: column; gap: 4px; }

/* Outer row: panels take all remaining space, colorbar is fixed width */
.panels-row {
  display: flex;
  align-items: stretch;
  gap: 8px;
  min-width: 0;
}

/* Three equal-width panels */
.panels-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.legend-row {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
  padding: 12px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 13px;
  color: var(--text-muted);
}
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-dot { width: 12px; height: 12px; border-radius: 2px; flex-shrink: 0; }
.legend-note { margin-left: auto; font-style: italic; }
</style>
