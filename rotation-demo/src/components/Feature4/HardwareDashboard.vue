<script setup>
import { ref, onMounted, watch } from 'vue'
import GaugeChart from './GaugeChart.vue'
import ProgressBar from './ProgressBar.vue'
import { useAnimatedCounter } from '../../composables/useAnimatedCounter.js'

const props = defineProps({ visible: Boolean })

const gauge = ref(null)

const { value: compressionRatio, start: startCR } = useAnimatedCounter(3.7, 1)
const { value: peakSpeedup,      start: startPS } = useAnimatedCounter(6.77, 2)
const { value: blockSize,        start: startBS } = useAnimatedCounter(16, 0)
const { value: precision,        start: startPR } = useAnimatedCounter(94, 0)

function startAll() {
  startCR(); startPS(); startBS(); startPR()
  setTimeout(() => gauge.value?.resize(), 100)
}

onMounted(() => {
  if (props.visible) startAll()
})

watch(() => props.visible, (v) => {
  if (v) startAll()
})

const progressBars = [
  { label: 'Memory Compression', percent: 73, colorClass: '', detail: 'FP16 (100%) → FP4 (27%) — 3.7× reduction' },
  { label: 'Compute Speedup',    percent: 85, colorClass: 'orange', detail: 'Up to 6.77× vs FP16 on MXFP4 (Llama-3.2-3B)' },
  { label: 'Precision Retention',percent: 94, colorClass: 'green',  detail: 'Perplexity degradation < 0.4 with LQH rotation' },
]

const stats = [
  { label: 'Compression Ratio', value: compressionRatio, suffix: '×', icon: '🗜️' },
  { label: 'Peak Speedup',      value: peakSpeedup,      suffix: '×', icon: '⚡' },
  { label: 'FP4 Block Size',    value: blockSize,        suffix: '',  icon: '📦' },
  { label: 'Precision Retained',value: precision,        suffix: '%', icon: '🎯' },
]

// Bit-width comparison data
const bitComparison = [
  { format: 'FP16',  bits: 16,  color: '#ff6b6b', pct: 100 },
  { format: 'BF16',  bits: 16,  color: '#FFC000', pct: 100 },
  { format: 'FP4',   bits: 4,   color: '#00e5ff', pct: 25 },
  { format: 'NVFP4', bits: 4.5, color: '#69db7c', pct: 28.125 },
]
</script>

<template>
  <div class="hw-dashboard">
    <div class="view-header">
      <div class="section-title">Hardware Dashboard</div>
      <p class="view-desc">Memory compression, compute efficiency, and precision metrics for FP4 quantization</p>
    </div>

    <!-- Stat counters row -->
    <div class="stats-grid">
      <div v-for="stat in stats" :key="stat.label" class="stat-card panel-card pulse-glow">
        <div class="stat-icon">{{ stat.icon }}</div>
        <div class="stat-value glow-text">{{ stat.value }}{{ stat.suffix }}</div>
        <div class="stat-label">{{ stat.label }}</div>
      </div>
    </div>

    <!-- Main content: gauge + progress bars -->
    <div class="main-row">
      <div class="gauge-section panel-card">
        <GaugeChart ref="gauge" :value="27" :visible="visible" />
        <div class="gauge-annotation">
          <span class="ann-fp16">FP16 = 100%</span>
          <span class="ann-arrow">→</span>
          <span class="ann-fp4">FP4 ≈ 27%</span>
        </div>
      </div>

      <div class="progress-section panel-card">
        <div class="section-title" style="margin-bottom:20px">Efficiency Metrics</div>
        <div class="progress-list">
          <ProgressBar
            v-for="bar in progressBars"
            :key="bar.label"
            v-bind="bar"
          />
        </div>
      </div>
    </div>

    <!-- Bit-width comparison -->
    <div class="bitwidth-section panel-card">
      <div class="section-title" style="margin-bottom:16px">Bit-Width Comparison</div>
      <div class="bitwidth-grid">
        <div v-for="item in bitComparison" :key="item.format" class="bitwidth-item">
          <div class="bw-label">{{ item.format }}</div>
          <div class="bw-bar-track">
            <div
              class="bw-bar-fill"
              :style="{ width: item.pct + '%', background: item.color }"
            />
          </div>
          <div class="bw-bits" :style="{ color: item.color }">{{ item.bits }}-bit</div>
        </div>
      </div>
    </div>

    <!-- Format detail cards -->
    <div class="format-cards">
      <div class="format-card panel-card">
        <div class="fc-header">
          <span class="fc-badge mxfp4">MXFP4</span>
          <span class="fc-sub">Microscaling FP4</span>
        </div>
        <div class="fc-spec">1S · 2E · 1M + 8E shared scale</div>
        <div class="fc-spec">Block size: 32 elements</div>
        <div class="fc-spec">Values: {0, ±0.5, ±1, ±1.5, ±2, ±3, ±4, ±6}</div>
        <div class="fc-metric">Speedup: up to <strong>6.77×</strong></div>
      </div>
      <div class="format-card panel-card">
        <div class="fc-header">
          <span class="fc-badge nvfp4">NVFP4</span>
          <span class="fc-sub">NVIDIA FP4 (Blackwell)</span>
        </div>
        <div class="fc-spec">1S · 2E · 1M + E4M3 shared scale</div>
        <div class="fc-spec">Block size: 16 elements</div>
        <div class="fc-spec">Scale: E4M3 precision (3-bit mantissa)</div>
        <div class="fc-metric">Speedup: up to <strong>6.27×</strong></div>
      </div>
      <div class="format-card panel-card">
        <div class="fc-header">
          <span class="fc-badge lqh">LQH Rotation</span>
          <span class="fc-sub">Linear Quantization Helper</span>
        </div>
        <div class="fc-spec">SQH: Symmetric + Hadamard</div>
        <div class="fc-spec">Spreads outliers across blocks</div>
        <div class="fc-spec">Equalizes W and X variance</div>
        <div class="fc-metric">PPL improvement: <strong>~0.9</strong></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.hw-dashboard { padding: 24px; display: flex; flex-direction: column; gap: 20px; }
.view-desc { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}
.stat-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 20px 12px;
  text-align: center;
}
.stat-icon { font-size: 24px; }
.stat-value {
  font-size: 32px;
  font-weight: 700;
  font-family: monospace;
  color: var(--accent-cyan);
  line-height: 1;
}
.stat-label { font-size: 11px; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.06em; }

.main-row {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 16px;
}
.gauge-section { display: flex; flex-direction: column; align-items: center; }
.gauge-annotation {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  margin-top: 4px;
}
.ann-fp16 { color: #ff6b6b; font-weight: 600; }
.ann-arrow { color: var(--text-muted); }
.ann-fp4 { color: var(--accent-cyan); font-weight: 600; }

.progress-section { }
.progress-list { display: flex; flex-direction: column; gap: 20px; }

.bitwidth-section { }
.bitwidth-grid { display: flex; flex-direction: column; gap: 10px; }
.bitwidth-item { display: grid; grid-template-columns: 60px 1fr 60px; align-items: center; gap: 12px; }
.bw-label { font-size: 12px; color: var(--text-muted); font-weight: 600; }
.bw-bar-track {
  height: 10px;
  background: var(--bg-secondary);
  border-radius: 5px;
  overflow: hidden;
  border: 1px solid var(--border-color);
}
.bw-bar-fill {
  height: 100%;
  border-radius: 5px;
  transition: width 1.2s ease-out;
  opacity: 0.85;
}
.bw-bits { font-size: 11px; font-weight: 700; font-family: monospace; text-align: right; }

.format-cards {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 16px;
}
.format-card { display: flex; flex-direction: column; gap: 8px; }
.fc-header { display: flex; align-items: center; gap: 8px; }
.fc-badge {
  font-size: 11px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: 0.04em;
}
.fc-badge.mxfp4 { background: rgba(79,195,247,0.15); color: #4fc3f7; border: 1px solid rgba(79,195,247,0.3); }
.fc-badge.nvfp4  { background: rgba(105,219,124,0.15); color: #69db7c; border: 1px solid rgba(105,219,124,0.3); }
.fc-badge.lqh    { background: rgba(0,229,255,0.12); color: #00e5ff; border: 1px solid rgba(0,229,255,0.3); }
.fc-sub { font-size: 11px; color: var(--text-muted); }
.fc-spec { font-size: 12px; color: var(--text-muted); padding-left: 4px; }
.fc-metric { font-size: 13px; color: var(--text-primary); margin-top: 4px; padding-top: 8px; border-top: 1px solid var(--border-color); }
</style>
