<template>
  <div class="param-inference-page">
    <div class="page-header">
      <div class="header-left">
        <el-icon :size="22" color="#2563eb"><Cpu /></el-icon>
        <h2 class="page-title">参数繁衍模块</h2>
        <span class="page-sub">基于地质与开挖参数，反演衍生设计指标与系统建议</span>
      </div>
    </div>

    <el-row :gutter="16" class="main-row">
      <!-- 左列：参数输入 -->
      <el-col :span="10" class="col-left">
        <el-card shadow="never" class="params-card">
          <template #header>
            <div class="card-header">
              <el-icon color="#2563eb"><Setting /></el-icon>
              <span>参数输入</span>
              <span class="hint">共 4 组 · {{ totalFields }} 项参数</span>
            </div>
          </template>

          <el-collapse v-model="activeCollapse" class="params-collapse">
            <!-- 1. 材料参数 -->
            <el-collapse-item title="1. 材料参数" name="material">
              <div class="param-grid">
                <div
                  v-for="f in groups.material"
                  :key="f.key"
                  class="param-item"
                >
                  <el-form-item
                    :label="f.label"
                    class="param-form-item"
                  >
                    <div class="param-input-wrap">
                      <el-input-number
                        v-model="formValues[f.key]"
                        :min="f.meta?.range?.[0]"
                        :max="f.meta?.range?.[1]"
                        :step="f.meta?.step || 1"
                        :precision="f.meta?.precision ?? 2"
                        controls-position="right"
                        size="default"
                        class="param-number"
                      />
                      <span class="param-unit">{{ f.unit }}</span>
                    </div>
                    <div class="param-tip" v-if="f.meta?.range">
                      范围：{{ f.meta.range[0] }} ~ {{ f.meta.range[1] }} {{ f.unit }}
                    </div>
                  </el-form-item>
                </div>
              </div>
            </el-collapse-item>

            <!-- 2. 开挖参数 -->
            <el-collapse-item title="2. 开挖参数" name="excavation">
              <div class="param-grid">
                <div
                  v-for="f in groups.excavation"
                  :key="f.key"
                  class="param-item"
                >
                  <el-form-item
                    :label="f.label"
                    class="param-form-item"
                  >
                    <div class="param-input-wrap">
                      <el-input-number
                        v-model="formValues[f.key]"
                        :min="f.meta?.range?.[0]"
                        :max="f.meta?.range?.[1]"
                        :step="f.meta?.step || 0.5"
                        :precision="f.meta?.precision ?? 2"
                        controls-position="right"
                        size="default"
                        class="param-number"
                      />
                      <span class="param-unit">{{ f.unit }}</span>
                    </div>
                    <div class="param-tip" v-if="f.meta?.range">
                      范围：{{ f.meta.range[0] }} ~ {{ f.meta.range[1] }} {{ f.unit }}
                    </div>
                  </el-form-item>
                </div>
              </div>
            </el-collapse-item>

            <!-- 3. 安全系数 -->
            <el-collapse-item title="3. 安全系数" name="safety">
              <div class="param-grid">
                <div
                  v-for="f in groups.safety"
                  :key="f.key"
                  class="param-item"
                >
                  <el-form-item
                    :label="f.label"
                    class="param-form-item"
                  >
                    <div class="param-input-wrap">
                      <el-input-number
                        v-model="formValues[f.key]"
                        :min="f.meta?.range?.[0]"
                        :max="f.meta?.range?.[1]"
                        :step="f.meta?.step || 0.05"
                        :precision="f.meta?.precision ?? 3"
                        controls-position="right"
                        size="default"
                        class="param-number"
                      />
                      <span class="param-unit">{{ f.unit }}</span>
                    </div>
                    <div class="param-tip" v-if="f.meta?.range">
                      范围：{{ f.meta.range[0] }} ~ {{ f.meta.range[1] }}
                    </div>
                  </el-form-item>
                </div>
              </div>
            </el-collapse-item>

            <!-- 4. 计算设置 -->
            <el-collapse-item title="4. 计算设置" name="calc">
              <div class="param-grid">
                <div
                  v-for="f in groups.calc"
                  :key="f.key"
                  class="param-item"
                >
                  <el-form-item
                    :label="f.label"
                    class="param-form-item"
                  >
                    <el-select
                      v-if="f.type === 'select'"
                      v-model="formValues[f.key]"
                      class="w-full"
                    >
                      <el-option
                        v-for="opt in f.meta?.options || []"
                        :key="opt.value"
                        :label="opt.label"
                        :value="opt.value"
                      />
                    </el-select>
                    <div v-else class="param-input-wrap">
                      <el-input-number
                        v-model="formValues[f.key]"
                        :min="f.meta?.range?.[0]"
                        :max="f.meta?.range?.[1]"
                        :step="f.meta?.step || 10"
                        :precision="f.meta?.precision ?? 0"
                        controls-position="right"
                        size="default"
                        class="param-number"
                      />
                      <span class="param-unit">{{ f.unit }}</span>
                    </div>
                    <div class="param-tip" v-if="f.meta?.range">
                      范围：{{ f.meta.range[0] }} ~ {{ f.meta.range[1] }}
                    </div>
                  </el-form-item>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>

          <div class="params-actions">
            <el-button @click="handleReset">
              <el-icon><Refresh /></el-icon>
              重置默认
            </el-button>
            <el-button
              type="primary"
              :loading="calculating"
              @click="handleCalculate"
            >
              <el-icon><DataAnalysis /></el-icon>
              {{ calculating ? '正在计算...' : '开始计算' }}
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 中列：衍生结果 -->
      <el-col :span="8" class="col-middle">
        <el-card shadow="never" class="result-card">
          <template #header>
            <div class="card-header">
              <el-icon color="#059669"><DataLine /></el-icon>
              <span>衍生参数与指标</span>
            </div>
          </template>

          <div class="metric-cards">
            <div class="metric-card mc-blue">
              <div class="mc-label">总层数</div>
              <div class="mc-value">{{ derived.totalLayers ?? '--' }}</div>
              <div class="mc-unit">层</div>
            </div>
            <div class="metric-card mc-cyan">
              <div class="mc-label">边坡水平宽度</div>
              <div class="mc-value">{{ formatNum(derived.slopeWidth) }}</div>
              <div class="mc-unit">m</div>
            </div>
            <div class="metric-card mc-indigo">
              <div class="mc-label">断面面积</div>
              <div class="mc-value">{{ formatNum(derived.sectionArea) }}</div>
              <div class="mc-unit">m²</div>
            </div>
            <div class="metric-card mc-violet">
              <div class="mc-label">开挖总方量</div>
              <div class="mc-value">{{ formatNum(derived.totalVolume) }}</div>
              <div class="mc-unit">m³</div>
            </div>
            <div class="metric-card mc-orange">
              <div class="mc-label">土体重力</div>
              <div class="mc-value">{{ formatNum(derived.soilWeight) }}</div>
              <div class="mc-unit">kN</div>
            </div>
            <div class="metric-card mc-emerald">
              <div class="mc-label">估算安全系数 Fs</div>
              <div class="mc-value">{{ formatNum(derived.fs, 3) }}</div>
              <div class="mc-unit">
                <el-tag
                  v-if="derived.fs"
                  :type="derived.fs >= 1.3 ? 'success' : derived.fs >= 1.1 ? 'warning' : 'danger'"
                  size="small"
                  effect="light"
                >
                  {{ derived.fs >= 1.3 ? '安全' : derived.fs >= 1.1 ? '临界' : '偏低' }}
                </el-tag>
              </div>
            </div>
            <div class="metric-card mc-rose">
              <div class="mc-label">最大沉降</div>
              <div class="mc-value">{{ formatNum(derived.maxSettlement, 1) }}</div>
              <div class="mc-unit">mm</div>
            </div>
            <div class="metric-card mc-amber">
              <div class="mc-label">方量等级</div>
              <div class="mc-value" style="font-size: 22px;">
                {{ derived.volumeGrade || '--' }}
              </div>
              <div class="mc-unit">
                <el-tag
                  :type="gradeType(derived.volumeGrade)"
                  size="small"
                  effect="light"
                >
                  {{ gradeText(derived.volumeGrade) }}
                </el-tag>
              </div>
            </div>
          </div>

          <div class="classification-section">
            <div class="sec-title">分类级别</div>
            <el-alert
              v-if="classification.stability"
              :title="`稳定等级：${classification.stability}`"
              :type="levelType(classification.stability)"
              :closable="false"
              show-icon
              class="mb-8"
            />
            <el-alert
              v-if="classification.deformation"
              :title="`变形等级：${classification.deformation}`"
              :type="levelType(classification.deformation)"
              :closable="false"
              show-icon
              class="mb-8"
            />
            <el-alert
              v-if="classification.depth"
              :title="`开挖深度等级：${classification.depth}`"
              :type="levelType(classification.depth)"
              :closable="false"
              show-icon
            />
          </div>
        </el-card>
      </el-col>

      <!-- 右列：建议与说明 -->
      <el-col :span="6" class="col-right">
        <el-card shadow="never" class="suggest-card">
          <template #header>
            <div class="card-header">
              <el-icon color="#d97706"><Reading /></el-icon>
              <span>系统建议</span>
            </div>
          </template>

          <div class="suggestions-list" v-if="suggestions.length">
            <div
              v-for="(s, i) in suggestions"
              :key="i"
              class="suggestion-item"
            >
              <div class="s-index">{{ i + 1 }}</div>
              <div class="s-content">
                <div class="s-title" v-if="s.title">{{ s.title }}</div>
                <div class="s-text">{{ s.content || s }}</div>
                <el-tag
                  v-if="s.level"
                  :type="sLevelType(s.level)"
                  size="small"
                  effect="plain"
                  class="s-tag"
                >
                  {{ s.level }}
                </el-tag>
              </div>
            </div>
          </div>
          <el-empty
            v-else
            description='点击「开始计算」后显示建议'
            :image-size="90"
          />
        </el-card>

        <el-card shadow="never" class="radar-card">
          <template #header>
            <div class="card-header">
              <el-icon color="#7c3aed"><PieChart /></el-icon>
              <span>参数对比雷达图</span>
            </div>
          </template>
          <div class="radar-wrap">
            <v-chart
              class="radar-chart"
              :option="radarOption"
              autoresize
            />
          </div>
          <div class="radar-legend">
            <div class="legend-item">
              <span class="dot dot-blue"></span>
              <span>输入值</span>
            </div>
            <div class="legend-item">
              <span class="dot dot-green"></span>
              <span>规范推荐阈值</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Cpu, Setting, Refresh, DataAnalysis, DataLine, Reading, PieChart
} from '@element-plus/icons-vue'
import {
  getParamSchema, getParamValues, calculateParams
} from '@/api'

// ========== 折叠面板状态 ==========
const activeCollapse = ref(['material', 'excavation', 'safety', 'calc'])

// ========== 参数 Schema ==========
const schema = ref({ groups: {} })
const formValues = reactive({})

// 各组字段列表（按需求固定，schema 返回后回填 meta / 默认值）
const groups = reactive({
  material: [
    { key: 'soil_density', label: '土体密度', unit: 'kN/m³', type: 'number', meta: { range: [14, 24], step: 0.1, precision: 2 }, default: 19.0 },
    { key: 'cohesion', label: '黏聚力', unit: 'kPa', type: 'number', meta: { range: [0, 80], step: 1, precision: 1 }, default: 25 },
    { key: 'friction_angle', label: '内摩擦角', unit: '°', type: 'number', meta: { range: [10, 45], step: 0.5, precision: 1 }, default: 28 },
    { key: 'elastic_modulus', label: '弹性模量', unit: 'MPa', type: 'number', meta: { range: [5, 200], step: 1, precision: 0 }, default: 60 },
    { key: 'poisson_ratio', label: '泊松比', unit: '', type: 'number', meta: { range: [0.15, 0.45], step: 0.01, precision: 2 }, default: 0.30 },
    { key: 'permeability', label: '渗透系数', unit: 'cm/s', type: 'number', meta: { range: [1e-7, 1e-2], step: 1e-6, precision: 7 }, default: 1e-4 },
  ],
  excavation: [
    { key: 'max_depth', label: '最大开挖深度', unit: 'm', type: 'number', meta: { range: [1, 120], step: 0.5, precision: 1 }, default: 45 },
    { key: 'layer_height', label: '单层高度', unit: 'm', type: 'number', meta: { range: [1, 10], step: 0.5, precision: 1 }, default: 3 },
    { key: 'slope_ratio', label: '坡率(1:m)', unit: '', type: 'number', meta: { range: [0.3, 3], step: 0.05, precision: 2 }, default: 1.0 },
    { key: 'bench_width', label: '马道宽度', unit: 'm', type: 'number', meta: { range: [0, 10], step: 0.5, precision: 1 }, default: 2.0 },
    { key: 'support_strength', label: '支护强度', unit: 'kPa', type: 'number', meta: { range: [0, 500], step: 10, precision: 0 }, default: 150 },
  ],
  safety: [
    { key: 'fs_global', label: '整体稳定安全系数', unit: '', type: 'number', meta: { range: [1.0, 2.0], step: 0.05, precision: 3 }, default: 1.30 },
    { key: 'fs_local', label: '局部稳定安全系数', unit: '', type: 'number', meta: { range: [1.0, 2.0], step: 0.05, precision: 3 }, default: 1.20 },
    { key: 'seismic_coef', label: '地震系数', unit: '', type: 'number', meta: { range: [0, 0.4], step: 0.01, precision: 2 }, default: 0.05 },
    { key: 'deformation_limit', label: '变形控制(mm)', unit: 'mm', type: 'number', meta: { range: [10, 500], step: 5, precision: 0 }, default: 50 },
  ],
  calc: [
    {
      key: 'analysis_method', label: '分析方法', unit: '', type: 'select',
      meta: { options: [
        { label: '极限平衡法 (LEM)', value: 'lem' },
        { label: '有限元强度折减法 (SRM)', value: 'srm' },
        { label: '有限差分法 (FLAC)', value: 'flac' },
        { label: '离散元法 (DEM)', value: 'dem' },
      ]}, default: 'lem'
    },
    {
      key: 'constitutive_model', label: '本构模型', unit: '', type: 'select',
      meta: { options: [
        { label: 'Mohr-Coulomb 线弹性', value: 'mc' },
        { label: 'Drucker-Prager', value: 'dp' },
        { label: '修正剑桥模型 MCC', value: 'mcc' },
        { label: '弹塑性 HS-Small', value: 'hss' },
      ]}, default: 'mc'
    },
    { key: 'max_iter', label: '最大迭代步', unit: '步', type: 'number', meta: { range: [100, 20000], step: 100, precision: 0 }, default: 1000 },
    { key: 'tolerance', label: '收敛容差', unit: '', type: 'number', meta: { range: [1e-8, 1e-2], step: 1e-6, precision: 6 }, default: 1e-4 },
  ],
})

const totalFields = computed(() => {
  return Object.values(groups).reduce((s, g) => s + g.length, 0)
})

// 加载 schema 并覆盖默认值/meta
async function loadSchema() {
  try {
    const res = await getParamSchema()
    const data = res.data?.data || res.data || {}
    const allFields = []
    Object.values(groups).forEach(g => allFields.push(...g))
    allFields.forEach(f => {
      const sv = data[f.key]
      if (!sv) return
      if (sv.default !== undefined) f.default = sv.default
      if (sv.meta) f.meta = { ...f.meta, ...sv.meta }
      if (sv.unit) f.unit = sv.unit
    })
  } catch (e) {
    // 使用默认值
  } finally {
    applyDefaults()
    // 尝试加载最近一次保存的参数值
    try {
      const rv = await getParamValues()
      const v = rv.data?.data || rv.data || {}
      Object.keys(v).forEach(k => {
        if (v[k] !== undefined && v[k] !== null) formValues[k] = v[k]
      })
    } catch (_) {}
  }
}

function applyDefaults() {
  const all = []
  Object.values(groups).forEach(g => all.push(...g))
  all.forEach(f => {
    if (formValues[f.key] === undefined) {
      formValues[f.key] = f.default
    }
  })
}

function handleReset() {
  const all = []
  Object.values(groups).forEach(g => all.push(...g))
  all.forEach(f => { formValues[f.key] = f.default })
  ElMessage.info('已重置为默认参数')
}

// ========== 计算 ==========
const calculating = ref(false)
const derived = reactive({})
const classification = reactive({})
const suggestions = ref([])

async function handleCalculate() {
  calculating.value = true
  try {
    const payload = { ...formValues }
    const res = await calculateParams(payload)
    const data = res.data?.data || res.data || {}
    Object.assign(derived, data.derived || data.metrics || {})
    Object.assign(classification, data.classification || {})
    suggestions.value = data.suggestions || []
    ElMessage.success('参数计算完成')
  } catch (e) {
    ElMessage.error('计算失败：' + (e.message || '请稍后重试'))
  } finally {
    calculating.value = false
  }
}

// ========== 工具函数 ==========
function formatNum(v, d = 2) {
  if (v === null || v === undefined || v === '') return '--'
  const n = Number(v)
  if (isNaN(n)) return '--'
  return n.toLocaleString('zh-CN', { minimumFractionDigits: 0, maximumFractionDigits: d })
}
function gradeType(g) {
  if (!g) return 'info'
  if (g === '大型' || g.includes('大')) return 'danger'
  if (g === '中型') return 'warning'
  return 'success'
}
function gradeText(g) {
  if (!g) return ''
  if (g === '大型') return '重大工程'
  if (g === '中型') return '一般工程'
  return '小型工程'
}
function levelType(l) {
  if (!l) return 'info'
  const s = String(l)
  if (s.includes('Ⅰ') || s.includes('A') || s.includes('安全') || s.includes('小')) return 'success'
  if (s.includes('Ⅱ') || s.includes('B') || s.includes('中') || s.includes('临界')) return 'warning'
  if (s.includes('Ⅲ') || s.includes('C') || s.includes('大') || s.includes('危险')) return 'error'
  return 'info'
}
function sLevelType(l) {
  if (!l) return 'info'
  if (l.includes('强') || l.includes('必') || l.includes('red') || l.includes('critical')) return 'danger'
  if (l.includes('中') || l.includes('建') || l.includes('warning')) return 'warning'
  return 'success'
}

// ========== 雷达图 ==========
// 6项：黏聚力/内摩擦角/弹性模量/开挖深度/坡率/安全系数
const radarOption = computed(() => {
  // 规范推荐阈值（基准上限或下限）
  const std = {
    cohesion: 25,
    friction_angle: 30,
    elastic_modulus: 50,
    max_depth: 60,
    slope_ratio: 1.2,
    fs_global: 1.3,
  }
  const maxV = {
    cohesion: 80, friction_angle: 50, elastic_modulus: 200,
    max_depth: 120, slope_ratio: 3, fs_global: 2.0,
  }
  const norm = (v, k) => {
    if (v === undefined || v === null) return 0
    return Math.min(100, Math.max(0, (Number(v) / (maxV[k] || 1)) * 100))
  }
  const indicator = [
    { name: '黏聚力', max: 100 },
    { name: '内摩擦角', max: 100 },
    { name: '弹性模量', max: 100 },
    { name: '开挖深度', max: 100 },
    { name: '坡率', max: 100 },
    { name: '安全系数', max: 100 },
  ]
  const inputData = [
    norm(formValues.cohesion, 'cohesion'),
    norm(formValues.friction_angle, 'friction_angle'),
    norm(formValues.elastic_modulus, 'elastic_modulus'),
    norm(formValues.max_depth, 'max_depth'),
    norm(formValues.slope_ratio, 'slope_ratio'),
    norm(formValues.fs_global, 'fs_global'),
  ]
  const stdData = [
    norm(std.cohesion, 'cohesion'),
    norm(std.friction_angle, 'friction_angle'),
    norm(std.elastic_modulus, 'elastic_modulus'),
    norm(std.max_depth, 'max_depth'),
    norm(std.slope_ratio, 'slope_ratio'),
    norm(std.fs_global, 'fs_global'),
  ]
  return {
    tooltip: {},
    legend: { show: false },
    radar: {
      indicator,
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#475569', fontSize: 11 },
      splitArea: { areaStyle: { color: ['#f8fafc', '#fff'] } },
      splitLine: { lineStyle: { color: '#e2e8f0' } },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
    },
    series: [{
      type: 'radar',
      emphasis: { lineStyle: { width: 3 } },
      data: [
        {
          name: '输入值',
          value: inputData,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { color: '#3b82f6', width: 2 },
          itemStyle: { color: '#3b82f6' },
          areaStyle: { color: 'rgba(59,130,246,0.2)' },
        },
        {
          name: '规范推荐阈值',
          value: stdData,
          symbol: 'diamond',
          symbolSize: 6,
          lineStyle: { color: '#10b981', width: 2, type: 'dashed' },
          itemStyle: { color: '#10b981' },
          areaStyle: { color: 'rgba(16,185,129,0.12)' },
        },
      ],
    }],
  }
})

onMounted(() => {
  loadSchema()
})
</script>

<style scoped>
.param-inference-page {
  padding: 16px 18px 24px;
  background: #f1f5f9;
  min-height: 100%;
}
.page-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 14px;
}
.header-left { display: flex; align-items: center; gap: 10px; }
.page-title { margin: 0; font-size: 20px; color: #0f172a; font-weight: 700; }
.page-sub { color: #64748b; font-size: 13px; margin-left: 8px; }

.main-row { align-items: stretch; }
.col-left :deep(.el-card__body),
.col-middle :deep(.el-card__body),
.col-right :deep(.el-card__body) { padding: 16px 18px 18px; }

.card-header {
  display: flex; align-items: center; gap: 8px;
  font-weight: 600; color: #0f172a;
}
.card-header .hint {
  margin-left: auto;
  font-size: 12px; color: #94a3b8; font-weight: normal;
}

.params-collapse { margin-bottom: 14px; }
.param-grid {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 4px 20px;
  padding: 8px 4px 12px;
}
.param-form-item {
  margin-bottom: 4px !important;
}
.param-form-item :deep(.el-form-item__label) {
  font-size: 12.5px;
  color: #334155;
  padding-bottom: 2px;
  font-weight: 500;
  width: 100% !important;
}
.param-form-item :deep(.el-form-item__content) {
  width: 100% !important;
}
.param-input-wrap {
  display: flex; align-items: center; gap: 6px;
  width: 100%;
}
.param-number { flex: 1; width: 100%; }
.param-unit {
  font-size: 12px; color: #64748b; min-width: 32px;
  flex-shrink: 0;
}
.param-tip {
  font-size: 11.5px; color: #94a3b8; margin-top: 2px;
}
.w-full { width: 100%; }

.params-actions {
  display: flex; gap: 10px; justify-content: flex-end;
  padding-top: 12px; border-top: 1px dashed #e2e8f0;
}

/* 中列：指标卡片 */
.metric-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 16px;
}
.metric-card {
  border-radius: 10px;
  padding: 12px 12px 10px;
  background: linear-gradient(135deg, #eff6ff 0%, #fff 100%);
  border: 1px solid #dbeafe;
  position: relative; overflow: hidden;
}
.metric-card::after {
  content: ''; position: absolute; right: -20px; top: -20px;
  width: 60px; height: 60px; border-radius: 50%;
  opacity: 0.3;
}
.mc-blue   { background: linear-gradient(135deg,#dbeafe,#fff); border-color:#bfdbfe; }
.mc-blue::after   { background:#3b82f6; }
.mc-cyan   { background: linear-gradient(135deg,#cffafe,#fff); border-color:#a5f3fc; }
.mc-cyan::after   { background:#06b6d4; }
.mc-indigo { background: linear-gradient(135deg,#e0e7ff,#fff); border-color:#c7d2fe; }
.mc-indigo::after { background:#6366f1; }
.mc-violet { background: linear-gradient(135deg,#ede9fe,#fff); border-color:#ddd6fe; }
.mc-violet::after { background:#8b5cf6; }
.mc-orange { background: linear-gradient(135deg,#ffedd5,#fff); border-color:#fed7aa; }
.mc-orange::after { background:#f97316; }
.mc-emerald{ background: linear-gradient(135deg,#d1fae5,#fff); border-color:#a7f3d0; }
.mc-emerald::after{ background:#10b981; }
.mc-rose   { background: linear-gradient(135deg,#ffe4e6,#fff); border-color:#fecdd3; }
.mc-rose::after   { background:#f43f5e; }
.mc-amber  { background: linear-gradient(135deg,#fef3c7,#fff); border-color:#fde68a; }
.mc-amber::after  { background:#f59e0b; }

.mc-label { font-size: 12px; color: #64748b; margin-bottom: 4px; }
.mc-value {
  font-size: 22px; font-weight: 700; color: #0f172a;
  line-height: 1.2;
}
.mc-unit {
  font-size: 11.5px; color: #94a3b8; margin-top: 4px;
  min-height: 18px;
}

.classification-section .sec-title {
  font-size: 13.5px; font-weight: 600; color: #0f172a;
  margin-bottom: 8px;
  padding-left: 8px;
  border-left: 3px solid #059669;
}
.mb-8 { margin-bottom: 8px; }

/* 右列 */
.suggest-card { margin-bottom: 14px; }
.suggestions-list { display: flex; flex-direction: column; gap: 10px; }
.suggestion-item {
  display: flex; gap: 10px;
  padding: 10px 12px;
  background: #fffbeb;
  border-left: 3px solid #f59e0b;
  border-radius: 0 8px 8px 0;
}
.s-index {
  width: 22px; height: 22px; border-radius: 50%;
  background: #f59e0b; color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; flex-shrink: 0;
}
.s-content { flex: 1; }
.s-title { font-size: 13px; font-weight: 600; color: #92400e; margin-bottom: 2px; }
.s-text { font-size: 12.5px; color: #78350f; line-height: 1.5; }
.s-tag { margin-top: 6px; }

.radar-wrap { height: 260px; }
.radar-chart { width: 100%; height: 100%; }
.radar-legend {
  display: flex; justify-content: center; gap: 16px;
  padding-top: 4px;
  font-size: 12px; color: #475569;
}
.legend-item { display: flex; align-items: center; gap: 6px; }
.dot { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.dot-blue { background: #3b82f6; }
.dot-green { background: #10b981; }
</style>
