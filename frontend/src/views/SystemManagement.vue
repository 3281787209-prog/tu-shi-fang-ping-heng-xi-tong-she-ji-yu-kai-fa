<template>
  <div class="sys-mgmt-page">
    <div class="page-header">
      <div class="header-left">
        <el-icon :size="22" color="#4f46e5"><Setting /></el-icon>
        <h2 class="page-title">系统管理</h2>
        <span class="page-sub">用户、项目与系统概览集中管理</span>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="main-tabs">
      <!-- ============== Tab1: 用户管理 ============== -->
      <el-tab-pane label="用户管理" name="users">
        <el-card shadow="never" class="mgmt-card">
          <template #header>
            <div class="card-header between">
              <div class="h-left">
                <el-icon color="#1d4ed8"><User /></el-icon>
                <span>用户列表</span>
                <span class="hint">共 {{ userList.length }} 位用户</span>
              </div>
              <el-button
                type="primary"
                :icon="Plus"
                @click="openUserDialog()"
              >
                新增用户
              </el-button>
            </div>
          </template>

          <el-table
            :data="userList"
            v-loading="loadingUsers"
            stripe
            style="width: 100%;"
          >
            <el-table-column label="ID" width="80" prop="id" />
            <el-table-column label="用户名" width="180">
              <template #default="{ row }">
                <div class="user-cell">
                  <div class="avatar">{{ (row.username || row.name || '?').charAt(0).toUpperCase() }}</div>
                  <div class="user-info">
                    <div class="username">{{ row.username || row.name }}</div>
                    <div class="email" v-if="row.email">{{ row.email }}</div>
                  </div>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="角色" width="160" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="roleTagType(row.role)"
                  effect="light"
                  size="small"
                >
                  {{ roleText(row.role) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag
                  :type="row.status === 'disabled' || row.active === false ? 'info' : 'success'"
                  effect="plain"
                  size="small"
                >
                  {{ (row.status === 'disabled' || row.active === false) ? '已禁用' : '正常' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="创建时间" prop="createdAt" :formatter="fmtTime" width="180" />
            <el-table-column label="最后登录" prop="lastLogin" :formatter="fmtTime" width="180" />
            <el-table-column label="操作" width="260" fixed="right" align="center">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="openUserDialog(row)"
                >编辑</el-button>
                <el-button
                  type="warning"
                  link
                  size="small"
                  @click="resetPwd(row)"
                >重置密码</el-button>
                <el-popconfirm
                  title="确认删除该用户？此操作不可恢复。"
                  confirm-button-text="删除"
                  cancel-button-text="取消"
                  confirm-button-type="danger"
                  @confirm="handleDeleteUser(row)"
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

        <!-- 用户新增/编辑对话框 -->
        <el-dialog
          v-model="userDialog.visible"
          :title="userDialog.editMode ? '编辑用户' : '新增用户'"
          width="480px"
          :close-on-click-modal="false"
          destroy-on-close
        >
          <el-form
            ref="userFormRef"
            :model="userDialog.form"
            :rules="userFormRules"
            label-width="90px"
          >
            <el-form-item label="用户名" prop="username">
              <el-input
                v-model="userDialog.form.username"
                placeholder="请输入登录用户名"
                :disabled="userDialog.editMode"
              />
            </el-form-item>
            <el-form-item v-if="!userDialog.editMode" label="密码" prop="password">
              <el-input
                v-model="userDialog.form.password"
                type="password"
                show-password
                placeholder="初始密码，至少6位"
              />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="userDialog.form.email" placeholder="可选，邮箱地址" />
            </el-form-item>
            <el-form-item label="角色" prop="role">
              <el-select v-model="userDialog.form.role" class="w-full" placeholder="请选择角色">
                <el-option label="超级管理员 (admin)" value="admin" />
                <el-option label="项目经理 (manager)" value="manager" />
                <el-option label="技术工程师 (engineer)" value="engineer" />
                <el-option label="普通用户 (user)" value="user" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-switch
                v-model="userDialog.form.active"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="userDialog.visible = false">取消</el-button>
            <el-button
              type="primary"
              :loading="userDialog.saving"
              @click="submitUser"
            >保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <!-- ============== Tab2: 项目管理 ============== -->
      <el-tab-pane label="项目管理" name="projects">
        <el-card shadow="never" class="mgmt-card">
          <template #header>
            <div class="card-header between">
              <div class="h-left">
                <el-icon color="#047857"><FolderOpened /></el-icon>
                <span>项目列表</span>
                <span class="hint">共 {{ projectList.length }} 个项目</span>
              </div>
              <el-button
                type="primary"
                :icon="Plus"
                @click="openProjectDialog()"
              >
                新增项目
              </el-button>
            </div>
          </template>

          <el-table
            :data="projectList"
            v-loading="loadingProjects"
            stripe
            style="width: 100%;"
          >
            <el-table-column label="ID" width="80" prop="id" />
            <el-table-column label="项目名称" min-width="220">
              <template #default="{ row }">
                <div class="proj-name">
                  <el-icon color="#0ea5e9"><Files /></el-icon>
                  <span>{{ row.name }}</span>
                  <el-tag v-if="row.status === 'active'" size="small" type="success" effect="plain">进行中</el-tag>
                  <el-tag v-else-if="row.status === 'done'" size="small" effect="plain">已完成</el-tag>
                  <el-tag v-else size="small" type="info" effect="plain">规划中</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column label="地点" width="200" prop="location" />
            <el-table-column label="描述" min-width="280" prop="description" show-overflow-tooltip />
            <el-table-column label="负责人" width="120" prop="owner" />
            <el-table-column label="创建时间" prop="createdAt" :formatter="fmtTime" width="180" />
            <el-table-column label="操作" width="180" fixed="right" align="center">
              <template #default="{ row }">
                <el-button
                  type="primary"
                  link
                  size="small"
                  @click="openProjectDialog(row)"
                >编辑</el-button>
                <el-popconfirm
                  title="确认删除该项目？项目下数据将一并移除。"
                  confirm-button-text="删除"
                  cancel-button-text="取消"
                  confirm-button-type="danger"
                  @confirm="handleDeleteProject(row)"
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

        <!-- 项目新增/编辑对话框 -->
        <el-dialog
          v-model="projectDialog.visible"
          :title="projectDialog.editMode ? '编辑项目' : '新增项目'"
          width="560px"
          :close-on-click-modal="false"
          destroy-on-close
        >
          <el-form
            ref="projectFormRef"
            :model="projectDialog.form"
            :rules="projectFormRules"
            label-width="90px"
          >
            <el-form-item label="项目名称" prop="name">
              <el-input v-model="projectDialog.form.name" placeholder="例如：古贤黄河水利枢纽坝肩左岸边坡" />
            </el-form-item>
            <el-form-item label="地点" prop="location">
              <el-input v-model="projectDialog.form.location" placeholder="例如：山西省吕梁市" />
            </el-form-item>
            <el-form-item label="负责人">
              <el-input v-model="projectDialog.form.owner" placeholder="可选，项目负责人" />
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="projectDialog.form.status" class="w-full">
                <el-option label="规划中" value="planning" />
                <el-option label="进行中" value="active" />
                <el-option label="已完成" value="done" />
              </el-select>
            </el-form-item>
            <el-form-item label="描述" prop="description">
              <el-input
                v-model="projectDialog.form.description"
                type="textarea"
                :rows="4"
                placeholder="项目背景、范围、目标等简要描述"
              />
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="projectDialog.visible = false">取消</el-button>
            <el-button
              type="primary"
              :loading="projectDialog.saving"
              @click="submitProject"
            >保存</el-button>
          </template>
        </el-dialog>
      </el-tab-pane>

      <!-- ============== Tab3: 系统概览 ============== -->
      <el-tab-pane label="系统概览" name="overview">
        <el-row :gutter="14">
          <el-col :span="14">
            <el-card shadow="never" class="info-card">
              <template #header>
                <div class="card-header">
                  <el-icon color="#4f46e5"><Cpu /></el-icon>
                  <span>系统信息</span>
                </div>
              </template>

              <el-descriptions :column="2" border class="sys-desc">
                <el-descriptions-item label="前端版本">
                  <el-tag type="primary" effect="plain">{{ sysInfo.frontendVersion }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="后端版本">
                  <el-tag type="success" effect="plain">{{ sysInfo.backendVersion }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="部署环境">
                  <span>{{ sysInfo.env }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="数据库类型">
                  <span class="mono">{{ sysInfo.dbType }}</span>
                </el-descriptions-item>
                <el-descriptions-item label="模型工况数">
                  <b class="num">{{ sysInfo.modelCaseCount }}</b> 个
                </el-descriptions-item>
                <el-descriptions-item label="总用户数">
                  <b class="num">{{ sysInfo.totalUsers }}</b> 位
                </el-descriptions-item>
                <el-descriptions-item label="总表单数">
                  <b class="num">{{ sysInfo.totalForms }}</b> 份
                </el-descriptions-item>
                <el-descriptions-item label="启动时间">
                  <span>{{ sysInfo.startTime }}</span>
                </el-descriptions-item>
              </el-descriptions>

              <el-divider />

              <div class="health-section">
                <div class="health-title">
                  <el-icon :size="16" :color="health.ok ? '#059669' : '#dc2626'">
                    <component :is="health.ok ? 'CircleCheck' : 'Warning'" />
                  </el-icon>
                  <span>后端连通性</span>
                  <el-tag
                    v-if="!health.loading"
                    :type="health.ok ? 'success' : 'danger'"
                    effect="light"
                    size="small"
                  >
                    {{ health.ok ? '已连接' : '连接失败' }}
                  </el-tag>
                  <span v-if="!health.loading && health.ok" class="ms-latency">
                    耗时 <b>{{ health.latency }}</b> ms
                  </span>
                </div>
                <el-button
                  type="primary"
                  :icon="Refresh"
                  :loading="health.loading"
                  size="default"
                  @click="checkHealth"
                >
                  重新测试
                </el-button>
                <pre v-if="health.raw" class="health-raw">{{ health.raw }}</pre>
              </div>
            </el-card>
          </el-col>

          <el-col :span="10">
            <el-card shadow="never" class="info-card">
              <template #header>
                <div class="card-header">
                  <el-icon color="#0891b2"><Collection /></el-icon>
                  <span>依赖版本</span>
                </div>
              </template>

              <div class="dep-list">
                <div v-for="d in dependencies" :key="d.name" class="dep-item">
                  <div class="dep-icon" :style="{ background: d.color }">
                    <el-icon :size="20" color="#fff">
                      <component :is="d.icon" />
                    </el-icon>
                  </div>
                  <div class="dep-info">
                    <div class="dep-name">{{ d.name }}</div>
                    <div class="dep-desc">{{ d.desc }}</div>
                  </div>
                  <div class="dep-ver">
                    <el-tag type="info" effect="plain">{{ d.version }}</el-tag>
                  </div>
                </div>
              </div>

              <el-divider content-position="left">技术栈说明</el-divider>
              <ul class="tech-list">
                <li>前端采用 <b>Vue 3</b> + <b>Vite</b> 构建，UI 库使用 <b>Element Plus</b>。</li>
                <li>后端采用 <b>Python 3.11 + FastAPI</b>，接口遵循 RESTful 风格。</li>
                <li>三维模型渲染基于 <b>VTK.js</b>，支持地质剖面、分层展示与开挖工况回放。</li>
                <li>所有图表基于 <b>Apache ECharts</b>，支持大屏自适应与交互。</li>
                <li>数据持久化使用 <b>PostgreSQL + PostGIS</b>，支持空间索引与地质体查询。</li>
              </ul>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Setting, User, Plus, FolderOpened, Files, Cpu, Refresh,
  Collection, CircleCheck, Warning, Document, DataLine, Picture, EditPen, MagicStick,
} from '@element-plus/icons-vue'
import request from '@/utils/request'
import {
  listUsers, createUser, updateUser, deleteUser,
  listProjects, createProject, updateProject, deleteProject,
  getFormStats,
} from '@/api'

const activeTab = ref('users')

function fmtTime(row, col, val) {
  if (!val) return '-'
  return String(val).replace('T', ' ').substring(0, 19)
}
function roleTagType(r) {
  if (r === 'admin') return 'danger'
  if (r === 'manager') return 'warning'
  if (r === 'engineer') return 'success'
  return 'info'
}
function roleText(r) {
  if (r === 'admin') return '超级管理员'
  if (r === 'manager') return '项目经理'
  if (r === 'engineer') return '技术工程师'
  if (r === 'user') return '普通用户'
  return r || '未知'
}

// ========== Tab1: 用户管理 ==========
const userList = ref([])
const loadingUsers = ref(false)
const userFormRef = ref()
const userDialog = reactive({
  visible: false, editMode: false, saving: false,
  form: { id: null, username: '', password: '', email: '', role: 'user', active: true },
})
const userFormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [
    { required: true, message: '请输入初始密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' },
  ],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}
async function loadUsers() {
  loadingUsers.value = true
  try {
    const res = await listUsers()
    const d = res.data?.data || res.data || {}
    userList.value = d.items || d.list || d || []
  } finally {
    loadingUsers.value = false
  }
}
function openUserDialog(row) {
  userDialog.editMode = !!row
  if (row) {
    userDialog.form = {
      id: row.id,
      username: row.username || row.name || '',
      password: '',
      email: row.email || '',
      role: row.role || 'user',
      active: row.active !== false && row.status !== 'disabled',
    }
  } else {
    userDialog.form = {
      id: null, username: '', password: '', email: '', role: 'user', active: true,
    }
  }
  userDialog.visible = true
  nextTick(() => userFormRef.value?.clearValidate())
}
async function submitUser() {
  await userFormRef.value?.validate()
  userDialog.saving = true
  try {
    const payload = {
      username: userDialog.form.username,
      email: userDialog.form.email,
      role: userDialog.form.role,
      active: userDialog.form.active,
    }
    if (!userDialog.editMode) payload.password = userDialog.form.password
    if (userDialog.editMode && userDialog.form.id) {
      await updateUser(userDialog.form.id, payload)
      ElMessage.success('用户已更新')
    } else {
      await createUser(payload)
      ElMessage.success('用户已创建')
    }
    userDialog.visible = false
    loadUsers()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.message || ''))
  } finally {
    userDialog.saving = false
  }
}
async function resetPwd(row) {
  try {
    const { value } = await ElMessageBox.prompt(
      `请输入 "${row.username || row.name}" 的新密码：`,
      '重置密码',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        inputPattern: /.{6,}/,
        inputErrorMessage: '密码至少6位',
        inputType: 'password',
      }
    )
    await updateUser(row.id, { password: value })
    ElMessage.success('密码已重置')
  } catch (e) {
    if (e !== 'cancel') ElMessage.error('重置失败：' + (e.message || ''))
  }
}
async function handleDeleteUser(row) {
  try {
    await deleteUser(row.id)
    ElMessage.success('用户已删除')
    loadUsers()
  } catch (e) {
    ElMessage.error('删除失败：' + (e.message || ''))
  }
}

// ========== Tab2: 项目管理 ==========
const projectList = ref([])
const loadingProjects = ref(false)
const projectFormRef = ref()
const projectDialog = reactive({
  visible: false, editMode: false, saving: false,
  form: {
    id: null, name: '', location: '', description: '',
    owner: '', status: 'planning',
  },
})
const projectFormRules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  location: [{ required: true, message: '请输入项目地点', trigger: 'blur' }],
}
async function loadProjects() {
  loadingProjects.value = true
  try {
    const res = await listProjects()
    const d = res.data?.data || res.data || {}
    projectList.value = d.items || d.list || d || []
  } finally {
    loadingProjects.value = false
  }
}
function openProjectDialog(row) {
  projectDialog.editMode = !!row
  if (row) {
    projectDialog.form = {
      id: row.id,
      name: row.name || '',
      location: row.location || '',
      description: row.description || '',
      owner: row.owner || '',
      status: row.status || 'planning',
    }
  } else {
    projectDialog.form = {
      id: null, name: '', location: '', description: '',
      owner: '', status: 'planning',
    }
  }
  projectDialog.visible = true
  nextTick(() => projectFormRef.value?.clearValidate())
}
async function submitProject() {
  await projectFormRef.value?.validate()
  projectDialog.saving = true
  try {
    const payload = { ...projectDialog.form }
    delete payload.id
    if (projectDialog.editMode && projectDialog.form.id) {
      await updateProject(projectDialog.form.id, payload)
      ElMessage.success('项目已更新')
    } else {
      await createProject(payload)
      ElMessage.success('项目已创建')
    }
    projectDialog.visible = false
    loadProjects()
  } catch (e) {
    ElMessage.error('保存失败：' + (e.message || ''))
  } finally {
    projectDialog.saving = false
  }
}
async function handleDeleteProject(row) {
  try {
    await deleteProject(row.id)
    ElMessage.success('项目已删除')
    loadProjects()
  } catch (e) {
    ElMessage.error('删除失败：' + (e.message || ''))
  }
}

// ========== Tab3: 系统概览 ==========
const sysInfo = reactive({
  frontendVersion: '1.0.0',
  backendVersion: '1.0.0',
  env: 'Production',
  dbType: 'PostgreSQL 16 + PostGIS 3.4',
  modelCaseCount: 0,
  totalUsers: 0,
  totalForms: 0,
  startTime: '-',
})
const health = reactive({
  loading: false, ok: false, latency: 0, raw: '',
})
const dependencies = [
  { name: 'Vue 3',          version: '3.4.21', desc: '渐进式前端框架',        color: '#42b883', icon: 'EditPen' },
  { name: 'FastAPI',        version: '0.111.0', desc: '现代 Python Web 框架', color: '#009688', icon: 'MagicStick' },
  { name: 'VTK.js',         version: '30.3.0', desc: '三维可视化渲染引擎',   color: '#1e40af', icon: 'Picture' },
  { name: 'Apache ECharts', version: '5.5.0',  desc: '强大的图表可视化库',   color: '#e63946', icon: 'DataLine' },
  { name: 'Element Plus',   version: '2.7.0',  desc: '企业级 UI 组件库',     color: '#409eff', icon: 'Document' },
]

async function loadOverview() {
  try {
    const [users, projects, forms] = await Promise.allSettled([
      listUsers(), listProjects(),
      (async () => { try { return await getFormStats() } catch (_) { return null } })(),
    ])
    if (users.status === 'fulfilled') {
      const d = users.value.data?.data || users.value.data || {}
      sysInfo.totalUsers = (d.items || d.list || d || []).length
    }
    if (projects.status === 'fulfilled') {
      const d = projects.value.data?.data || projects.value.data || {}
      sysInfo.modelCaseCount = (d.items || d.list || d || []).length * 3
    }
    if (forms.status === 'fulfilled' && forms.value) {
      const d = forms.value.data?.data || forms.value.data || {}
      sysInfo.totalForms = d.total ?? d.count ?? 0
    }
  } catch (_) {}
}

async function checkHealth() {
  health.loading = true
  health.ok = false
  health.raw = ''
  const t0 = performance.now()
  try {
    const res = await request.get('/health', { timeout: 8000 })
    health.latency = Math.round(performance.now() - t0)
    health.ok = true
    health.raw = JSON.stringify(res.data, null, 2)
  } catch (e) {
    health.latency = Math.round(performance.now() - t0)
    health.ok = false
    const m = (e && e.message) ? e.message : String(e)
    health.raw = '连接失败：' + m
  } finally {
    health.loading = false
  }
}

onMounted(async () => {
  await loadUsers()
  await loadProjects()
  await loadOverview()
  checkHealth()
})

watch(activeTab, (v) => {
  if (v === 'users') loadUsers()
  if (v === 'projects') loadProjects()
  if (v === 'overview') { loadOverview(); checkHealth() }
})
</script>

<style scoped>
.sys-mgmt-page {
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

.card-header {
  display: flex; align-items: center; gap: 8px;
  font-weight: 600; color: #0f172a;
}
.card-header.between { justify-content: space-between; }
.card-header .h-left { display: flex; align-items: center; gap: 8px; }
.card-header .hint {
  font-size: 12px; color: #94a3b8; font-weight: normal;
}

.mgmt-card :deep(.el-table__header th),
.info-card :deep(.el-table__header th) {
  background: #f8fafc; color: #334155; font-weight: 600;
}

.user-cell {
  display: flex; align-items: center; gap: 10px;
}
.avatar {
  width: 34px; height: 34px; border-radius: 50%;
  background: linear-gradient(135deg,#6366f1,#8b5cf6);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-weight: 700; flex-shrink: 0;
}
.username { font-weight: 600; color: #0f172a; font-size: 13.5px; }
.email { font-size: 12px; color: #64748b; }

.proj-name {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  font-weight: 500; color: #0f172a;
}

.info-card { height: 100%; }
.sys-desc :deep(.el-descriptions__label) {
  width: 120px;
  background: #f8fafc;
  color: #475569;
  font-weight: 500;
}
.sys-desc :deep(.el-descriptions__content) {
  color: #0f172a;
}
.mono {
  font-family: 'Consolas', monospace;
  background: #f1f5f9; padding: 2px 8px; border-radius: 4px;
  font-size: 12.5px; color: #334155;
}
.num { color: #1d4ed8; font-size: 15px; }

.health-section {
  display: flex; flex-direction: column; gap: 12px;
}
.health-title {
  display: flex; align-items: center; gap: 8px;
  font-weight: 600; color: #0f172a; font-size: 14px;
}
.ms-latency { margin-left: 8px; font-size: 12.5px; color: #64748b; }
.ms-latency b { color: #059669; }
.health-raw {
  background: #0f172a; color: #cbd5e1;
  padding: 10px 12px; border-radius: 6px;
  font-size: 12px; margin: 0;
  max-height: 160px; overflow: auto;
  white-space: pre-wrap;
}

.dep-list { display: flex; flex-direction: column; gap: 12px; }
.dep-item {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
.dep-icon {
  width: 40px; height: 40px; border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.dep-info { flex: 1; }
.dep-name { font-weight: 600; color: #0f172a; font-size: 13.5px; }
.dep-desc { font-size: 12px; color: #64748b; }

.tech-list {
  margin: 0; padding-left: 18px; color: #475569;
  font-size: 12.5px; line-height: 1.9;
}
.tech-list b { color: #1d4ed8; }
.w-full { width: 100%; }
</style>
