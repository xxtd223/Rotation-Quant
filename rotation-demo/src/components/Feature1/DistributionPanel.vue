<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  values: Float32Array,
  title: String,
  isBaseline: Boolean,
  isLQH: { type: Boolean, default: false },
  color: { type: String, default: '#4A7C59' },
})

const el = ref(null)
let plotted = false
let pendingRender = null

const N_BINS = 60
const KDE_PTS = 150

function computeHistAndKDE(values) {
  if (!values || values.length === 0) return null
  const arr = Array.from(values)
  const n = arr.length

  let absMax = 0
  for (const v of arr) if (Math.abs(v) > absMax) absMax = Math.abs(v)
  absMax = absMax * 1.15 + 1e-8

  const lo = -absMax, hi = absMax
  const binWidth = (hi - lo) / N_BINS

  const counts = new Array(N_BINS).fill(0)
  for (const v of arr) {
    const idx = Math.floor((v - lo) / binWidth)
    if (idx >= 0 && idx < N_BINS) counts[idx]++
  }

  const binCenters = Array.from({ length: N_BINS }, (_, i) => lo + (i + 0.5) * binWidth)
  const density = counts.map(c => c / (n * binWidth))

  const mean = arr.reduce((a, b) => a + b, 0) / n
  const std = Math.sqrt(arr.reduce((a, b) => a + (b - mean) ** 2, 0) / n) + 1e-8
  const h = 1.06 * std * Math.pow(n, -0.2)

  const kdeStep = (hi - lo) / KDE_PTS
  const kdeX = [], kdeY = []
  for (let i = 0; i <= KDE_PTS; i++) {
    const x = lo + i * kdeStep
    let d = 0
    for (const xi of arr) {
      const u = (x - xi) / h
      d += Math.exp(-0.5 * u * u)
    }
    kdeX.push(x)
    kdeY.push(d / (n * h * Math.sqrt(2 * Math.PI)))
  }

  const maxDensity = Math.max(...density, ...kdeY)
  return { binCenters, density, binWidth, kdeX, kdeY, absMax, maxDensity }
}

function buildTraces(values) {
  const result = computeHistAndKDE(values)
  if (!result) return []
  const { binCenters, density, binWidth, kdeX, kdeY } = result
  return [
    {
      type: 'bar',
      x: binCenters,
      y: density,
      width: binWidth * 0.95,
      opacity: 0.6,
      marker: { color: props.color, line: { color: 'transparent', width: 0 } },
      name: 'Histogram',
      showlegend: false,
    },
    {
      type: 'scatter',
      x: kdeX,
      y: kdeY,
      mode: 'lines',
      line: { color: '#C17C5F', width: 1.8, shape: 'spline', smoothing: 0.8 },
      name: 'KDE',
      showlegend: false,
    },
  ]
}

function buildLayout(values) {
  const result = computeHistAndKDE(values)
  const absMax = result ? result.absMax : 1
  const maxDensity = result ? result.maxDensity : 1
  return {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'rgba(245,242,237,0.5)',
    font: { color: '#2c2c2c', size: 12 },
    margin: { t: 10, b: 40, l: 44, r: 10 },
    xaxis: {
      title: 'Value',
      range: [-absMax, absMax],
      gridcolor: '#e0d9cf',
      zerolinecolor: '#c8c0b4',
      zerolinewidth: 1.2,
      automargin: true,
    },
    yaxis: {
      title: 'Density',
      range: [0, maxDensity * 1.2],
      gridcolor: '#e0d9cf',
      zerolinecolor: '#e0d9cf',
    },
    bargap: 0.02,
  }
}

const config = { displayModeBar: false, responsive: true }

const ANIM = {
  transition: { duration: 500, easing: 'cubic-in-out' },
  frame: { duration: 500, redraw: false },
}

const AXIS_DUR = 280

function render() {
  if (!el.value || !props.values) return

  // Cancel any pending phase-2 from a previous render
  if (pendingRender) { clearTimeout(pendingRender); pendingRender = null }

  const traces = buildTraces(props.values)
  const layout = buildLayout(props.values)

  if (!plotted) {
    const zeroTraces = [
      { ...traces[0], y: traces[0].y.map(() => 0) },
      { ...traces[1], y: traces[1].y.map(() => 0) },
    ]
    window.Plotly.newPlot(el.value, zeroTraces, layout, config)
    plotted = true
    window.Plotly.animate(el.value, { data: traces }, ANIM)
  } else {
    // Phase 1: commit + animate axis ranges via react+transition.
    // react properly writes the new layout into Plotly's internal state so
    // nothing can revert it, while layout.transition drives the SVG animation.
    // We pass the OLD trace data so bars don't move yet.
    const currentData = el.value.data   // Plotly stores current traces here
    window.Plotly.react(el.value, currentData, {
      ...layout,
      transition: { duration: AXIS_DUR, easing: 'cubic-in-out' },
    }, config)

    // Phase 2: after axes have settled, animate bar heights
    pendingRender = setTimeout(() => {
      pendingRender = null
      window.Plotly.animate(el.value, { data: traces }, ANIM)
    }, AXIS_DUR + 20)
  }
}

onMounted(render)
watch(() => props.values, render)
onUnmounted(() => {
  if (pendingRender) clearTimeout(pendingRender)
  if (el.value) window.Plotly.purge(el.value)
  plotted = false
})
defineExpose({ resize: () => el.value && window.Plotly.Plots.resize(el.value) })
</script>

<template>
  <div class="dist-panel panel-card" :class="{ 'lqh-highlight': isLQH }">
    <div class="panel-title">
      {{ title }}
      <span v-if="isBaseline" class="baseline-badge">Baseline</span>
      <span v-if="isLQH" class="ours-badge">Ours</span>
    </div>
    <div ref="el" class="plot-area" />
  </div>
</template>

<style scoped>
.dist-panel { display: flex; flex-direction: column; min-width: 0; }
.plot-area { height: 280px; width: 100%; }
</style>
