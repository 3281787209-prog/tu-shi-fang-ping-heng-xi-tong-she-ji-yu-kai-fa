<template>
  <div class="dashboard-page">
    <!-- 顶部标题行 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">
          <el-icon :size="22" color="#3b82f6"><DataAnalysis /></el-icon>
          业务首页总览
        </h2>
        <p class="page-subtitle">古贤黄河水利枢纽 · 坝肩左岸边坡开挖工程数字化管理平台</p>
      </div>
      <div class="header-right">
        <el-tag type="info" effect="plain" round>
          <el-icon><Clock /></el-icon>
          &nbsp;{{ currentTime }}
        </el-tag>
      </div>
    </div>

    <!-- 8个统计卡片 -->
    <div class="stat-cards">
      <div v-for="(card, idx) in statCards" :key="idx" class="stat-card" :class="card.colorClass">
        <div class="stat-icon">
          <el-icon :size="26"><component :is="card.icon" /></el-icon>
        </div>
        <div class="stat-info">
          <div class="stat-value">{{ card.value }}</div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
        <div class="stat-trend" :class="card.trend >= 0 ? 'up' : 'down'">
          <el-icon><component :is="card.trend >= 0 ? 'CaretTop' : 'CaretBottom'" /></el-icon>
          {{ Math.abs(card.trend) }}%
        </div>
      </div>
    </div>

    <!-- 第一行：土石方平衡图 + 表单趋势 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">
              <el-icon color="#3b82f6"><Histogram /></el-icon>
              &nbsp;土石方平衡分析
            </h3>
            <div class="chart-extra">
              <el-tag size="small" type="success" effect="plain">利用率：{{ earthwork.utilization }}%</el-tag>
              <el-tag size="small" type="info" effect="plain">平衡值：{{ formatNum(earthwork.balance) }} m³</el-tag>
            </div>
          </div>
          <div class="chart-body">
            <v-chart :option="earthworkOption" autoresize class="chart-vue" />
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">
              <el-icon color="#f59e0b"><TrendCharts /></el-icon>
              &nbsp;近14天表单趋势
            </h3>
            <div class="chart-extra">
              <span class="legend-dot dot-draft"></span>草稿
              <span class="legend-dot dot-pending"></span>待审
              <span class="legend-dot dot-approved"></span>通过
              <span class="legend-dot dot-rejected"></span>驳回
            </div>
          </div>
          <div class="chart-body">
            <v-chart :option="formTrendOption" autoresize class="chart-vue" />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第二行：工况位移/应力趋势 + 表单类型统计 -->
    <el-row :gutter="16" class="chart-row">
      <el-col :span="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">
              <el-icon color="#10b981"><Monitor /></el-icon>
              &nbsp;23工况位移/应力趋势
            </h3>
            <div class="chart-extra">
              <span class="legend-line line-blue"></span>位移 (mm)
              <span class="legend-line line-orange"></span>应力 (MPa)
            </div>
          </div>
          <div class="chart-body">
            <v-chart :option="displacementOption" autoresize class="chart-vue" />
          </div>
        </div>
      </el-col>
      <el-col :span="12">
        <div class="chart-card">
          <div class="chart-header">
            <h3 class="chart-title">
              <el-icon color="#8b5cf6"><PieChart /></el-icon>
              &nbsp;表单类型统计
            </h3>
            <div class="chart-extra">
              <el-tag size="small" effect="plain">总计：{{ formTypeTotal }} 份</el-tag>
            </div>
          </div>
          <div class="chart-body">
            <v-chart :option="formTypeOption" autoresize class="chart-vue" />
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 第三行：最近活动动态时间线 -->
    <div class="chart-card timeline-card">
      <div class="chart-header">
        <h3 class="chart-title">
          <el-icon color="#06b6d4"><List /></el-icon>
          &nbsp;最近活动动态
        </h3>
        <el-button link type="primary" size="small" @click="loadActivities">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      <div class="chart-body timeline-body">
        <el-timeline>
          <el-timeline-item
            v-for="(act, idx) in activities"
            :key="idx"
            :timestamp="act.time"
            :type="act.colorType"
            :icon="act.icon"
            placement="top"
            size="large"
          >
            <div class="activity-item">
              <div class="activity-title">
                <span class="activity-tag" :class="`tag-${act.colorType}`">{{ act.category }}</span>
                {{ act.title }}
              </div>
              <div class="activity-desc">{{ act.description }}</div>
              <div class="activity-meta">
                <el-icon><User /></el-icon>
                {{ act.user }}
                <span class="meta-divider">·</span>
                <el-tag v-if="act.status" :type="act.statusType" size="small" effect="plain">{{ act.status }}</el-tag>
              </div>
            </div>
          </el-timeline-item>
        </el-timeline>
        <el-empty v-if="activities.length === 0" description="暂无活动记录" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import * as api from '@/api'

// ========== 当前时间 ==========
const currentTime = ref('')
let timer = null
function updateTime() {
  const now = new Date()
  const pad = (n) => String(n).padStart(2, '0')
  currentTime.value = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())} ${pad(now.getHours())}:${pad(now.getMinutes())}:${pad(now.getSeconds())}`
}
updateTime()
timer = setInterval(updateTime, 1000)
onUnmounted(() => timer && clearInterval(timer))

// ========== 8个统计卡片 ==========
const summary = reactive({
  project_count: 0,
  pending_approval: 0,
  sensor_count: 0,
  pending_alerts: 0,
  stage_count: 0,
  max_displacement: 0,
  max_stress: 0,
  borehole_count: 0,
})

const statCards = computed(() => [
  {
    label: '项目数', value: summary.project_count, icon: 'Folder',
    colorClass: 'card-blue', trend: 5.2,
  },
  {
    label: '待办审批', value: summary.pending_approval, icon: 'DocumentChecked',
    colorClass: 'card-orange', trend: 12.8,
  },
  {
    label: '传感器', value: summary.sensor_count, icon: 'Cpu',
    colorClass: 'card-green', trend: 3.1,
  },
  {
    label: '待处理告警', value: summary.pending_alerts, icon: 'Warning',
    colorClass: 'card-red', trend: -8.5,
  },
  {
    label: '工况数', value: summary.stage_count, icon: 'Menu',
    colorClass: 'card-purple', trend: 0,
  },
  {
    label: '最大位移 (mm)', value: summary.max_displacement, icon: 'Rank',
    colorClass: 'card-cyan', trend: 2.4,
  },
  {
    label: '最大应力 (MPa)', value: summary.max_stress, icon: 'Odometer',
    colorClass: 'card-pink', trend: 1.6,
  },
  {
    label: '钻孔数', value: summary.borehole_count, icon: 'Aim',
    colorClass: 'card-indigo', trend: 0,
  },
])

function formatNum(v) {
  if (v === null || v === undefined) return '0'
  return Number(v).toLocaleString('zh-CN', { maximumFractionDigits: 2 })
}

// ========== 土石方平衡 ==========
const earthwork = reactive({
  excavation: 0, backfill: 0, borrow: 0, waste: 0, balance: 0, utilization: 0,
})
const earthworkOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
    formatter: (params) => {
      let html = `<div style="font-weight:600;margin-bottom:6px">土石方平衡</div>`
      params.forEach(p => {
        html += `<div style="display:flex;align-items:center;gap:6px;margin:2px 0">
          <span style="width:10px;height:10px;border-radius:2px;background:${p.color};display:inline-block"></span>
          <span>${p.seriesName}：</span>
          <b>${formatNum(p.value)} m³</b>
        </div>`
      })
      return html
    },
  },
  legend: {
    data: ['开挖量', '回填量', '借方量', '弃方量', '平衡值'],
    bottom: 0,
    textStyle: { color: '#64748b', fontSize: 12 },
  },
  grid: { left: '4%', right: '4%', top: '8%', bottom: '16%', containLabel: true },
  xAxis: {
    type: 'category',
    data: ['土石方平衡'],
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisTick: { show: false },
  },
  yAxis: {
    type: 'value',
    name: '方量 (m³)',
    nameTextStyle: { color: '#94a3b8', fontSize: 12 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    axisLabel: { color: '#94a3b8', formatter: (v) => (v >= 10000 ? (v/10000).toFixed(1)+'万' : v) },
  },
  series: [
    {
      name: '开挖量', type: 'bar', stack: 'total', barWidth: 80,
      itemStyle: { color: '#3b82f6', borderRadius: [0,0,0,0] },
      data: [earthwork.excavation],
      label: { show: true, position: 'inside', color: '#fff', fontWeight: 600, formatter: (p) => formatNum(p.value) },
    },
    {
      name: '借方量', type: 'bar', stack: 'total',
      itemStyle: { color: '#60a5fa' },
      data: [earthwork.borrow],
      label: { show: true, position: 'inside', color: '#fff', fontWeight: 600, formatter: (p) => formatNum(p.value) },
    },
    {
      name: '回填量', type: 'bar', stack: 'total2',
      itemStyle: { color: '#10b981' },
      data: [earthwork.backfill],
      label: { show: true, position: 'inside', color: '#fff', fontWeight: 600, formatter: (p) => formatNum(p.value) },
    },
    {
      name: '弃方量', type: 'bar', stack: 'total2',
      itemStyle: { color: '#f59e0b' },
      data: [earthwork.waste],
      label: { show: true, position: 'inside', color: '#fff', fontWeight: 600, formatter: (p) => formatNum(p.value) },
    },
    {
      name: '平衡值', type: 'bar',
      barWidth: 18,
      itemStyle: {
        color: earthwork.balance >= 0 ? '#06b6d4' : '#ef4444',
        borderRadius: [4,4,0,0],
      },
      data: [earthwork.balance],
      label: { show: true, position: 'top', color: '#0f172a', fontWeight: 600, formatter: (p) => (p.value >= 0 ? '+' : '') + formatNum(p.value) },
    },
  ],
}))

// ========== 近14天表单趋势 ==========
const formTrend = reactive({ dates: [], draft: [], pending: [], approved: [], rejected: [] })
const formTrendOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'shadow' },
  },
  legend: { show: false },
  grid: { left: '4%', right: '4%', top: '8%', bottom: '10%', containLabel: true },
  xAxis: {
    type: 'category',
    data: formTrend.dates,
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisTick: { show: false },
    axisLabel: { color: '#94a3b8', fontSize: 11, interval: 0, rotate: 30 },
  },
  yAxis: {
    type: 'value',
    name: '数量',
    nameTextStyle: { color: '#94a3b8', fontSize: 12 },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    axisLabel: { color: '#94a3b8' },
  },
  series: [
    { name: '草稿', type: 'bar', stack: 'form', barWidth: 18, itemStyle: { color: '#94a3b8' }, data: formTrend.draft },
    { name: '待审', type: 'bar', stack: 'form', itemStyle: { color: '#f59e0b' }, data: formTrend.pending },
    { name: '通过', type: 'bar', stack: 'form', itemStyle: { color: '#10b981' }, data: formTrend.approved },
    { name: '驳回', type: 'bar', stack: 'form', itemStyle: { color: '#ef4444', borderRadius: [4,4,0,0] }, data: formTrend.rejected },
  ],
}))

// ========== 23工况位移/应力趋势 ==========
const stageTrend = reactive({ stages: [], displacement: [], stress: [] })
const displacementOption = computed(() => ({
  tooltip: {
    trigger: 'axis',
    axisPointer: { type: 'cross' },
  },
  legend: { show: false },
  grid: { left: '4%', right: '6%', top: '8%', bottom: '10%', containLabel: true },
  xAxis: {
    type: 'category',
    data: stageTrend.stages,
    name: '工况',
    nameTextStyle: { color: '#94a3b8', fontSize: 12 },
    boundaryGap: false,
    axisLine: { lineStyle: { color: '#e2e8f0' } },
    axisTick: { show: false },
    axisLabel: { color: '#94a3b8', fontSize: 10, interval: 1 },
  },
  yAxis: [
    {
      type: 'value',
      name: '位移 (mm)',
      position: 'left',
      nameTextStyle: { color: '#3b82f6', fontSize: 12 },
      axisLine: { show: true, lineStyle: { color: '#3b82f6' } },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
      axisLabel: { color: '#94a3b8' },
    },
    {
      type: 'value',
      name: '应力 (MPa)',
      position: 'right',
      nameTextStyle: { color: '#f59e0b', fontSize: 12 },
      axisLine: { show: true, lineStyle: { color: '#f59e0b' } },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { color: '#94a3b8' },
    },
  ],
  series: [
    {
      name: '位移', type: 'line', smooth: true,
      yAxisIndex: 0,
      itemStyle: { color: '#3b82f6' },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59,130,246,0.35)' },
            { offset: 1, color: 'rgba(59,130,246,0.02)' },
          ],
        },
      },
      symbol: 'circle', symbolSize: 5,
      data: stageTrend.displacement,
    },
    {
      name: '应力', type: 'line', smooth: true,
      yAxisIndex: 1,
      itemStyle: { color: '#f59e0b' },
      lineStyle: { type: 'dashed' },
      symbol: 'diamond', symbolSize: 5,
      data: stageTrend.stress,
    },
  ],
}))

// ========== 表单类型统计 ==========
const formByType = ref([])
const formTypeTotal = computed(() => formByType.value.reduce((s, i) => s + (i.value || 0), 0))
const formTypeColors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#06b6d4', '#ef4444', '#ec4899', '#6366f1']
const formTypeOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    formatter: (p) => `${p.name}<br/>数量：<b>${p.value}</b><br/>占比：<b>${p.percent}%</b>`,
  },
  legend: {
    orient: 'vertical',
    right: '5%',
    top: 'center',
    textStyle: { color: '#64748b', fontSize: 12 },
    itemWidth: 12,
    itemHeight: 12,
  },
  series: [{
    type: 'pie',
    radius: ['42%', '72%'],
    center: ['38%', '50%'],
    roseType: 'radius',
    itemStyle: {
      borderRadius: 4,
      borderColor: '#fff',
      borderWidth: 2,
    },
    label: {
      show: true,
      color: '#475569',
      fontSize: 11,
      formatter: '{d}%',
    },
    labelLine: { length: 8, length2: 8 },
    data: formByType.value.map((item, idx) => ({
      name: item.name,
      value: item.value,
      itemStyle: { color: formTypeColors[idx % formTypeColors.length] },
    })),
  }],
}))

// ========== 最近活动 ==========
const activities = ref([])
const activityIconMap = {
  form: 'DocumentChecked',
  monitoring: 'Monitor',
  alert: 'Warning',
  project: 'Folder',
  user: 'User',
}
const activityColorMap = {
  form: 'primary',
  monitoring: 'success',
  alert: 'danger',
  project: 'warning',
  user: 'info',
}
const activityStatusTypeMap = {
  approved: 'success',
  pending: 'warning',
  rejected: 'danger',
  draft: 'info',
  triggered: 'danger',
  resolved: 'success',
}

function normalizeActivities(list) {
  return (list || []).map(a => ({
    time: a.time || a.created_at || '-',
    title: a.title || a.content || '未知活动',
    description: a.description || a.detail || '',
    category: a.category_label || a.category || '系统',
    user: a.user || a.user_name || a.creator || '系统',
    colorType: activityColorMap[a.category] || 'primary',
    icon: activityIconMap[a.category] || 'Bell',
    status: a.status_label || a.status || '',
    statusType: activityStatusTypeMap[a.status] || 'info',
  }))
}

// ========== 数据加载 ==========
async function loadSummary() {
  try {
    const r = await api.getDashboardSummary()
    // 兼容两种格式：后端返回嵌套的 counters / extremes，或扁平字段
    const c = r && typeof r === 'object' && 'counters' in r ? (r.counters || {}) : (r || {})
    const e = r && typeof r === 'object' && 'extremes' in r ? (r.extremes || {}) : (r || {})
    // 位移：后端返回 m，前端显示 mm → ×1000，保留 1 位小数
    let dispMm = 0
    if (typeof r.max_displacement === 'number') dispMm = +(r.max_displacement).toFixed(1)
    else if (typeof e.max_displacement_m === 'number') dispMm = +(e.max_displacement_m * 1000).toFixed(1)
    // 应力：后端返回 MPa 或超大 Pa 值，若 > 1000 视为 Pa 自动除以 1e6
    let stressMpa = 0
    if (typeof r.max_stress === 'number') stressMpa = +(r.max_stress).toFixed(2)
    else if (typeof e.max_stress_MPa === 'number') {
      stressMpa = e.max_stress_MPa > 1000 ? +(e.max_stress_MPa / 1e6).toFixed(2) : +(e.max_stress_MPa).toFixed(2)
    }
    Object.assign(summary, {
      project_count:      c.project_count      ?? r.project_count      ?? r.projects      ?? 0,
      pending_approval:   c.pending_form_count ?? c.my_pending_count   ?? r.pending_approval ?? r.approvals ?? c.form_count ?? 0,
      sensor_count:       c.sensor_count       ?? r.sensor_count       ?? r.sensors      ?? 0,
      pending_alerts:     c.open_alert_count   ?? c.alert_count        ?? r.pending_alerts ?? r.alerts   ?? 0,
      stage_count:        c.stage_count        ?? r.stage_count        ?? r.stages       ?? 0,
      max_displacement:   dispMm,
      max_stress:         stressMpa,
      borehole_count:     c.borehole_count     ?? r.borehole_count     ?? r.boreholes    ?? 0,
    })
  } catch {
    Object.assign(summary, {
      project_count: 12, pending_approval: 8, sensor_count: 48,
      pending_alerts: 3, stage_count: 23, max_displacement: '15.6',
      max_stress: '2.45', borehole_count: 36,
    })
  }
}

async function loadEarthworkBalance() {
  try {
    const r = await api.getEarthworkBalance()
    Object.assign(earthwork, {
      excavation: r.excavation ?? r.dig ?? 0,
      backfill: r.backfill ?? 0,
      borrow: r.borrow ?? 0,
      waste: r.waste ?? r.dump ?? 0,
      balance: r.balance ?? 0,
      utilization: r.utilization ?? 0,
    })
  } catch {
    Object.assign(earthwork, {
      excavation: 1256800, backfill: 865400, borrow: 58200, waste: 449600,
      balance: 0, utilization: 68.9,
    })
  }
}

async function loadFormTrend() {
  try {
    const r = await api.getFormTrend({ days: 14 })
    const list = r.list || r.data || []
    formTrend.dates = list.map(x => x.date || x.day)
    formTrend.draft = list.map(x => x.draft ?? 0)
    formTrend.pending = list.map(x => x.pending ?? 0)
    formTrend.approved = list.map(x => x.approved ?? 0)
    formTrend.rejected = list.map(x => x.rejected ?? 0)
  } catch {
    const dates = []
    const now = new Date()
    for (let i = 13; i >= 0; i--) {
      const d = new Date(now.getTime() - i * 86400000)
      dates.push(`${d.getMonth()+1}/${d.getDate()}`)
    }
    formTrend.dates = dates
    formTrend.draft = dates.map(() => Math.floor(Math.random() * 4) + 1)
    formTrend.pending = dates.map(() => Math.floor(Math.random() * 3) + 1)
    formTrend.approved = dates.map(() => Math.floor(Math.random() * 6) + 2)
    formTrend.rejected = dates.map(() => Math.floor(Math.random() * 2))
  }
}

async function loadStageDisplacementTrend() {
  try {
    const r = await api.getStageDisplacementTrend()
    const list = r.list || r.data || []
    stageTrend.stages = list.map(x => x.stage || x.name || x.key)
    stageTrend.displacement = list.map(x => x.displacement ?? x.disp ?? 0)
    stageTrend.stress = list.map(x => x.stress ?? 0)
  } catch {
    const stages = Array.from({ length: 23 }, (_, i) => `工况${i+1}`)
    stageTrend.stages = stages
    stageTrend.displacement = stages.map((_, i) => (2 + i * 0.6 + Math.random() * 2).toFixed(2))
    stageTrend.stress = stages.map((_, i) => (0.8 + i * 0.07 + Math.random() * 0.3).toFixed(3))
  }
}

async function loadFormByType() {
  try {
    const r = await api.getFormByType()
    const list = r.list || r.data || []
    formByType.value = list.map(x => ({ name: x.name || x.label || x.type, value: x.value || x.count || 0 }))
  } catch {
    formByType.value = [
      { name: '施工进度计划', value: 18 },
      { name: '变更申请', value: 12 },
      { name: '异常报告', value: 8 },
      { name: '地质勘察报告', value: 6 },
      { name: '监测报告', value: 15 },
      { name: '参数计算书', value: 5 },
      { name: '土石方调配', value: 9 },
    ]
  }
}

async function loadActivities() {
  try {
    const r = await api.getRecentActivities({ limit: 10 })
    activities.value = normalizeActivities(r.list || r.data || r)
  } catch {
    activities.value = normalizeActivities([
      { time: '2026-08-03 14:25', category: 'form', title: '【变更申请】坝肩开挖高程调整 已通过审批', description: '变更范围：EL580~EL620 段，调整边坡比 1:0.5→1:0.75', user: '张工', status: 'approved' },
      { time: '2026-08-03 13:10', category: 'monitoring', title: '传感器 S-023 新增监测读数', description: '位移：14.2mm / 应力：2.38MPa，速率正常', user: '监测系统', status: '' },
      { time: '2026-08-03 11:45', category: 'alert', title: '【安全告警】S-017 位移速率超过阈值', description: '连续 2 小时速率 > 0.5mm/h，已触发黄色预警', user: '预警系统', status: 'triggered' },
      { time: '2026-08-03 10:20', category: 'form', title: '【施工进度计划】2026年8月进度计划 提交审批', description: '开挖量：85000m³ / 回填量：42000m³', user: '李工', status: 'pending' },
      { time: '2026-08-03 09:05', category: 'project', title: '项目【左岸边坡开挖】进度已更新', description: '当前完成 62.5%，预计完工日期：2026-12-30', user: '王经理', status: '' },
      { time: '2026-08-02 17:30', category: 'form', title: '【异常报告】3号钻孔遇破碎带 已归档', description: '深度 32.5m 处揭露破碎带，已补充灌浆处理方案', user: '赵工', status: 'approved' },
      { time: '2026-08-02 15:00', category: 'user', title: '新用户 【周工】加入项目团队', description: '角色：技术工程师 · 部门：地质勘察部', user: '系统', status: '' },
    ])
  }
}

onMounted(async () => {
  await Promise.all([
    loadSummary(),
    loadEarthworkBalance(),
    loadFormTrend(),
    loadStageDisplacementTrend(),
    loadFormByType(),
    loadActivities(),
  ])
})
</script>

<style scoped>
.dashboard-page {
  padding: 20px;
  min-height: 100%;
}

/* ===== 页面头部 ===== */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}
.header-left .page-title {
  margin: 0 0 4px;
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 10px;
}
.header-left .page-subtitle {
  margin: 0;
  font-size: 13px;
  color: #64748b;
}

/* ===== 统计卡片 ===== */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 14px;
  margin-bottom: 18px;
}
.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 16px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(15,23,42,0.06);
  border: 1px solid #f1f5f9;
  transition: transform 0.2s, box-shadow 0.2s;
}
.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(15,23,42,0.1);
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 4px; height: 100%;
  border-radius: 12px 0 0 12px;
}
.stat-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 10px;
}
.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.2;
}
.stat-label {
  font-size: 12.5px;
  color: #64748b;
  margin-top: 4px;
}
.stat-trend {
  position: absolute;
  top: 16px; right: 14px;
  font-size: 11.5px;
  display: flex; align-items: center; gap: 2px;
  padding: 2px 6px;
  border-radius: 4px;
}
.stat-trend.up { color: #059669; background: #d1fae5; }
.stat-trend.down { color: #dc2626; background: #fee2e2; }

.card-blue::before { background: #3b82f6; }
.card-blue .stat-icon { background: #dbeafe; color: #3b82f6; }

.card-orange::before { background: #f59e0b; }
.card-orange .stat-icon { background: #fef3c7; color: #f59e0b; }

.card-green::before { background: #10b981; }
.card-green .stat-icon { background: #d1fae5; color: #10b981; }

.card-red::before { background: #ef4444; }
.card-red .stat-icon { background: #fee2e2; color: #ef4444; }

.card-purple::before { background: #8b5cf6; }
.card-purple .stat-icon { background: #ede9fe; color: #8b5cf6; }

.card-cyan::before { background: #06b6d4; }
.card-cyan .stat-icon { background: #cffafe; color: #06b6d4; }

.card-pink::before { background: #ec4899; }
.card-pink .stat-icon { background: #fce7f3; color: #ec4899; }

.card-indigo::before { background: #6366f1; }
.card-indigo .stat-icon { background: #e0e7ff; color: #6366f1; }

/* ===== 图表卡片 ===== */
.chart-row {
  margin-bottom: 16px;
}
.chart-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
  box-shadow: 0 1px 3px rgba(15,23,42,0.06);
  overflow: hidden;
}
.chart-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid #f1f5f9;
}
.chart-title {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 8px;
}
.chart-extra {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: #64748b;
}
.legend-dot {
  display: inline-block;
  width: 10px; height: 10px;
  border-radius: 2px;
  margin-right: 4px;
  vertical-align: middle;
}
.dot-draft { background: #94a3b8; }
.dot-pending { background: #f59e0b; }
.dot-approved { background: #10b981; }
.dot-rejected { background: #ef4444; }

.legend-line {
  display: inline-block;
  width: 16px; height: 3px;
  border-radius: 2px;
  margin-right: 4px;
  vertical-align: middle;
}
.line-blue { background: #3b82f6; }
.line-orange { background: #f59e0b; }

.chart-body {
  padding: 16px 20px 20px;
}
.chart-vue {
  width: 100%;
  height: 300px;
}

/* ===== 时间线 ===== */
.timeline-card {
  margin-bottom: 20px;
}
.timeline-body {
  padding: 24px 20px 8px;
}
.activity-item {
  padding: 2px 0;
}
.activity-title {
  font-size: 14px;
  color: #0f172a;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}
.activity-tag {
  font-size: 11px;
  padding: 1px 8px;
  border-radius: 4px;
  font-weight: 500;
}
.tag-primary { background: #dbeafe; color: #1d4ed8; }
.tag-success { background: #d1fae5; color: #047857; }
.tag-danger { background: #fee2e2; color: #b91c1c; }
.tag-warning { background: #fef3c7; color: #b45309; }
.tag-info { background: #e0f2fe; color: #0369a1; }

.activity-desc {
  font-size: 13px;
  color: #64748b;
  margin-bottom: 8px;
  line-height: 1.6;
}
.activity-meta {
  font-size: 12px;
  color: #94a3b8;
  display: flex;
  align-items: center;
  gap: 6px;
}
.meta-divider { color: #cbd5e1; }

/* ===== 响应式 ===== */
@media (max-width: 1800px) {
  .stat-cards { grid-template-columns: repeat(4, 1fr); }
}
@media (max-width: 992px) {
  .stat-cards { grid-template-columns: repeat(2, 1fr); }
}
</style>
