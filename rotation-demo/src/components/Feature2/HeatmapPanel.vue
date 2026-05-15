<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { nvfp4QuantError, flatTo2D } from '../../composables/useQuantization.js'
import { applyTransformFull } from '../../composables/useTransformer.js'

const props = defineProps({
  title: String,
  isBaseline: Boolean,
  method: String,
  rawData: Object,
  sharedAbsMax: { type: Number, default: 0 },
})

const wrapper = ref(null)   // the square wrapper div
const el = ref(null)        // the Plotly target div
let plotted = false
let currentSize = 0
const mae = ref(0)

function buildErrorMatrix() {
  if (!props.rawData) return null
  const { X, W, D, N, M, gs } = props.rawData
  const { X_prime, W_prime } = applyTransformFull(X, W, D, N, M, gs, props.method)
  const { error, mae: maeVal } = nvfp4QuantError(W, D, M, X, N, X_prime, W_prime)
  mae.value = maeVal
  return flatTo2D(error, Math.min(M, 64), Math.min(N, 64))
}

function render() {
  if (!el.value || !props.rawData || currentSize === 0) return
  const z = buildErrorMatrix()
  if (!z) return

  const absMax = props.sharedAbsMax > 0
    ? props.sharedAbsMax
    : Math.max(...z.flat().map(Math.abs), 1e-6)

  const traces = [{
    type: 'heatmap',
    z,
    colorscale: [
      [0,   '#0d1117'],
      [0.2, '#1a3a5c'],
      [0.5, '#FFC000'],
      [0.8, '#ff6b35'],
      [1,   '#C00000'],
    ],
    zmin: 0,
    zmax: absMax,
    showscale: false,
  }]

  const layout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'rgba(13,17,23,0.6)',
    font: { color: '#e0e0e0', size: 11 },
    width: currentSize,
    height: currentSize,
    margin: { t: 4, b: 4, l: 4, r: 4 },
    xaxis: { showticklabels: false, showgrid: false, zeroline: false },
    yaxis: { showticklabels: false, showgrid: false, zeroline: false, autorange: 'reversed' },
  }

  const transition = { duration: 350, easing: 'cubic-in-out' }
  if (!plotted) {
    window.Plotly.newPlot(el.value, traces, layout, { displayModeBar: false, responsive: false })
    plotted = true
  } else {
    window.Plotly.react(el.value, traces, layout, { displayModeBar: false, responsive: false })
    window.Plotly.animate(el.value, { data: traces }, { transition, frame: { duration: 350 } })
  }
}

// ResizeObserver fires whenever the wrapper's size changes, including on first layout
let ro = null
onMounted(() => {
  ro = new ResizeObserver(entries => {
    const w = Math.round(entries[0].contentRect.width)
    if (w > 0 && w !== currentSize) {
      currentSize = w
      // If already plotted, just resize; otherwise do a full render
      if (plotted && el.value) {
        window.Plotly.relayout(el.value, { width: w, height: w })
      } else {
        render()
      }
    }
  })
  if (wrapper.value) ro.observe(wrapper.value)
})

watch(() => [props.rawData, props.method, props.sharedAbsMax], render)

onUnmounted(() => {
  ro?.disconnect()
  if (el.value) window.Plotly.purge(el.value)
  plotted = false
  currentSize = 0
})

defineExpose({
  resize: () => {
    if (!wrapper.value || !el.value) return
    const w = Math.round(wrapper.value.getBoundingClientRect().width)
    if (w > 0) {
      currentSize = w
      window.Plotly.relayout(el.value, { width: w, height: w })
    }
  }
})
</script>

<template>
  <div class="heatmap-panel panel-card">
    <div class="panel-title">
      {{ title }}
      <span v-if="isBaseline" class="baseline-badge">Baseline</span>
    </div>
    <!-- wrapper is observed by ResizeObserver; its width drives the square size -->
    <div ref="wrapper" class="plot-wrapper">
      <div ref="el" class="plot-area" />
    </div>
    <div class="mae-row">
      <span class="mae-label">Output MAE</span>
      <span class="mae-value" :class="{ 'mae-high': mae > 0.001 }">{{ mae.toExponential(3) }}</span>
    </div>
  </div>
</template>

<style scoped>
.heatmap-panel { display: flex; flex-direction: column; min-width: 0; }

/* The wrapper just needs a width; height is set by Plotly via layout.height = width */
.plot-wrapper {
  width: 100%;
}
.plot-area {
  /* Plotly manages its own size; no CSS height needed */
}

.mae-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 12px;
}
.mae-label { color: var(--text-muted); }
.mae-value { font-weight: 700; color: var(--accent-green); font-family: monospace; }
.mae-high { color: #ff6b6b; }
</style>
