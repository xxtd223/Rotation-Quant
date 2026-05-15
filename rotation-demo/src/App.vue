<script setup>
import { ref } from 'vue'
import NavTabs from './components/NavTabs.vue'
import DistributionView from './components/Feature1/DistributionView.vue'
import HeatmapView from './components/Feature2/HeatmapView.vue'
import MetricsView from './components/Feature3/MetricsView.vue'
import HardwareDashboard from './components/Feature4/HardwareDashboard.vue'

const activeTab = ref('dist')
</script>

<template>
  <div class="app-shell">
    <NavTabs v-model:active="activeTab" />

    <main class="app-main">
      <DistributionView  v-show="activeTab === 'dist'"    :visible="activeTab === 'dist'" />
      <HeatmapView       v-show="activeTab === 'heatmap'" :visible="activeTab === 'heatmap'" />
      <MetricsView       v-show="activeTab === 'metrics'" :visible="activeTab === 'metrics'" />
      <HardwareDashboard v-show="activeTab === 'hw'"      :visible="activeTab === 'hw'" />
    </main>
  </div>
</template>

<style>
.app-shell {
  min-height: 100vh;
  background: var(--bg-primary);
  display: flex;
  flex-direction: column;
}
.app-main {
  flex: 1;
  overflow-y: auto;
}
</style>
