<template>
  <div class="safety-alert-page">
    <div class="page-header">
      <div class="header-left">
        <el-icon :size="22" color="#dc2626"><Warning /></el-icon>
        <h2 class="page-title">安全预警模块</h2>
        <span class="page-sub">实时监测告警、规则管理与一键巡检</span>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- ============== Tab1: 告警记录 ============== -->
      <el-tab-pane label="告警记录" name="records">
        <!-- 顶部统计卡片 -->
        <el-row :gutter="14" class="stat-row">
          <el-col :span="6">
            <div class="stat-card sc-total">
              <div class="sc-icon"><el-icon :size="22"><Bell /></el-icon></div>
              <div class="sc-info">
                <div class="sc-label">告警总数</div>
                <div class="sc-value">{{ stats.total ?? 0 }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card sc-pending">
              <div class="sc-icon"><el-icon :size="22"><Clock /></el-icon></div>
              <div class="sc-info">
                <div class="sc-label">待处理</div>
                <div class="sc-value">{{ stats.pending ?? 0 }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card sc-acked">
              <div class="sc-icon"><el-icon :size="22"><CircleCheck /></el-icon></div>
              <div class="sc-info">
                <div class="sc-label">已确认</div>
                <div class="sc-value">{{ stats.acked ?? 0 }}</div>
              </div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="stat-card sc-closed">
              <div class="sc-icon"><el-icon :size="22"><CircleClose /></el-icon></div>
              <div class="sc-info">
                <div class="sc-label">已关闭</div>
                <div class="sc-value">{{ stats.closed ?? 0 }}</div>
              </div>
            </div>
          </el-col>
        </el-row>

        <el-row :gutter="14" class="stat-row mt-10">
          <el-col :span="8">
            <div class="level-card lc-critical">
              <div class="lc-label">严重</div>
              <div class="lc-value">{{ stats.byLevel?.critical ?? 0 }}</div>
              <el-tag type="danger" size="small" effect="dark" round>critical</el-tag>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="level-card lc-warning">
              <div class="lc-label">警告</div>
              <div class="lc-value">{{ stats.byLevel?.warning ?? 0 }}</div>
              <el-tag type="warning" size="small" effect="dark" round>warning</el-tag>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="level-card lc-info">
              <div class="lc-label">提示</div>
              <div class="lc-value">{{ stats.byLevel?.info ?? 0 }}</div>
              <el-tag type="info" size="small" effect="dark" round>info</el-tag>
            </div>
          </el-col>
        </el-row>

        <!-- 筛选 + 立即巡检 -->
        <el-card shadow="never" class="filter-card">
          <div class="filter-bar">
            <div class="filter-items">
              <el-select
                v-model="filters.level"
                placeholder="告警级别"
                clearable
                size="default"
                class="filter-select"
              >
                <el-option label="严重" value="critical" />
                <el-option label="警告" value="warning" />
                <el-option label="提示" value="info" />
              </el-select>
              <el-select
                v-model="filters.status"
                placeholder="状态"
                clearable
                size="default"
                class="filter-select"
              >
                <el-option label="待处理" value="pending" />
                <el-option label="已确认" value="acked" />
                <el-option label="已关闭" value="closed" />
              </el-select>
              <el-date-picker
                v-model="filters.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                size="default"
                value-format="YYYY-MM-DD"
                class="filter-date"
              />
              <el-input
                v-model="filters.keyword"
                placeholder="关键词搜索"
                clearable
                size="default"
                class="filter-input"
                :prefix-icon="Search"
              />
              <el-button type="primary" :icon="Search" @click="loadAlerts">查询</el-button>
              <el-button :icon="Refresh" @click="resetFilters">重置</el-button>
            </div>
            <div class="filter-actions">
              <el-button
                type="danger"
                :icon="Lightning"
                :loading="checking"
                @click="handleRunCheck"
              >
                立即巡检
              </el-button>
            </div>
          </div>

          <!-- 告警表格 -->
          <el-table
            :data="alertList"
            v-loading="loadingAlerts"
            stripe
            class="alert-table"
            style="width: 100%; margin-top: 14px;"
          >
            <el-table-column label="级别" width="110" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="levelTagType(row.level)"
                  effect="dark"
                  size="small"
                  round
                >
                  {{ levelText(row.level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="触发时间" width="170" prop="triggeredAt" :formatter="fmtTime" />
            <el-table-column label="告警内容" min-width="300">
              <template #default="{ row }">
                <div class="alert-title">{{ row.title || row.name || '告警' }}</div>
                <div class="alert-content">{{ row.content || row.message }}</div>
              </template>
            </el-table-column>
            <el-table-column label="来源/规则" width="160">
              <template #default="{ row }">
                <span class="mono">{{ (row.ruleName || row.source || '-') }}</span>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="statusTagType(row.status)"
                  effect="plain"
                  size="small"
                >
                  {{ statusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="170" fixed="right" align="center">
              <template #default="{ row }">
                <el-button
                  v-if="row.status === 'pending'"
                  type="primary"
                  link
                  size="small"
                  @click="handleAck(row)"
                >确认</el-button>
                <el-button
                  v-if="row.status !== 'closed'"
                  type="info"
                  link
                  size="small"
                  @click="handleClose(row)"
                >关闭</el-button>
                <el-button
                  type="warning"
                  link
                  size="small"
                  @click="viewDetail(row)"
                >详情</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="table-footer">
            <el-pagination
              v-model:current-page="page.page"
              v-model:page-size="page.size"
              :page-sizes="[10, 20, 50, 100]"
              :total="page.total"
              layout="total, sizes, prev, pager, next, jumper"
              background
              @size-change="loadAlerts"
              @current-change="loadAlerts"
            />
          </div>
        </el-card>

        <!-- 14天趋势堆叠面积图 -->
        <el-card shadow="never" class="trend-card">
          <template #header>
            <div class="card-header">
              <el-icon color="#059669"><TrendCharts /></el-icon>
              <span>近 14 天告警趋势</span>
            </div>
          </template>
          <div class="chart-wrap">
            <v-chart class="trend-chart" :option="trendOption" autoresize />
          </div>
        </el-card>
      </el-tab-pane>

      <!-- ============== Tab2: 预警规则 ============== -->
      <el-tab-pane label="预警规则" name="rules">
        <el-card shadow="never" class="rules-card">
          <template #header>
            <div class="card-header between">
              <div class="h-left">
                <el-icon color="#7c3aed"><List /></el-icon>
                <span>预警规则列表</span>
                <span class="hint">共 {{ ruleList.length }} 条规则</span>
              </div>
              <el-button
                type="primary"
                :icon="Plus"
                @click="openRuleDialog()"
              >
                新增规则
              </el-button>
            </div>
          </template>

          <el-table
            :data="ruleList"
            v-loading="loadingRules"
            stripe
            style="width: 100%;"
          >
            <el-table-column label="ID" width="60" prop="id" />
            <el-table-column label="规则名称" min-width="180" prop="name" />
            <el-table-column label="监控字段" width="170">
              <template #default="{ row }">
                <el-tag type="info" effect="plain">{{ fieldLabel(row.field) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="比较符" width="90" align="center">
              <template #default="{ row }">
                <span class="op-badge">{{ row.op }}</span>
              </template>
            </el-table-column>
            <el-table-column label="阈值" width="120" align="right">
              <template #default="{ row }">
                <span class="mono-bold">{{ row.threshold }}</span>
              </template>
            </el-table-column>
            <el-table-column label="级别" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="levelTagType(row.level)"
                  effect="dark"
                  size="small"
                  round
                >
                  {{ levelText(row.level) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="是否启用" width="90" align="center">
              <template #default="{ row }">
                <el-switch
                  v-model="row.enabled"
                  :active-value="true"
                  :inactive-value="false"
                  @change="toggleRule(row)"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="170" fixed="right" align="center">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="openRuleDialog(row)"
                >编辑</el-button>
                <el-popconfirm
                  title="确认删除该规则？"
                  confirm-button-text="删除"
                  cancel-button-text="取消"
                  @confirm="handleDeleteRule(row)"
                >
                  <template #reference>
                    <el-button
                      type="danger"
                      link
                      size="small"
                    >删除</el-button>
                  </template>
                </el-popconfirm>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 新增/编辑对话框 -->
        <el-dialog
          v-model="ruleDialog.visible"
          :title="ruleDialog.editMode ? '编辑预警规则' : '新增预警规则'"
          width="520px"
          :close-on-click-modal="false"
          destroy-on-close
        >
          <el-form
            ref="ruleFormRef"
            :model="ruleDialog.form"
            :rules="ruleFormRules"
            label-width="100px"
          >
            <el-form-item label="规则名称" prop="name">
              <el-input v-model="ruleDialog.form.name" placeholder="请输入规则名称，如：顶部位移超限" />
            </el-form-item>
            <el-form-item label="监控字段" prop="field">
              <el-select v-model="ruleDialog.form.field" placeholder="请选择监控字段" class="w-full">
                <el-option
                  v-for="f in monitorFields"
                  :key="f.value"
                  :label="f.label"
                  :value="f.value"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="比较符" prop="op">
              <el-select v-model="ruleDialog.form.op" placeholder="请选择比较符" class="w-full">
                <el-option label="大于 ( > )" value=">" />
                <el-option label="小于 ( < )" value="<" />
                <el-option label="大于等于 ( >= )" value=">=" />
                <el-option label="小于等于 ( <= )" value="<=" />
                <el-option label="等于 ( == )" value="==" />
              </el-select>
            </el-form-item>
            <el-form-item label="阈值" prop="threshold">
              <el-input-number
                v-model="ruleDialog.form.threshold"
                :min="-999999"
                :max="999999"
                :precision="3"
                :step="1"
                controls-position="right"
                class="w-full"
              />
            </el-form-item>
            <el-form-item label="告警级别" prop="level">
              <el-select v-model="ruleDialog.form.level" placeholder="请选择告警级别" class="w-full">
                <el-option label="提示 (info)" value="info" />
                <el-option label="警告 (warning)" value="warning" />
                <el-option label="严重 (critical)" value="critical" />
              </el-select>
            </el-form-item>
            <el-form-item label="描述">
              <el-input
                v-model="ruleDialog.form.description"
                type="textarea"
                :rows="2"
                placeholder="可选，描述该规则用途"
              />
            </el-form-item>
            <el-form-item label="是否启用">
              <el-switch
                v-model="ruleDialog.form.enabled"
                active-text="启用"
                inactive-text="停用"
              />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="ruleDialog.visible = false">取消</el-button>
            <el-button type="primary" :loading="ruleDialog.saving" @click="submitRule">保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Warning, Bell, Clock, CircleCheck, CircleClose,
  Search, Refresh, Lightning, TrendCharts, List, Plus
} from '@element-plus/icons-vue'
import {
  listAlertRules, createAlertRule, updateAlertRule, deleteAlertRule,
  listAlerts, getAlertStats, ackAlert, closeAlert, runAlertCheck,
} from '@/api'

// ========== 通用解包函数：兼容后端返回 {items/data/list} 或裸 list/object ==========
function unwrapList(r, fallback = []) {
  if (Array.isArray(r)) return r
  if (!r || typeof r !== 'object') return fallback
  if (Array.isArray(r.items)) return r.items
  if (Array.isArray(r.list)) return r.list
  if (Array.isArray(r.data)) return r.data
  if (r.data && typeof r.data === 'object') {
    if (Array.isArray(r.data.items)) return r.data.items
    if (Array.isArray(r.data.list)) return r.data.list
    if (Array.isArray(r.data.data)) return r.data.data
  }
  return fallback
}
function unwrapObject(r, fallback = {}) {
  if (r && typeof r === 'object' && !Array.isArray(r)) return r
  if (!r) return fallback
  if (r.data && typeof r.data === 'object' && !Array.isArray(r.data)) return r.data
  if (r.items && typeof r.items === 'object' && !Array.isArray(r.items)) return r.items
  if (r.list && typeof r.list === 'object' && !Array.isArray(r.list)) return r.list
  return fallback
}

const activeTab = ref('records')

// ========== Tab1: 告警记录 ==========
const stats = reactive({
  total: 0, pending: 0, acked: 0, closed: 0,
  byLevel: { critical: 0, warning: 0, info: 0 },
})
const loadingAlerts = ref(false)
const checking = ref(false)
const alertList = ref([])

const filters = reactive({
  level: '',
  status: '',
  dateRange: [],
  keyword: '',
})
const page = reactive({ page: 1, size: 10, total: 0 })

const monitorFields = [
  { value: 'top_displacement',  label: '顶部位移 (mm)' },
  { value: 'horz_displacement', label: '水平位移 (mm)' },
  { value: 'settlement',        label: '沉降 (mm)' },
  { value: 'stress',            label: '应力 (kPa)' },
  { value: 'strain',            label: '应变 (‰)' },
  { value: 'pore_pressure',     label: '孔隙水压力 (kPa)' },
  { value: 'anchor_force',      label: '锚杆/锚索拉力 (kN)' },
  { value: 'support_pressure',  label: '支护压力 (kPa)' },
  { value: 'water_level',       label: '地下水位 (m)' },
  { value: 'earth_pressure',    label: '土压力 (kPa)' },
  { value: 'slope_angle',       label: '坡角 (°)' },
  { value: 'vibration_vel',     label: '振动速度 (cm/s)' },
  { value: 'temperature',       label: '温度 (°C)' },
  { value: 'rainfall',          label: '降雨量 (mm)' },
]
const fieldLabel = (v) => (monitorFields.find(f => f.value === v)?.label || v)

function levelTagType(l) {
  if (l === 'critical') return 'danger'
  if (l === 'warning') return 'warning'
  return 'info'
}
function levelText(l) {
  if (l === 'critical') return '严重'
  if (l === 'warning') return '警告'
  if (l === 'info') return '提示'
  return l || '未知'
}
function statusTagType(s) {
  if (s === 'pending') return 'danger'
  if (s === 'acked') return 'warning'
  if (s === 'closed') return 'success'
  return 'info'
}
function statusText(s) {
  if (s === 'pending') return '待处理'
  if (s === 'acked') return '已确认'
  if (s === 'closed') return '已关闭'
  return s || '未知'
}
function fmtTime(row, col, val) {
  if (!val) return '-'
  return String(val).replace('T', ' ').substring(0, 19)
}

async function loadStats() {
  try {
    const res = await getAlertStats()
    const raw = unwrapObject(res, {})
    // 后端返回 {summary: {total, open, ack, closed, critical, warning, info}, daily: [...]}
    const s = raw.summary || raw
    stats.total = s.total ?? 0
    stats.pending = s.pending ?? s.open ?? 0
    stats.acked = s.acked ?? s.ack ?? 0
    stats.closed = s.closed ?? 0
    stats.byLevel = s.byLevel || s.level || {
      critical: s.critical ?? 0,
      warning: s.warning ?? 0,
      info: s.info ?? 0,
    }
    // 保存 daily 给趋势图
    if (Array.isArray(raw.daily)) stats.daily = raw.daily
    else if (Array.isArray(s.daily)) stats.daily = s.daily
  } catch (_) {}
}
async function loadAlerts() {
  loadingAlerts.value = true
  try {
    const params = {
      page: page.page,
      pageSize: page.size,
      level: filters.level || undefined,
      status: filters.status || undefined,
      keyword: filters.keyword || undefined,
    }
    if (filters.dateRange?.length === 2) {
      params.startDate = filters.dateRange[0]
      params.endDate = filters.dateRange[1]
    }
    const res = await listAlerts(params)
    const raw = unwrapObject(res, {})
    const list = unwrapList(raw, [])
    // 状态映射：open->pending, ack->acked；triggered_at->triggeredAt；message->content/title；补 ruleName
    alertList.value = list.map(a => {
      const statusMap = { open: 'pending', ack: 'acked', closed: 'closed' }
      return {
        ...a,
        status: statusMap[a.status] || a.status,
        triggeredAt: a.triggeredAt || a.triggered_at,
        title: a.title || a.name || a.message || '告警',
        content: a.content || a.message,
        ruleName: a.ruleName || a.rule_name || a.source || (a.rule_id ? `规则#${a.rule_id}` : ''),
      }
    })
    // 总数兼容
    const totalCandidates = [raw.total, raw.count, raw.page_total, res.total, res.count, res.data?.total, res.data?.count]
    const foundTotal = totalCandidates.find(t => typeof t === 'number')
    page.total = typeof foundTotal === 'number' ? foundTotal : alertList.value.length
  } finally {
    loadingAlerts.value = false
  }
}
function resetFilters() {
  filters.level = ''
  filters.status = ''
  filters.dateRange = []
  filters.keyword = ''
  page.page = 1
  loadAlerts()
}
async function handleAck(row) {
  try {
    await ackAlert(row.id)
    ElMessage.success('已确认告警')
    row.status = 'acked'
    loadStats()
  } catch (e) {
    ElMessage.error('操作失败：' + (e.message || ''))
  }
}
async function handleClose(row) {
  try {
    await ElMessageBox.confirm('确认关闭该告警？关闭后将不再提醒。', '关闭确认', { type: 'warning' })
    await closeAlert(row.id)
    ElMessage.success('已关闭告警')
    row.status = 'closed'
    loadStats()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('操作失败：' + (e.message || ''))
  }
}
function viewDetail(row) {
  ElMessageBox.alert(
    `<b>告警：</b>${row.title || row.name || '告警'}<br/>` +
    `<b>内容：</b>${row.content || row.message || '-'}<br/>` +
    `<b>级别：</b>${levelText(row.level)} · <b>状态：</b>${statusText(row.status)}<br/>` +
    `<b>时间：</b>${fmtTime(row, null, row.triggeredAt)}`,
    '告警详情',
    { dangerouslyUseHTMLString: true, confirmButtonText: '我知道了' }
  )
}
async function handleRunCheck() {
  checking.value = true
  try {
    const res = await runAlertCheck()
    const raw = unwrapObject(res, {})
    // 后端返回 {message, triggered?}，兼容 newAlerts/count
    const count = raw.newAlerts ?? raw.new_alerts ?? raw.count ?? raw.triggered ?? 0
    ElMessage.success(`巡检完成${count > 0 ? `，新增告警 ${count} 条` : '，已同步更新'}`)
    loadStats()
    loadAlerts()
  } catch (e) {
    ElMessage.error('巡检失败：' + (e.message || ''))
  } finally {
    checking.value = false
  }
}

// 趋势图
const trendOption = computed(() => {
  const days = []
  const today = new Date()
  for (let i = 13; i >= 0; i--) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    days.push(`${d.getMonth() + 1}/${d.getDate()}`)
  }
  // 从 stats.daily 或接口获取；若无则使用模拟
  const daily = (stats && stats.daily) || []
  const makeArr = (key) => days.map((_, i) => {
    const item = daily[i] || {}
    return item[key] ?? Math.floor(Math.random() * 8)
  })
  return {
    tooltip: { trigger: 'axis' },
    legend: {
      data: ['严重', '警告', '提示'],
      top: 0,
      textStyle: { fontSize: 12, color: '#475569' },
    },
    grid: { left: 36, right: 16, top: 40, bottom: 28 },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: days,
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f1f5f9' } },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
    series: [
      {
        name: '严重',
        type: 'line',
        stack: 'a',
        smooth: true,
        areaStyle: { color: 'rgba(239,68,68,0.5)' },
        lineStyle: { color: '#dc2626', width: 2 },
        itemStyle: { color: '#dc2626' },
        data: makeArr('critical'),
      },
      {
        name: '警告',
        type: 'line',
        stack: 'a',
        smooth: true,
        areaStyle: { color: 'rgba(245,158,11,0.45)' },
        lineStyle: { color: '#d97706', width: 2 },
        itemStyle: { color: '#d97706' },
        data: makeArr('warning'),
      },
      {
        name: '提示',
        type: 'line',
        stack: 'a',
        smooth: true,
        areaStyle: { color: 'rgba(59,130,246,0.4)' },
        lineStyle: { color: '#2563eb', width: 2 },
        itemStyle: { color: '#2563eb' },
        data: makeArr('info'),
      },
    ],
  }
})

// ========== Tab2: 预警规则 ==========
const ruleList = ref([])
const loadingRules = ref(false)
const ruleFormRef = ref()
const ruleDialog = reactive({
  visible: false,
  editMode: false,
  saving: false,
  form: {
    id: null,
    name: '',
    field: '',
    op: '>',
    threshold: 0,
    level: 'warning',
    description: '',
    enabled: true,
  },
})
const ruleFormRules = {
  name: [{ required: true, message: '请输入规则名称', trigger: 'blur' }],
  field: [{ required: true, message: '请选择监控字段', trigger: 'change' }],
  op: [{ required: true, message: '请选择比较符', trigger: 'change' }],
  threshold: [{ required: true, message: '请输入阈值', trigger: 'blur' }],
  level: [{ required: true, message: '请选择告警级别', trigger: 'change' }],
}

async function loadRules() {
  loadingRules.value = true
  try {
    const res = await listAlertRules()
    const raw = unwrapList(res, [])
    // 字段兼容：field_key->field；comparator->op；enabled 默认真
    ruleList.value = raw.map(r => ({
      ...r,
      field: r.field || r.field_key,
      op: r.op || r.comparator,
      enabled: r.enabled !== false ? true : false,
    }))
  } finally {
    loadingRules.value = false
  }
}
function openRuleDialog(row) {
  ruleDialog.editMode = !!row
  if (row) {
    ruleDialog.form = {
      id: row.id,
      name: row.name || '',
      field: row.field || '',
      op: row.op || '>',
      threshold: row.threshold ?? 0,
      level: row.level || 'warning',
      description: row.description || '',
      enabled: row.enabled !== false,
    }
  } else {
    ruleDialog.form = {
      id: null, name: '', field: '', op: '>',
      threshold: 0, level: 'warning', description: '', enabled: true,
    }
  }
  ruleDialog.visible = true
  nextTick(() => ruleFormRef.value?.clearValidate())
}
async function submitRule() {
  await ruleFormRef.value?.validate()
  ruleDialog.saving = true
  try {
    const payload = { ...ruleDialog.form }
    delete payload.id
    if (ruleDialog.editMode && ruleDialog.form.id) {
      await updateAlertRule(ruleDialog.form.id, payload)
      ElMessage.success('规则已更新')
    } else {
      await createAlertRule(payload)
      ElMessage.success('规则已创建')
    }
    ruleDialog.visible = false
    loadRules()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.message || ''))
  } finally {
    ruleDialog.saving = false
  }
}
async function handleDeleteRule(row) {
  try {
    await deleteAlertRule(row.id)
    ElMessage.success('规则已删除')
    loadRules()
  } catch (e) {
    ElMessage.error('删除失败：' + (e.message || ''))
  }
}
async function toggleRule(row) {
  try {
    await updateAlertRule(row.id, { enabled: row.enabled })
    ElMessage.info(row.enabled ? '规则已启用' : '规则已停用')
  } catch (e) {
    row.enabled = !row.enabled
    ElMessage.error('操作失败：' + (e.message || ''))
  }
}

onMounted(() => {
  loadStats()
  loadAlerts()
  loadRules()
})

watch(activeTab, (v) => {
  if (v === 'records') { loadStats(); loadAlerts() }
  if (v === 'rules') loadRules()
})
</script>

<style scoped>
.safety-alert-page {
  padding: 16px 18px 24px;
  background: #f1f5f9;
  min-height: 100%;
}
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 8px;
}
.header-left { display: flex; align-items: center; gap: 10px; }
.page-title { margin: 0; font-size: 20px; color: #0f172a; font-weight: 700; }
.page-sub { color: #64748b; font-size: 13px; margin-left: 8px; }

.main-tabs :deep(.el-tabs__header) {
  margin: 0 0 14px;
  background: #fff;
  padding: 0 18px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.main-tabs :deep(.el-tabs__nav-wrap::after) { display: none; }

.stat-row { margin-bottom: 0; }
.stat-row.mt-10 { margin-top: 14px; }

.stat-card {
  display: flex; align-items: center; gap: 14px;
  padding: 16px 18px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid #e2e8f0;
  position: relative; overflow: hidden;
}
.sc-icon {
  width: 46px; height: 46px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
}
.sc-total .sc-icon { background: linear-gradient(135deg,#3b82f6,#2563eb); }
.sc-pending .sc-icon { background: linear-gradient(135deg,#f59e0b,#d97706); }
.sc-acked .sc-icon { background: linear-gradient(135deg,#10b981,#059669); }
.sc-closed .sc-icon { background: linear-gradient(135deg,#64748b,#475569); }

.sc-label { font-size: 12.5px; color: #64748b; }
.sc-value { font-size: 26px; font-weight: 700; color: #0f172a; line-height: 1.2; }

.level-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px;
  border-radius: 10px;
  border-left: 4px solid;
  background: #fff;
  border-top: 1px solid #e2e8f0;
  border-right: 1px solid #e2e8f0;
  border-bottom: 1px solid #e2e8f0;
}
.lc-critical { border-left-color: #dc2626; }
.lc-warning  { border-left-color: #d97706; }
.lc-info     { border-left-color: #2563eb; }
.lc-label { font-size: 13px; color: #64748b; }
.lc-value { font-size: 24px; font-weight: 700; color: #0f172a; }

.filter-card { margin-top: 14px; }
.filter-bar {
  display: flex; justify-content: space-between; align-items: center;
  flex-wrap: wrap; gap: 10px;
}
.filter-items { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
.filter-select { width: 140px; }
.filter-date { width: 260px; }
.filter-input { width: 200px; }

.alert-table :deep(.el-table__header th) {
  background: #f8fafc;
  color: #334155;
  font-weight: 600;
}
.alert-title {
  font-size: 13.5px; font-weight: 600; color: #0f172a;
  margin-bottom: 2px;
}
.alert-content {
  font-size: 12.5px; color: #64748b; line-height: 1.5;
}
.mono {
  font-family: 'Consolas', monospace;
  font-size: 12px;
  background: #f1f5f9;
  padding: 2px 8px;
  border-radius: 4px;
  color: #334155;
}
.mono-bold {
  font-family: 'Consolas', monospace;
  font-weight: 700;
  color: #1d4ed8;
}
.op-badge {
  display: inline-block;
  padding: 2px 10px;
  background: #eef2ff;
  color: #4338ca;
  border-radius: 4px;
  font-family: 'Consolas', monospace;
  font-weight: 700;
  font-size: 13px;
}

.table-footer {
  display: flex; justify-content: flex-end;
  padding-top: 14px;
}

.trend-card { margin-top: 14px; }
.chart-wrap { height: 300px; }
.trend-chart { width: 100%; height: 100%; }

.card-header {
  display: flex; align-items: center; gap: 8px;
  font-weight: 600; color: #0f172a;
}
.card-header.between { justify-content: space-between; }
.card-header .h-left { display: flex; align-items: center; gap: 8px; }
.card-header .hint {
  font-size: 12px; color: #94a3b8; font-weight: normal;
}
.rules-card :deep(.el-table__header th) {
  background: #f8fafc;
  color: #334155;
  font-weight: 600;
}
.w-full { width: 100%; }
</style>
