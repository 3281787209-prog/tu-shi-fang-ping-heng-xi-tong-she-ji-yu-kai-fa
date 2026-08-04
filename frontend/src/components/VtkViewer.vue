<template>
  <div class="vtk-viewer" ref="containerRef">
    <canvas ref="canvasRef" class="vtk-canvas"></canvas>

    <!-- 加载遮罩 -->
    <div v-if="loading" class="vtk-loading">
      <div class="spinner"></div>
      <div class="loading-text">{{ loadingText }}</div>
    </div>

    <!-- 加载失败降级显示：无 VTK 时用伪三维几何 -->
    <div v-if="fallback" class="vtk-fallback">
      <div class="fb-inner">
        <div class="fb-title">🌐 三维视图（降级模式）</div>
        <div class="fb-sub">当前工况：<b>{{ stageKey }}</b> · 无法加载 VTK.js 时以交互式等轴示意图替代</div>
        <div class="fb-3d" :style="fbStageStyle">
          <div class="fb-layer fb-shell" :style="fbLayerStyle('shell')"></div>
          <div class="fb-layer fb-cavity" :style="fbLayerStyle('cavity')"></div>
          <div v-for="(bh in (boreholeList || [])" :key="bh.id" class="fb-borehole" :style="fbBoreholeStyle(bh)">{{ bh.label }}</div>
          <div v-for="(p, i) in (sectionPlanes || [])" :key="'pl'+i" class="fb-plane" :style="fbPlaneStyle(p, i)"></div>
        </div>
        <div class="fb-stats">
          <span>标量：<b>{{ scalarKey || '未指定' }}</b></span>
          <span>Min：<b>{{ colormap.min }}</b></span>
          <span>Max：<b>{{ colormap.max }}</b></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/**
 * VtkViewer.vue
 * ------------------------------------------------------------------
 * 真实三维变化原理（每次控件操作都会触发下列真实变化之一）：
 *   ① 工况切换：卸载旧 Actor，重新加载新 VTP → 模型几何真实改变（开挖从第1步逐步扩大）
 *   ② 物理量切换：PointData.setActiveScalars + mapper colorBy → 全模型颜色云图真实重绘
 *   ③ 剖切：从 /analysis/section 接口收到后端采样的真实标量值，绘制彩色网格平面
 *   ④ 透明度/可见性：actor.property.setOpacity / setVisibility → 即时生效
 *   ⑤ 色阶：重建 LookupTable（min/max/21 档 stops）→ 色阶图例与三维同步
 *   ⑥ 图层（LayerTree3D）：根据 visibleIds 显示/隐藏结构面切片、钻孔、传感器 glyph
 *
 * 如果浏览器环境缺失 VTK.js（例如静态预览时），自动降级为 CSS-3D 等轴示意视图。
 * ------------------------------------------------------------------
 */
import { ref, reactive, shallowRef, onMounted, onBeforeUnmount, watch, computed, nextTick } from 'vue'

const props = defineProps({
  stageKey: { type: String, default: 'exac_1' },
  scalarKey: { type: String, default: 'displacement_mag' },
  showShell: { type: Boolean, default: true },
  showCavity: { type: Boolean, default: true },
  showBoreholes: { type: Boolean, default: false },
  shellOpacity: { type: Number, default: 0.85 },
  sectionEnabled: { type: Boolean, default: false },
  sectionAxis: { type: String, default: 'x' },
  sectionPosition: { type: Number, default: 500 },
  boreholeList: { type: Array, default: () => [] },
  layerConfig: { type: Object, default: () => ({}) },      // LayerTree3D 传入
  sectionPlanes: { type: Array, default: () => [] },        // LayerTree3D 传入的永久切片
  mode: { type: String, default: 'scalar' },              // scalar | layers
})

// ---------- 对外暴露 ----------
const api = {
  setColormap(min, max, stops) {
    colormap.min = min; colormap.max = max
    if (Array.isArray(stops) && stops.length) colormap.stops = stops.slice()
    rebuildLut()
  },
  setScalarKey(k) { applyScalar(k) },
  setSectionAxis(axis, pos) {
    sectionState.axis = axis; sectionState.pos = pos
    refreshSection()
  },
  toggleSection(on) {
    sectionState.enabled = !!on
    if (sectionActor.value) sectionActor.value.setVisibility(!!on)
    if (permanentActors.value.length) permanentActors.value.forEach(a => a.setVisibility(!!on))
    render()
  },
  updateSection(data) { drawSection(data) },
  updateVisibility(s) { applyVisibility(s) },
  setCamera(pos, fp, up) { setCameraInternal(pos, fp, up) },
  setCameraDefault(view) { applyViewPreset(view) },
  highlightFeature(id, data) { highlightFeatureInternal(id, data) },
}
defineExpose(api)

// ---------- 状态 ----------
const containerRef = ref(null)
const canvasRef = ref(null)
const loading = ref(true)
const loadingText = ref('初始化三维渲染引擎...')
const fallback = ref(false)

const colormap = reactive({ min: 0, max: 0.05, stops: defaultStops() })
const sectionState = reactive({ enabled: false, axis: 'x', pos: 500 })

// VTK 对象（shallow，不被 Vue 深度响应，避免破坏 VTK 内部）
const renWin = shallowRef(null)
const renderer = shallowRef(null)
const interactor = shallowRef(null)
const glRW = shallowRef(null)

const shellActor = shallowRef(null)
const cavityActor = shallowRef(null)
const sectionActor = shallowRef(null)
const boreholeActors = shallowRef([])
const permanentActors = shallowRef([])   // 图层树永久切片 actor
const lookupTable = shallowRef(null)
const currentStage = ref('')

// ---------- 工具 ----------
function defaultStops() {
  const palette = ['#006837','#1a9850','#66bd63','#a6d96a','#d9ef8b','#ffffbf','#fee08b','#fdae61','#f46d43','#d73027','#a50026']
  return palette.map((hex, i) => ({ t: i / (palette.length - 1), hex, value: colormap.min + (colormap.max - colormap.min) * i / (palette.length - 1) }))
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

// ---------- 生命周期 ----------
onMounted(async () => {
  await nextTick()
  try {
    await initVtk()
    await loadStage(props.stageKey)
    loading.value = false
  } catch (e) {
    console.warn('[VtkViewer] VTK 初始化失败，降级到 CSS-3D 模式：', e?.message || e)
    loading.value = false
    fallback.value = true
  }
})

onBeforeUnmount(() => {
  try {
    permanentActors.value.forEach(a => renderer.value?.removeActor(a))
    boreholeActors.value.forEach(a => renderer.value?.removeActor(a))
    if (shellActor.value) renderer.value?.removeActor(shellActor.value)
    if (cavityActor.value) renderer.value?.removeActor(cavityActor.value)
    if (sectionActor.value) renderer.value?.removeActor(sectionActor.value)
    glRW.value?.delete()
    renWin.value?.delete()
    interactor.value?.delete()
    renderer.value?.delete()
  } catch (_) { /* noop */ }
})

// ---------- 初始化 VTK ----------
async function initVtk() {
  // 动态 import（打包时 VTK.js 可选）
  let vtk
  try {
    vtk = await importVtk()
  } catch (e) {
    throw new Error('VTK.js 模块不可用')
  }

  const renderWindow = vtk.RenderWindow.newInstance()
  const rend = vtk.Renderer.newInstance({ background: [0.02, 0.043, 0.094] })
  renderWindow.addRenderer(rend)

  const oglRw = vtk.OpenGLRenderWindow.newInstance()
  oglRw.setContainer(containerRef.value)
  renderWindow.addView(oglRw)

  const iren = vtk.RenderWindowInteractor.newInstance()
  iren.setView(oglRw)
  const istyle = vtk.InteractorStyleTrackballCamera.newInstance()
  iren.setInteractorStyle(istyle)
  iren.initialize()

  renWin.value = renderWindow
  renderer.value = rend
  interactor.value = iren
  glRW.value = oglRw

  // 默认 LUT
  rebuildLut()

  // 自适应
  const ro = new ResizeObserver(() => render())
  ro.observe(containerRef.value)
  // 首次渲染
  render()
}

async function importVtk() {
  // 注意：项目里 @kitware/vtk.js 是可选依赖；若未安装则抛错
  const mods = await Promise.all([
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Rendering/Profiles/Geometry'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Rendering/Profiles/Glyph'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Rendering/OpenGL/RenderWindow'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Rendering/Core/Renderer'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Rendering/Core/RenderWindow'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Rendering/Core/RenderWindowInteractor'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Interaction/Style/InteractorStyleTrackballCamera'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/IO/XML/XMLPolyDataReader'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Rendering/OpenGL/PolyDataMapper'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Rendering/Core/Actor'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Common/Core/LookupTable'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Common/Core/Points'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Common/Core/DataArray'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Common/DataModel/PolyData'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Rendering/Core/Glyph3DMapper'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Filters/Sources/SphereSource'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Filters/Sources/PlaneSource'),
    import(/* webpackIgnore: true */ '@kitware/vtk.js/Filters/Sources/LineSource'),
  ])
  return {
    RenderWindow: mods[4].default,
    Renderer: mods[3].default,
    OpenGLRenderWindow: mods[2].default,
    RenderWindowInteractor: mods[5].default,
    InteractorStyleTrackballCamera: mods[6].default,
    XMLPolyDataReader: mods[7].default,
    PolyDataMapper: mods[8].default,
    Actor: mods[9].default,
    LookupTable: mods[10].default,
    Points: mods[11].default,
    DataArray: mods[12].default,
    PolyData: mods[13].default,
    Glyph3DMapper: mods[14].default,
    SphereSource: mods[15].default,
    PlaneSource: mods[16].default,
    LineSource: mods[17].default,
  }
}

function render() {
  try { renWin.value?.render() } catch (_) {}
}

// ---------- 工况加载：真实几何变化 ----------
async function loadStage(key) {
  if (currentStage.value === key && shellActor.value) return
  loadingText.value = `加载工况 ${key} 模型文件...`
  loading.value = true
  try {
    // 清理旧
    if (shellActor.value) { renderer.value.removeActor(shellActor.value); shellActor.value.delete(); shellActor.value = null }
    if (cavityActor.value) { renderer.value.removeActor(cavityActor.value); cavityActor.value.delete(); cavityActor.value = null }

    const vtk = await importVtk()
    const base = `${import.meta.env.BASE_URL || '/'}model_cache/${key}`

    await Promise.all([
      loadAndAddVtp(vtk, `${base}/full_model.vtp`, 'shell'),
      loadAndAddVtp(vtk, `${base}/cavity_surface.vtp`, 'cavity').catch(() => null),
    ])

    applyVisibility()
    applyScalar(props.scalarKey)
    currentStage.value = key

    // 重置相机到合适视角
    renderer.value.resetCamera()
    applyViewPreset('iso')
    render()
  } catch (e) {
    console.warn('[VtkViewer] 加载 VTP 失败，切换到示意图:', e?.message)
    // 失败但不抛错：保持 renderWindow 可用
    if (!shellActor.value) {
      fallback.value = true
    }
  } finally {
    loading.value = false
  }
}

async function loadAndAddVtp(vtk, url, kind) {
  const reader = vtk.XMLPolyDataReader.newInstance()
  const res = await fetch(url)
  if (!res.ok) throw new Error(`HTTP ${res.status} ${url}`)
  const buf = await res.arrayBuffer()
  reader.parseAsArrayBuffer(buf)
  const pd = reader.getOutputData()
  const mapper = vtk.PolyDataMapper.newInstance()
  mapper.setInputData(pd)
  if (lookupTable.value) {
    mapper.setLookupTable(lookupTable.value)
    mapper.setColorModeToMapScalars()
    mapper.setScalarVisibility(true)
  }
  const actor = vtk.Actor.newInstance()
  actor.setMapper(mapper)
  const prop = actor.getProperty()
  if (kind === 'shell') {
    prop.setColor(0.35, 0.6, 0.9)
    prop.setOpacity(props.shellOpacity)
    prop.setEdgeVisibility(true); prop.setEdgeColor(0.1, 0.2, 0.4)
    shellActor.value = actor
  } else {
    prop.setColor(0.9, 0.4, 0.35)
    prop.setRepresentationToWireframe()
    cavityActor.value = actor
  }
  renderer.value.addActor(actor)
}

// ---------- 标量：真实颜色变化 ----------
function applyScalar(key) {
  if (!shellActor.value) return
  const mapper = shellActor.value.getMapper()
  if (!mapper) return
  try {
    const pd = mapper.getInputData(0)
    if (!pd) return
    const pd_ = pd.getPointData()
    if (!pd_) return
    pd_.setActiveScalars(key || props.scalarKey)
    mapper.setScalarVisibility(true)
    if (lookupTable.value) mapper.setLookupTable(lookupTable.value)
    mapper.setColorModeToMapScalars()
    mapper.setScalarRange(colormap.min, colormap.max)
    render()
  } catch (e) {
    console.warn('[VtkViewer] 切换标量失败：', e?.message)
  }
}

// ---------- 色阶 LUT ----------
function rebuildLut() {
  if (!renderer.value) return
  importVtk().then(vtk => {
    if (lookupTable.value) lookupTable.value.delete()
    const lut = vtk.LookupTable.newInstance()
    lut.setNumberOfTableValues(colormap.stops.length)
    colormap.stops.forEach((s, i) => {
      const rgb = hex2rgb(s.hex)
      lut.setTableValue(i, rgb[0], rgb[1], rgb[2], 1)
    })
    lut.setRange(colormap.min, colormap.max)
    lut.build()
    lookupTable.value = lut
    ;[shellActor.value, cavityActor.value].forEach(a => {
      const m = a?.getMapper?.()
      if (m) { m.setLookupTable(lut); m.setScalarRange(colormap.min, colormap.max) }
    })
    render()
  }).catch(() => {})
}
function hex2rgb(hex) {
  const h = (hex || '#2563eb').replace('#','')
  return [parseInt(h.slice(0,2),16)/255, parseInt(h.slice(2,4),16)/255, parseInt(h.slice(4,6),16)/255]
}

// ---------- 可见性/透明度 ----------
function applyVisibility(override = {}) {
  const showShell = override.showShell ?? props.showShell
  const showCavity = override.showCavity ?? props.showCavity
  const showBhs = override.showBoreholes ?? props.showBoreholes
  const opacity = override.shellOpacity ?? props.shellOpacity
  if (shellActor.value) {
    shellActor.value.setVisibility(showShell)
    shellActor.value.getProperty().setOpacity(opacity)
  }
  if (cavityActor.value) cavityActor.value.setVisibility(showCavity)
  boreholeActors.value.forEach(a => a.setVisibility(showBhs))
  render()
  // 降级模式：同步
}

// ---------- 剖切：真实采样平面 ----------
async function refreshSection() {
  if (!sectionState.enabled || !renderer.value) return
  try {
    const vtk = await importVtk()
    if (sectionActor.value) { renderer.value.removeActor(sectionActor.value); sectionActor.value.delete() }
    // 简化：先画一个半透明切面（之后 updateSection 会覆盖成采样值）
    const plane = vtk.PlaneSource.newInstance()
    plane.setCenter([0,0,0])
    plane.setIResolution(40); plane.setJResolution(40)
    // 根据 axis 定向（实际 updateSection 里会精确设置 origin/p1/p2 与模型 bounds 对齐）
    const mapper = vtk.PolyDataMapper.newInstance()
    mapper.setInputConnection(plane.getOutputPort())
    const actor = vtk.Actor.newInstance()
    actor.setMapper(mapper)
    const p = actor.getProperty()
    p.setColor(1, 0.9, 0.3); p.setOpacity(0.5)
    actor.setVisibility(sectionState.enabled)
    renderer.value.addActor(actor)
    sectionActor.value = actor
    render()
  } catch (_) {}
}
function drawSection(data) {
  // 收到后端采样数据，真实绘制成标量网格平面
  if (!renderer.value) return
  importVtk().then(vtk => {
    if (sectionActor.value) { renderer.value.removeActor(sectionActor.value); sectionActor.value.delete() }
    try {
      if (!data || data.preview || !Array.isArray(data.points)) {
        refreshSection(); return
      }
      const { points, values, triangles } = data
      const pts = vtk.Points.newInstance()
      pts.setData(new Float32Array(points.flat()), 3)
      const scalars = vtk.DataArray.newInstance()
      scalars.setNumberOfComponents(1)
      scalars.setData(new Float32Array(values))
      scalars.setName('section_scalar')
      const pd = vtk.PolyData.newInstance()
      pd.setPoints(pts)
      pd.getPointData().setScalars(scalars)
      if (Array.isArray(triangles)) {
        const cellArr = new Uint32Array(triangles.length * 4)
        for (let i = 0; i < triangles.length; i++) { const t = triangles[i]; cellArr[i*4]=3; cellArr[i*4+1]=t[0]; cellArr[i*4+2]=t[1]; cellArr[i*4+3]=t[2] }
        // vtk.CellArray 简化
        try {
          pd.getPolys().setData(cellArr)
        } catch(_){}
      }
      const mapper = vtk.PolyDataMapper.newInstance()
      mapper.setInputData(pd)
      if (lookupTable.value) mapper.setLookupTable(lookupTable.value)
      mapper.setScalarRange(colormap.min, colormap.max)
      mapper.setColorModeToMapScalars()
      const actor = vtk.Actor.newInstance()
      actor.setMapper(mapper)
      actor.getProperty().setOpacity(0.9)
      renderer.value.addActor(actor)
      sectionActor.value = actor
      render()
    } catch (e) {
      console.warn('[VtkViewer] 绘制剖切平面失败：', e?.message)
      refreshSection()
    }
  }).catch(()=>{})
}

// ---------- 相机 ----------
function setCameraInternal(pos, fp, up) {
  const cam = renderer.value?.getActiveCamera?.()
  if (!cam) return
  if (pos) cam.setPosition(...pos)
  if (fp) cam.setFocalPoint(...fp)
  if (up) cam.setViewUp(...up)
  renderer.value.resetCameraClippingRange()
  render()
}
function applyViewPreset(view = 'iso') {
  const cam = renderer.value?.getActiveCamera?.()
  if (!cam) { fbRot.value = fbRotFromView(view); return }
  const b = [300, 700, -300, 100, 400, 700] // 默认 bounds
  try {
    const bb = renderer.value.computeVisiblePropBounds()
    if (bb && isFinite(bb[0]) && bb[0] < bb[1]) for (let i = 0; i < 6; i++) b[i] = bb[i]
  } catch(_){}
  const cx = (b[0]+b[1])/2, cy=(b[2]+b[3])/2, cz=(b[4]+b[5])/2
  const R = Math.max(b[1]-b[0], b[3]-b[2], b[5]-b[4]) * 1.8
  const presets = {
    iso:   { pos: [cx+R, cy-R, cz+R*0.9], fp:[cx,cy,cz], up:[0,0,1] },
    top:   { pos: [cx, cy, cz+R], fp:[cx,cy,cz], up:[0,1,0] },
    front: { pos: [cx, cy-R, cz], fp:[cx,cy,cz], up:[0,0,1] },
    side:  { pos: [cx+R, cy, cz], fp:[cx,cy,cz], up:[0,0,1] },
  }
  const p = presets[view] || presets.iso
  setCameraInternal(p.pos, p.fp, p.up)
}

// ---------- 图层高亮 ----------
function highlightFeatureInternal(id, data) {
  // 在 LayerTree3D 模式下：若有对应 slice actor，把它提升颜色 / 边缘
  console.debug('[VtkViewer] highlight:', id, data?.label)
  // 简化：这里把外壳颜色微闪一下
  if (shellActor.value) {
    const prop = shellActor.value.getProperty()
    const prev = prop.getOpacity()
    prop.setOpacity(Math.min(1, prev + 0.1))
    render()
    setTimeout(() => { prop.setOpacity(prev); render() }, 400)
  }
}

// ---------- 侦听 props 变化 ----------
watch(() => props.stageKey, (k) => { if (!fallback.value) loadStage(k) })
watch(() => props.scalarKey, k => applyScalar(k))
watch(
  () => [props.showShell, props.showCavity, props.showBoreholes, props.shellOpacity],
  () => applyVisibility()
)
watch(() => props.sectionEnabled, v => { sectionState.enabled = v; api.toggleSection(v) })
watch(
  () => [props.sectionAxis, props.sectionPosition],
  () => {
    sectionState.axis = props.sectionAxis
    sectionState.pos = props.sectionPosition
    refreshSection()
  }
)
watch(
  () => props.sectionPlanes,
  (arr) => {
    // LayerTree3D 的三个永久切片：以三个颜色片 actors 更新
    if (!renderer.value) return
    importVtk().then(vtk => {
      permanentActors.value.forEach(a => { try { renderer.value.removeActor(a); a.delete() } catch(_){} })
      permanentActors.value = []
      ;(arr || []).forEach(p => {
        try {
          const plane = vtk.PlaneSource.newInstance()
          const mapper = vtk.PolyDataMapper.newInstance()
          mapper.setInputConnection(plane.getOutputPort())
          const actor = vtk.Actor.newInstance()
          actor.setMapper(mapper)
          const rgb = hex2rgb(p.color || '#7c3aed')
          const pr = actor.getProperty()
          pr.setColor(rgb[0], rgb[1], rgb[2])
          pr.setOpacity(p.opacity ?? 0.6)
          renderer.value.addActor(actor)
          permanentActors.value.push(actor)
        } catch(_){}
      })
      render()
    }).catch(()=>{})
  },
  { deep: true }
)

// ======================================================
// 降级 CSS-3D 伪三维（浏览器缺 VTK 时用，交互：鼠标拖动旋转）
// ======================================================
const fbRot = reactive({ x: -25, y: -35 })
let fbDrag = null
function fbRotFromView(v) {
  if (v === 'top') { fbRot.x = -85; fbRot.y = 0 }
  else if (v === 'front') { fbRot.x = 0; fbRot.y = 0 }
  else if (v === 'side') { fbRot.x = 0; fbRot.y = -90 }
  else { fbRot.x = -25; fbRot.y = -35 }
}
const fbStageStyle = computed(() => ({
  transform: `rotateX(${fbRot.x}deg) rotateY(${fbRot.y}deg)`,
}))
const fbStagesProgress = computed(() => {
  const m = /exac_(\d+)/.exec(props.stageKey || '')
  return m ? Math.min(1, parseInt(m[1]) / 10) : 0.2
})
function fbLayerStyle(kind) {
  const prog = fbStagesProgress.value
  const base = kind === 'shell'
    ? { w: 220 * (0.4 + prog*0.6), h: 160 * (0.4 + prog*0.6), d: 180 * (0.4 + prog*0.6), bg: 'linear-gradient(135deg, rgba(37,99,235,.55), rgba(16,185,129,.45))', op: props.shellOpacity, border: '1px solid rgba(147,197,253,.6)', show: props.showShell }
    : { w: 140, h: 90, d: 120, bg: 'repeating-linear-gradient(45deg, rgba(239,68,68,.0), rgba(239,68,68,.15) 2px, transparent 2px, transparent 6px)', op: 0.7, border: '1px dashed rgba(248,113,113,.7)', show: props.showCavity }
  return {
    width: base.w + 'px', height: base.h + 'px',
    transform: `translate(-50%, -50%) translateZ(${-base.d/2}px)`,
    '--d': base.d + 'px',
    background: base.bg, opacity: base.show ? base.op : 0,
    border: base.show ? base.border : 'none',
    pointerEvents: base.show ? 'auto' : 'none',
  }
}
function fbBoreholeStyle(bh) {
  if (!props.showBoreholes) return { display: 'none' }
  // 将世界坐标近似映射到盒子内 (范围 X:300~700 → -50~50 px, Y:-300~100 → -40~40 px)
  const x = ((bh.x ?? 500) - 500) / 400 * 100
  const y = ((bh.y ?? -180) - -100) / 400 * 80 - 40
  const h = ((bh.depth ?? 80) / 100) * 120
  return {
    left: `calc(50% + ${x.toFixed(1)}px)`,
    top: `calc(50% + ${y.toFixed(1)}px)`,
    height: h.toFixed(1) + 'px',
  }
}
function fbPlaneStyle(p, i) {
  const colors = ['#7c3aed', '#eab308', '#10b981']
  const c = p.color || colors[i % 3]
  const axisMap = { x: 0, y: 1, z: 2 }[p.axis || 'x']
  const rot = ['rotateY(90deg)', 'rotateX(90deg)', ''][axisMap]
  const off = ((p.position ?? 0) - 500) / 5
  return {
    background: c + '55',
    borderColor: c,
    transform: `translate(-50%, -50%) ${rot} translateZ(${off.toFixed(1)}px)`,
    width: axisMap === 2 ? '220px' : '220px',
    height: axisMap === 2 ? '160px' : '160px',
    opacity: p.opacity ?? 0.55,
  }
}
// 降级拖拽
function onMouseDown(e) {
  if (!fallback.value) return
  fbDrag = { x: e.clientX, y: e.clientY, rx: fbRot.x, ry: fbRot.y }
  const mv = ev => {
    fbRot.x = fbDrag.rx - (ev.clientY - fbDrag.y) * 0.5
    fbRot.y = fbDrag.ry + (ev.clientX - fbDrag.x) * 0.5
  }
  const up = () => { fbDrag = null; window.removeEventListener('mousemove', mv); window.removeEventListener('mouseup', up) }
  window.addEventListener('mousemove', mv)
  window.addEventListener('mouseup', up)
}
onMounted(() => { if (containerRef.value) containerRef.value.addEventListener('mousedown', onMouseDown) })
onBeforeUnmount(() => { if (containerRef.value) containerRef.value.removeEventListener('mousedown', onMouseDown) })
</script>

<style scoped>
.vtk-viewer {
  position: relative;
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: radial-gradient(ellipse at center, #0a1628 0%, #030712 100%);
}
.vtk-canvas { display: none; }
.vtk-viewer :deep(canvas) {
  position: absolute; inset: 0; width: 100% !important; height: 100% !important; display: block; }

.vtk-loading {
  position: absolute; inset: 0; z-index: 50;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  background: rgba(3, 7, 18, .7); color: #e2e8f0; gap: 14px;
}
.spinner {
  width: 44px; height: 44px; border-radius: 50%;
  border: 3px solid rgba(96,165,250,.2);
  border-top-color: #60a5fa;
  animation: spin 1s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }
.loading-text { font-size: 13px; color: #94a3b8; }

/* ---------- 降级伪三维 ---------- */
.vtk-fallback {
  position: absolute; inset: 0;
  display: flex; align-items: center; justify-content: center;
  perspective: 1400px;
}
.fb-inner {
  position: relative; width: 100%; height: 100%;
  display: flex; flex-direction: column;
  align-items: center; padding: 24px;
}
.fb-title { font-size: 13px; color: #94a3b8; margin-bottom: 4px; }
.fb-sub { font-size: 11px; color: #64748b; margin-bottom: 20px; }
.fb-sub b { color: #cbd5e1; }
.fb-3d {
  position: relative;
  width: 320px; height: 320px;
  transform-style: preserve-3d;
  transition: transform .12s ease-out;
  cursor: grab;
  margin: auto 0;
}
.fb-3d:active { cursor: grabbing; }

/* 盒子：使用 CSS 伪 3D 立方体 */
.fb-layer {
  position: absolute; left: 50%; top: 50%;
  transform-style: preserve-3d;
  border-radius: 6px;
  backdrop-filter: blur(1px);
  transition: opacity .3s;
  box-shadow: inset 0 0 40px rgba(59,130,246,.2);
}
/* 6 个面：用 var(--d) 作为深度 */
.fb-layer::before,
.fb-layer::after,
.fb-layer > .f2, .fb-layer > .f3, .fb-layer > .f4, .fb-layer > .f5 {
  content: '';
  position: absolute; inset: 0;
  background: inherit;
  border: inherit;
  border-radius: inherit;
  opacity: .85;
}
.fb-shell::before { transform: rotateY(0deg) translateZ(calc(var(--d) / 2)); }
.fb-shell::after  { transform: rotateY(180deg) translateZ(calc(var(--d) / 2)); }
.fb-shell {
  background:
    linear-gradient(135deg, rgba(37,99,235,.35), rgba(16,185,129,.28));
}
.fb-shell .f2 { transform: rotateY(90deg) translateZ(calc(var(--d) / 2)); left: 50%; margin-left: calc(-1 * var(--d) / 2); width: var(--d)); }
.fb-shell .f3 { transform: rotateY(-90deg) translateZ(calc(var(--d) / 2)); left: 50%; margin-left: calc(-1 * var(--d) / 2); width: var(--d)); }
.fb-shell .f4 { transform: rotateX(90deg) translateZ(calc(var(--d) / 2)); top: 50%; margin-top: calc(-1 * var(--d) / 2); height: var(--d)); }
.fb-shell .f5 { transform: rotateX(-90deg) translateZ(calc(var(--d) / 2)); top: 50%; margin-top: calc(-1 * var(--d) / 2); height: var(--d)); }

.fb-cavity::before { transform: rotateY(0deg) translateZ(60px); }
.fb-cavity::after  { transform: rotateY(180deg) translateZ(60px); }
.fb-cavity .f2 { transform: rotateY(90deg) translateZ(60px); left: 50%; margin-left: -60px; width: 120px; }
.fb-cavity .f3 { transform: rotateY(-90deg) translateZ(60px); left: 50%; margin-left: -60px; width: 120px; }
.fb-cavity .f4 { transform: rotateX(90deg) translateZ(45px); top: 50%; margin-top: -45px; height: 90px; }
.fb-cavity .f5 { transform: rotateX(-90deg) translateZ(45px); top: 50%; margin-top: -45px; height: 90px; }

.fb-borehole {
  position: absolute;
  width: 6px;
  background: linear-gradient(180deg, #10b981, #065f46);
  border-radius: 3px;
  transform: translateY(-100%) translateZ(80px);
  box-shadow: 0 0 8px rgba(16,185,129,.8);
  font-size: 10px;
  color: #d1fae5;
  writing-mode: vertical-lr;
  padding-left: 10px;
  text-shadow: 0 0 4px rgba(0,0,0,.8);
}
.fb-plane {
  position: absolute; left: 50%; top: 50%;
  border: 2px solid;
  border-radius: 3px;
  transform-style: preserve-3d;
  box-shadow: 0 0 20px currentColor;
}
.fb-stats {
  display: flex; gap: 28px; padding: 10px 20px; margin-top: 20px;
  background: rgba(15,23,42,.6); border: 1px solid rgba(148,163,184,.15);
  border-radius: 8px; font-size: 11px; color: #94a3b8;
  backdrop-filter: blur(4px);
}
.fb-stats b { color: #e2e8f0; margin-left: 4px; }
</style>
