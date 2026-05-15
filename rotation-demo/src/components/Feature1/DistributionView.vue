<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import DistributionPanel from './DistributionPanel.vue'
import { generateData, DIST_OPTIONS } from '../../composables/useDataGenerator.js'
import { applyTransformDist, METHOD_OPTIONS } from '../../composables/useTransformer.js'

const props = defineProps({ visible: Boolean })

const distKey   = ref('one_extreme')
const methodMid = ref('hadamard')
const methodRight = ref('SQH')
const seed = ref(0)

const SIZE = 1024

const rawData = ref(null)

function regenerate() {
  seed.value++
  rawData.value = generateData(distKey.value, SIZE)
}

const baselineData = computed(() => rawData.value)
const midData      = computed(() => rawData.value ? applyTransformDist(rawData.value, methodMid.value) : null)
const rightData    = computed(() => rawData.value ? applyTransformDist(rawData.value, methodRight.value) : null)

const midLabel   = computed(() => METHOD_OPTIONS.find(m => m.value === methodMid.value)?.label ?? methodMid.value)
const rightLabel = computed(() => METHOD_OPTIONS.find(m => m.value === methodRight.value)?.label ?? methodRight.value)

const panelMid   = ref(null)
const panelRight = ref(null)

watch(() => props.visible, (v) => {
  if (v) {
    setTimeout(() => {
      panelMid.value?.resize()
      panelRight.value?.resize()
    }, 50)
  }
})

watch(distKey, regenerate)
onMounted(regenerate)
</script>

<template>
  <div class="dist-view">
    <div class="view-header">
      <div>
        <div class="section-title">Distribution Comparison</div>
        <p class="view-desc">Activation value distribution before and after linear transformation</p>
      </div>
    </div>

    <div class="controls-row">
      <div class="ctrl-group">
        <label class="ctrl-label">Data Distribution</label>
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

    <div class="panels-grid">
      <DistributionPanel
        :values="baselineData"
        title="None"
        :isBaseline="true"
        color="#8b949e"
      />
      <DistributionPanel
        ref="panelMid"
        :values="midData"
        :title="midLabel"
        color="#4fc3f7"
      />
      <DistributionPanel
        ref="panelRight"
        :values="rightData"
        :title="rightLabel"
        color="#69db7c"
      />
    </div>

    <div class="insight-row">
      <div class="insight-card">
        <span class="insight-icon">💡</span>
        <span>Hadamard spreads outlier energy across all block elements, eliminating spikes.</span>
      </div>
      <div class="insight-card">
        <span class="insight-icon">📐</span>
        <span>Whitening-based methods (White, WUS, WUSH) normalize variance to ~1, ideal for uniform quantization grids.</span>
      </div>
      <div class="insight-card">
        <span class="insight-icon">🎯</span>
        <span>SQH combines symmetric joint optimization with Hadamard for best quantization alignment.</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dist-view { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.view-header { display: flex; align-items: flex-start; justify-content: space-between; }
.view-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }
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
.panels-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}
.insight-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
}
.insight-card {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  padding: 12px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.5;
}
.insight-icon { font-size: 16px; flex-shrink: 0; }
</style>
