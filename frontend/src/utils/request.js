import axios from 'axios'
import { ElMessage } from 'element-plus'

const baseURL = import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_BASE || '/api'

/**
 * 静态演示模式开关：
 *   1. 环境变量 VITE_DEMO_MODE=true 强制开启
 *   2. URL 带 ?demo=true 开启
 *   3. 后端首次请求失败（非 401/403）后自动切换
 * 开启后所有 API 回退到 public/api-mock/*.json，保证 GitHub Pages 纯静态部署也能体验全功能
 */
let DEMO_MODE = Boolean(import.meta.env.VITE_DEMO_MODE)
if (typeof location !== 'undefined' && location.search.includes('demo=true')) DEMO_MODE = true

// 静态资源基础路径（支持 GitHub Pages 子路径部署）
// import.meta.env.BASE_URL 在 vite.config.js 的 base 配置生效时自动为 /<repo>/
const ASSETS_BASE = (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.BASE_URL)
  ? import.meta.env.BASE_URL.replace(/\/$/, '')
  : ''

/**
 * 把 API 相对路径映射为 mock JSON 文件名
 * 规则与 public/api-mock/ 下生成的文件名一致
 */
function apiToMockFile(apiPath, method = 'GET', params = null, data = null) {
  // 去掉开头的 /api/ 或 /api
  let p = String(apiPath || '').replace(/^\/api\/?/, '')
  // query 参数附加（已通过 URL 传入的 params 已在 path 里？这里兼容 request.js 调用时 config.params）
  if (params && typeof params === 'object' && Object.keys(params).length) {
    const qs = new URLSearchParams()
    for (const [k, v] of Object.entries(params)) {
      if (v !== undefined && v !== null && v !== '') qs.append(k, v)
    }
    const s = qs.toString()
    if (s) p += (p.includes('?') ? '&' : '?') + s
  }
  // method 后缀：POST 用 :POST，GET 省略（和 Python 脚本生成 mock 时一致）
  const m = (method || 'GET').toUpperCase()
  if (m !== 'GET') p += ':' + m
  // 文件名安全化：/ -> __  ? -> _Q_  = -> _  & -> _  : -> _M_
  const safe = p
    .replace(/\//g, '__')
    .replace(/\?/g, '_Q_')
    .replace(/=/g, '_')
    .replace(/&/g, '_')
    .replace(/:/g, '_M_')
  return (ASSETS_BASE || '.') + '/api-mock/' + (safe || 'index') + '.json'
}

/**
 * 用 fetch 读取 mock JSON 文件（不依赖 axios，避免 404 走统一拦截）
 */
async function fetchMock(url) {
  const r = await fetch(url, { cache: 'no-cache' })
  if (!r.ok) throw new Error('MOCK_NOT_FOUND:' + url)
  return await r.json()
}

const request = axios.create({
  baseURL,
  timeout: 30000,
})

// 请求拦截：Token + demo 模式特殊处理（记录原 method/config 供 mock 使用）
request.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers = config.headers || {}
    config.headers.Authorization = `Bearer ${token}`
  }
  // demo 模式登录：直接生成本地假 token，不走后端
  if (DEMO_MODE) {
    const isLogin = /auth\/login[^a-zA-Z0-9_]?$/.test(config.url || '') && (config.method || '').toUpperCase() === 'POST'
    if (isLogin) {
      config.__DEMO_LOGIN__ = true
    }
  }
  return config
})

// 响应拦截：成功取 data / 失败走 mock 回退 / 401 处理
request.interceptors.response.use(
  (resp) => resp.data,
  async (err) => {
    const config = err.config || {}
    const status = err?.response?.status
    const respData = err?.response?.data

    // Demo 模式登录：直接返回假 token
    if (config.__DEMO_LOGIN__) {
      const payload = {
        access_token: 'DEMO_STATIC_TOKEN_FOR_GITHUB_PAGES',
        token_type: 'bearer',
        user: { username: 'admin', role: 'admin', name: '演示账号（静态模式）' },
      }
      localStorage.setItem('token', payload.access_token)
      localStorage.setItem('user', JSON.stringify(payload.user))
      return payload
    }

    // 401：清 token，跳登录
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (typeof location !== 'undefined' && location.hash !== '#/login') {
        if (!DEMO_MODE) ElMessage.error('登录已过期，请重新登录')
        location.hash = '#/login'
      }
      return Promise.reject(err)
    }

    // Demo 模式或已判定离线：自动 fallback 到 mock JSON
    const method = (config.method || 'GET').toUpperCase()
    const isWritable = ['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)
    const canFallback = DEMO_MODE ||
      !status ||
      status >= 500 ||
      (status === 404 && !isWritable) ||
      /network error|timeout|failed to fetch|Connection refused/i.test(err.message || '')

    if (canFallback) {
      try {
        const mockUrl = apiToMockFile(config.url, method, config.params, config.data)
        const mock = await fetchMock(mockUrl)
        // 对于写操作：返回 check-all 这类已经写好的模拟响应；其他写操作提示演示模式
        if (isWritable && !config.url?.includes('check-all') && !config.url?.includes('login')) {
          ElMessage && ElMessage.warning && ElMessage.warning('演示模式：本次操作未保存到服务器，刷新后恢复原样')
        }
        return mock
      } catch (fallbackErr) {
        // mock 也找不到：非 demo 模式开启 demo 模式再试
        if (!DEMO_MODE) {
          DEMO_MODE = true
          try {
            const mockUrl2 = apiToMockFile(config.url, method, config.params, config.data)
            const mock2 = await fetchMock(mockUrl2)
            ElMessage && ElMessage.info && ElMessage.info('当前为离线演示模式（后端不可达），已切换到内置种子数据')
            return mock2
          } catch (_) { /* ignore */ }
        }
      }
    }

    // 正常错误提示
    const msg = (respData && (respData.detail || respData.message)) || err.message || '请求失败'
    if (status === 403) {
      ElMessage.error('权限不足：' + msg)
    } else if (status && status >= 400) {
      ElMessage.error(msg)
    } else if (!DEMO_MODE) {
      // 纯网络错误：提示并切换演示模式（下一次请求生效）
      ElMessage.warning('后端不可达，已切换到离线演示模式')
      DEMO_MODE = true
    }
    return Promise.reject(err)
  },
)

export default request
export { DEMO_MODE, ASSETS_BASE, apiToMockFile }
