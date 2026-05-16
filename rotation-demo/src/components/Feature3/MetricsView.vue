<script setup>
import { ref, watch } from 'vue'
import SpeedupChart from './SpeedupChart.vue'
import VramChart from './VramChart.vue'
import InferenceCard from './InferenceCard.vue'

const props = defineProps({ visible: Boolean })

const activeModel = ref('Llama-3.2-3B')
const vramType    = ref('static')

const MODELS = ['Llama-3.2-3B', 'Qwen3-8B']

const speedupChart = ref(null)
const vramChart    = ref(null)

watch(() => props.visible, (v) => {
  if (v) setTimeout(() => { speedupChart.value?.resize(); vramChart.value?.resize() }, 50)
})

const inferenceCards = [
  {
    label: 'FP16 Full Precision',
    format: 'FP16',
    method: 'No Quantization',
    quality: 'reference',
    text: 'The transformer architecture relies on self-attention mechanisms to capture long-range dependencies. Each token attends to all other tokens in the sequence, enabling the model to understand complex contextual relationships with high fidelity.',
  },
  {
    label: 'MXFP4 — No Rotation',
    format: 'MXFP4',
    method: 'None',
    quality: 'degraded',
    text: 'The transformer architecture relies on self-attention mechanisms to capture long-range dependencies. Each token attends to all other tokens in the sequence, enabling the model to understand complex contextual relationships with high fidelity.',
  },
  {
    label: 'MXFP4 + LQH Rotation',
    format: 'MXFP4',
    method: '+ LQH',
    quality: 'good',
    text: 'The transformer architecture relies on self-attention mechanisms to capture long-range dependencies. Each token attends to all other tokens in the sequence, enabling the model to understand complex contextual relationships with high fidelity.',
  },
]

const pplData = {
  'Llama-3.2-3B': { fp16: 11.4, mxfp4_none: 14.44, mxfp4_lqh: 12.75, nvfp4_none: 12.94, nvfp4_sqh: 11.81 },
  'Qwen3-8B':     { fp16: 10.25, mxfp4_none: 11.81, mxfp4_lqh: 10.94, nvfp4_none: 10.94, nvfp4_sqh: 10.44 },
}
</script>

<template>
  <div class="metrics-view">
    <div class="view-header">
      <div>
        <div class="section-title">Performance Metrics</div>
        <p class="view-desc">Speedup, VRAM usage, and inference quality across quantization formats and rotation methods</p>
      </div>
      <div class="model-toggle">
        <button
          v-for="m in MODELS"
          :key="m"
          class="toggle-btn"
          :class="{ active: activeModel === m }"
          @click="activeModel = m"
        >{{ m }}</button>
      </div>
    </div>

    <div class="charts-row">
      <SpeedupChart ref="speedupChart" :model="activeModel" :visible="visible" />
      <div class="vram-section">
        <div class="vram-toggle">
          <button class="toggle-btn" :class="{ active: vramType === 'static' }" @click="vramType = 'static'">Static</button>
          <button class="toggle-btn" :class="{ active: vramType === 'peak' }" @click="vramType = 'peak'">Peak</button>
        </div>
        <VramChart ref="vramChart" :model="activeModel" :vramType="vramType" :visible="visible" />
      </div>
    </div>

    <hr class="divider" />

    <div class="ppl-row">
      <div class="section-title" style="margin-bottom:12px">Perplexity (WikiText-2) — {{ activeModel }}</div>
      <div class="ppl-cards">
        <div class="ppl-card">
          <div class="ppl-label">FP16</div>
          <div class="ppl-value ref">{{ pplData[activeModel].fp16 }}</div>
        </div>
        <div class="ppl-arrow">→</div>
        <div class="ppl-card">
          <div class="ppl-label">MXFP4 + None</div>
          <div class="ppl-value bad">{{ pplData[activeModel].mxfp4_none }}</div>
          <div class="ppl-delta">+{{ (pplData[activeModel].mxfp4_none - pplData[activeModel].fp16).toFixed(2) }}</div>
        </div>
        <div class="ppl-arrow">vs</div>
        <div class="ppl-card">
          <div class="ppl-label">MXFP4 + LQH</div>
          <div class="ppl-value good">{{ pplData[activeModel].mxfp4_lqh }}</div>
          <div class="ppl-delta good">+{{ (pplData[activeModel].mxfp4_lqh - pplData[activeModel].fp16).toFixed(2) }}</div>
        </div>
        <div class="ppl-group-sep">|</div>
        <div class="ppl-card">
          <div class="ppl-label">NVFP4 + None</div>
          <div class="ppl-value bad">{{ pplData[activeModel].nvfp4_none }}</div>
          <div class="ppl-delta">+{{ (pplData[activeModel].nvfp4_none - pplData[activeModel].fp16).toFixed(2) }}</div>
        </div>
        <div class="ppl-arrow">vs</div>
        <div class="ppl-card">
          <div class="ppl-label">NVFP4 + LQH</div>
          <div class="ppl-value good">{{ pplData[activeModel].nvfp4_sqh }}</div>
          <div class="ppl-delta good">+{{ (pplData[activeModel].nvfp4_sqh - pplData[activeModel].fp16).toFixed(2) }}</div>
        </div>
      </div>
    </div>

    <hr class="divider" />

    <div class="inference-section">
      <div class="section-title" style="margin-bottom:12px">End-to-End Inference Output Comparison</div>
      <div class="inference-grid">
        <InferenceCard v-for="card in inferenceCards" :key="card.label" v-bind="card" />
      </div>
      <div class="inference-note">
        * Output text is representative. Actual quality differences are measured via perplexity on WikiText-2.
      </div>
    </div>
  </div>
</template>

<style scoped>
.metrics-view { padding: 24px; display: flex; flex-direction: column; gap: 20px; overflow: hidden; }
.view-header { display: flex; align-items: flex-start; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
.view-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

.model-toggle, .vram-toggle {
  display: flex;
  gap: 4px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: 6px;
  padding: 3px;
}
.toggle-btn {
  padding: 5px 14px;
  border-radius: 4px;
  border: none;
  background: none;
  color: var(--text-muted);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.toggle-btn.active {
  background: rgba(0, 229, 255, 0.15);
  color: var(--accent-cyan);
}

.charts-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  min-width: 0;
}
.vram-section { display: flex; flex-direction: column; gap: 8px; }

.ppl-row { }
.ppl-cards {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}
.ppl-card {
  padding: 16px 24px;
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius);
  text-align: center;
  min-width: 120px;
}
.ppl-label { font-size: 11px; color: var(--text-muted); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.05em; }
.ppl-value { font-size: 28px; font-weight: 700; font-family: monospace; }
.ppl-value.ref { color: var(--accent-cyan); }
.ppl-value.bad { color: #ff6b6b; }
.ppl-value.good { color: var(--accent-green); }
.ppl-delta { font-size: 12px; margin-top: 4px; color: #ff6b6b; }
.ppl-delta.good { color: var(--accent-green); }
.ppl-arrow { font-size: 20px; color: var(--text-muted); }
.ppl-group-sep { font-size: 24px; color: var(--border-color); padding: 0 4px; }

.inference-section { }
.inference-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}
.inference-note {
  margin-top: 10px;
  font-size: 11px;
  color: var(--text-dim);
  font-style: italic;
}
</style>
