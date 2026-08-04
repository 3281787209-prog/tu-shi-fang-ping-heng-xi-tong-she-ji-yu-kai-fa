<template>
  <div class="geology-info-page">
    <!-- 上部：三维模型可视化区 -->
    <div class="visualization-section">
      <!-- 左侧：三维模型 -->
      <div class="viewer-panel">
        <div class="panel-header">
          <span class="panel-title">
            <el-icon><Box /></el-icon>
            三维地质模型可视化
          </span>
          <span class="stage-badge" v-if="selectedStage">
            当前工况：{{ stageLabels[selectedStage] || selectedStage }}
          </span>
        </div>
        <div class="viewer-container">
          <!-- VTK 可视化组件占位 -->
          <VtkViewer v-if="selectedStage" :stage-key="selectedStage" />
          <div v-else class="viewer-placeholder">
            <el-icon :size="64" color="#94a3b8"><Picture /></el-icon>
            <p>请选择工况以加载三维模型</p>
          </div>
        </div>
      </div>

      <!-- 右侧：控制面板 -->
      <div class="control-panel">
        <div class="panel-header">
          <span class="panel-title">
            <el-icon><Setting /></el-icon>
            可视化控制
          </span>
        </div>

        <div class="control-content">
          <!-- 工况选择 -->
          <div class="control-group">
            <label class="control-label">工况选择</label>
            <el-select v-model="selectedStage" placeholder="请选择工况" class="w-full" @change="handleStageChange">
              <el-option
                v-for="stage in stageList"
                :key="stage.key"
                :label="stage.label"
                :value="stage.key"
              />
            </el-select>
          </div>

          <!-- 图层复选 -->
          <div class="control-group">
            <label class="control-label">图层显示</label>
            <el-checkbox-group v-model="visibleLayers">
              <el-checkbox value="shell">壳面</el-checkbox>
              <el-checkbox value="excavation">开挖面</el-checkbox>
              <el-checkbox value="section">剖切面</el-checkbox>
              <el-checkbox value="topology">拓扑线</el-checkbox>
            </el-checkbox-group>
          </div>

          <!-- 不透明度 -->
          <div class="control-group">
            <label class="control-label">模型不透明度：{{ opacity }}%</label>
            <el-slider v-model="opacity" :min="10" :max="100" :step="5" />
          </div>

          <!-- 剖切轴按钮组 -->
          <div class="control-group">
            <label class="control-label">剖切方向</label>
            <el-radio-group v-model="cutAxis" class="w-full">
              <el-radio-button value="X">X轴</el-radio-button>
              <el-radio-button value="Y">Y轴</el-radio-button>
              <el-radio-button value="Z">Z轴</el-radio-button>
              <el-radio-button value="none">关闭</el-radio-button>
            </el-radio-group>
          </div>

          <!-- 剖切序号滑块 -->
          <div class="control-group" v-if="cutAxis !== 'none'">
            <label class="control-label">剖切位置：{{ cutIndex }}</label>
            <el-slider v-model="cutIndex" :min="1" :max="50" :step="1" />
          </div>

          <!-- 物理量选择 -->
          <div class="control-group">
            <label class="control-label">物理量显示</label>
            <el-select v-model="physicalQuantity" class="w-full">
              <el-option label="总位移 (mm)" value="total_displacement" />
              <el-option label="X方向位移 (mm)" value="x_displacement" />
              <el-option label="Y方向位移 (mm)" value="y_displacement" />
              <el-option label="Z方向位移 (mm)" value="z_displacement" />
              <el-option label="最大主应力 (MPa)" value="sigma1" />
              <el-option label="中间主应力 (MPa)" value="sigma2" />
              <el-option label="最小主应力 (MPa)" value="sigma3" />
              <el-option label="等效塑性应变" value="peeq" />
            </el-select>
          </div>

          <!-- 视角复位 -->
          <div class="control-group">
            <el-button type="primary" class="w-full" @click="resetView">
              <el-icon><Refresh /></el-icon>
              &nbsp;视角复位
            </el-button>
          </div>

          <!-- 工况物理量指标表 -->
          <div class="metrics-section" v-if="stageMetrics">
            <div class="metrics-title">
              <el-icon><DataLine /></el-icon>
              当前工况物理量范围
            </div>
            <el-table :data="metricsTableData" size="small" border stripe>
              <el-table-column prop="name" label="物理量" min-width="110" />
              <el-table-column prop="range_min" label="最小值" width="90" align="right">
                <template #default="{ row }">
                  <span class="metric-value min">{{ row.range_min?.toFixed(3) ?? '--' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="range_max" label="最大值" width="90" align="right">
                <template #default="{ row }">
                  <span class="metric-value max">{{ row.range_max?.toFixed(3) ?? '--' }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="unit" label="单位" width="70" align="center" />
            </el-table>
          </div>
        </div>
      </div>
    </div>

    <!-- 下部：地质信息 Tab -->
    <div class="info-section">
      <el-tabs v-model="activeTab" class="info-tabs">
        <!-- Tab1 地质图层 -->
        <el-tab-pane label="地质图层管理" name="layers">
          <div class="tab-toolbar">
            <el-button type="primary" @click="openLayerDialog()">
              <el-icon><Plus /></el-icon>
              &nbsp;新增地质图层
            </el-button>
            <el-button @click="loadLayers">
              <el-icon><Refresh /></el-icon>
              &nbsp;刷新
            </el-button>
          </div>

          <el-table :data="layerList" v-loading="layersLoading" border stripe>
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="name" label="图层名称" min-width="140" />
            <el-table-column prop="layer_type" label="类型" width="120" align="center">
              <template #default="{ row }">
                <el-tag :type="layerTypeTag(row.layer_type)" effect="light">
                  {{ layerTypeLabel(row.layer_type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
            <el-table-column prop="related_stages" label="关联工况" width="180">
              <template #default="{ row }">
                <div class="stage-tags">
                  <el-tag
                    v-for="s in (row.related_stages || []).slice(0, 3)"
                    :key="s"
                    size="small"
                    type="info"
                    effect="plain"
                    style="margin-right: 4px; margin-bottom: 2px;"
                  >
                    {{ stageLabels[s] || s }}
                  </el-tag>
                  <el-tag
                    v-if="(row.related_stages || []).length > 3"
                    size="small"
                    type="info"
                  >
                    +{{ (row.related_stages || []).length - 3 }}
                  </el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="160" align="center" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="openLayerDialog(row)">
                  编辑
                </el-button>
                <el-button size="small" type="danger" link @click="confirmDeleteLayer(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>

        <!-- Tab2 钻孔数据 -->
        <el-tab-pane label="钻孔数据管理" name="boreholes">
          <div class="tab-toolbar">
            <el-button type="primary" @click="openBoreholeDialog()">
              <el-icon><Plus /></el-icon>
              &nbsp;新增钻孔
            </el-button>
            <el-button @click="loadBoreholes">
              <el-icon><Refresh /></el-icon>
              &nbsp;刷新
            </el-button>
          </div>

          <el-table :data="boreholeList" v-loading="boreholesLoading" border stripe>
            <el-table-column type="index" label="序号" width="60" align="center" />
            <el-table-column prop="hole_no" label="孔号" width="120" align="center" />
            <el-table-column label="坐标 (X, Y, Z)" width="240">
              <template #default="{ row }">
                <span class="coord-text">
                  {{ row.x?.toFixed(2) }}, {{ row.y?.toFixed(2) }}, {{ row.z?.toFixed(2) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="depth" label="孔深 (m)" width="100" align="right" />
            <el-table-column prop="stratigraphy" label="分层数" width="90" align="center">
              <template #default="{ row }">
                <el-tag size="small">{{ (row.stratigraphy || []).length }} 层</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="180" align="center" fixed="right">
              <template #default="{ row }">
                <el-button size="small" type="primary" link @click="showStratigraphy(row)">
                  柱状图预览
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>

    <!-- 新增/编辑图层对话框 -->
    <el-dialog
      v-model="layerDialogVisible"
      :title="editingLayer ? '编辑地质图层' : '新增地质图层'"
      width="620px"
      destroy-on-close
    >
      <el-form ref="layerFormRef" :model="layerForm" :rules="layerRules" label-width="100px">
        <el-form-item label="图层名称" prop="name">
          <el-input v-model="layerForm.name" placeholder="请输入图层名称" />
        </el-form-item>
        <el-form-item label="图层类型" prop="layer_type">
          <el-select v-model="layerForm.layer_type" class="w-full" placeholder="请选择图层类型">
            <el-option label="地层 (Stratum)" value="stratum" />
            <el-option label="基岩 (Bedrock)" value="bedrock" />
            <el-option label="断层 (Fault)" value="fault" />
            <el-option label="滑动带 (Slip Zone)" value="slip_zone" />
            <el-option label="开挖面 (Excavation)" value="excavation" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="layerForm.description"
            type="textarea"
            :rows="2"
            placeholder="请输入图层描述"
          />
        </el-form-item>
        <el-form-item label="关联工况" prop="related_stages">
          <el-select
            v-model="layerForm.related_stages"
            multiple
            collapse-tags
            collapse-tags-tooltip
            class="w-full"
            placeholder="请选择关联工况"
          >
            <el-option
              v-for="stage in stageList"
              :key="stage.key"
              :label="stage.label"
              :value="stage.key"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="属性参数">
          <div class="properties-editor">
            <el-table :data="layerForm.propertiesList" border size="small">
              <el-table-column label="属性键" width="180">
                <template #default="{ row }">
                  <el-input v-model="row.key" size="small" placeholder="key" />
                </template>
              </el-table-column>
              <el-table-column label="属性值">
                <template #default="{ row }">
                  <el-input v-model="row.value" size="small" placeholder="value" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="70" align="center">
                <template #default="{ $index }">
                  <el-button
                    size="small"
                    type="danger"
                    link
                    @click="layerForm.propertiesList.splice($index, 1)"
                  >
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <el-button
              size="small"
              type="primary"
              plain
              style="margin-top: 8px;"
              @click="layerForm.propertiesList.push({ key: '', value: '' })"
            >
              <el-icon><Plus /></el-icon>
              &nbsp;添加属性
            </el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="layerDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="layerSubmitting" @click="submitLayer">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 新增钻孔对话框 -->
    <el-dialog
      v-model="boreholeDialogVisible"
      title="新增钻孔数据"
      width="580px"
      destroy-on-close
    >
      <el-form ref="boreholeFormRef" :model="boreholeForm" :rules="boreholeRules" label-width="90px">
        <el-form-item label="孔号" prop="hole_no">
          <el-input v-model="boreholeForm.hole_no" placeholder="如：ZK-001" />
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="8">
            <el-form-item label="X坐标" prop="x">
              <el-input-number v-model="boreholeForm.x" :precision="2" :step="1" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Y坐标" prop="y">
              <el-input-number v-model="boreholeForm.y" :precision="2" :step="1" class="w-full" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="Z坐标" prop="z">
              <el-input-number v-model="boreholeForm.z" :precision="2" :step="1" class="w-full" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="孔深 (m)" prop="depth">
          <el-input-number v-model="boreholeForm.depth" :precision="2" :min="0" :step="1" class="w-full" />
        </el-form-item>
        <el-form-item label="分层数据">
          <div class="stratigraphy-editor">
            <div class="hint-text">
              JSON数组格式：[{"layer_name":"素填土","top":0,"bottom":2.5,"color":"#d4a373"}, ...]
            </div>
            <el-input
              v-model="boreholeForm.stratigraphyJson"
              type="textarea"
              :rows="6"
              placeholder='[{"layer_name":"素填土","top":0,"bottom":2.5,"color":"#d4a373"},{"layer_name":"粉质黏土","top":2.5,"bottom":8.0,"color":"#a3b18a"}]'
            />
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="boreholeDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="boreholeSubmitting" @click="submitBorehole">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 钻孔分层柱状图对话框 -->
    <el-dialog
      v-model="stratigraphyVisible"
      :title="`钻孔 ${currentBorehole?.hole_no} - 分层柱状图`"
      width="420px"
      destroy-on-close
    >
      <div class="stratigraphy-viewer" v-if="currentBorehole">
        <div class="borehole-info">
          <el-descriptions :column="1" size="small" border>
            <el-descriptions-item label="孔号">{{ currentBorehole.hole_no }}</el-descriptions-item>
            <el-descriptions-item label="坐标">
              X:{{ currentBorehole.x?.toFixed(2) }}
              Y:{{ currentBorehole.y?.toFixed(2) }}
              Z:{{ currentBorehole.z?.toFixed(2) }}
            </el-descriptions-item>
            <el-descriptions-item label="孔深">{{ currentBorehole.depth }} m</el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="stratigraphy-chart">
          <div class="chart-header">
            <span>深度 (m)</span>
            <span>地层柱状</span>
            <span>地层名称</span>
          </div>
          <div class="chart-body">
            <div
              v-for="(layer, idx) in currentBorehole.stratigraphy || []"
              :key="idx"
              class="stratum-row"
              :style="{ height: getStratumHeight(layer, currentBorehole.depth) + 'px' }"
            >
              <div class="depth-marks">
                <span class="mark-top">{{ layer.top?.toFixed(2) }}</span>
                <span class="mark-bottom">{{ layer.bottom?.toFixed(2) }}</span>
              </div>
              <div
                class="stratum-bar"
                :style="{ background: layer.color || defaultColors[idx % defaultColors.length] }"
              ></div>
              <div class="stratum-name">{{ layer.layer_name }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listGeologyLayers, createGeologyLayer, updateGeologyLayer, deleteGeologyLayer,
  listBoreholes, createBorehole,
  listStages, getStageMetrics,
} from '@/api'

// ========== 通用解包函数：兼容后端返回 {items/data/list} 或裸 list/object ==========
function unwrapList(r, fallback = []) {
  if (Array.isArray(r)) return r
  if (!r || typeof r !== 'object') return fallback
  if (Array.isArray(r.items)) return r.items
  if (Array.isArray(r.list)) return r.list
  if (Array.isArray(r.data)) return r.data
  // 再解一层 data
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

// VtkViewer 组件占位（后续创建）
const VtkViewer = {
  name: 'VtkViewer',
  props: {
    stageKey: { type: String, default: '' },
  },
  template: `
    <div class="vtk-viewer-placeholder">
      <div class="placeholder-inner">
        <el-icon :size="48" color="#60a5fa"><Cpu /></el-icon>
        <p class="title">VTK 三维模型渲染区</p>
        <p class="subtitle">工况: {{ stageKey }}</p>
        <p class="tip">组件 @/components/VtkViewer.vue 将在此处挂载</p>
      </div>
    </div>
  `,
}

// ========== 工况与指标 ==========
const stageList = ref([])
const stageLabels = computed(() => {
  const map = {}
  stageList.value.forEach(s => { map[s.key] = s.label })
  return map
})
const selectedStage = ref('')
const stageMetrics = ref(null)

const metricsTableData = computed(() => {
  if (!stageMetrics.value) return []
  const items = []
  const mapping = [
    { key: 'total_displacement', name: '总位移', unit: 'mm' },
    { key: 'x_displacement', name: 'X位移', unit: 'mm' },
    { key: 'y_displacement', name: 'Y位移', unit: 'mm' },
    { key: 'z_displacement', name: 'Z位移', unit: 'mm' },
    { key: 'sigma1', name: '最大主应力', unit: 'MPa' },
    { key: 'sigma3', name: '最小主应力', unit: 'MPa' },
    { key: 'peeq', name: '等效塑性应变', unit: '-' },
  ]
  mapping.forEach(m => {
    const v = stageMetrics.value[m.key]
    if (v) {
      items.push({
        name: m.name,
        range_min: v.range_min,
        range_max: v.range_max,
        unit: m.unit,
      })
    }
  })
  return items
})

async function loadStages() {
  try {
    const res = await listStages()
    const raw = unwrapList(res, [])
    // 兼容后端返回字段 stage_key -> key，并补 label
    stageList.value = raw.map((s, idx) => ({
      key: s.key || s.stage_key || `stage_${String(idx + 1).padStart(2, '0')}`,
      label: s.label || s.name || `工况 ${idx + 1}${s.stage_key ? ' - ' + s.stage_key : ''}`,
      ...s,
    }))
    if (stageList.value.length && !selectedStage.value) {
      selectedStage.value = stageList.value[0].key
    }
  } catch (e) {
    // fallback mock data
    stageList.value = Array.from({ length: 23 }, (_, i) => ({
      key: `stage_${String(i + 1).padStart(2, '0')}`,
      label: `工况 ${i + 1} - ${['初始', '开挖I', '开挖II', '开挖III', '支护'][i % 5]}`,
    }))
    selectedStage.value = stageList.value[0].key
  }
}

async function loadStageMetrics() {
  if (!selectedStage.value) return
  try {
    const res = await getStageMetrics(selectedStage.value)
    const raw = unwrapObject(res, null)
    // 后端返回 {stage_key, metrics: [{scalar_key, range_min, range_max, ...}]}
    // 前端期望 {total_displacement: {range_min, range_max}, ...}，做转换兼容
    const converted = {}
    if (raw && Array.isArray(raw.metrics)) {
      // 常见字段映射：后端 scalar_key -> 前端 key
      const keyMap = {
        'total_displacement': 'total_displacement', 'TotalDisplacement': 'total_displacement', 'disp_total': 'total_displacement',
        'x_displacement': 'x_displacement', 'X_Disp': 'x_displacement', 'disp_x': 'x_displacement',
        'y_displacement': 'y_displacement', 'Y_Disp': 'y_displacement', 'disp_y': 'y_displacement',
        'z_displacement': 'z_displacement', 'Z_Disp': 'z_displacement', 'disp_z': 'z_displacement',
        'sigma1': 'sigma1', 'Stress_Max_Principal': 'sigma1', 'SIGMA1': 'sigma1',
        'sigma2': 'sigma2', 'Stress_Mid_Principal': 'sigma2', 'SIGMA2': 'sigma2',
        'sigma3': 'sigma3', 'Stress_Min_Principal': 'sigma3', 'SIGMA3': 'sigma3',
        'peeq': 'peeq', 'PEEQ': 'peeq', '等效塑性应变': 'peeq',
      }
      raw.metrics.forEach(m => {
        const k = keyMap[m.scalar_key] || m.scalar_key
        converted[k] = { range_min: m.range_min, range_max: m.range_max, source_file: m.source_file }
      })
    } else if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
      // 可能后端已经返回扁平结构或只有 data 包装
      Object.keys(raw).forEach(k => {
        if (k !== 'stage_key' && typeof raw[k] === 'object') converted[k] = raw[k]
      })
    }
    stageMetrics.value = Object.keys(converted).length ? converted : (raw || null)
  } catch {
    stageMetrics.value = {
      total_displacement: { range_min: 0.12, range_max: 45.67 },
      x_displacement: { range_min: -23.4, range_max: 18.9 },
      y_displacement: { range_min: -15.2, range_max: 22.1 },
      z_displacement: { range_min: -38.5, range_max: 5.3 },
      sigma1: { range_min: 0.02, range_max: 8.75 },
      sigma3: { range_min: -12.4, range_max: 0.15 },
      peeq: { range_min: 0, range_max: 0.085 },
    }
  }
}

function handleStageChange() {
  loadStageMetrics()
}

watch(selectedStage, () => loadStageMetrics())

// ========== 可视化控制 ==========
const visibleLayers = ref(['shell', 'excavation'])
const opacity = ref(85)
const cutAxis = ref('none')
const cutIndex = ref(25)
const physicalQuantity = ref('total_displacement')

function resetView() {
  ElMessage.info('视角已复位')
}

// ========== 地质图层 ==========
const activeTab = ref('layers')
const layersLoading = ref(false)
const layerList = ref([])
const layerDialogVisible = ref(false)
const editingLayer = ref(null)
const layerSubmitting = ref(false)
const layerFormRef = ref()
const layerForm = reactive({
  name: '',
  layer_type: '',
  description: '',
  related_stages: [],
  propertiesList: [{ key: '', value: '' }],
})
const layerRules = {
  name: [{ required: true, message: '请输入图层名称', trigger: 'blur' }],
  layer_type: [{ required: true, message: '请选择图层类型', trigger: 'change' }],
}

function layerTypeLabel(t) {
  return {
    stratum: '地层', bedrock: '基岩', fault: '断层',
    slip_zone: '滑动带', excavation: '开挖面',
  }[t] || t
}
function layerTypeTag(t) {
  return {
    stratum: 'success', bedrock: '', fault: 'danger',
    slip_zone: 'warning', excavation: 'primary',
  }[t] || 'info'
}

async function loadLayers() {
  layersLoading.value = true
  try {
    const res = await listGeologyLayers()
    const raw = unwrapList(res, [])
    // 兼容字段：后端 stage_key / stage_keys -> 前端 related_stages
    layerList.value = raw.map(l => ({
      ...l,
      related_stages: l.related_stages || l.stage_keys || (l.stage_key ? [l.stage_key] : []) || [],
    }))
  } catch {
    layerList.value = [
      { id: 1, name: '第四系覆盖层', layer_type: 'stratum', description: '表层松散堆积物，平均厚度5m', related_stages: ['stage_01', 'stage_02', 'stage_03'] },
      { id: 2, name: 'T2l砂岩', layer_type: 'bedrock', description: '中厚层状砂岩，岩体较完整', related_stages: ['stage_01', 'stage_02', 'stage_03', 'stage_04', 'stage_05'] },
      { id: 3, name: 'F1断层', layer_type: 'fault', description: '张扭性断层，破碎带宽度0.5-2m', related_stages: ['stage_03', 'stage_04', 'stage_05'] },
      { id: 4, name: '软弱夹层S1', layer_type: 'slip_zone', description: '泥化夹层，厚度5-30cm', related_stages: ['stage_02', 'stage_03', 'stage_04'] },
      { id: 5, name: '开挖面-I区', layer_type: 'excavation', description: '一级马道以上开挖面', related_stages: ['stage_01'] },
    ]
  } finally {
    layersLoading.value = false
  }
}

function openLayerDialog(row = null) {
  editingLayer.value = row
  if (row) {
    layerForm.name = row.name
    layerForm.layer_type = row.layer_type
    layerForm.description = row.description || ''
    layerForm.related_stages = [...(row.related_stages || [])]
    layerForm.propertiesList = Object.entries(row.properties || {}).map(([k, v]) => ({ key: k, value: String(v) }))
    if (!layerForm.propertiesList.length) layerForm.propertiesList = [{ key: '', value: '' }]
  } else {
    layerForm.name = ''
    layerForm.layer_type = ''
    layerForm.description = ''
    layerForm.related_stages = []
    layerForm.propertiesList = [{ key: '', value: '' }]
  }
  layerDialogVisible.value = true
}

async function submitLayer() {
  await layerFormRef.value?.validate()
  layerSubmitting.value = true
  try {
    const properties = {}
    layerForm.propertiesList.forEach(p => {
      if (p.key && p.value !== '') properties[p.key] = p.value
    })
    const payload = {
      name: layerForm.name,
      layer_type: layerForm.layer_type,
      description: layerForm.description,
      related_stages: layerForm.related_stages,
      properties,
    }
    if (editingLayer.value) {
      await updateGeologyLayer(editingLayer.value.id, payload)
      ElMessage.success('图层已更新')
    } else {
      await createGeologyLayer(payload)
      ElMessage.success('图层已创建')
    }
    layerDialogVisible.value = false
    loadLayers()
  } finally {
    layerSubmitting.value = false
  }
}

async function confirmDeleteLayer(row) {
  try {
    await ElMessageBox.confirm(`确定删除图层「${row.name}」吗？`, '确认删除', { type: 'warning' })
    await deleteGeologyLayer(row.id)
    ElMessage.success('已删除')
    loadLayers()
  } catch { /* cancel */ }
}

// ========== 钻孔数据 ==========
const boreholesLoading = ref(false)
const boreholeList = ref([])
const boreholeDialogVisible = ref(false)
const boreholeSubmitting = ref(false)
const boreholeFormRef = ref()
const boreholeForm = reactive({
  hole_no: '',
  x: 0, y: 0, z: 0,
  depth: 0,
  stratigraphyJson: '',
})
const boreholeRules = {
  hole_no: [{ required: true, message: '请输入孔号', trigger: 'blur' }],
  x: [{ required: true, message: '请输入X坐标', trigger: 'blur' }],
  y: [{ required: true, message: '请输入Y坐标', trigger: 'blur' }],
  z: [{ required: true, message: '请输入Z坐标', trigger: 'blur' }],
  depth: [{ required: true, message: '请输入孔深', trigger: 'blur' }],
}
const defaultColors = ['#d4a373', '#a3b18a', '#588157', '#3a5a40', '#9c6644', '#7f5539', '#606c38', '#463f3a']

async function loadBoreholes() {
  boreholesLoading.value = true
  try {
    const res = await listBoreholes()
    const raw = unwrapList(res, [])
    // 兼容字段：后端 hole_code -> 前端 hole_no
    boreholeList.value = raw.map(b => ({
      ...b,
      hole_no: b.hole_no || b.hole_code || '',
    }))
  } catch {
    boreholeList.value = [
      {
        id: 1, hole_no: 'ZK-001', x: 1250.50, y: 860.30, z: 545.20, depth: 25.0,
        stratigraphy: [
          { layer_name: '素填土', top: 0, bottom: 2.5, color: '#d4a373' },
          { layer_name: '粉质黏土', top: 2.5, bottom: 8.0, color: '#a3b18a' },
          { layer_name: '强风化砂岩', top: 8.0, bottom: 15.5, color: '#9c6644' },
          { layer_name: '中风化砂岩', top: 15.5, bottom: 25.0, color: '#606c38' },
        ],
      },
      {
        id: 2, hole_no: 'ZK-002', x: 1320.80, y: 910.15, z: 538.70, depth: 32.0,
        stratigraphy: [
          { layer_name: '素填土', top: 0, bottom: 1.8, color: '#d4a373' },
          { layer_name: '含砾粉质黏土', top: 1.8, bottom: 6.5, color: '#a3b18a' },
          { layer_name: '强风化砂岩', top: 6.5, bottom: 14.0, color: '#9c6644' },
          { layer_name: 'F1断层破碎带', top: 14.0, bottom: 16.5, color: '#bc6c25' },
          { layer_name: '中风化砂岩', top: 16.5, bottom: 32.0, color: '#606c38' },
        ],
      },
      {
        id: 3, hole_no: 'ZK-003', x: 1180.25, y: 790.60, z: 552.80, depth: 20.0,
        stratigraphy: [
          { layer_name: '耕植土', top: 0, bottom: 1.2, color: '#dda15e' },
          { layer_name: '粉质黏土', top: 1.2, bottom: 7.0, color: '#a3b18a' },
          { layer_name: '强风化泥岩', top: 7.0, bottom: 13.0, color: '#7f5539' },
          { layer_name: '中风化砂岩', top: 13.0, bottom: 20.0, color: '#463f3a' },
        ],
      },
    ]
  } finally {
    boreholesLoading.value = false
  }
}

function openBoreholeDialog() {
  boreholeForm.hole_no = ''
  boreholeForm.x = 0
  boreholeForm.y = 0
  boreholeForm.z = 0
  boreholeForm.depth = 0
  boreholeForm.stratigraphyJson = ''
  boreholeDialogVisible.value = true
}

async function submitBorehole() {
  await boreholeFormRef.value?.validate()
  boreholeSubmitting.value = true
  try {
    let stratigraphy = []
    if (boreholeForm.stratigraphyJson.trim()) {
      stratigraphy = JSON.parse(boreholeForm.stratigraphyJson)
    }
    await createBorehole({
      hole_no: boreholeForm.hole_no,
      x: boreholeForm.x,
      y: boreholeForm.y,
      z: boreholeForm.z,
      depth: boreholeForm.depth,
      stratigraphy,
    })
    ElMessage.success('钻孔已创建')
    boreholeDialogVisible.value = false
    loadBoreholes()
  } catch (e) {
    if (e instanceof SyntaxError) {
      ElMessage.error('分层数据JSON格式错误')
    } else {
      ElMessage.error('创建失败')
    }
  } finally {
    boreholeSubmitting.value = false
  }
}

// ========== 钻孔柱状图 ==========
const stratigraphyVisible = ref(false)
const currentBorehole = ref(null)

function getStratumHeight(layer, totalDepth) {
  if (!totalDepth) return 40
  const thickness = (layer.bottom || 0) - (layer.top || 0)
  // 总高度 360px，按比例，最小24px
  return Math.max(24, Math.round(thickness / totalDepth * 360))
}

function showStratigraphy(row) {
  currentBorehole.value = row
  stratigraphyVisible.value = true
}

// ========== 初始化 ==========
onMounted(() => {
  loadStages().then(() => loadStageMetrics())
  loadLayers()
  loadBoreholes()
})
</script>

<style scoped>
.geology-info-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  height: calc(100vh - 110px);
  padding: 8px 4px;
}

/* 上部可视化区 */
.visualization-section {
  display: flex;
  gap: 14px;
  flex: 1 1 50%;
  min-height: 0;
}
.viewer-panel {
  flex: 0 0 70%;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
.control-panel {
  flex: 1;
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
  padding: 10px 16px;
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
.stage-badge {
  font-size: 12px;
  color: #1d4ed8;
  background: #dbeafe;
  padding: 3px 10px;
  border-radius: 12px;
  font-weight: 500;
}
.viewer-container {
  flex: 1;
  position: relative;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
  overflow: hidden;
}
.viewer-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: #cbd5e1;
}
.viewer-placeholder p { margin: 0; font-size: 13px; }
.vtk-viewer-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder-inner {
  text-align: center;
  color: #93c5fd;
}
.placeholder-inner .title {
  margin: 8px 0 4px;
  font-size: 15px;
  font-weight: 500;
  color: #dbeafe;
}
.placeholder-inner .subtitle {
  margin: 0;
  font-size: 12px;
  color: #60a5fa;
}
.placeholder-inner .tip {
  margin: 6px 0 0;
  font-size: 11px;
  color: #475569;
}

/* 控制面板内容 */
.control-content {
  flex: 1;
  overflow-y: auto;
  padding: 14px 16px;
}
.control-group { margin-bottom: 16px; }
.control-label {
  display: block;
  font-size: 12.5px;
  font-weight: 600;
  color: #334155;
  margin-bottom: 6px;
}
.control-group :deep(.el-checkbox) { margin-right: 14px; }
.w-full { width: 100%; }

/* 指标表 */
.metrics-section {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;
}
.metrics-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 8px;
}
.metrics-title .el-icon { color: #2563eb; }
.metric-value.min { color: #059669; font-weight: 500; }
.metric-value.max { color: #dc2626; font-weight: 500; }

/* 下部信息区 */
.info-section {
  flex: 1 1 50%;
  min-height: 0;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
}
.info-tabs {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}
.info-tabs :deep(.el-tabs__content) {
  flex: 1;
  overflow-y: auto;
  padding: 0 16px 16px;
}
.info-tabs :deep(.el-tab-pane) {
  height: 100%;
  display: flex;
  flex-direction: column;
}
.tab-toolbar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}
.stage-tags { display: flex; flex-wrap: wrap; }
.coord-text { font-family: 'Consolas', monospace; font-size: 12.5px; color: #334155; }

/* 属性编辑器 */
.properties-editor { width: 100%; }

/* 分层编辑器 */
.hint-text {
  font-size: 11.5px;
  color: #64748b;
  margin-bottom: 6px;
  background: #f8fafc;
  padding: 4px 8px;
  border-radius: 4px;
}

/* 钻孔柱状图 */
.borehole-info { margin-bottom: 14px; }
.stratigraphy-chart {
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  overflow: hidden;
}
.chart-header {
  display: grid;
  grid-template-columns: 100px 1fr 140px;
  background: #f1f5f9;
  padding: 8px 10px;
  font-size: 12px;
  font-weight: 600;
  color: #334155;
  text-align: center;
}
.chart-body {
  max-height: 400px;
  overflow-y: auto;
}
.stratum-row {
  display: grid;
  grid-template-columns: 100px 1fr 140px;
  border-bottom: 1px solid #e2e8f0;
  min-height: 24px;
}
.stratum-row:last-child { border-bottom: none; }
.depth-marks {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 2px 6px;
  font-size: 10.5px;
  color: #64748b;
  font-family: 'Consolas', monospace;
  border-right: 1px solid #f1f5f9;
}
.mark-top { color: #334155; }
.mark-bottom { color: #94a3b8; }
.stratum-bar {
  border-right: 1px solid rgba(0,0,0,0.1);
  position: relative;
}
.stratum-bar::after {
  content: '';
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    45deg,
    rgba(255,255,255,0.08) 0px,
    rgba(255,255,255,0.08) 4px,
    transparent 4px,
    transparent 8px
  );
}
.stratum-name {
  display: flex;
  align-items: center;
  padding-left: 10px;
  font-size: 12px;
  color: #1e293b;
}
</style>
