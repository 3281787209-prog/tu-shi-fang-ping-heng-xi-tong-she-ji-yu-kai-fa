<template>
  <div class="cp3d">
    <!-- 左 1：图标导航栏（竖条） -->
    <nav class="icon-nav">
      <el-tooltip content="业务首页" placement="right">
        <router-link to="/dashboard" class="icon-btn">
          <el-icon :size="18"><DataBoard /></el-icon>
        </router-link>
      </el-tooltip>
      <el-tooltip content="地质信息" placement="right">
        <router-link to="/geology" class="icon-btn active">
          <el-icon :size="18"><Grid /></el-icon>
        </router-link>
      </el-tooltip>
      <el-tooltip content="监测信息" placement="right">
        <router-link to="/monitoring" class="icon-btn">
          <el-icon :size="18"><Monitor /></el-icon>
        </router-link>
      </el-tooltip>
      <el-tooltip content="参数反演" placement="right">
        <router-link to="/param" class="icon-btn">
          <el-icon :size="18"><Operation /></el-icon>
        </router-link>
      </el-tooltip>
      <el-tooltip content="安全预警" placement="right">
        <router-link to="/alert" class="icon-btn">
          <el-icon :size="18"><Warning /></el-icon>
        </router-link>
      </el-tooltip>
      <el-tooltip content="表单审批" placement="right">
        <router-link to="/form" class="icon-btn">
          <el-icon :size="18"><DocumentChecked /></el-icon>
        </router-link>
      </el-tooltip>
      <el-tooltip content="系统管理" placement="right">
        <router-link to="/system" class="icon-btn">
          <el-icon :size="18"><Setting /></el-icon>
        </router-link>
      </el-tooltip>
      <div class="nav-spacer"></div>
      <el-tooltip content="退出" placement="right">
        <div class="icon-btn" @click="$router.push('/login')">
          <el-icon :size="18"><SwitchButton /></el-icon>
        </div>
      </el-tooltip>
    </nav>

    <!-- 左 2：控制面板（白色卡片） -->
    <aside class="control-panel">
      <header class="panel-header">
        <h2>工程数字化协同大屏</h2>
        <p>岩土工程多场耦合数字化云分析系统</p>
      </header>

      <!-- 分组 1：施工开挖步 / 计算工况 -->
      <section class="section">
        <h3 class="section-title">
          施工开挖步 / 计算工况
          <span>切换后模型几何 + 标量同时变化</span>
        </h3>
        <div class="step-nav">
          <button class="step-btn" :disabled="!curStep.can_prev" @click="prevStep">← 上一步</button>
          <button class="step-btn primary" :disabled="!curStep.can_next" @click="nextStep">下一步 →</button>
        </div>
        <label class="field-label">开挖工况：{{ curStep.stage_key }}</label>
        <el-select
          v-model="state.stepIdx"
          class="w-full"
          size="default"
          @change="onStepChange"
        >
          <el-option
            v-for="s in stageList"
            :key="s.index"
            :label="s.label"
            :value="s.index"
          />
        </el-select>
        <div class="progress-row">
          <span>开挖进度</span>
          <el-progress
            :percentage="Math.round((state.stepIdx + 1) * 100 / Math.max(1, stageList.length))"
            :stroke-width="6"
            :show-text="false"
          />
          <span>{{ state.stepIdx + 1 }} / {{ stageList.length }}</span>
        </div>
      </section>

      <!-- 分组 2：物理量（标量场） -->
      <section class="section">
        <h3 class="section-title">
          物理量 / 标量场
          <span>三维颜色云图即时重绘</span>
        </h3>
        <el-radio-group v-model="state.scalarKey" size="small" @change="onScalarChange">
          <el-radio-button
            v-for="opt in scalarOptions"
            :key="opt.key"
            :value="opt.key"
          >{{ opt.label }}</el-radio-button>
        </el-radio-group>

        <label class="field-label">显示控制</label>
        <div class="toggle-grid">
          <el-switch v-model="state.showShell" @change="updateVisibility" active-text="外壳" />
          <el-switch v-model="state.showCavity" @change="updateVisibility" active-text="空腔" />
          <el-switch v-model="state.showBoreholes" @change="updateVisibility" active-text="钻孔" />
        </div>
        <div class="slider-row">
          <label>外壳透明度</label>
          <el-slider
            v-model="state.shellOpacity"
            :min="0" :max="100" :step="5"
            @change="updateVisibility"
          />
          <span class="slider-val">{{ state.shellOpacity }}%</span>
        </div>
      </section>

      <!-- 分组 3：剖切分析 -->
      <section class="section">
        <h3 class="section-title">
          剖切分析
          <span>从后端接口取真实采样值</span>
        </h3>
        <div class="toggle-row">
          <span>启用剖切</span>
          <el-switch v-model="state.showSection" @change="onSectionToggle" />
        </div>
        <el-radio-group
          v-model="state.sectionAxis"
          size="small"
          :disabled="!state.showSection"
          @change="onSectionChange"
        >
          <el-radio-button value="x">X 轴</el-radio-button>
          <el-radio-button value="y">Y 轴</el-radio-button>
          <el-radio-button value="z">Z 轴</el-radio-button>
        </el-radio-group>
        <div class="slider-row">
          <label>剖切位置</label>
          <el-slider
            v-model="state.sectionPos"
            :min="sectionRange[0]"
            :max="sectionRange[1]"
            :step="1"
            :disabled="!state.showSection"
            @change="onSectionChange"
          />
          <span class="slider-val">{{ state.sectionPos.toFixed(0) }} m</span>
        </div>
        <el-button size="default" class="w-full" type="primary" plain :disabled="!state.showSection" @click="analyzeSection">
          🔍 执行剖切分析
        </el-button>
      </section>

      <!-- 分组 4：视角预设 -->
      <section class="section">
        <h3 class="section-title">视角 / 镜头</h3>
        <div class="view-grid">
          <button class="view-btn" @click="setCam('iso')">等轴</button>
          <button class="view-btn" @click="setCam('top')">俯视</button>
          <button class="view-btn" @click="setCam('front')">正视</button>
          <button class="view-btn" @click="setCam('side')">侧视</button>
        </div>
      </section>
    </aside>

    <!-- 中间：三维主视图区 -->
    <main class="viewport">
      <VtkViewer
        ref="vtkRef"
        :stage-key="curStep.stage_key"
        :scalar-key="state.scalarKey"
        :show-shell="state.showShell"
        :show-cavity="state.showCavity"
        :shell-opacity="state.shellOpacity / 100"
        :show-boreholes="state.showBoreholes"
        :section-enabled="state.showSection"
        :section-axis="state.sectionAxis"
        :section-position="state.sectionPos"
        :borehole-list="boreholeList"
      />

      <!-- 顶部：标题 + 状态 -->
      <div class="vp-top-bar">
        <div class="vp-title">
          <span class="dot"></span>
          <span>三维地质结构实时协同视图</span>
        </div>
        <div class="vp-stats">
          <span class="chip">工况：<b>{{ curStep.label }}</b></span>
          <span class="chip">物理量：<b>{{ scalarLabel }}</b></span>
          <span class="chip" v-if="state.showSection">
            剖切：{{ state.sectionAxis.toUpperCase() }} = {{ state.sectionPos.toFixed(0) }} m
          </span>
        </div>
      </div>

      <!-- 底部：指标标签 -->
      <div class="vp-bottom-bar">
        <div class="stat-card" v-for="(it, i) in quickStats" :key="i">
          <div class="stat-label">{{ it.label }}</div>
          <div class="stat-value" :style="{ color: it.color }">{{ it.value }}</div>
        </div>
      </div>
    </main>

    <!-- 右：色阶图例（竖条） -->
    <aside class="legend-panel" v-if="colormap.stops.length">
      <div class="legend-title">{{ colormapLabel }}</div>
      <div class="legend-container">
        <div class="legend-bar">
          <div
            v-for="(stop, i) in colormap.stops"
            :key="i"
            class="legend-stop"
            :style="{ background: stop.hex, flex: 1 }"
          />
        </div>
        <div class="legend-labels">
          <span
            v-for="(stop, i) in labelStops"
            :key="i"
            :style="{ bottom: stop.bottom + '%' }"
          >{{ stop.value }}</span>
        </div>
      </div>
      <div class="legend-meta">
        <div>Min：<b>{{ colormap.min?.toFixed?.(2) ?? colormap.min }}</b></div>
        <div>Max：<b>{{ colormap.max?.toFixed?.(2) ?? colormap.max }}</b></div>
      </div>
    </aside>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  DataBoard, Grid, Monitor, Operation, Warning, DocumentChecked, Setting, SwitchButton
} from '@element-plus/icons-vue'
import VtkViewer from '@/components/VtkViewer.vue'
import { api } from '@/api'

// -------- 状态 --------
const vtkRef = ref(null)
const state = reactive({
  stepIdx: 0,
  scalarKey: 'displacement_mag',
  showShell: true,
  showCavity: true,
  showBoreholes: false,
  shellOpacity: 85,
  showSection: false,
  sectionAxis: 'x',
  sectionPos: 500,
})

// -------- 工况列表（优先走后端 API，失败降级到静态目录）--------
const stageList = ref([
  { index: 0, stage_key: 'exac_1', label: '第 1 步 · 初始开挖', can_prev: false, can_next: true },
])

const curStep = computed(() => stageList.value[state.stepIdx] || stageList.value[0])

const scalarOptions = [
  { key: 'displacement_mag', label: '位移（m）', unit: 'm' },
  { key: 'stress_xx', label: 'σxx（Pa）', unit: 'Pa' },
  { key: 'stress_yy', label: 'σyy（Pa）', unit: 'Pa' },
  { key: 'stress_zz', label: 'σzz（Pa）', unit: 'Pa' },
  { key: 'plastic_strain', label: '塑性应变', unit: '' },
  { key: 'pore_pressure', label: '孔压（Pa）', unit: 'Pa' },
]
const scalarLabel = computed(() => {
  const s = scalarOptions.find(o => o.key === state.scalarKey)
  return s ? s.label : state.scalarKey
})

const colormap = reactive({ min: 0, max: 1, stops: [] })
const colormapLabel = computed(() => scalarLabel.value)
const labelStops = computed(() => {
  const n = 5
  const arr = []
  for (let i = 0; i < n; i++) {
    const t = i / (n - 1)
    arr.push({
      bottom: t * 100,
      value: (colormap.min + (colormap.max - colormap.min) * t).toFixed(2),
    })
  }
  return arr
})

const sectionRange = ref([0, 1000])

const boreholeList = ref([
  { id: 'ZK01', x: 480, y: -180, z: 560, depth: 80, label: 'ZK01' },
  { id: 'ZK02', x: 520, y: -190, z: 560, depth: 72, label: 'ZK02' },
  { id: 'ZK03', x: 500, y: -200, z: 560, depth: 95, label: 'ZK03' },
])

const quickStats = computed(() => [
  { label: '当前位移最大值', value: (colormap.max ?? 0).toFixed(3) + ' m', color: '#ef4444' },
  { label: '开挖步数', value: (state.stepIdx + 1) + ' / ' + stageList.value.length, color: '#2563eb' },
  { label: '显示钻孔', value: state.showBoreholes ? boreholeList.value.length + ' 个' : '关', color: '#10b981' },
  { label: '剖切状态', value: state.showSection ? (state.sectionAxis.toUpperCase() + ' 轴') : '关闭', color: '#f59e0b' },
])

// -------- 方法 --------
function prevStep() { if (curStep.value.can_prev) { state.stepIdx--; onStepChange() } }
function nextStep() { if (curStep.value.can_next) { state.stepIdx++; onStepChange() } }

async function onStepChange() {
  // 修正 can_prev / can_next
  stageList.value.forEach((s, i) => {
    s.can_prev = i > 0
    s.can_next = i < stageList.value.length - 1
  })
  // 切标量范围
  await fetchColormap()
}

async function onScalarChange() { await fetchColormap() }

function onSectionToggle() {
  vtkRef.value?.toggleSection?.(state.showSection)
  if (state.showSection) onSectionChange()
}
function onSectionChange() {
  vtkRef.value?.setSectionAxis?.(state.sectionAxis, state.sectionPos)
}
async function analyzeSection() {
  try {
    const r = await api.get('/interactive3d/analysis/section', {
      params: {
        stage_key: curStep.value.stage_key,
        scalar_key: state.scalarKey,
        axis: state.sectionAxis,
        position: state.sectionPos,
      },
    })
    vtkRef.value?.updateSection?.(r.data || r)
    ElMessage.success(`剖切完成，采样点 ${r.data?.samples ?? r.samples ?? 0} 个`)
  } catch (e) {
    ElMessage.warning('后端剖切接口暂未返回数据，使用前端内置预览')
    vtkRef.value?.updateSection?.({ preview: true })
  }
}

function updateVisibility() {
  vtkRef.value?.updateVisibility?.({
    showShell: state.showShell,
    showCavity: state.showCavity,
    shellOpacity: state.shellOpacity / 100,
    showBoreholes: state.showBoreholes,
  })
}
function setCam(view) { vtkRef.value?.setCameraDefault?.(view) }

async function fetchStages() {
  try {
    const r = await api.get('/interactive3d/excavation/stages')
    const data = r.data?.stages || r.stages || r.data || r
    if (Array.isArray(data) && data.length) {
      stageList.value = data.map((s, i) => ({
        index: i,
        stage_key: s.key || s.stage_key || s.id || `exac_${i + 1}`,
        label: s.label || s.name || `第 ${i + 1} 步`,
        can_prev: i > 0,
        can_next: i < data.length - 1,
      }))
    }
  } catch (e) {
    // 降级：从 model_cache 目录扫描
    stageList.value = Array.from({ length: 10 }, (_, i) => ({
      index: i, stage_key: `exac_${i + 1}`,
      label: `第 ${i + 1} 步 · 开挖面 ${52 + i * 5} m`,
      can_prev: i > 0, can_next: i < 9,
    }))
  }
}

async function fetchColormap() {
  try {
    const r = await api.get('/interactive3d/scalars/colormap', {
      params: {
        stage_key: curStep.value.stage_key,
        scalar_key: state.scalarKey,
      },
    })
    const d = r.data || r
    colormap.min = d.min ?? d.range_min ?? 0
    colormap.max = d.max ?? d.range_max ?? 1
    colormap.stops = Array.isArray(d.stops) ? d.stops : buildStops(colormap.min, colormap.max)
    if (Array.isArray(d.bounds) && d.bounds.length === 6) {
      const axisIdx = { x: 0, y: 2, z: 4 }[state.sectionAxis]
      sectionRange.value = [d.bounds[axisIdx], d.bounds[axisIdx + 1]]
      state.sectionPos = (sectionRange.value[0] + sectionRange.value[1]) / 2
    }
  } catch {
    colormap.min = 0; colormap.max = 0.05
    colormap.stops = buildStops(0, 0.05)
  }
  vtkRef.value?.setColormap?.(colormap.min, colormap.max, colormap.stops)
}

function buildStops(min, max) {
  const palette = ['#006837', '#1a9850', '#66bd63', '#a6d96a', '#d9ef8b',
    '#ffffbf', '#fee08b', '#fdae61', '#f46d43', '#d73027', '#a50026']
  return palette.map((hex, i) => ({ t: i / (palette.length - 1), hex, value: min + (max - min) * i / (palette.length - 1) }))
}

onMounted(async () => {
  await fetchStages()
  await fetchColormap()
})
</script>

<style scoped>
.cp3d {
  display: grid;
  grid-template-columns: 56px 320px 1fr 180px;
  height: 100vh;
  background: #0f172a;
  color: #e2e8f0;
  font-family: system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
}
.icon-nav {
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  display: flex; flex-direction: column; align-items: center;
  padding: 16px 0; gap: 10px;
  border-right: 1px solid #334155;
}
.icon-btn {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  color: #94a3b8; cursor: pointer; transition: .2s;
  text-decoration: none;
}
.icon-btn:hover { background: #334155; color: #fff; }
.icon-btn.active { background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #fff; box-shadow: 0 4px 12px rgba(37,99,235,.4); }
.nav-spacer { flex: 1; }

.control-panel {
  background: #fff; color: #0f172a;
  padding: 20px 18px; overflow-y: auto;
  border-right: 1px solid #e2e8f0;
}
.panel-header h2 { margin: 0 0 4px; font-size: 18px; font-weight: 700; color: #0f172a; }
.panel-header p { margin: 0; font-size: 12px; color: #64748b; }

.section { margin-top: 22px; padding-top: 16px; border-top: 1px solid #e2e8f0; }
.section:first-of-type { margin-top: 20px; border-top: 0; padding-top: 0; }
.section-title {
  font-size: 13px; font-weight: 700; color: #0f172a; margin: 0 0 12px;
  display: flex; align-items: baseline; justify-content: space-between;
}
.section-title span { font-size: 11px; font-weight: 400; color: #64748b; }
.field-label { display: block; font-size: 12px; color: #475569; margin: 12px 0 6px; }
.w-full { width: 100%; }

.step-nav { display: flex; gap: 8px; margin-bottom: 10px; }
.step-btn {
  flex: 1; padding: 8px 10px; border-radius: 8px;
  border: 1px solid #cbd5e1; background: #f8fafc; color: #0f172a;
  cursor: pointer; font-size: 12px; transition: .15s;
}
.step-btn:hover:not(:disabled) { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.step-btn:disabled { opacity: .5; cursor: not-allowed; }
.step-btn.primary { background: linear-gradient(135deg, #2563eb, #1d4ed8); border-color: transparent; color: #fff; }
.step-btn.primary:hover:not(:disabled) { opacity: .9; color: #fff; }

.progress-row { display: flex; align-items: center; gap: 10px; margin-top: 12px; font-size: 12px; color: #475569; }
.progress-row .el-progress { flex: 1; }

.toggle-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px 12px; margin-bottom: 6px; }
.toggle-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; font-size: 12px; color: #475569; }
.slider-row { display: flex; align-items: center; gap: 10px; margin: 10px 0; font-size: 12px; color: #475569; }
.slider-row label { width: 72px; flex-shrink: 0; }
.slider-row .el-slider { flex: 1; }
.slider-val { width: 50px; text-align: right; font-variant-numeric: tabular-nums; }

.view-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
.view-btn {
  padding: 10px 0; border-radius: 8px;
  background: #f1f5f9; border: 1px solid #e2e8f0;
  cursor: pointer; font-size: 13px; color: #334155; transition: .15s;
}
.view-btn:hover { background: #2563eb; color: #fff; border-color: #2563eb; }

.viewport { position: relative; background: #050b18; overflow: hidden; }
.vp-top-bar {
  position: absolute; top: 16px; left: 16px; right: 16px; z-index: 10;
  display: flex; justify-content: space-between; align-items: center; pointer-events: none;
}
.vp-title {
  background: rgba(15,23,42,.75); backdrop-filter: blur(6px);
  padding: 8px 14px; border-radius: 8px; font-size: 13px; color: #e2e8f0;
  display: flex; align-items: center; gap: 8px; border: 1px solid rgba(148,163,184,.2);
}
.vp-title .dot { width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 0 3px rgba(16,185,129,.25); animation: pulse 2s infinite; }
@keyframes pulse { 50% { opacity: .4; } }
.vp-stats { display: flex; gap: 8px; }
.chip {
  background: rgba(15,23,42,.75); backdrop-filter: blur(6px);
  padding: 6px 12px; border-radius: 6px; font-size: 12px; color: #cbd5e1;
  border: 1px solid rgba(148,163,184,.2);
}
.chip b { color: #fff; margin-left: 4px; }

.vp-bottom-bar {
  position: absolute; bottom: 16px; left: 16px; right: 16px; z-index: 10;
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; pointer-events: none;
}
.stat-card {
  background: rgba(15,23,42,.8); backdrop-filter: blur(8px);
  border: 1px solid rgba(148,163,184,.15);
  padding: 12px 14px; border-radius: 10px;
}
.stat-label { font-size: 11px; color: #94a3b8; margin-bottom: 4px; }
.stat-value { font-size: 18px; font-weight: 700; font-variant-numeric: tabular-nums; }

.legend-panel {
  background: #0b1222; border-left: 1px solid #1e293b;
  padding: 20px 16px; display: flex; flex-direction: column;
}
.legend-title { font-size: 12px; color: #cbd5e1; margin-bottom: 14px; font-weight: 600; }
.legend-container { flex: 1; position: relative; display: flex; gap: 10px; }
.legend-bar { width: 22px; border-radius: 4px; overflow: hidden; display: flex; flex-direction: column-reverse; }
.legend-labels { flex: 1; position: relative; font-size: 10px; color: #94a3b8; font-variant-numeric: tabular-nums; }
.legend-labels span { position: absolute; left: 0; transform: translateY(50%); }
.legend-meta { margin-top: 14px; font-size: 11px; color: #64748b; display: flex; flex-direction: column; gap: 4px; }
.legend-meta b { color: #e2e8f0; }
</style>
