<template>
  <el-container class="layout-root">
    <!-- 侧边栏 -->
    <el-aside :width="collapsed ? '64px' : '220px'" class="aside">
      <div class="aside-inner">
        <div class="logo-bar">
          <div class="logo-icon">
            <el-icon :size="22"><Grid /></el-icon>
          </div>
          <transition name="fade">
            <div v-if="!collapsed" class="logo-text">
              <div class="title">土石方协同</div>
              <div class="sub">Earthwork Balance</div>
            </div>
          </transition>
        </div>
        <el-menu
          :default-active="route.path"
          router
          :collapse="collapsed"
          :collapse-transition="false"
          class="side-menu"
          background-color="transparent"
          text-color="#cbd5e1"
          active-text-color="#60a5fa"
        >
          <template v-for="item in menus" :key="item.path">
            <el-menu-item
              v-if="!item.role || userStore.hasRole(...item.role)"
              :index="item.path"
            >
              <el-icon><component :is="item.icon" /></el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
          </template>
        </el-menu>
      </div>
      <div class="aside-footer" @click="collapsed = !collapsed" :title="collapsed ? '展开' : '收起'">
        <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
      </div>
    </el-aside>

    <!-- 主区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item :to="{ path: '/dashboard' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tooltip content="待办审批">
            <el-badge :value="pendingCount" :hidden="pendingCount === 0" class="header-btn" @click="$router.push('/forms?tab=pending')">
              <el-icon :size="18"><DocumentChecked /></el-icon>
            </el-badge>
          </el-tooltip>
          <el-tooltip content="安全告警">
            <el-badge :value="alertCount" :hidden="alertCount === 0" class="header-btn" type="danger" @click="$router.push('/alerts')">
              <el-icon :size="18"><Warning /></el-icon>
            </el-badge>
          </el-tooltip>
          <el-dropdown trigger="click" @command="handleUserCmd">
            <div class="user-chip">
              <el-avatar :size="30" :style="{background: avatarBg}">
                {{ (userStore.username || 'U').slice(0,1).toUpperCase() }}
              </el-avatar>
              <span class="uname">{{ userStore.username }}</span>
              <el-tag size="small" effect="plain" :type="roleTagType">{{ roleLabel }}</el-tag>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile"><el-icon><User /></el-icon>个人信息</el-dropdown-item>
                <el-dropdown-item command="logout" divided><el-icon><SwitchButton /></el-icon>退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import {
  Grid, DataAnalysis, DocumentChecked, Monitor, Cpu, Warning, Setting,
  Fold, Expand, ArrowDown, User, SwitchButton,
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import * as api from '@/api'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const collapsed = ref(false)
const pendingCount = ref(0)
const alertCount = ref(0)

const menus = [
  { path: '/dashboard', title: '业务首页', icon: 'DataAnalysis' },
  { path: '/forms', title: '表单审批', icon: 'DocumentChecked' },
  { path: '/geology', title: '地质信息', icon: 'Grid' },
  { path: '/monitoring', title: '监测信息', icon: 'Monitor' },
  { path: '/params', title: '参数繁衍', icon: 'Cpu' },
  { path: '/alerts', title: '安全预警', icon: 'Warning' },
  { path: '/control-3d', title: '3D 协同大屏', icon: 'Compass' },
  { path: '/layer-3d', title: '3D 结构图层', icon: 'Aim' },
  { path: '/system', title: '系统管理', icon: 'Setting', role: ['admin'] },
]

const all3dPaths = ['/control-3d', '/layer-3d']
const currentTitle = computed(() => {
  const m = menus.find(x => {
    if (all3dPaths.includes(x.path)) return route.path === x.path
    return route.path.startsWith(x.path)
  })
  return m?.title || ''
})
const roleMap = { admin: ['danger', '超级管理员'], manager: ['warning', '项目经理'], engineer: ['success', '技术工程师'], user: ['info', '普通用户'] }
const roleTagType = computed(() => roleMap[userStore.role]?.[0] || 'info')
const roleLabel = computed(() => roleMap[userStore.role]?.[1] || userStore.role)
const avatarBg = computed(() => ({
  admin: '#ef4444', manager: '#f59e0b', engineer: '#10b981', user: '#3b82f6',
}[userStore.role] || '#3b82f6'))

async function loadCounts() {
  try {
    const fs = await api.getFormStats()
    pendingCount.value = fs.my_pending || 0
  } catch {}
  try {
    const as = await api.getAlertStats({ days: 3 })
    alertCount.value = as.summary?.open || 0
  } catch {}
}
function handleUserCmd(c) {
  if (c === 'logout') {
    ElMessageBox.confirm('确定要退出登录吗？', '提示', { type: 'warning' }).then(() => {
      userStore.logout()
      router.push('/login')
    }).catch(() => {})
  }
}
onMounted(loadCounts)
</script>

<style scoped>
.layout-root { height: 100%; width: 100%; }
.aside {
  background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
  transition: width 0.25s;
  position: relative;
  color: #cbd5e1;
}
.aside-inner { height: calc(100% - 48px); overflow: hidden; display: flex; flex-direction: column; }
.logo-bar {
  height: 60px;
  padding: 0 16px;
  display: flex; align-items: center; gap: 10px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.logo-icon {
  width: 36px; height: 36px; border-radius: 9px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.logo-text .title { font-size: 15px; font-weight: 700; color: #fff; }
.logo-text .sub { font-size: 10.5px; color: #94a3b8; letter-spacing: 0.5px; }
.side-menu {
  flex: 1;
  border-right: none !important;
  padding: 8px 0;
}
:deep(.el-menu-item) {
  height: 44px;
  margin: 2px 8px;
  border-radius: 8px;
}
:deep(.el-menu-item.is-active) {
  background: rgba(59,130,246,0.14) !important;
}
:deep(.el-menu-item:hover) {
  background: rgba(255,255,255,0.06) !important;
}
.aside-footer {
  position: absolute; left: 0; right: 0; bottom: 0;
  height: 48px;
  border-top: 1px solid rgba(255,255,255,0.06);
  display: flex; align-items: center; justify-content: center;
  color: #94a3b8; cursor: pointer;
}
.aside-footer:hover { color: #fff; background: rgba(255,255,255,0.04); }

.header {
  height: 60px;
  background: #fff;
  border-bottom: 1px solid #e2e8f0;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 20px;
}
.header-right { display: flex; align-items: center; gap: 18px; }
.header-btn {
  width: 36px; height: 36px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer; color: #475569;
}
.header-btn:hover { background: #f1f5f9; color: #0f172a; }
.user-chip {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 10px; border-radius: 22px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  height: 40px;
}
.user-chip:hover { background: #f1f5f9; }
.uname { font-size: 14px; color: #0f172a; font-weight: 500; }

.main {
  padding: 0;
  background: #f0f2f5;
  overflow: auto;
  height: calc(100vh - 60px);
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
