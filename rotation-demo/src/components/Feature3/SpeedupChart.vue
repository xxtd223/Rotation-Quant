<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  model: { type: String, default: 'Llama-3.2-3B' },
  visible: Boolean,
})

const el = ref(null)
let plotted = false

const FORMATS = ['MXFP4', 'NVFP4']
const METHODS = ['None', '+ Hadamard', '+ LQH']
const COLORS  = ['#4A7C59', '#D4A853', '#C17C5F']

const DATA = {
  'Llama-3.2-3B': [[6.77, 6.00, 5.89], [6.27, 5.67, 5.58]],
  'Qwen3-8B':     [[6.66, 6.09, 6.01], [6.24, 5.84, 5.77]],
}

function buildTraces() {
  const modelData = DATA[props.model]
  const bars = METHODS.map((method, j) => ({
    type: 'bar',
    name: method,
    x: FORMATS,
    y: FORMATS.map((_, k) => modelData[k][j]),
    marker: {
      color: COLORS[j],
      line: { color: '#333', width: 1 },
    },
    width: 0.2,
    offset: (j - 1) * 0.22,
  }))
  return [...bars, LEGEND_TRACE]
}

const layout = {
  paper_bgcolor: 'transparent',
  plot_bgcolor: 'rgba(245,242,237,0.5)',
  font: { color: '#2c2c2c', size: 12 },
  margin: { t: 10, b: 50, l: 50, r: 10 },
  xaxis: { title: 'Format', gridcolor: '#e0d9cf', tickfont: { size: 12 } },
  yaxis: { title: 'Speedup vs FP16', gridcolor: '#e0d9cf', range: [0, 8] },
  legend: { orientation: 'h', y: -0.2, font: { size: 11 } },
  barmode: 'overlay',
  shapes: [{
    type: 'line',
    xref: 'paper', x0: 0, x1: 1,
    yref: 'y',     y0: 1, y1: 1,
    line: { color: '#6b6b6b', dash: 'dash', width: 1.2 },
  }],
}

const LEGEND_TRACE = {
  type: 'scatter',
  x: [null], y: [null],
  mode: 'lines',
  line: { color: '#6b6b6b', dash: 'dash', width: 1.2 },
  name: 'FP16 Baseline',
  showlegend: true,
}

const ANIM = {
  transition: { duration: 450, easing: 'cubic-in-out' },
  frame: { duration: 450, redraw: false },
}

function render() {
  if (!el.value) return
  const traces = buildTraces()
  if (!plotted) {
    // Render with zero-height bars first, then animate to real values
    const zeroTraces = traces.map(t =>
      t.type === 'bar' ? { ...t, y: t.y.map(() => 0) } : t
    )
    window.Plotly.newPlot(el.value, zeroTraces, layout, { displayModeBar: false, responsive: true })
    plotted = true
    window.Plotly.animate(el.value, { data: traces }, ANIM)
  } else {
    window.Plotly.animate(el.value, { data: traces }, ANIM)
  }
}

onMounted(render)
watch(() => [props.model, props.visible], () => {
  if (props.visible) setTimeout(render, 50)
  else render()
})
onUnmounted(() => { if (el.value) window.Plotly.purge(el.value); plotted = false })
defineExpose({ resize: () => el.value && window.Plotly.Plots.resize(el.value) })
</script>

<template>
  <div class="chart-card panel-card">
    <div class="panel-title">Speedup vs FP16 Baseline</div>
    <div ref="el" class="plot-area" />
  </div>
</template>

<style scoped>
.chart-card { display: flex; flex-direction: column; }
.plot-area { height: 300px; width: 100%; }
</style>
