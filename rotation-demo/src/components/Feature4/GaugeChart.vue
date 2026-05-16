<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  valueMin: { type: Number, default: 26.56 },
  valueMax: { type: Number, default: 28.50 },
  visible: Boolean,
})

const el = ref(null)
let plotted = false

function render() {
  if (!el.value) return

  const traces = [{
    type: 'indicator',
    mode: 'gauge+number',
    value: props.valueMin,
    number: { suffix: '%', font: { size: 34, color: '#4A7C59' } },
    gauge: {
      axis: {
        range: [0, 100],
        tickwidth: 1,
        tickcolor: '#e0d9cf',
        tickfont: { color: '#6b6b6b', size: 10 },
        nticks: 6,
      },
      bar: { color: '#4A7C59', thickness: 0.22 },
      bgcolor: 'transparent',
      borderwidth: 0,
      steps: [
        { range: [0, props.valueMin],  color: 'rgba(74,124,89,0.08)' },
        { range: [props.valueMin, props.valueMax], color: 'rgba(74,124,89,0.22)' },
        { range: [props.valueMax, 100], color: 'rgba(193,124,95,0.06)' },
      ],
      threshold: {
        line: { color: '#C17C5F', width: 1.5 },
        thickness: 0.75,
        value: 100,
      },
    },
    title: {
      text: `Memory Footprint<br><span style="font-size:12px;color:#6b6b6b">Range: ${props.valueMin}% – ${props.valueMax}%</span>`,
      font: { color: '#2c2c2c', size: 14 },
    },
  }]

  const layout = {
    paper_bgcolor: 'transparent',
    font: { color: '#2c2c2c' },
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
