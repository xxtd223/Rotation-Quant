<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  values: Float32Array,
  title: String,
  isBaseline: Boolean,
  color: { type: String, default: '#4fc3f7' },
})

const el = ref(null)
let plotted = false

const N_BINS = 60   // number of histogram bins
const KDE_PTS = 150 // KDE evaluation points

// Pre-compute histogram as fixed-bin bar trace so Plotly can animate y values.
// x-axis is always symmetric around 0: range = [-absMax*1.15, +absMax*1.15]
function computeHistAndKDE(values) {
  if (!values || values.length === 0) return null
  const arr = Array.from(values)
  const n = arr.length

  // Determine symmetric range around 0
  let absMax = 0
  for (const v of arr) if (Math.abs(v) > absMax) absMax = Math.abs(v)
  absMax = absMax * 1.15 + 1e-8   // 15% padding

  const lo = -absMax, hi = absMax
  const binWidth = (hi - lo) / N_BINS

  // Bin counts
  const counts = new Array(N_BINS).fill(0)
  for (const v of arr) {
    const idx = Math.floor((v - lo) / binWidth)
    if (idx >= 0 && idx < N_BINS) counts[idx]++
  }

  // Convert to probability density
  const binCenters = Array.from({ length: N_BINS }, (_, i) => lo + (i + 0.5) * binWidth)
  const density = counts.map(c => c / (n * binWidth))

  // KDE (Silverman bandwidth)
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

  return { binCenters, density, binWidth, kdeX, kdeY, absMax }
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
      line: { color: '#ff6b6b', width: 2, shape: 'spline', smoothing: 0.8 },
      name: 'KDE',
      showlegend: false,
    },
  ]
}

// Build layout with x-axis fixed symmetrically around 0
function buildLayout(values) {
  const result = computeHistAndKDE(values)
  const absMax = result ? result.absMax : 1
  return {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'rgba(13,17,23,0.6)',
    font: { color: '#e0e0e0', size: 11 },
    margin: { t: 10, b: 40, l: 44, r: 10 },
    xaxis: {
      title: 'Value',
      range: [-absMax, absMax],
      gridcolor: '#1e2a3a',
      zerolinecolor: '#4a5568',
      zerolinewidth: 1.5,
      automargin: true,
    },
    yaxis: {
      title: 'Density',
      gridcolor: '#1e2a3a',
      zerolinecolor: '#30363d',
    },
    bargap: 0.02,
    transition: { duration: 450, easing: 'cubic-in-out' },
  }
}

const config = { displayModeBar: false, responsive: true }

function render() {
  if (!el.value || !props.values) return
  const traces = buildTraces(props.values)
  const layout = buildLayout(props.values)

  if (!plotted) {
    window.Plotly.newPlot(el.value, traces, layout, config)
    plotted = true
  } else {
    // Use Plotly.animate for smooth bar height + KDE line transitions.
    // Also update layout (x-axis range) via react first so the axis rescales smoothly.
    window.Plotly.react(el.value, traces, layout, config)
    window.Plotly.animate(
      el.value,
      { data: traces, layout },
      {
        transition: { duration: 450, easing: 'cubic-in-out' },
        frame: { duration: 450, redraw: false },
      }
    )
  }
}

onMounted(render)
watch(() => props.values, render)
onUnmounted(() => { if (el.value) window.Plotly.purge(el.value); plotted = false })
defineExpose({ resize: () => el.value && window.Plotly.Plots.resize(el.value) })
</script>

<template>
  <div class="dist-panel panel-card">
    <div class="panel-title">
      {{ title }}
      <span v-if="isBaseline" class="baseline-badge">Baseline</span>
    </div>
    <div ref="el" class="plot-area" />
  </div>
</template>

<style scoped>
.dist-panel { display: flex; flex-direction: column; min-width: 0; }
.plot-area { height: 280px; width: 100%; }
</style>
