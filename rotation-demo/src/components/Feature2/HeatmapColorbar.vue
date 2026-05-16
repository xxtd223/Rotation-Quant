<script setup>
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'

const props = defineProps({
  absMax: { type: Number, default: 1 },
})

const el = ref(null)
let plotted = false

function render() {
  if (!el.value) return

  const traces = [{
    type: 'heatmap',
    z: [[props.absMax || 1]],
    colorscale: [
      [0,    '#e4f1e6'],
      [0.3,  '#d4a853'],
      [0.65, '#c17c5f'],
      [1,    '#8b4a3a'],
    ],
    zmin: 0,
    zmax: props.absMax || 1,
    showscale: true,
    colorbar: {
      tickfont: { color: '#6b6b6b', size: 10 },
      title: { text: '|Error|', font: { color: '#6b6b6b', size: 10 }, side: 'right' },
      thickness: 12,
      len: 0.85,
      x: 0.05,
      xanchor: 'left',
      tickformat: '.2e',
    },
    opacity: 0,
  }]

  const layout = {
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    margin: { t: 4, b: 4, l: 4, r: 4 },
    xaxis: { visible: false },
    yaxis: { visible: false },
  }

  if (!plotted) {
    nextTick(() => requestAnimationFrame(() => {
      if (!el.value) return
      window.Plotly.newPlot(el.value, traces, layout, { displayModeBar: false, responsive: true })
      plotted = true
    }))
  } else {
    window.Plotly.react(el.value, traces, layout, { displayModeBar: false, responsive: true })
  }
}

onMounted(render)
watch(() => props.absMax, render)
onUnmounted(() => {
  if (el.value) window.Plotly.purge(el.value)
  plotted = false
})
</script>

<template>
  <div class="colorbar-wrap">
    <div ref="el" class="colorbar-plot" />
  </div>
</template>

<style scoped>
.colorbar-wrap {
  width: 70px;
  flex-shrink: 0;
  /* Fixed height matches typical panel height; avoids 0-height on first render */
  min-height: 300px;
  display: flex;
  align-items: stretch;
}
.colorbar-plot {
  width: 100%;
  height: 100%;
}
</style>
