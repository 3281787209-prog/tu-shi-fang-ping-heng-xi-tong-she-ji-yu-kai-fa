<template>
  <div class="login-page">
    <div class="login-bg">
      <div class="bg-grid"></div>
      <div class="bg-orbs orb-1"></div>
      <div class="bg-orbs orb-2"></div>
      <div class="bg-orbs orb-3"></div>
    </div>
    <div class="login-box">
      <div class="login-header">
        <div class="logo">
          <el-icon :size="36" color="#3b82f6"><Compass /></el-icon>
        </div>
        <h1 class="title">土石方平衡协同系统</h1>
        <p class="subtitle">古贤黄河水利枢纽 · 坝肩左岸边坡开挖工程数字化平台</p>
      </div>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        size="large"
        @keyup.enter="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :prefix-icon="User" placeholder="admin / manager / engineer / user01" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password :prefix-icon="Lock" placeholder="对应密码见下方说明" />
        </el-form-item>
        <el-button type="primary" class="w-full" :loading="loading" @click="handleLogin">
          <el-icon><Right /></el-icon> &nbsp; 登录系统
        </el-button>
      </el-form>
      <div class="account-tips">
        <h4>测试账号</h4>
        <ul>
          <li><b>admin</b> / admin123 <span class="tag tag-info">超级管理员</span></li>
          <li><b>manager</b> / manager123 <span class="tag tag-warning">项目经理</span></li>
          <li><b>engineer</b> / engineer123 <span class="tag tag-success">技术工程师</span></li>
          <li><b>user01</b> / user123 <span class="tag">普通用户</span></li>
        </ul>
      </div>
      <div class="footer-tip">
        © 2024 土石方平衡数字化协同平台 · 前端 Vue3 + 后端 FastAPI
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Right, Compass } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const store = useUserStore()
const formRef = ref()
const loading = ref(false)
const form = reactive({ username: 'admin', password: 'admin123' })
const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
async function handleLogin() {
  await formRef.value?.validate()
  loading.value = true
  try {
    await store.login(form.username, form.password)
    ElMessage.success('登录成功，正在进入系统...')
    router.push(route.query.redirect || '/dashboard')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  position: relative;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  background: linear-gradient(135deg, #0f172a 0%, #1e3a8a 50%, #0c4a6e 100%);
}
.login-bg { position: absolute; inset: 0; overflow: hidden; }
.bg-grid {
  position: absolute; inset: 0;
  background-image:
    linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px);
  background-size: 40px 40px;
}
.bg-orbs { position: absolute; border-radius: 50%; filter: blur(60px); opacity: 0.45; }
.orb-1 { width: 480px; height: 480px; background: #3b82f6; top: -120px; left: -120px; }
.orb-2 { width: 520px; height: 520px; background: #06b6d4; bottom: -160px; right: -120px; }
.orb-3 { width: 320px; height: 320px; background: #8b5cf6; top: 40%; left: 55%; }
.login-box {
  position: relative; z-index: 1;
  width: 420px;
  padding: 36px 36px 20px;
  background: rgba(255,255,255,0.96);
  backdrop-filter: blur(16px);
  border-radius: 14px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.25);
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
}
.login-header { text-align: center; margin-bottom: 24px; }
.logo {
  width: 64px; height: 64px; border-radius: 14px;
  background: linear-gradient(135deg, #dbeafe, #bfdbfe);
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 14px;
}
.title { font-size: 22px; font-weight: 700; color: #0f172a; margin: 0 0 6px; }
.subtitle { font-size: 13px; color: #64748b; margin: 0; }
.w-full { width: 100%; margin-top: 8px; height: 44px; font-size: 15px; }
.account-tips {
  margin-top: 20px;
  padding: 12px 14px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 12.5px;
}
.account-tips h4 { margin: 0 0 8px; color: #334155; font-size: 13px; }
.account-tips ul { margin: 0; padding: 0; list-style: none; }
.account-tips li { padding: 2px 0; color: #475569; display: flex; align-items: center; gap: 8px; }
.tag { padding: 0 6px; border-radius: 4px; font-size: 11px; background: #f1f5f9; color: #475569; }
.tag-info { background: #dbeafe; color: #1d4ed8; }
.tag-warning { background: #fef3c7; color: #b45309; }
.tag-success { background: #d1fae5; color: #047857; }
.footer-tip {
  margin-top: 18px;
  text-align: center;
  font-size: 11.5px;
  color: #94a3b8;
}
</style>
