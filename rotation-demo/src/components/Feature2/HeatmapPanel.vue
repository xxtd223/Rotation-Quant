<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { nvfp4QuantError, flatTo2D } from '../../composables/useQuantization.js'
import { applyTransformFull } from '../../composables/useTransformer.js'

const props = defineProps({
  title: String,
  isBaseline: Boolean,
  method: String,
  rawData: Object,
  sharedAbsMax: { type: Number, default: 0 },
})

const isLQH = computed(() => props.method === 'LQH' || props.method === 'LQ')

const wrapper = ref(null)
const el = ref(null)
const snapshotEl = ref(null)
let plotted = false
let currentSize = 0
const mae = ref(0)

// Overlay covers the panel only on first render (before any data is shown).
const overlayOpacity = ref(1)
let overlayTimer = null

function revealOverlay() {
  clearTimeout(overlayTimer)
  overlayTimer = setTimeout(() => { overlayOpacity.value = 0 }, 40)
}

// Cross-fade: snapshot opacity managed directly on the DOM element to avoid
// Vue's async reactivity causing a flash between render() and DOM update.
let snapshotTimer = null

function setSnapshotOpacity(val, withTransition) {
  if (!snapshotEl.value) return
  snapshotEl.value.style.transition = withTransition ? 'opacity 0.5s ease' : 'none'
  snapshotEl.value.style.opacity = val
}

function buildErrorMatrix() {
  if (!props.rawData) return null
  const { X, W, D, N, M, gs } = props.rawData
  const { X_prime, W_prime } = applyTransformFull(X, W, D, N, M, gs, props.method)
  const scale = 1.0
  const { error, mae: maeVal } = nvfp4QuantError(W, D, M, X, N, X_prime, W_prime, scale)
  mae.value = maeVal
  return flatTo2D(error, Math.min(M, 64), Math.min(N, 64))
}

function buildTracesAndLayout(z, absMax) {
  const traces = [{
    type: 'heatmap',
    z,
    colorscale: [
      [0,    '#e4f1e6'],
      [0.3,  '#d4a853'],
      [0.65, '#c17c5f'],
      [1,    '#8b4a3a'],
    ],
    zmin: 0,
    zmax: absMax,
    showscale: false,
  }]
  const layout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'rgba(245,242,237,0.5)',
    font: { color: '#2c2c2c', size: 11 },
    width: currentSize,
    height: currentSize,
    margin: { t: 4, b: 4, l: 4, r: 4 },
    xaxis: { showticklabels: false, showgrid: false, zeroline: false },
    yaxis: { showticklabels: false, showgrid: false, zeroline: false, autorange: 'reversed' },
  }
  return { traces, layout }
}

function render() {
  if (!el.value || !props.rawData || currentSize === 0) return
  const z = buildErrorMatrix()
  if (!z) return
  const absMax = props.sharedAbsMax > 0
    ? props.sharedAbsMax
    : Math.max(...z.flat().map(Math.abs), 1e-6)
  const { traces, layout } = buildTracesAndLayout(z, absMax)

  if (!plotted) {
    window.Plotly.newPlot(el.value, traces, layout, { displayModeBar: false, responsive: false })
    plotted = true
  } else {
    window.Plotly.react(el.value, traces, layout, { displayModeBar: false, responsive: false })
  }
}

// Cross-fade update: snapshot the current heatmap, update data, fade snapshot out.
function renderWithCrossFade() {
  if (!plotted) {
    render()
    revealOverlay()
    return
  }

  clearTimeout(snapshotTimer)

  // 1. Capture current heatmap SVG as a blob URL and show it synchronously
  //    via direct DOM manipulation — Vue reactivity is async and would cause
  //    a one-frame flash between render() and the opacity update.
  const svg = el.value?.querySelector('svg.main-svg')
  if (svg && snapshotEl.value) {
    const serialized = new XMLSerializer().serializeToString(svg)
    const blob = new Blob([serialized], { type: 'image/svg+xml' })
    const url = URL.createObjectURL(blob)
    snapshotEl.value.onload = () => URL.revokeObjectURL(url)
    snapshotEl.value.src = url
    setSnapshotOpacity(1, false)   // instant — no transition
  }

  // 2. Update heatmap data (instant, synchronous)
  render()

  // 3. After two animation frames (new heatmap is painted), fade snapshot out
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      setSnapshotOpacity(0, true)  // fade out with transition
    })
  })
}

// ResizeObserver fires whenever the wrapper's size changes, including on first layout
let ro = null
onMounted(() => {
  ro = new ResizeObserver(entries => {
    const w = Math.round(entries[0].contentRect.width)
    if (w > 0 && w !== currentSize) {
      currentSize = w
      if (plotted && el.value) {
        window.Plotly.relayout(el.value, { width: w, height: w })
      } else {
        render()
        revealOverlay()
      }
    }
  })
  if (wrapper.value) ro.observe(wrapper.value)
})

watch(() => [props.rawData, props.method, props.sharedAbsMax], renderWithCrossFade)

onUnmounted(() => {
  ro?.disconnect()
  clearTimeout(overlayTimer)
  clearTimeout(snapshotTimer)
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
  <div class="heatmap-panel panel-card" :class="{ 'lqh-highlight': isLQH }">
    <div class="panel-title">
      {{ title }}
      <span v-if="isBaseline" class="baseline-badge">Baseline</span>
      <span v-if="isLQH" class="ours-badge">Ours</span>
    </div>
    <div ref="wrapper" class="plot-wrapper">
      <div ref="el" class="plot-area" />
      <!-- SVG snapshot for cross-fade; opacity controlled directly via DOM -->
      <img ref="snapshotEl" class="snapshot-overlay" alt="" />
      <!-- Base-color overlay: only used on first render -->
      <div class="base-overlay" :style="{ opacity: overlayOpacity }" />
    </div>
    <div class="mae-row">
      <span class="mae-label">Output MAE</span>
      <span class="mae-value" :class="{ 'mae-high': mae > 0.001 }">{{ mae.toExponential(3) }}</span>
    </div>
  </div>
</template>

<style scoped>
.heatmap-panel { display: flex; flex-direction: column; min-width: 0; }

.plot-wrapper {
  position: relative;
  width: 100%;
}
.plot-area {
  /* Plotly manages its own size */
}
.snapshot-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  object-fit: fill;
  opacity: 0;
}
.base-overlay {
  position: absolute;
  inset: 0;
  background: #e4f1e6;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.mae-row {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
  font-size: 13px;
}
.mae-label { color: var(--text-muted); }
.mae-value { font-weight: 600; color: var(--primary); font-family: monospace; }
.mae-high { color: var(--terracotta); }
</style>
