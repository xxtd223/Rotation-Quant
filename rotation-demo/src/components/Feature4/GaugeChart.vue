<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  value: { type: Number, default: 27 },
  visible: Boolean,
})

const el = ref(null)
let plotted = false

function render() {
  if (!el.value) return

  const traces = [{
    type: 'indicator',
    mode: 'gauge+number+delta',
    value: props.value,
    delta: { reference: 100, valueformat: '.0f', suffix: '%', increasing: { color: '#ff6b6b' }, decreasing: { color: '#69db7c' } },
    number: { suffix: '%', font: { size: 36, color: '#00e5ff' } },
    gauge: {
      axis: {
        range: [0, 100],
        tickwidth: 1,
        tickcolor: '#30363d',
        tickfont: { color: '#8b949e', size: 10 },
        nticks: 6,
      },
      bar: { color: '#00e5ff', thickness: 0.25 },
      bgcolor: 'transparent',
      borderwidth: 0,
      steps: [
        { range: [0, props.value], color: 'rgba(0,229,255,0.08)' },
        { range: [props.value, 100], color: 'rgba(255,107,107,0.06)' },
      ],
      threshold: {
        line: { color: '#ff6b6b', width: 2 },
        thickness: 0.75,
        value: 100,
      },
    },
    title: { text: 'Memory Footprint<br><span style="font-size:12px;color:#8b949e">FP16 → FP4 Compression</span>', font: { color: '#e0e0e0', size: 14 } },
  }]

  const layout = {
    paper_bgcolor: 'transparent',
    font: { color: '#e0e0e0' },
    margin: { t: 60, b: 20, l: 20, r: 20 },
    height: 260,
  }

  if (!plotted) {
    window.Plotly.newPlot(el.value, traces, layout, { displayModeBar: false, responsive: true })
    plotted = true
  } else {
    window.Plotly.react(el.value, traces, layout)
  }
}

onMounted(render)
watch(() => props.visible, (v) => { if (v) setTimeout(render, 50) })
onUnmounted(() => { if (el.value) window.Plotly.purge(el.value); plotted = false })
defineExpose({ resize: () => el.value && window.Plotly.Plots.resize(el.value) })
</script>

<template>
  <div ref="el" class="gauge-el" />
</template>

<style scoped>
.gauge-el { width: 100%; }
</style>
