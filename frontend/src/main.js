import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import ECharts from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart, PieChart, GaugeChart, ScatterChart, RadarChart } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, TitleComponent, LegendComponent,
  VisualMapComponent, DataZoomComponent, MarkLineComponent, MarkPointComponent,
} from 'echarts/components'

import App from './App.vue'
import router from './router'
import './style.css'

use([
  CanvasRenderer,
  LineChart, BarChart, PieChart, GaugeChart, ScatterChart, RadarChart,
  GridComponent, TooltipComponent, TitleComponent, LegendComponent,
  VisualMapComponent, DataZoomComponent, MarkLineComponent, MarkPointComponent,
])

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)
app.use(ElementPlus, { locale: zhCn })
for (const [k, v] of Object.entries(ElementPlusIconsVue)) {
  app.component(k, v)
}
app.component('VChart', ECharts)
app.mount('#app')
