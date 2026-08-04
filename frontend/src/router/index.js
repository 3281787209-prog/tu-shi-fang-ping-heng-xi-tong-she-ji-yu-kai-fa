import { createRouter, createWebHashHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const Layout = () => import('@/layouts/MainLayout.vue')
const Login = () => import('@/views/Login.vue')
const Dashboard = () => import('@/views/Dashboard.vue')
const FormApproval = () => import('@/views/FormApproval.vue')
const GeologyInfo = () => import('@/views/GeologyInfo.vue')
const MonitoringInfo = () => import('@/views/MonitoringInfo.vue')
const ParamInference = () => import('@/views/ParamInference.vue')
const SafetyAlert = () => import('@/views/SafetyAlert.vue')
const SystemManagement = () => import('@/views/SystemManagement.vue')
const ControlPanel3D = () => import('@/views/ControlPanel3D.vue')
const LayerTree3D = () => import('@/views/LayerTree3D.vue')

const routes = [
  { path: '/login', component: Login, meta: { public: true, title: '登录' } },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: Dashboard, meta: { title: '业务首页', icon: 'DataAnalysis' } },
      { path: 'forms', component: FormApproval, meta: { title: '表单审批', icon: 'DocumentChecked' } },
      { path: 'geology', component: GeologyInfo, meta: { title: '地质信息', icon: 'Grid' } },
      { path: 'monitoring', component: MonitoringInfo, meta: { title: '监测信息', icon: 'Monitor' } },
      { path: 'params', component: ParamInference, meta: { title: '参数繁衍', icon: 'Cpu' } },
      { path: 'alerts', component: SafetyAlert, meta: { title: '安全预警', icon: 'Warning' } },
      { path: 'system', component: SystemManagement, meta: { title: '系统管理', icon: 'Setting', role: ['admin'] } },
    ],
  },
  // —— 三维大屏（独立全屏视图，不嵌套在 MainLayout 内）——
  { path: '/control-3d', component: ControlPanel3D, meta: { title: '三维协同大屏' } },
  { path: '/layer-3d', component: LayerTree3D, meta: { title: '结构图层目录' } },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const store = useUserStore()
  const hasToken = store.isLoggedIn || !!localStorage.getItem('token')
  if (to.meta?.title) document.title = to.meta.title + ' - 土石方平衡协同系统'
  // 三维大屏和图层树大屏：免登录（方便演示 / 链接分享打开）
  if (to.path === '/control-3d' || to.path === '/layer-3d') return true
  if (!to.meta?.public && !hasToken) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta?.role && !store.hasRole(...to.meta.role)) {
    try { window.ElMessage?.error?.('权限不足') } catch(_){}
    return { path: '/dashboard' }
  }
  return true
})

export default router
