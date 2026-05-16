import { createApp } from 'vue'
import App from './App.vue'
import './assets/theme.css'
import Plotly from 'plotly.js-dist-min'

window.Plotly = Plotly

createApp(App).mount('#app')
