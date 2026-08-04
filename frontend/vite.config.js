import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'node:path'
import fs from 'node:fs'

/**
 * 自定义插件：开发时拦截 /model_cache/* 请求，直接从 public/model_cache 读文件
 * 打包后把 model_cache 目录一并拷贝进 rebuild-dist
 */
function localDataBridge() {
  return {
    name: 'local-data-bridge',
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (!req.url) return next()
        if (req.url.startsWith('/model_cache/') || req.url === '/vite.svg') {
          const root = process.cwd()
          const target = path.join(root, 'public', req.url)
          if (fs.existsSync(target) && fs.statSync(target).isFile()) {
            const ext = path.extname(target).toLowerCase()
            const mime = {
              '.json': 'application/json',
              '.vtp': 'application/octet-stream',
              '.svg': 'image/svg+xml',
            }[ext] || 'application/octet-stream'
            res.setHeader('Content-Type', mime)
            res.setHeader('Access-Control-Allow-Origin', '*')
            fs.createReadStream(target).pipe(res)
            return
          }
        }
        next()
      })
    },
    closeBundle() {
      const outDir = path.resolve(process.cwd(), 'rebuild-dist')
      const src = path.resolve(process.cwd(), 'public', 'model_cache')
      const dst = path.join(outDir, 'model_cache')
      if (fs.existsSync(src)) {
        if (!fs.existsSync(dst)) fs.mkdirSync(dst, { recursive: true })
        cp_r(src, dst)
      }
      const svgSrc = path.resolve(process.cwd(), 'public', 'vite.svg')
      if (fs.existsSync(svgSrc)) {
        fs.copyFileSync(svgSrc, path.join(outDir, 'vite.svg'))
      }
    },
  }
}

function cp_r(src, dst) {
  const names = fs.readdirSync(src)
  for (const n of names) {
    const s = path.join(src, n)
    const d = path.join(dst, n)
    const st = fs.statSync(s)
    if (st.isDirectory()) {
      if (!fs.existsSync(d)) fs.mkdirSync(d, { recursive: true })
      cp_r(s, d)
    } else {
      fs.copyFileSync(s, d)
    }
  }
}

// GitHub Pages / 自定义子路径部署支持：
//   构建时：VITE_BASE=/tu-shi-fang-ping-heng-xi-tong-she-ji-yu-kai-fa/ npm run build
//   或在 GitHub Actions 中自动传入 base = /<仓库名>/
const GITHUB_REPO_NAME = process.env.VITE_GITHUB_REPO || ''
const VITE_BASE_USER = process.env.VITE_BASE || process.env.BASE_URL || ''
// 默认根路径 /；若设置了仓库名或 VITE_BASE，则使用子路径部署
const base = (VITE_BASE_USER || (GITHUB_REPO_NAME ? `/${GITHUB_REPO_NAME}/` : '/'))

export default defineConfig({
  base,
  plugins: [vue(), localDataBridge()],
  resolve: {
    alias: {
      '@': path.resolve(process.cwd(), 'src'),
    },
  },
  build: {
    outDir: 'rebuild-dist',
    emptyOutDir: true,
    sourcemap: false,
    chunkSizeWarningLimit: 4000,
    rollupOptions: {
      output: {
        manualChunks: {
          vtk: ['@kitware/vtk.js'],
          echarts: ['echarts', 'vue-echarts'],
          element: ['element-plus', '@element-plus/icons-vue'],
        },
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 4173,
  },
})
