<template>
  <div class="lt3d">
    <!-- 左侧深色文字导航 -->
    <nav class="side-nav">
      <div class="nav-header">
        <div class="logo">🌐</div>
        <div>
          <div class="sys-title">古贤坝址治理</div>
          <div class="sys-sub">地下厂房洞室群监测<br/>稳定智能分析与预警</div>
        </div>
      </div>

      <ul class="nav-list">
        <li :class="active === 'home' ? 'active' : ''" @click="active = 'home'">
          <span class="nav-icon">🏠</span>
          <span>业务工作区 (工作台)</span>
        </li>
        <li :class="active === 'geo' ? 'active' : ''" @click="active = 'geo'">
          <span class="nav-icon">🪨</span>
          <span>地质信息模块</span>
        </li>
        <li :class="active === 'mon' ? 'active' : ''" @click="active = 'mon'">
          <span class="nav-icon">📡</span>
          <span>监测信息模块</span>
        </li>
        <li :class="active === 'param' ? 'active' : ''" @click="active = 'param'">
          <span class="nav-icon">🧮</span>
          <span>参数反演模块</span>
        </li>
        <li :class="active === 'alert' ? 'active' : ''" @click="active = 'alert'">
          <span class="nav-icon">🚨</span>
          <span>安全预警模块</span>
        </li>
        <li :class="active === 'form' ? 'active' : ''" @click="active = 'form'">
          <span class="nav-icon">📝</span>
          <span>表单审批模块</span>
        </li>
        <li :class="active === 'sys' ? 'active' : ''" @click="active = 'sys'">
          <span class="nav-icon">⚙️</span>
          <span>系统管理</span>
        </li>
      </ul>

      <div class="nav-footer">
        <div class="user-card">
          <div class="avatar">张</div>
          <div>
            <div class="username">张工程师</div>
            <div class="userrole">项目负责人 · 在线</div>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主视口（三维） -->
    <main class="main-area">
      <!-- 顶部 breadcrumb + 右上角快捷入口 -->
      <header class="top-bar">
        <div class="breadcrumb">
          <span>🏠 首页</span>
          <span class="sep">/</span>
          <span class="current">地质信息模块</span>
          <span class="sep">/</span>
          <span class="current">三维地质结构</span>
        </div>
        <div class="top-actions">
          <el-button size="default" round plain>📤 导出截图</el-button>
          <el-button size="default" round type="primary">📐 测量工具</el-button>
          <div class="project-chip">项目工 ▾</div>
        </div>
      </header>

      <div class="viewport-wrapper">
        <!-- 叠加：图层树（白色卡片） -->
        <div class="overlay-layer-tree">
          <div class="panel-title-row">
            <h3>结构图层目录</h3>
            <div class="tools">
              <el-button size="small" text @click="expandAll">⊞</el-button>
              <el-button size="small" text @click="refreshTree">🔄</el-button>
              <el-button size="small" text>🔍</el-button>
            </div>
          </div>

          <div class="tree-wrap">
            <el-tree
              ref="treeRef"
              :data="layerTree"
              show-checkbox
              node-key="id"
              :default-expand-all="true"
              :expand-on-click-node="false"
              @check="onTreeCheck"
              @node-click="onNodeClick"
              :props="{ label: 'label', children: 'children' }"
            >
              <template #default="{ node, data }">
                <span class="tree-node">
                  <span
                    class="dot"
                    v-if="data.type"
                    :style="{ background: data.color || '#2563eb' }"
                  ></span>
                  <span class="name" :title="data.label">{{ data.label }}</span>
                  <span v-if="data.code" class="code">({{ data.code }})</span>
                </span>
              </template>
            </el-tree>
          </div>

          <div class="tree-footer">
            <div class="legend-row">
              <span class="ldot" style="background:#7c3aed"></span>结构面
              <span class="ldot" style="background:#eab308"></span>地层
              <span class="ldot" style="background:#10b981"></span>钻孔
              <span class="ldot" style="background:#ef4444"></span>监测点
            </div>
          </div>
        </div>

        <!-- 叠加：详情卡片 -->
        <transition name="fade">
          <div class="overlay-detail-card" v-if="selectedNode">
            <header class="detail-header">
              <h4>结构详情 · {{ selectedNode.id }}</h4>
              <button class="close-btn" @click="selectedNode = null">×</button>
            </header>
            <div class="detail-body">
              <table class="detail-table">
                <tbody>
                  <tr v-for="(v, k) in detailRows" :key="k" :class="k === '描述' ? 'desc' : ''">
                    <th>{{ k }}</th>
                    <td>{{ formatVal(v) }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-if="!detailRows || Object.keys(detailRows).length === 0" class="empty-detail">
                暂无详细参数
              </div>
            </div>
          </div>
        </transition>

        <!-- 叠加：右上 3 个永久切片图例 -->
        <div class="overlay-legend-planes">
          <div class="plane-chip" style="--c:#7c3aed">
            <span class="psq"></span>剖面 X = 474
          </div>
          <div class="plane-chip" style="--c:#eab308">
            <span class="psq"></span>剖面 Y = -185
          </div>
          <div class="plane-chip" style="--c:#10b981">
            <span class="psq"></span>剖面 Z = 547
          </div>
        </div>

        <!-- VTK 三维视图 -->
        <VtkViewer
          ref="vtkRef"
          :stage-key="currentStageKey"
          :layer-config="layerConfig"
          :section-planes="sectionPlanes"
          mode="layers"
        />
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import VtkViewer from '@/components/VtkViewer.vue'
import { api } from '@/api'

const active = ref('geo')
const treeRef = ref(null)
const vtkRef = ref(null)

// -------- 图层树（后端 /layers/tree + 前端合并）--------
const layerTree = ref([])
const checkedIds = ref(new Set())
const selectedNode = ref(null)
const currentStageKey = ref('exac_1')

const sectionPlanes = reactive([
  { axis: 'x', position: 474, color: '#7c3aed', opacity: 0.6 },
  { axis: 'y', position: -185, color: '#eab308', opacity: 0.6 },
  { axis: 'z', position: 547, color: '#10b981', opacity: 0.6 },
])

const layerConfig = computed(() => ({
  visibleIds: Array.from(checkedIds.value),
  selectedId: selectedNode.value?.id ?? null,
}))

const detailRows = computed(() => {
  const n = selectedNode.value
  if (!n) return {}
  const base = {
    '名称': n.label ?? n.name,
    '编号': n.code ?? n.id ?? '-',
    '类型': n.type ?? '图层',
    '颜色': n.color ?? '-',
  }
  if (n.props && typeof n.props === 'object') Object.assign(base, n.props)
  if (n.desc) base['描述'] = n.desc
  return base
})

function formatVal(v) {
  if (v === null || v === undefined) return '-'
  if (typeof v === 'number') return v.toLocaleString()
  return String(v)
}

function onTreeCheck(_, info) {
  checkedIds.value = new Set(info.checkedKeys)
  ElMessage({ message: `已勾选 ${checkedIds.value.size} 项`, type: 'info', duration: 1200 })
}
function onNodeClick(data) {
  selectedNode.value = data
  vtkRef.value?.highlightFeature?.(data.id, data)
}
function expandAll() {
  treeRef.value?.store?.nodesMap?.forEach?.(n => { n.expanded = true })
}
async function refreshTree() {
  await loadLayerTree()
  ElMessage.success('图层树已刷新')
}

async function loadLayerTree() {
  try {
    const r = await api.get('/interactive3d/layers/tree', { params: { project_id: 1 } })
    const raw = r.data?.tree || r.tree || []
    if (Array.isArray(raw) && raw.length) {
      layerTree.value = decorate(raw)
      // 默认全选
      const ids = collectIds(raw)
      checkedIds.value = new Set(ids)
    } else {
      layerTree.value = defaultTree()
      checkedIds.value = new Set(collectIds(layerTree.value))
    }
  } catch {
    layerTree.value = defaultTree()
    checkedIds.value = new Set(collectIds(layerTree.value))
  }
}

function decorate(nodes) {
  return nodes.map(n => ({
    ...n,
    id: n.id ?? Math.random().toString(36).slice(2, 9),
    label: n.label ?? n.name ?? '未命名',
    children: Array.isArray(n.children) ? decorate(n.children) : undefined,
  }))
}
function collectIds(nodes, out = []) {
  nodes.forEach(n => {
    out.push(n.id)
    if (Array.isArray(n.children)) collectIds(n.children, out)
  })
  return out
}
function defaultTree() {
  return [
    {
      id: 'g-strata', label: '地层模型', type: 'group', color: '#64748b',
      children: [
        { id: 's1', label: '耕植土', code: 'Q', type: 'stratum', color: '#eab308', props: { '厚度': '1.5~2.3 m', '重度': '18.2 kN/m³', '黏聚力': '12 kPa' }, desc: '表层松散覆盖层，结构疏松，含植物根系。' },
        { id: 's2', label: '粉质黏土', code: 'Qdl', type: 'stratum', color: '#f59e0b', props: { '厚度': '3.8~6.1 m', '重度': '19.5 kN/m³', '压缩模量': '8.5 MPa' } },
        { id: 's3', label: '强风化砂岩', code: 'T3x', type: 'stratum', color: '#d97706', props: { '厚度': '8.0~12.5 m', 'RQD': '30~50%', '单轴抗压': '15 MPa' } },
        { id: 's4', label: '中风化砂岩', code: 'T3x-2', type: 'stratum', color: '#b45309', props: { '厚度': '15.0~22.0 m', 'RQD': '70~85%', '单轴抗压': '42 MPa' } },
        { id: 's5', label: '微风化砂质泥岩互层', code: 'T3x-3', type: 'stratum', color: '#78350f', props: { '厚度': '>30 m', 'RQD': '85~95%', '单轴抗压': '68 MPa' } },
      ],
    },
    {
      id: 'g-structure', label: '地质结构面', type: 'group', color: '#7c3aed',
      children: [
        { id: 'f1', label: '断层 F1', code: 'F1', type: 'fault', color: '#7c3aed', props: { '产状': 'N45°E/SE∠70°', '宽度': '0.8~1.2 m', '充填物': '断层泥+角砾' }, desc: '横贯厂房左侧边墙，施工期需加强锚喷支护。' },
        { id: 'f2', label: '断层 F2', code: 'F2', type: 'fault', color: '#6d28d9', props: { '产状': 'N20°W/NE∠55°', '宽度': '0.3~0.6 m' } },
        { id: 'j1', label: '节理组 J1', code: 'J1', type: 'joint', color: '#a78bfa', props: { '产状': 'N60°E/NW∠45°', '间距': '0.3~0.8 m', '延伸长度': '3~8 m' } },
        { id: 'j2', label: '节理组 J2', code: 'J2', type: 'joint', color: '#c4b5fd', props: { '产状': 'N30°W/SW∠60°', '间距': '0.5~1.2 m' } },
      ],
    },
    {
      id: 'g-borehole', label: '勘察钻孔', type: 'group', color: '#10b981',
      children: [
        { id: 'zk01', label: 'ZK01', code: 'ZK01', type: 'borehole', color: '#10b981', props: { '孔口高程': '567.20 m', '孔深': '95.40 m', '终孔层位': 'T3x-3' } },
        { id: 'zk02', label: 'ZK02', code: 'ZK02', type: 'borehole', color: '#059669', props: { '孔口高程': '565.80 m', '孔深': '88.20 m', '终孔层位': 'T3x-3' } },
        { id: 'zk03', label: 'ZK03', code: 'ZK03', type: 'borehole', color: '#047857', props: { '孔口高程': '568.10 m', '孔深': '102.60 m', '终孔层位': 'T3x-3' } },
      ],
    },
    {
      id: 'g-cavern', label: '洞室群', type: 'group', color: '#2563eb',
      children: [
        { id: 'c-main', label: '主厂房', code: 'C-1', type: 'cavern', color: '#2563eb', props: { '尺寸': 'L×W×H = 220×28×60 m', '开挖方式': '分层分块钻爆法' } },
        { id: 'c-trans', label: '主变室', code: 'C-2', type: 'cavern', color: '#3b82f6', props: { '尺寸': 'L×W×H = 180×18×30 m' } },
        { id: 'c-tail', label: '尾水调压室', code: 'C-3', type: 'cavern', color: '#60a5fa', props: { '尺寸': 'L×W×H = 120×20×45 m' } },
      ],
    },
    {
      id: 'g-monitor', label: '监测仪器', type: 'group', color: '#ef4444',
      children: [
        { id: 'm-disp', label: '多点位移计', code: 'MD', type: 'sensor', color: '#ef4444', props: { '布置数量': 24, '量程': '±100 mm', '精度': '0.01 mm' } },
        { id: 'm-stress', label: '应力计', code: 'MS', type: 'sensor', color: '#dc2626', props: { '布置数量': 18, '量程': '0~20 MPa' } },
        { id: 'm-seep', label: '渗压计', code: 'MP', type: 'sensor', color: '#b91c1c', props: { '布置数量': 12, '量程': '0~2 MPa' } },
      ],
    },
  ]
}

onMounted(async () => { await loadLayerTree() })
</script>

<style scoped>
.lt3d {
  display: grid;
  grid-template-columns: 240px 1fr;
  height: 100vh;
  background: #0f172a;
  font-family: system-ui, -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #0f172a;
}
.side-nav {
  background: linear-gradient(180deg, #111827 0%, #0b1220 100%);
  color: #cbd5e1;
  display: flex; flex-direction: column;
  padding: 18px 14px;
  border-right: 1px solid #1f2937;
}
.nav-header {
  display: flex; gap: 12px; align-items: flex-start;
  padding-bottom: 18px; margin-bottom: 10px;
  border-bottom: 1px solid #1f2937;
}
.logo { width: 40px; height: 40px; border-radius: 10px; background: linear-gradient(135deg, #2563eb, #7c3aed); display: flex; align-items: center; justify-content: center; font-size: 20px; flex-shrink: 0; }
.sys-title { font-size: 15px; font-weight: 700; color: #fff; margin-bottom: 4px; }
.sys-sub { font-size: 11px; color: #94a3b8; line-height: 1.5; }

.nav-list { list-style: none; margin: 8px 0; padding: 0; flex: 1; }
.nav-list li {
  padding: 10px 12px; margin: 2px 0; border-radius: 8px;
  display: flex; align-items: center; gap: 10px;
  cursor: pointer; transition: .2s; font-size: 13px; color: #cbd5e1;
}
.nav-list li:hover { background: #1f2937; color: #fff; }
.nav-list li.active { background: linear-gradient(135deg, rgba(37,99,235,.25), rgba(124,58,237,.25)); color: #fff; border: 1px solid rgba(96,165,250,.3); }
.nav-icon { font-size: 15px; }

.nav-footer { padding-top: 12px; border-top: 1px solid #1f2937; }
.user-card { display: flex; gap: 10px; align-items: center; padding: 6px 4px; }
.avatar {
  width: 36px; height: 36px; border-radius: 50%;
  background: linear-gradient(135deg, #10b981, #059669);
  color: #fff; display: flex; align-items: center; justify-content: center; font-weight: 700;
}
.username { font-size: 13px; color: #fff; font-weight: 600; }
.userrole { font-size: 11px; color: #64748b; margin-top: 2px; }

.main-area { display: flex; flex-direction: column; overflow: hidden; background: #0a1020; }
.top-bar {
  height: 54px; background: rgba(255,255,255,.96); backdrop-filter: blur(10px);
  border-bottom: 1px solid #e2e8f0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 22px;
}
.breadcrumb { font-size: 13px; color: #475569; }
.breadcrumb .sep { margin: 0 8px; color: #cbd5e1; }
.breadcrumb .current { color: #0f172a; font-weight: 600; }
.top-actions { display: flex; align-items: center; gap: 10px; }
.project-chip {
  padding: 6px 12px; border-radius: 6px; background: #f1f5f9;
  border: 1px solid #e2e8f0; font-size: 12px; color: #334155; cursor: pointer;
}

.viewport-wrapper { flex: 1; position: relative; overflow: hidden; background: #050b18; }

.overlay-layer-tree {
  position: absolute; top: 18px; left: 18px; z-index: 20;
  width: 300px; max-height: calc(100% - 36px);
  background: rgba(255,255,255,.98); border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0,0,0,.25);
  border: 1px solid rgba(226,232,240,.8);
  display: flex; flex-direction: column;
  backdrop-filter: blur(10px);
}
.panel-title-row {
  padding: 14px 16px; border-bottom: 1px solid #e2e8f0;
  display: flex; justify-content: space-between; align-items: center;
}
.panel-title-row h3 { margin: 0; font-size: 14px; font-weight: 700; color: #0f172a; }
.panel-title-row .tools { display: flex; gap: 2px; }
.tree-wrap { flex: 1; overflow-y: auto; padding: 8px 10px 12px; }
.tree-node { display: flex; align-items: center; gap: 6px; font-size: 12.5px; color: #334155; }
.tree-node .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 0 0 2px rgba(255,255,255,.9); }
.tree-node .name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tree-node .code { color: #94a3b8; font-size: 11px; }
.tree-footer { padding: 10px 14px 14px; border-top: 1px dashed #e2e8f0; }
.legend-row { display: flex; flex-wrap: wrap; gap: 12px; font-size: 11px; color: #64748b; align-items: center; }
.ldot { display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 4px; vertical-align: middle; }

.overlay-detail-card {
  position: absolute; top: 18px; right: 18px; z-index: 20;
  width: 320px; max-height: 60vh;
  background: rgba(255,255,255,.98); border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0,0,0,.25);
  border: 1px solid rgba(226,232,240,.8);
  backdrop-filter: blur(10px);
  overflow: hidden;
  display: flex; flex-direction: column;
}
.detail-header {
  padding: 12px 16px; background: linear-gradient(135deg, #1e3a8a, #6d28d9);
  color: #fff; display: flex; justify-content: space-between; align-items: center;
}
.detail-header h4 { margin: 0; font-size: 13px; font-weight: 600; }
.close-btn { background: rgba(255,255,255,.2); border: 0; color: #fff; width: 24px; height: 24px; border-radius: 6px; cursor: pointer; font-size: 18px; line-height: 1; }
.close-btn:hover { background: rgba(255,255,255,.35); }
.detail-body { padding: 12px 0; overflow-y: auto; }
.detail-table { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.detail-table th { text-align: left; padding: 7px 16px; color: #64748b; font-weight: 500; width: 100px; background: #f8fafc; border-bottom: 1px solid #f1f5f9; }
.detail-table td { padding: 7px 16px; color: #0f172a; border-bottom: 1px solid #f1f5f9; font-variant-numeric: tabular-nums; }
.detail-table tr.desc th { vertical-align: top; }
.detail-table tr.desc td { line-height: 1.6; color: #334155; }
.empty-detail { padding: 40px 16px; text-align: center; color: #94a3b8; font-size: 12px; }

.overlay-legend-planes {
  position: absolute; top: 18px; left: 50%; transform: translateX(-50%); z-index: 15;
  display: flex; gap: 10px;
  background: rgba(15,23,42,.7); backdrop-filter: blur(8px);
  padding: 8px 14px; border-radius: 8px; border: 1px solid rgba(148,163,184,.2);
}
.plane-chip {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: #e2e8f0;
  padding: 2px 6px;
}
.psq { width: 12px; height: 12px; border-radius: 3px; background: var(--c); box-shadow: 0 0 0 2px rgba(255,255,255,.2); }

.fade-enter-active, .fade-leave-active { transition: opacity .25s, transform .25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; transform: translateX(30px); }
</style>
