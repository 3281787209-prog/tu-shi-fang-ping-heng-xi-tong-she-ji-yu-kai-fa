<template>
  <div class="monitoring-info-page">
    <!-- 顶部统计卡片 -->
    <div class="stats-row">
      <div class="stat-card stat-total">
        <div class="stat-icon"><el-icon :size="28"><Sensor /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value">{{ overview.total_sensors || 0 }}</div>
          <div class="stat-label">总传感器数量</div>
        </div>
      </div>

      <div class="stat-card stat-types">
        <div class="stat-icon"><el-icon :size="28"><Histogram /></el-icon></div>
        <div class="stat-body">
          <div class="stat-types-row">
            <div
              v-for="t in sensorTypesList.slice(0, 5)"
              :key="t.key"
              class="type-chip"
              :style="{ background: t.color + '15', color: t.color, borderColor: t.color + '40' }"
            >
              <span class="chip-count">{{ typeCountMap[t.key] || 0 }}</span>
              <span class="chip-name">{{ t.label }}</span>
            </div>
          </div>
          <div class="stat-label" style="margin-top: 8px;">按类型分布</div>
        </div>
      </div>

      <div class="stat-card stat-readings">
        <div class="stat-icon"><el-icon :size="28"><DataBoard /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value">
            {{ formatNumber(overview.readings_24h || 0) }}
            <span class="stat-unit">条</span>
          </div>
          <div class="stat-label">24小时读数条数</div>
        </div>
      </div>

      <div class="stat-card stat-alert">
        <div class="stat-icon"><el-icon :size="28"><Warning /></el-icon></div>
        <div class="stat-body">
          <div class="stat-value" :class="{ 'is-alert': (overview.abnormal_count || 0) > 0 }">
            {{ overview.abnormal_count || 0 }}
            <span class="stat-unit">个</span>
          </div>
          <div class="stat-label">异常传感器数量</div>
        </div>
      </div>
    </div>

    <!-- 主体 左3右9 -->
    <div class="main-content">
      <!-- 左侧：传感器列表 -->
      <div class="sensor-list-panel">
        <div class="panel-header">
          <span class="panel-title">
            <el-icon><List /></el-icon>
            传感器列表
          </span>
          <el-button
            size="small"
            type="primary"
            link
            @click="openSensorDialog()"
          >
            <el-icon><Plus /></el-icon>
            新增
          </el-button>
        </div>

        <div class="list-filters">
          <el-select
            v-model="filterType"
            placeholder="类型"
            size="small"
            clearable
            class="w-full"
            style="margin-bottom: 8px;"
          >
            <el-option
              v-for="t in sensorTypesList"
              :key="t.key"
              :label="t.label"
              :value="t.key"
            />
          </el-select>
          <el-input
            v-model="filterKeyword"
            placeholder="关键词搜索"
            size="small"
            clearable
            style="margin-bottom: 8px;"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>
          <el-switch
            v-model="filterAbnormalOnly"
            active-text="只看异常"
            inactive-text=""
            size="small"
          />
        </div>

        <div class="sensor-list">
          <div
            v-for="sensor in filteredSensors"
            :key="sensor.id"
            class="sensor-item"
            :class="{ active: selectedSensor?.id === sensor.id, abnormal: sensor.status === 'abnormal' }"
            @click="selectSensor(sensor)"
          >
            <div class="item-header">
              <div class="item-id" :style="{ color: getSensorTypeColor(sensor.type) }">
                <el-icon class="type-icon">
                  <component :is="getSensorTypeIcon(sensor.type)" />
                </el-icon>
                {{ sensor.code }}
              </div>
              <span
                class="status-dot"
                :class="sensor.status"
                :title="statusText(sensor.status)"
              ></span>
            </div>
            <div class="item-name">{{ sensor.name }}</div>
            <div class="item-footer">
              <span class="item-value">
                {{ sensor.latest_value ?? '--' }}
                <small>{{ sensor.unit || '' }}</small>
              </span>
              <span class="item-time">
                {{ formatTime(sensor.latest_time) }}
              </span>
            </div>
          </div>
          <el-empty
            v-if="!filteredSensors.length"
            description="暂无传感器数据"
            :image-size="80"
          />
        </div>
      </div>

      <!-- 右侧：传感器详情 -->
      <div class="sensor-detail-panel">
        <template v-if="selectedSensor">
          <el-tabs v-model="detailTab" class="detail-tabs">
            <!-- Tab1 实时数据 -->
            <el-tab-pane label="实时数据" name="realtime">
              <div class="realtime-section">
                <el-row :gutter="16">
                  <el-col :span="12">
                    <el-card shadow="never" class="info-card">
                      <template #header>
                        <div class="card-header">
                          <el-icon><InfoFilled /></el-icon>
                          基本信息
                        </div>
                      </template>
                      <el-descriptions :column="1" size="default" border>
                        <el-descriptions-item label="传感器编号">
                          {{ selectedSensor.code }}
                        </el-descriptions-item>
                        <el-descriptions-item label="传感器名称">
                          {{ selectedSensor.name }}
                        </el-descriptions-item>
                        <el-descriptions-item label="类型">
                          <el-tag :type="getSensorTagType(selectedSensor.type)" effect="light">
                            {{ typeLabel(selectedSensor.type) }}
                          </el-tag>
                        </el-descriptions-item>
                        <el-descriptions-item label="安装位置">
                          {{ selectedSensor.location || '--' }}
                        </el-descriptions-item>
                        <el-descriptions-item label="安装时间">
                          {{ formatDate(selectedSensor.install_date) }}
                        </el-descriptions-item>
                        <el-descriptions-item label="状态">
                          <span
                            class="status-badge"
                            :class="selectedSensor.status"
                          >
                            <span class="status-dot small" :class="selectedSensor.status"></span>
                            {{ statusText(selectedSensor.status) }}
                          </span>
                        </el-descriptions-item>
                      </el-descriptions>
                    </el-card>
                  </el-col>

                  <el-col :span="12">
                    <el-card shadow="never" class="info-card">
                      <template #header>
                        <div class="card-header">
                          <el-icon><Cpu /></el-icon>
                          最新读数
                        </div>
                      </template>
                      <div class="latest-reading">
                        <div class="reading-value">
                          {{ selectedSensor.latest_value ?? '--' }}
                          <span class="reading-unit">{{ selectedSensor.unit || '' }}</span>
                        </div>
                        <div class="reading-time">
                          更新时间：{{ formatFullTime(selectedSensor.latest_time) }}
                        </div>
                        <div class="reading-thresholds" v-if="selectedSensor.threshold">
                          <div class="threshold-item">
                            <span>上限值：</span>
                            <b class="val-upper">{{ selectedSensor.threshold.upper ?? '--' }}</b>
                          </div>
                          <div class="threshold-item">
                            <span>下限值：</span>
                            <b class="val-lower">{{ selectedSensor.threshold.lower ?? '--' }}</b>
                          </div>
                        </div>
                      </div>
                    </el-card>

                    <el-card shadow="never" class="info-card" style="margin-top: 16px;">
                      <template #header>
                        <div class="card-header">
                          <el-icon><TrendCharts /></el-icon>
                          统计指标（24h）
                        </div>
                      </template>
                      <div class="metrics-row">
                        <div class="metric-box avg">
                          <div class="metric-label">平均值</div>
                          <div class="metric-num">{{ sensorStats.avg?.toFixed(2) ?? '--' }}</div>
                        </div>
                        <div class="metric-box max">
                          <div class="metric-label">最大值</div>
                          <div class="metric-num">{{ sensorStats.max?.toFixed(2) ?? '--' }}</div>
                        </div>
                        <div class="metric-box min">
                          <div class="metric-label">最小值</div>
                          <div class="metric-num">{{ sensorStats.min?.toFixed(2) ?? '--' }}</div>
                        </div>
                      </div>
                    </el-card>
                  </el-col>
                </el-row>
              </div>
            </el-tab-pane>

            <!-- Tab2 趋势曲线 -->
            <el-tab-pane label="趋势曲线" name="trend">
              <div class="trend-section">
                <div class="trend-toolbar">
                  <div class="time-range-group">
                    <el-radio-group v-model="timeRange" size="default" @change="loadReadings">
                      <el-radio-button value="24h">近24小时</el-radio-button>
                      <el-radio-button value="7d">近7天</el-radio-button>
                      <el-radio-button value="30d">近30天</el-radio-button>
                    </el-radio-group>
                  </div>
                  <div class="field-group">
                    <span class="group-label">物理量叠加：</span>
                    <el-checkbox-group v-model="selectedFields" @change="loadReadings">
                      <el-checkbox
                        v-for="f in availableFields"
                        :key="f.key"
                        :value="f.key"
                        :label="f.key"
                      >
                        {{ f.label }}
                      </el-checkbox>
                    </el-checkbox-group>
                  </div>
                  <el-button size="small" @click="loadReadings">
                    <el-icon><Refresh /></el-icon>
                    刷新数据
                  </el-button>
                </div>

                <div class="chart-container">
                  <v-chart :option="trendChartOption" autoresize style="width: 100%; height: 100%;" />
                </div>
              </div>
            </el-tab-pane>

            <!-- Tab3 读数录入 -->
            <el-tab-pane label="读数录入" name="entry">
              <div class="entry-section">
                <el-row :gutter="20">
                  <!-- 单条录入 -->
                  <el-col :span="12">
                    <el-card shadow="never">
                      <template #header>
                        <div class="card-header">
                          <el-icon><EditPen /></el-icon>
                          单条读数录入
                        </div>
                      </template>
                      <el-form ref="singleFormRef" :model="singleForm" :rules="singleRules" label-width="100px">
                        <el-form-item label="传感器" prop="sensor_id">
                          <el-input :model-value="selectedSensor.name" disabled />
                        </el-form-item>
                        <el-form-item label="采集时间" prop="recorded_at">
                          <el-date-picker
                            v-model="singleForm.recorded_at"
                            type="datetime"
                            class="w-full"
                            placeholder="选择采集时间"
                            value-format="YYYY-MM-DD HH:mm:ss"
                          />
                        </el-form-item>
                        <el-form-item label="物理量" prop="field_key">
                          <el-select v-model="singleForm.field_key" class="w-full">
                            <el-option
                              v-for="f in availableFields"
                              :key="f.key"
                              :label="f.label"
                              :value="f.key"
                            />
                          </el-select>
                        </el-form-item>
                        <el-form-item label="数值" prop="value">
                          <el-input-number v-model="singleForm.value" :precision="4" class="w-full" />
                        </el-form-item>
                        <el-form-item label="备注">
                          <el-input
                            v-model="singleForm.remark"
                            type="textarea"
                            :rows="2"
                            placeholder="选填"
                          />
                        </el-form-item>
                        <el-form-item>
                          <el-button
                            type="primary"
                            class="w-full"
                            :loading="singleSubmitting"
                            @click="submitSingleReading"
                          >
                            <el-icon><Check /></el-icon>
                            提交读数
                          </el-button>
                        </el-form-item>
                      </el-form>
                    </el-card>
                  </el-col>

                  <!-- 批量操作 -->
                  <el-col :span="12">
                    <el-card shadow="never" style="margin-bottom: 16px;">
                      <template #header>
                        <div class="card-header">
                          <el-icon><Upload /></el-icon>
                          批量CSV导入
                        </div>
                      </template>
                      <div class="batch-import">
                        <el-upload
                          drag
                          :auto-upload="false"
                          :on-change="handleCsvFile"
                          accept=".csv"
                          :limit="1"
                        >
                          <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
                          <div class="el-upload__text">
                            拖拽CSV文件到此处，或<em>点击上传</em>
                          </div>
                          <template #tip>
                            <div class="el-upload__tip">
                              格式：recorded_at,field_key,value,remark（CSV，含表头）
                            </div>
                          </template>
                        </el-upload>
                        <el-button
                          style="margin-top: 10px;"
                          type="primary"
                          class="w-full"
                          :disabled="!csvRows.length"
                          :loading="batchSubmitting"
                          @click="submitBatchCsv"
                        >
                          <el-icon><Document /></el-icon>
                          解析并批量导入（{{ csvRows.length }} 条）
                        </el-button>
                      </div>
                    </el-card>

                    <el-card shadow="never">
                      <template #header>
                        <div class="card-header">
                          <el-icon><MagicStick /></el-icon>
                          模拟数据生成
                        </div>
                      </template>
                      <el-form label-width="90px" size="default">
                        <el-form-item label="起始时间">
                          <el-date-picker
                            v-model="simForm.start_time"
                            type="datetime"
                            class="w-full"
                            value-format="YYYY-MM-DD HH:mm:ss"
                          />
                        </el-form-item>
                        <el-form-item label="结束时间">
                          <el-date-picker
                            v-model="simForm.end_time"
                            type="datetime"
                            class="w-full"
                            value-format="YYYY-MM-DD HH:mm:ss"
                          />
                        </el-form-item>
                        <el-form-item label="采集间隔">
                          <el-select v-model="simForm.interval" class="w-full">
                            <el-option label="5 分钟" value="5m" />
                            <el-option label="15 分钟" value="15m" />
                            <el-option label="30 分钟" value="30m" />
                            <el-option label="1 小时" value="1h" />
                            <el-option label="6 小时" value="6h" />
                          </el-select>
                        </el-form-item>
                        <el-form-item label="数值范围">
                          <el-input-number
                            v-model="simForm.min_val"
                            :precision="2"
                            style="width: 45%;"
                          />
                          <span style="padding: 0 8px; color: #94a3b8;">~</span>
                          <el-input-number
                            v-model="simForm.max_val"
                            :precision="2"
                            style="width: 45%;"
                          />
                        </el-form-item>
                        <el-form-item>
                          <el-button
                            type="primary"
                            class="w-full"
                            :loading="simSubmitting"
                            @click="generateSimulatedData"
                          >
                            <el-icon><Lightning /></el-icon>
                            生成模拟读数（调用 batchReadings）
                          </el-button>
                        </el-form-item>
                      </el-form>
                    </el-card>
                  </el-col>
                </el-row>
              </div>
            </el-tab-pane>
          </el-tabs>
        </template>

        <div v-else class="empty-detail">
          <el-empty description="请从左侧选择一个传感器查看详情">
            <template #image>
              <el-icon :size="80" color="#93c5fd"><Mouse /></el-icon>
            </template>
          </el-empty>
        </div>
      </div>
    </div>

    <!-- 新增传感器对话框 -->
    <el-dialog
      v-model="sensorDialogVisible"
      :title="editingSensor ? '编辑传感器' : '新增传感器'"
      width="560px"
      destroy-on-close
    >
      <el-form ref="sensorFormRef" :model="sensorForm" :rules="sensorRules" label-width="100px">
        <el-form-item label="编号" prop="code">
          <el-input v-model="sensorForm.code" placeholder="如：GNSS-001" />
        </el-form-item>
        <el-form-item label="名称" prop="name">
          <el-input v-model="sensorForm.name" placeholder="请输入传感器名称" />
        </el-form-item>
        <el-form-item label="类型" prop="type">
          <el-select v-model="sensorForm.type" class="w-full">
            <el-option
              v-for="t in sensorTypesList"
              :key="t.key"
              :label="t.label"
              :value="t.key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="sensorForm.unit" placeholder="如：mm / MPa / ℃" />
        </el-form-item>
        <el-form-item label="安装位置">
          <el-input v-model="sensorForm.location" placeholder="描述安装位置" />
        </el-form-item>
        <el-form-item label="安装时间">
          <el-date-picker
            v-model="sensorForm.install_date"
            type="date"
            class="w-full"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="阈值上限">
              <el-input-number v-model="sensorForm.upper" :precision="3" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="阈值下限">
              <el-input-number v-model="sensorForm.lower" :precision="3" class="w-full" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="sensorDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="sensorSubmitting" @click="submitSensor">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, h } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  getMonitoringOverview, getSensorTypes,
  listSensors, getSensor, getSensorReadings,
  addSensorReading, batchReadings,
  createSensor, updateSensor, deleteSensor,
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

// ========== 传感器类型配置 ==========
const sensorTypesList = ref([])

const defaultTypes = [
  { key: 'gnss', label: 'GNSS位移', icon: 'LocationFilled', color: '#2563eb' },
  { key: 'inclinometer', label: '测斜仪', icon: 'Aim', color: '#0891b2' },
  { key: 'piezometer', label: '渗压计', icon: 'Watermelon', color: '#0ea5e9' },
  { key: 'strain_gauge', label: '应变计', icon: 'ScaleToOriginal', color: '#6366f1' },
  { key: 'stress_meter', label: '应力计', icon: 'Connection', color: '#8b5cf6' },
  { key: 'thermometer', label: '温度计', icon: 'Sunny', color: '#f59e0b' },
  { key: 'crack_meter', label: '裂缝计', icon: 'Cpu', color: '#dc2626' },
  { key: 'rain_gauge', label: '雨量计', icon: 'Umbrella', color: '#06b6d4' },
]

function typeLabel(k) {
  const found = sensorTypesList.value.find(t => t.key === k) || defaultTypes.find(t => t.key === k)
  return found?.label || k
}
function getSensorTypeColor(k) {
  const found = sensorTypesList.value.find(t => t.key === k) || defaultTypes.find(t => t.key === k)
  return found?.color || '#2563eb'
}
function getSensorTypeIcon(k) {
  const found = defaultTypes.find(t => t.key === k)
  return found?.icon || 'Monitor'
}
function getSensorTagType(k) {
  const map = {
    gnss: 'primary', inclinometer: 'success', piezometer: 'info',
    strain_gauge: '', stress_meter: 'warning', thermometer: 'warning',
    crack_meter: 'danger', rain_gauge: 'info',
  }
  return map[k] || 'info'
}

// ========== 概览数据 ==========
const overview = ref({})
const typeCountMap = ref({})

async function loadOverview() {
  try {
    const res = await getMonitoringOverview()
    const raw = unwrapObject(res, {})
    // 后端字段兼容：reading_count_24h -> readings_24h；by_type 数组转对象 map
    overview.value = {
      total_sensors: raw.total_sensors ?? 0,
      readings_24h: raw.readings_24h ?? raw.reading_count_24h ?? 0,
      abnormal_count: raw.abnormal_count ?? 0,
      by_type: Array.isArray(raw.by_type)
        ? raw.by_type.reduce((acc, t) => { acc[t.type || t.key] = t.count ?? 0; return acc }, {})
        : (raw.by_type || {}),
    }
    typeCountMap.value = overview.value.by_type || {}
  } catch {
    overview.value = {
      total_sensors: 48,
      readings_24h: 18426,
      abnormal_count: 3,
      by_type: {
        gnss: 12, inclinometer: 8, piezometer: 6,
        strain_gauge: 10, stress_meter: 5, thermometer: 4,
        crack_meter: 2, rain_gauge: 1,
      },
    }
    typeCountMap.value = overview.value.by_type
  }
}

async function loadSensorTypes() {
  try {
    const res = await getSensorTypes()
    const raw = unwrapList(res, [])
    // 后端返回 [{type,label}] -> 前端 [{key,label,icon,color}]
    sensorTypesList.value = raw.map(t => {
      const base = defaultTypes.find(d => d.key === t.type) || {}
      return {
        key: t.key || t.type,
        label: t.label || base.label || t.type,
        icon: t.icon || base.icon || 'Monitor',
        color: t.color || base.color || '#2563eb',
      }
    })
  } catch {
    sensorTypesList.value = defaultTypes
  }
}

// ========== 传感器列表 ==========
const sensorList = ref([])
const sensorListLoading = ref(false)
const filterType = ref('')
const filterKeyword = ref('')
const filterAbnormalOnly = ref(false)
const selectedSensor = ref(null)

const filteredSensors = computed(() => {
  let list = sensorList.value
  if (filterType.value) list = list.filter(s => s.type === filterType.value)
  if (filterKeyword.value) {
    const kw = filterKeyword.value.toLowerCase()
    list = list.filter(s =>
      s.code?.toLowerCase().includes(kw) ||
      s.name?.toLowerCase().includes(kw) ||
      s.location?.toLowerCase().includes(kw)
    )
  }
  if (filterAbnormalOnly.value) list = list.filter(s => s.status === 'abnormal')
  return list
})

async function loadSensors() {
  sensorListLoading.value = true
  try {
    const res = await listSensors()
    const raw = unwrapList(res, [])
    // 字段兼容：sensor_type->type；last_value->latest_value；last_time->latest_time；补 status/threshold/unit/location/install_date
    sensorList.value = raw.map(s => {
      const stype = s.type || s.sensor_type
      const lval = s.latest_value ?? s.last_value
      const thr = s.threshold || { upper: null, lower: null }
      let status = s.status || 'normal'
      if (!s.status && thr.upper != null && lval > thr.upper) status = 'abnormal'
      else if (!s.status && thr.lower != null && lval < thr.lower) status = 'warning'
      const defaultUnit = defaultTypes.find(d => d.key === stype)?.label.match(/\(([^)]+)\)/)?.[1] || ''
      return {
        ...s,
        type: stype,
        code: s.code || s.sensor_code,
        name: s.name || s.sensor_name,
        unit: s.unit || defaultUnit,
        latest_value: lval,
        latest_time: s.latest_time ?? s.last_time,
        threshold: {
          upper: thr.upper ?? s.upper ?? null,
          lower: thr.lower ?? s.lower ?? null,
        },
        location: s.location || s.install_location || s.install_pos || '',
        install_date: s.install_date || s.created_at || '',
        status,
      }
    })
  } catch {
    sensorList.value = [
      { id: 1, code: 'GNSS-001', name: 'I区马道GNSS位移-1号', type: 'gnss', unit: 'mm', location: '坝肩左岸I区马道高程540m', install_date: '2024-03-15', latest_value: 23.45, latest_time: new Date(Date.now() - 5 * 60000).toISOString(), status: 'normal', threshold: { upper: 50, lower: -50 } },
      { id: 2, code: 'GNSS-002', name: 'II区坡面GNSS位移-2号', type: 'gnss', unit: 'mm', location: '坝肩左岸II区坡面高程510m', install_date: '2024-03-15', latest_value: 48.72, latest_time: new Date(Date.now() - 4 * 60000).toISOString(), status: 'warning', threshold: { upper: 50, lower: -50 } },
      { id: 3, code: 'INC-005', name: 'F1断层测斜-5号', type: 'inclinometer', unit: 'mm/m', location: 'F1断层带', install_date: '2024-04-02', latest_value: 56.83, latest_time: new Date(Date.now() - 10 * 60000).toISOString(), status: 'abnormal', threshold: { upper: 50, lower: -50 } },
      { id: 4, code: 'PZ-003', name: 'III区渗压计-3号', type: 'piezometer', unit: 'kPa', location: 'III区排水廊道', install_date: '2024-04-10', latest_value: 185.6, latest_time: new Date(Date.now() - 15 * 60000).toISOString(), status: 'normal', threshold: { upper: 300, lower: 0 } },
      { id: 5, code: 'SG-012', name: 'II级马道应变计-12号', type: 'strain_gauge', unit: 'με', location: 'II级马道内侧', install_date: '2024-04-20', latest_value: 286.4, latest_time: new Date(Date.now() - 8 * 60000).toISOString(), status: 'normal', threshold: { upper: 500, lower: -500 } },
      { id: 6, code: 'SM-004', name: '支护应力计-4号', type: 'stress_meter', unit: 'MPa', location: '锚索支护段', install_date: '2024-05-05', latest_value: 3.82, latest_time: new Date(Date.now() - 12 * 60000).toISOString(), status: 'normal', threshold: { upper: 10, lower: 0 } },
      { id: 7, code: 'TH-002', name: '环境温度计-2号', type: 'thermometer', unit: '℃', location: 'I区气象站', install_date: '2024-03-01', latest_value: 26.8, latest_time: new Date(Date.now() - 3 * 60000).toISOString(), status: 'normal', threshold: { upper: 50, lower: -20 } },
      { id: 8, code: 'CM-001', name: '裂缝计-J1节理', type: 'crack_meter', unit: 'mm', location: 'J1节理张开缝', install_date: '2024-06-01', latest_value: 2.15, latest_time: new Date(Date.now() - 20 * 60000).toISOString(), status: 'abnormal', threshold: { upper: 2, lower: 0 } },
      { id: 9, code: 'RG-001', name: '区域雨量计', type: 'rain_gauge', unit: 'mm', location: '坝区气象站', install_date: '2024-03-01', latest_value: 0.4, latest_time: new Date(Date.now() - 30 * 60000).toISOString(), status: 'normal', threshold: { upper: 100, lower: 0 } },
      { id: 10, code: 'GNSS-003', name: 'III区GNSS位移-3号', type: 'gnss', unit: 'mm', location: 'III区坡顶高程560m', install_date: '2024-03-16', latest_value: 15.32, latest_time: new Date(Date.now() - 6 * 60000).toISOString(), status: 'normal', threshold: { upper: 50, lower: -50 } },
      { id: 11, code: 'INC-006', name: 'S1夹层测斜-6号', type: 'inclinometer', unit: 'mm/m', location: 'S1软弱夹层', install_date: '2024-04-03', latest_value: 32.18, latest_time: new Date(Date.now() - 11 * 60000).toISOString(), status: 'warning', threshold: { upper: 50, lower: -50 } },
      { id: 12, code: 'CM-002', name: '裂缝计-J2节理', type: 'crack_meter', unit: 'mm', location: 'J2节理', install_date: '2024-06-02', latest_value: 1.28, latest_time: new Date(Date.now() - 25 * 60000).toISOString(), status: 'normal', threshold: { upper: 2, lower: 0 } },
    ]
  } finally {
    sensorListLoading.value = false
    if (sensorList.value.length && !selectedSensor.value) {
      selectSensor(sensorList.value[0])
    }
  }
}

async function selectSensor(sensor) {
  selectedSensor.value = sensor
  try {
    const res = await getSensor(sensor.id)
    const raw = unwrapObject(res, null)
    if (raw) {
      const stype = raw.type || raw.sensor_type
      const lval = raw.latest_value ?? raw.last_value ?? raw.avg_value
      const thr = raw.threshold || { upper: raw.upper ?? null, lower: raw.lower ?? null }
      let status = raw.status || sensor.status || 'normal'
      if (!raw.status && thr.upper != null && lval > thr.upper) status = 'abnormal'
      else if (!raw.status && thr.lower != null && lval < thr.lower) status = 'warning'
      Object.assign(sensor, {
        ...raw,
        type: stype,
        code: raw.code || raw.sensor_code || sensor.code,
        name: raw.name || raw.sensor_name || sensor.name,
        unit: raw.unit || sensor.unit,
        latest_value: lval,
        latest_time: raw.latest_time ?? raw.last_time ?? sensor.latest_time,
        threshold: {
          upper: thr.upper ?? raw.upper ?? sensor.threshold?.upper,
          lower: thr.lower ?? raw.lower ?? sensor.threshold?.lower,
        },
        location: raw.location || raw.install_location || sensor.location,
        install_date: raw.install_date || raw.created_at || sensor.install_date,
        status,
      })
    }
  } catch { /* ignore */ }
  loadSensorStats()
  loadReadings()
}

function statusText(s) {
  return { normal: '正常', warning: '预警', abnormal: '异常', offline: '离线' }[s] || s
}

// ========== 详情Tab ==========
const detailTab = ref('realtime')
const sensorStats = reactive({ avg: null, max: null, min: null })

async function loadSensorStats() {
  if (!selectedSensor.value) return
  try {
    const res = await getSensorReadings(selectedSensor.value.id, { range: '24h', field_key: 'value', agg: 'stats' })
    const raw = unwrapObject(res, {})
    // 后端 stats 可能在 raw.stats 子对象，也可能直接在 raw
    const d = raw.stats || raw
    sensorStats.avg = d?.avg ?? d?.average ?? null
    sensorStats.max = d?.max ?? d?.max_value ?? null
    sensorStats.min = d?.min ?? d?.min_value ?? null
  } catch {
    sensorStats.avg = (selectedSensor.value.latest_value ?? 0) * 0.98
    sensorStats.max = (selectedSensor.value.latest_value ?? 0) * 1.15
    sensorStats.min = (selectedSensor.value.latest_value ?? 0) * 0.82
  }
}

// ========== 趋势曲线 ==========
const timeRange = ref('24h')
const availableFields = computed(() => {
  const type = selectedSensor.value?.type
  const map = {
    gnss: [
      { key: 'total', label: '总位移', yAxisIndex: 0, unit: 'mm' },
      { key: 'x', label: 'X方向', yAxisIndex: 0, unit: 'mm' },
      { key: 'y', label: 'Y方向', yAxisIndex: 0, unit: 'mm' },
      { key: 'z', label: 'Z方向', yAxisIndex: 0, unit: 'mm' },
    ],
    inclinometer: [
      { key: 'value', label: '累计位移', yAxisIndex: 0, unit: 'mm/m' },
      { key: 'rate', label: '变化速率', yAxisIndex: 1, unit: 'mm/d' },
    ],
    piezometer: [
      { key: 'value', label: '孔隙水压力', yAxisIndex: 0, unit: 'kPa' },
      { key: 'level', label: '水位高度', yAxisIndex: 1, unit: 'm' },
    ],
    strain_gauge: [
      { key: 'value', label: '应变值', yAxisIndex: 0, unit: 'με' },
      { key: 'temp', label: '温度补偿', yAxisIndex: 1, unit: '℃' },
    ],
    stress_meter: [
      { key: 'value', label: '应力值', yAxisIndex: 0, unit: 'MPa' },
    ],
    thermometer: [
      { key: 'value', label: '温度', yAxisIndex: 0, unit: '℃' },
    ],
    crack_meter: [
      { key: 'value', label: '裂缝宽度', yAxisIndex: 0, unit: 'mm' },
      { key: 'rate', label: '扩展速率', yAxisIndex: 1, unit: 'mm/d' },
    ],
    rain_gauge: [
      { key: 'value', label: '降雨量', yAxisIndex: 0, unit: 'mm' },
    ],
  }
  return map[type] || [{ key: 'value', label: '数值', yAxisIndex: 0, unit: selectedSensor.value?.unit || '' }]
})
const selectedFields = ref(['value'])

watch(() => selectedSensor.value?.id, () => {
  const defaultField = availableFields.value[0]?.key || 'value'
  selectedFields.value = [defaultField]
}, { immediate: true })

const readingsData = ref({})

async function loadReadings() {
  if (!selectedSensor.value) return
  readingsData.value = {}
  try {
    for (const field of selectedFields.value) {
      const res = await getSensorReadings(selectedSensor.value.id, {
        range: timeRange.value,
        field_key: field,
      })
      const raw = unwrapObject(res, {})
      // 后端读数数据在 raw.data (list)；也兼容 items/list 包装
      const arr = Array.isArray(raw.data) ? raw.data
        : Array.isArray(raw.items) ? raw.items
        : Array.isArray(raw.list) ? raw.list
        : Array.isArray(res.data?.data) ? res.data.data
        : []
      // 字段映射：time -> recorded_at，field_key 映射 value 保留
      readingsData.value[field] = arr.map(r => ({
        recorded_at: r.recorded_at || r.time || r.timestamp || '',
        value: r.value,
        field_key: r.field_key || field,
      }))
    }
  } catch {
    // mock
    for (const field of selectedFields.value) {
      readingsData.value[field] = generateMockReadings(field, timeRange.value)
    }
  }
}

function generateMockReadings(field, range) {
  const now = Date.now()
  const counts = { '24h': 96, '7d': 168, '30d': 360 }
  const steps = { '24h': 15 * 60000, '7d': 60 * 60000, '30d': 2 * 60 * 60000 }
  const count = counts[range] || 96
  const step = steps[range] || 900000
  const base = (selectedSensor.value?.latest_value ?? 20)
  const amp = { total: 5, x: 3, y: 3, z: 4, value: 8, rate: 2, level: 0.5, temp: 3 }[field] || 5
  const items = []
  for (let i = count - 1; i >= 0; i--) {
    const t = new Date(now - i * step)
    const phase = Math.sin(i * 0.1 + field.length) * amp
    const drift = (count - i) / count * amp * 0.3
    const noise = (Math.random() - 0.5) * amp * 0.4
    items.push({
      recorded_at: formatFullTime(t.toISOString()),
      value: Number((base + phase + drift + noise).toFixed(3)),
    })
  }
  return items
}

const trendChartOption = computed(() => {
  const fieldCfgs = availableFields.value.filter(f => selectedFields.value.includes(f.key))
  if (!fieldCfgs.length) return {}

  // 找一个基础时间轴
  const firstField = fieldCfgs[0].key
  const baseSeries = readingsData.value[firstField] || []
  const xAxisData = baseSeries.map(i => i.recorded_at)

  const series = fieldCfgs.map((f, idx) => {
    const data = (readingsData.value[f.key] || []).map(i => i.value)
    const colors = ['#2563eb', '#0891b2', '#8b5cf6', '#f59e0b', '#dc2626', '#059669']
    return {
      name: f.label,
      type: 'line',
      smooth: true,
      showSymbol: false,
      yAxisIndex: f.yAxisIndex || 0,
      lineStyle: { width: 2, color: colors[idx % colors.length] },
      itemStyle: { color: colors[idx % colors.length] },
      areaStyle: idx === 0 ? {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: colors[idx % colors.length] + '30' },
            { offset: 1, color: colors[idx % colors.length] + '05' },
          ],
        },
      } : undefined,
      data,
    }
  })

  const yAxisList = [
    {
      type: 'value',
      name: fieldCfgs.filter(f => (f.yAxisIndex || 0) === 0).map(f => f.unit).join('/'),
      position: 'left',
      axisLine: { show: true, lineStyle: { color: '#2563eb' } },
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      axisLabel: { color: '#64748b', fontSize: 11 },
    },
  ]
  if (fieldCfgs.some(f => f.yAxisIndex === 1)) {
    yAxisList.push({
      type: 'value',
      name: fieldCfgs.filter(f => (f.yAxisIndex || 0) === 1).map(f => f.unit).join('/'),
      position: 'right',
      axisLine: { show: true, lineStyle: { color: '#8b5cf6' } },
      splitLine: { show: false },
      nameTextStyle: { color: '#64748b', fontSize: 11 },
      axisLabel: { color: '#64748b', fontSize: 11 },
    })
  }

  return {
    tooltip: { trigger: 'axis', backgroundColor: 'rgba(15,23,42,0.92)', borderWidth: 0, textStyle: { color: '#fff', fontSize: 12 } },
    legend: { top: 4, textStyle: { color: '#475569' }, icon: 'roundRect' },
    grid: { left: 60, right: yAxisList.length > 1 ? 60 : 20, top: 40, bottom: 50 },
    xAxis: {
      type: 'category',
      data: xAxisData,
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      axisLabel: { color: '#64748b', fontSize: 11, rotate: timeRange.value === '30d' ? 30 : 0 },
    },
    yAxis: yAxisList,
    dataZoom: [{ type: 'inside' }, { type: 'slider', height: 18, bottom: 8, borderColor: 'transparent' }],
    series,
  }
})

// ========== 读数录入 - 单条 ==========
const singleFormRef = ref()
const singleSubmitting = ref(false)
const singleForm = reactive({
  recorded_at: '',
  field_key: 'value',
  value: 0,
  remark: '',
})
const singleRules = {
  recorded_at: [{ required: true, message: '请选择采集时间', trigger: 'change' }],
  field_key: [{ required: true, message: '请选择物理量', trigger: 'change' }],
  value: [{ required: true, message: '请输入数值', trigger: 'blur' }],
}

async function submitSingleReading() {
  await singleFormRef.value?.validate()
  singleSubmitting.value = true
  try {
    await addSensorReading(selectedSensor.value.id, {
      recorded_at: singleForm.recorded_at,
      field_key: singleForm.field_key,
      value: singleForm.value,
      remark: singleForm.remark,
    })
    ElMessage.success('读数录入成功')
    singleForm.recorded_at = ''
    singleForm.value = 0
    singleForm.remark = ''
    loadSensors()
    loadReadings()
  } finally {
    singleSubmitting.value = false
  }
}

// ========== 读数录入 - 批量CSV ==========
const csvRows = ref([])
const batchSubmitting = ref(false)

function handleCsvFile(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    const text = e.target.result
    const lines = text.split(/\r?\n/).filter(l => l.trim())
    const headers = lines.shift()?.split(',') || []
    csvRows.value = lines.map(line => {
      const cols = line.split(',')
      const obj = {}
      headers.forEach((h, i) => { obj[h.trim()] = cols[i]?.trim() })
      return obj
    })
    ElMessage.success(`已解析 ${csvRows.value.length} 条数据`)
  }
  reader.readAsText(file.raw)
}

async function submitBatchCsv() {
  if (!csvRows.value.length) return
  batchSubmitting.value = true
  try {
    const readings = csvRows.value.map(r => ({
      sensor_id: selectedSensor.value.id,
      recorded_at: r.recorded_at,
      field_key: r.field_key || 'value',
      value: Number(r.value),
      remark: r.remark || '',
    }))
    await batchReadings({ readings })
    ElMessage.success(`成功导入 ${readings.length} 条读数`)
    csvRows.value = []
    loadSensors()
    loadReadings()
  } finally {
    batchSubmitting.value = false
  }
}

// ========== 模拟数据生成 ==========
const simSubmitting = ref(false)
const simForm = reactive({
  start_time: '',
  end_time: '',
  interval: '15m',
  min_val: 0,
  max_val: 100,
})

function intervalToMs(iv) {
  const map = { '5m': 5 * 60, '15m': 15 * 60, '30m': 30 * 60, '1h': 60 * 60, '6h': 6 * 60 * 60 }
  return (map[iv] || 900) * 1000
}

async function generateSimulatedData() {
  if (!simForm.start_time || !simForm.end_time) {
    ElMessage.warning('请设置起始和结束时间')
    return
  }
  simSubmitting.value = true
  try {
    const start = new Date(simForm.start_time).getTime()
    const end = new Date(simForm.end_time).getTime()
    const step = intervalToMs(simForm.interval)
    const readings = []
    const span = simForm.max_val - simForm.min_val
    for (let t = start; t <= end; t += step) {
      const rnd = Math.random()
      readings.push({
        sensor_id: selectedSensor.value.id,
        recorded_at: formatFullTime(new Date(t).toISOString()),
        field_key: selectedFields.value[0] || 'value',
        value: Number((simForm.min_val + rnd * span).toFixed(3)),
      })
    }
    await batchReadings({ readings })
    ElMessage.success(`已生成并提交 ${readings.length} 条模拟读数`)
    loadSensors()
    loadReadings()
  } finally {
    simSubmitting.value = false
  }
}

// ========== 新增/编辑传感器 ==========
const sensorDialogVisible = ref(false)
const editingSensor = ref(null)
const sensorSubmitting = ref(false)
const sensorFormRef = ref()
const sensorForm = reactive({
  code: '', name: '', type: '', unit: '',
  location: '', install_date: '',
  upper: null, lower: null,
})
const sensorRules = {
  code: [{ required: true, message: '请输入编号', trigger: 'blur' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  type: [{ required: true, message: '请选择类型', trigger: 'change' }],
}

function openSensorDialog(row = null) {
  editingSensor.value = row
  if (row) {
    Object.assign(sensorForm, {
      code: row.code, name: row.name, type: row.type, unit: row.unit,
      location: row.location || '', install_date: row.install_date || '',
      upper: row.threshold?.upper ?? null,
      lower: row.threshold?.lower ?? null,
    })
  } else {
    Object.assign(sensorForm, {
      code: '', name: '', type: '', unit: '',
      location: '', install_date: '',
      upper: null, lower: null,
    })
  }
  sensorDialogVisible.value = true
}

async function submitSensor() {
  await sensorFormRef.value?.validate()
  sensorSubmitting.value = true
  try {
    const payload = {
      code: sensorForm.code,
      name: sensorForm.name,
      type: sensorForm.type,
      unit: sensorForm.unit,
      location: sensorForm.location,
      install_date: sensorForm.install_date,
      threshold: { upper: sensorForm.upper, lower: sensorForm.lower },
    }
    if (editingSensor.value) {
      await updateSensor(editingSensor.value.id, payload)
      ElMessage.success('已更新')
    } else {
      await createSensor(payload)
      ElMessage.success('已创建')
    }
    sensorDialogVisible.value = false
    loadSensors()
    loadOverview()
  } finally {
    sensorSubmitting.value = false
  }
}

// ========== 工具函数 ==========
function formatNumber(n) {
  if (n == null) return '0'
  return n.toLocaleString('zh-CN')
}
function formatTime(iso) {
  if (!iso) return '--'
  const d = new Date(iso)
  const now = new Date()
  const diff = (now - d) / 1000
  if (diff < 60) return `${Math.floor(diff)}秒前`
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`
  return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}
function formatFullTime(iso) {
  if (!iso) return '--'
  const d = new Date(iso)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}:${String(d.getSeconds()).padStart(2, '0')}`
}
function formatDate(d) {
  if (!d) return '--'
  const dt = typeof d === 'string' ? new Date(d) : d
  return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
}

// ========== 初始化 ==========
onMounted(() => {
  loadSensorTypes()
  loadOverview()
  loadSensors()
})
</script>

<style scoped>
.monitoring-info-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  height: calc(100vh - 110px);
  padding: 8px 4px;
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: 1fr 1.5fr 1fr 1fr;
  gap: 14px;
  flex-shrink: 0;
}
.stat-card {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 16px 18px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
  position: relative;
  overflow: hidden;
}
.stat-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 4px; height: 100%;
}
.stat-total::before { background: #2563eb; }
.stat-types::before { background: #8b5cf6; }
.stat-readings::before { background: #0891b2; }
.stat-alert::before { background: #dc2626; }
.stat-icon {
  width: 52px; height: 52px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-total .stat-icon { background: #dbeafe; color: #2563eb; }
.stat-types .stat-icon { background: #ede9fe; color: #8b5cf6; }
.stat-readings .stat-icon { background: #cffafe; color: #0891b2; }
.stat-alert .stat-icon { background: #fee2e2; color: #dc2626; }
.stat-body { flex: 1; min-width: 0; }
.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.1;
  font-family: 'Inter', 'Consolas', monospace;
}
.stat-value.is-alert { color: #dc2626; animation: pulse-alert 1.6s infinite; }
.stat-unit { font-size: 13px; font-weight: 500; color: #64748b; margin-left: 4px; }
.stat-label {
  font-size: 12.5px;
  color: #64748b;
  margin-top: 4px;
}
.stat-types-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.type-chip {
  display: flex;
  align-items: center;
  gap: 5px;
  padding: 3px 8px;
  border-radius: 10px;
  border: 1px solid;
  font-size: 11.5px;
  font-weight: 500;
}
.chip-count { font-weight: 700; }

/* 主体区域 */
.main-content {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: 3fr 9fr;
  gap: 14px;
}

/* 传感器列表 */
.sensor-list-panel {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid #f1f5f9;
  background: linear-gradient(180deg, #f8fafc, #fff);
}
.panel-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  color: #0f172a;
}
.panel-title .el-icon { color: #2563eb; }
.list-filters {
  padding: 12px;
  border-bottom: 1px solid #f1f5f9;
}
.sensor-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}
.sensor-item {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  margin-bottom: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
}
.sensor-item:hover {
  border-color: #93c5fd;
  background: #f0f7ff;
}
.sensor-item.active {
  border-color: #2563eb;
  background: linear-gradient(135deg, #eff6ff, #dbeafe);
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.15);
}
.sensor-item.abnormal:not(.active) {
  border-color: #fecaca;
  background: #fef2f2;
}
.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}
.item-id {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 700;
  font-family: 'Consolas', monospace;
}
.type-icon { font-size: 14px; }
.item-name {
  font-size: 12.5px;
  color: #334155;
  margin-bottom: 6px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.item-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.item-value {
  font-size: 13px;
  font-weight: 700;
  color: #0f172a;
  font-family: 'Consolas', monospace;
}
.item-value small {
  font-weight: 500;
  color: #64748b;
  font-size: 10.5px;
  margin-left: 2px;
}
.item-time {
  font-size: 10.5px;
  color: #94a3b8;
}

/* 状态点 */
.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
  box-shadow: 0 0 0 2px rgba(255,255,255,0.8);
}
.status-dot.small { width: 7px; height: 7px; box-shadow: none; }
.status-dot.normal { background: #10b981; box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2); }
.status-dot.warning { background: #f59e0b; box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2); animation: pulse-alert 2s infinite; }
.status-dot.abnormal { background: #dc2626; box-shadow: 0 0 0 2px rgba(220, 38, 38, 0.2); animation: pulse-alert 1.2s infinite; }
.status-dot.offline { background: #94a3b8; }
@keyframes pulse-alert {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.6; transform: scale(1.15); }
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}
.status-badge.normal { background: #d1fae5; color: #047857; }
.status-badge.warning { background: #fef3c7; color: #b45309; }
.status-badge.abnormal { background: #fee2e2; color: #b91c1c; }
.status-badge.offline { background: #f1f5f9; color: #475569; }

/* 详情面板 */
.sensor-detail-panel {
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
.detail-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.detail-tabs :deep(.el-tabs__header) { margin: 0 16px; }
.detail-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
  padding: 12px 16px 16px;
  min-height: 0;
}
.empty-detail {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Tab1 实时数据 */
.realtime-section { height: 100%; }
.info-card { border: 1px solid #e2e8f0; }
.card-header {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 600;
  font-size: 14px;
  color: #0f172a;
}
.card-header .el-icon { color: #2563eb; }
.latest-reading { padding: 8px 4px; }
.reading-value {
  font-size: 40px;
  font-weight: 700;
  color: #2563eb;
  text-align: center;
  font-family: 'Inter', 'Consolas', monospace;
  line-height: 1.2;
  margin: 6px 0;
}
.reading-unit {
  font-size: 16px;
  font-weight: 500;
  color: #64748b;
  margin-left: 6px;
}
.reading-time {
  text-align: center;
  font-size: 12px;
  color: #94a3b8;
  margin-bottom: 12px;
}
.reading-thresholds {
  display: flex;
  justify-content: space-around;
  padding: 10px;
  background: #f8fafc;
  border-radius: 8px;
  font-size: 12.5px;
}
.val-upper { color: #dc2626; }
.val-lower { color: #2563eb; }

.metrics-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}
.metric-box {
  padding: 12px 8px;
  border-radius: 8px;
  text-align: center;
}
.metric-box.avg { background: #eff6ff; border: 1px solid #bfdbfe; }
.metric-box.max { background: #fef2f2; border: 1px solid #fecaca; }
.metric-box.min { background: #ecfdf5; border: 1px solid #bbf7d0; }
.metric-label { font-size: 12px; color: #64748b; margin-bottom: 4px; }
.metric-num {
  font-size: 20px;
  font-weight: 700;
  font-family: 'Consolas', monospace;
}
.metric-box.avg .metric-num { color: #1d4ed8; }
.metric-box.max .metric-num { color: #b91c1c; }
.metric-box.min .metric-num { color: #047857; }

/* Tab2 趋势曲线 */
.trend-section {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.trend-toolbar {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 8px;
  flex-wrap: wrap;
}
.group-label {
  font-size: 12.5px;
  color: #475569;
  font-weight: 500;
  margin-right: 4px;
}
.field-group {
  display: flex;
  align-items: center;
  flex: 1;
  flex-wrap: wrap;
  gap: 4px;
}
.chart-container {
  flex: 1;
  min-height: 360px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 8px;
}

/* Tab3 读数录入 */
.entry-section { height: 100%; }
.batch-import { padding: 4px; }
.el-upload__tip { color: #94a3b8; font-size: 11.5px; }

.w-full { width: 100%; }

/* 响应式 */
@media (max-width: 1280px) {
  .stats-row { grid-template-columns: 1fr 1fr; }
}
</style>
