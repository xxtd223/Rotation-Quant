<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  model: { type: String, default: 'Llama-3.2-3B' },
  vramType: { type: String, default: 'static' },
  visible: Boolean,
})

const el = ref(null)
let plotted = false

const FORMATS = ['MXFP4', 'NVFP4']
const METHODS = ['None', '+ Hadamard', '+ LQH']
const COLORS  = ['#4F9DA3', '#FFC000', '#C00000']

const DATA = {
  static: {
    'Llama-3.2-3B': [[26.56, 27.30, 27.30], [28.12, 28.50, 28.50]],
    'Qwen3-8B':     [[26.56, 27.08, 27.08], [28.20, 28.46, 28.46]],
  },
  peak: {
    'Llama-3.2-3B': [[26.56, 27.17, 27.17], [28.12, 28.43, 28.43]],
    'Qwen3-8B':     [[26.56, 27.04, 27.04], [28.12, 28.36, 28.36]],
  },
}

function buildTraces() {
  const modelData = DATA[props.vramType][props.model]
  return METHODS.map((method, j) => ({
    type: 'bar',
    name: method,
    x: FORMATS,
    y: FORMATS.map((_, k) => modelData[k][j]),
    marker: { color: COLORS[j], line: { color: '#000', width: 1 } },
    width: 0.2,
    offset: (j - 1) * 0.22,
  }))
}

function buildLayout() {
  return {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'rgba(13,17,23,0.6)',
    font: { color: '#e0e0e0', size: 11 },
    margin: { t: 10, b: 50, l: 55, r: 10 },
    xaxis: { title: 'Format', gridcolor: '#1e2a3a', tickfont: { size: 12 } },
    yaxis: {
      title: `${props.vramType === 'static' ? 'Static' : 'Peak'} VRAM Usage (%)`,
      gridcolor: '#1e2a3a',
      range: [24, 30],
    },
    legend: { orientation: 'h', y: -0.2, font: { size: 11 } },
    barmode: 'overlay',
  }
}

const ANIM = {
  transition: { duration: 450, easing: 'cubic-in-out' },
  frame: { duration: 450, redraw: false },
}

function render() {
  if (!el.value) return
  const traces = buildTraces()
  const layout = buildLayout()
  if (!plotted) {
    const zeroTraces = traces.map(t => ({ ...t, y: t.y.map(() => 0) }))
    window.Plotly.newPlot(el.value, zeroTraces, layout, { displayModeBar: false, responsive: true })
    plotted = true
    window.Plotly.animate(el.value, { data: traces }, ANIM)
  } else {
    // Layout may change (y-axis title), update it then animate bars
    window.Plotly.relayout(el.value, { 'yaxis.title': layout.yaxis.title })
    window.Plotly.animate(el.value, { data: traces }, ANIM)
  }
}

onMounted(render)
watch(() => [props.model, props.vramType, props.visible], () => {
  if (props.visible) setTimeout(render, 50)
  else render()
})
onUnmounted(() => { if (el.value) window.Plotly.purge(el.value); plotted = false })
defineExpose({ resize: () => el.value && window.Plotly.Plots.resize(el.value) })
</script>

<template>
  <div class="chart-card panel-card">
    <div class="panel-title">
      {{ vramType === 'static' ? 'Static' : 'Peak' }} VRAM Usage (%)
    </div>
    <div ref="el" class="plot-area" />
  </div>
</template>

<style scoped>
.chart-card { display: flex; flex-direction: column; }
.plot-area { height: 300px; width: 100%; }
</style>
