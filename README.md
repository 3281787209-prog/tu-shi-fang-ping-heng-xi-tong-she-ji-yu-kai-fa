# 土石方平衡与工程数字化协同系统

> **古贤黄河水利枢纽 · 坝肩左岸边坡开挖工程 · 数字化协同平台

面向水利水电工程的土石方平衡、边坡开挖数值模拟结果可视化、表单审批流程、安全监测预警一体化管理系统。前端 Vue3 + VTK.js 三维可视化，后端 FastAPI + SQLAlchemy，全栈开源，可一键部署到 Render / GitHub Pages。

[![Vue 3][vue] [![FastAPI][fastapi] [![VTK.js][vtk] [![ECharts][echarts] [![Element Plus][el]]

[vue]: https://img.shields.io/badge/Vue-3.5-42b883?logo=vuedotjs
[fastapi]: https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi
[vtk]: https://img.shields.io/badge/VTK.js-34.x-blue?logo=kitware
[echarts]: https://img.shields.io/badge/ECharts-5.5-ff6b6b?logo=apacheecharts
[el]: https://img.shields.io/badge/Element--Plus-2.8-409eff?logo=element

---

## 一、功能模块（七大核心业务首页

| 模块 | 路由路径 | 功能简介 |
| --- | --- | --- |
| 🏠 业务首页 | `/dashboard` | 数据看板：土石方平衡、表单趋势、工况位移/应力曲线、近期活动 |
| 📋 表单审批 | `/forms` | 土石方调度方案 / 变更申请 / 异常上报 / 参数计算 / 勘察 / 监测报告，7类表单，自定义角色审批链（manager → engineer → admin） |
| ⛰️ 地质信息 | `/geology` | 23 步开挖工况三维可视化、XYZ剖切、标量场着色、地质图层、钻孔柱状图 |
| 📡 监测信息 | `/monitoring` | 传感器档案、14个物理量实时趋势曲线、批量读数录入与自动告警联动 |
| 🧮 参数繁衍 | `/params` | 材料 / 开挖 / 安全系数 / 计算设置，4组19项参数输入，一键推导衍生指标（方量 / 稳定系数 / 沉降估算） |
| ⚠️ 安全预警 | `/alerts` | 阈值规则配置、自动触发、告警分级处理、14天趋势统计 |
| ⚙️ 系统管理 | `/system` | 用户管理（4级角色）/ 项目管理 / 系统概览 |

---

## 二、技术栈

### 前端 earthwork-balance-system/frontend

| 分类 | 技术 | 版本 | 用途 |
| --- | --- | --- | --- |
| 框架 | **Vue 3** | ^3.5.18 | Composition API + `<script setup>` |
| 构建 | **Vite** | ^7.1.0 | 开发服务与打包 |
| UI | **Element Plus** | ^2.8.4 | 组件库（中后台 |
| 样式 | **Tailwind CSS** | ^3.4.10 | 原子化 CSS |
| 状态 | **Pinia** | ^2.2.2 | 用户状态 / 权限 |
| 路由 | **Vue Router** | ^4.4.5 | Hash 路由（兼容静态托管） |
| 请求 | **Axios** | ^1.7.7 | 拦截器 401 自动跳登录 |
| 图表 | **ECharts 5** + vue-echarts | ^7.0.3 | 统计 / 位移应力曲线 / 饼 / 桑基 / 雷达 |
| 三维 | **@kitware/vtk.js** | ^34.14.0 | VTK PolyData 模型渲染、剖切、标量映射 |

### 后端 earthwork-balance-system/backend

| 分类 | 技术 | 版本 | 用途 |
| --- | --- | --- | --- |
| Web 框架 | **FastAPI** | 0.115.0 | 异步 + 自动文档 `/docs` + `/redoc` |
| ORM | **SQLAlchemy** | 2.0.34 | 支持 SQLite / PostgreSQL / MySQL |
| 数据校验 | **Pydantic** | 2.8.2 | 2.0 schema 定义 |
| 认证 | **python-jose + passlib[bcrypt] | - | JWT + bcrypt 密码哈希 |
| 部署服务器 | **Uvicorn[standard]** | 0.30.6 | ASGI 运行 uvicorn app.main:app

---

## 三、目录结构

```
earthwork-balance-system/
├── backend/                          # FastAPI 后端
│   ├── app/
│   │   ├── main.py                  # 入口：CORS / 静态 /api 路由
│   │   ├── init_db.py              # 数据库初始化 + 种子数据
│   │   ├── core/
│   │   │   ├── config.py          # pydantic-settings 环境变量
│   │   │   └── security.py      # JWT + 密码工具
│   │   ├── db/
│   │   │   ├── base.py          # SQLAlchemy Base
│   │   │   └── session.py   # 会话工厂 + get_db 依赖
│   │   ├── models/              # 8 张表
│   │   │   ├── user.py              # 用户
│   │   │   ├── project.py        # 项目
│   │   │   ├── form.py        # 表单 + 审批步骤
│   │   │   ├── geology.py        # 地质图层 + 钻孔
│   │   │   ├── monitoring.py   # 传感器 + 读数
│   │   │   ├── alerts.py          # 规则 + 告警
│   │   │   └── model_metric.py  # 工况物理量指标
│   │   ├── schemas/               # Pydantic Schema
│   │   ├── api/
│   │   │   ├── router.py          # 总路由 7 个子路由
│   │   │   ├── deps.py         # 认证 / 权限依赖
│   │   │   └── routes/
│   │   │       ├── auth.py             # 登录 / 用户 CRUD
│   │   │       ├── projects.py          # 项目管理
│   │   │       ├── forms.py           # 表单审批链
│   │   │       ├── models.py      # 三维 / 地质 / 参数繁衍
│   │   │       ├── monitoring.py # 监测传感器读数
│   │   │       ├── alerts.py    # 预警规则告警
│   │   │       └── dashboard.py      # 首页汇总接口
│   │   ├── services/
│   │   │   └── model_cache.py   # VTP 头部提取真实 Range
│   │   └── static/
│   │       └── model_cache/         # index.json (工况索引）
│   ├── requirements.txt             # Python 依赖
│   └── .env.example              # 环境变量样例
│
└── frontend/                        # Vue 3 前端
    ├── src/
    │   ├── main.js                 # 入口：Pinia / Router / Element Plus / ECharts
    │   ├── App.vue
    │   ├── style.css               # Tailwind + 全局自定义样式
    │   ├── api/
    │   │   └── index.js         # Axios 封装全部接口
    │   ├── router/
    │   │   └── index.js      # 路由 + 登录守卫
    │   ├── stores/
    │   │   └── user.js          # Pinia 用户状态
    │   ├── utils/
    │   │   └── request.js   # Axios 拦截器
    │   ├── layouts/
    │   │   └── MainLayout.vue    # 侧边栏 + 顶栏 布局
    │   ├── components/
    │   │   └── VtkViewer.vue # VTK.js 三维可视化核心组件
    │   └── views/
    │       ├── Login.vue             # 登录页
    │       ├── Dashboard.vue         # 业务首页
    │       ├── FormApproval.vue      # 表单审批
    │       ├── GeologyInfo.vue       # 地质信息
    │       ├── MonitoringInfo.vue    # 监测信息
    │       ├── ParamInference.vue     # 参数繁衍
    │       ├── SafetyAlert.vue      # 安全预警
    │       └── SystemManagement.vue # 系统管理
    ├── public/
    │   └── model_cache/          # 23 工况 VTP 模型
    │       └── index.json
    ├── index.html
    ├── vite.config.js           # 代理 / 打包 model_cache 拷贝
    ├── tailwind.config.js
    └── package.json
```

---

## 四、快速开始（本地开发，前后端互联）

### 环境要求

- Node.js **>= 18** (推荐 20 LTS)
- Python **>= 3.10** (推荐 3.11 / 3.12)
- Git

### 第 1 步：克隆（第一次安装依赖

```bash
# ============ 后端 ============
cd earthwork-balance-system/backend

# （推荐）创建虚拟环境
python -m venv .venv
# Windows 激活
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# ============ 前端 ============
cd ../frontend
npm install
```

### 第 2 步：初始化数据库 + 种子数据

```bash
cd ../backend  # 回到 backend

# 复制环境变量（生产务必修改 SECRET_KEY！）
copy .env.example .env

# 执行初始化：建表 + 4个用户 + 示例项目 + 地质/钻孔/传感器/传感器读数/表单等所有种子数据
python -m app.init_db
```

成功输出：
```
[OK] 默认用户已初始化: admin/admin123, manager/manager123, ...
[OK] 示例项目已创建
[OK] 地质图层 8 个 / 钻孔 5 个已创建
[OK] 传感器 15 个已创建
[OK] 模拟监测读数 xxxxx 条已生成
[OK] 预警规则 7 条已创建
[OK] 示例表单 7 份已创建
[OK] 工况物理量指标 xxx 条已入库
[OK] 历史告警 6 条已创建
```

### 第 3 步：启动后端（端口 8000）

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

验证：浏览器访问 <http://localhost:8000/docs> 打开 Swagger UI，可以在 Authorize 里用 `admin/admin123` 登录调试所有接口。

### 第 4 步：启动前端（端口 5173）

```bash
cd frontend
npm run dev
```

浏览器访问 <http://localhost:5173>，自动通过 Vite 代理把 `/api/**` 转发到 `http://localhost:8000`，所以 **前端无需任何 CORS 配置。

登录：`admin` / `admin123`

---

## 五、连接原理（前后端如何互联）

### 5.1 本地开发连接

```
浏览器 → Vite dev server (5173)
         ├─ /              → 前端静态资源 / Vue 路由 hash 模式
         └─ /api/*        → proxy → http://localhost:8000/api/* (FastAPI)
         └─ /model_cache/* → 本地 public/model_cache
```

`vite.config.js` 里已写好：

```js
server: {
  proxy: {
    '/api': { target: 'http://localhost:8000', changeOrigin: true }
  }
}
```

Axios 实例默认 `baseURL: '/api' → 代理。

### 5.2 生产部署 / 前后端分离部署

#### 方案 A：后端 API 服务 (FastAPI 放 Render

| 服务 | 地址 | 环境变量 |
| --- | --- | --- |
| 前端 | `https://<前端.onrender.com` | `VITE_API_BASE=https://<后端>.onrender.com/api` |
| 后端 | `https://<后端>.onrender.com` | `CORS_ORIGINS=https://<前端>.onrender.com` |

关键：
1. 前端 build 时把 `VITE_API_BASE` 设为后端真实地址
2. 后端 `.env` 里把 `CORS_ORIGINS` 追加前端域名，`*` 也行

#### 方案 B：同源部署（Nginx 反代）

同一域名，Nginx 把 `/api` 反代到 uvicorn，其他给前端静态

```nginx
location /api/ { proxy_pass http://127.0.0.1:8000; }
location /model_cache/ { alias /opt/model_cache; }
location / { try_files $uri /index.html; }
```

### 5.3 三维模型数据来源与同步

- **真实 VTP 数据位置：`input/dist/dist/model_cache/`（23 工况 × 156 文件 = 3588 VTP = 2GB）
- **前端 / 后端 index.json 精简版**：由 `init_db.py` 里的 `sync_index_json()` 从 input 目录读取，每个 exac 只取每个方向中间 5 个切片，生成到 frontend/public/model_cache/index.json 和 backend/static/model_cache/index.json。
- 需要全量切片时：直接把整个 `input/dist/dist/model_cache/*` 覆盖到 `frontend/public/model_cache/` 即可。

---

## 六、默认账号（4 级权限）

| 用户名 | 密码 | 角色 | 权限 |
| --- | --- | --- | --- |
| `admin` | `admin123` | admin | 所有权限 + 系统管理 |
| `manager` | `manager123` | manager | 创建/审批表单第1步、传感器/

---

## 七、API 总览（Swagger 文档：`/redoc`

| 前缀 | 标签 | 核心端点 |
| --- | --- | --- |
| `/api/auth` | 认证用户 | `POST /login` /login-json`，`GET /me`，`GET/POST/PUT/DELETE /users` |
| `/api/projects` | 项目 | CRUD |
| `/api/forms` | 表单审批 | `GET /types`, `GET /stats`, `POST /{id}/submit`, `POST /{id}/approve` |
| `/api/models` | 三维地质参数 | `GET /catalog`, `GET /stages/{k}/metrics`, `GET /geology/layers`, `GET /geology/boreholes`, `GET /params/schema`, `POST /params/calculate` |
| `/api/monitoring` | 监测 | `GET /overview`, sensors CRUD, `GET /sensors/{id}/readings`, `POST /readings/batch` |
| `/api/alerts` | 预警 | rules CRUD, alerts list/ack/close, `POST /check-all` 巡检 |
| `/api/dashboard` | 首页 | `summary`, `form-trend`, `earthwork-balance`, `stage-displacement-trend`, `recent-activities` |

---

## 八、上传到 GitHub

```bash
cd earthwork-balance-system
git init
git add -A
git commit -m "feat: 土石方平衡协同系统 v1.0 完整开源"
git branch -M main
git remote add origin https://github.com/<你的用户名>/earthwork-balance-system.git
git push -u origin main
```

建议 `.gitignore`（已自动生效的常见项）：
- Python: `backend/.venv/`, `backend/data.db`, `backend/__pycache__/`
- Node: `frontend/node_modules/`, `frontend/rebuild-dist/`
- 环境：`.env`

---

## 九、Render 一键部署指南

### 9.1 部署后端（New → Web Service）

| 字段 | 填写 |
| --- | --- |
| **Root Directory** | `earthwork-balance-system/backend` |
| **Runtime** | Python 3.11 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Environment Variables** | 见下方 |

后端环境变量：
| Key | Value（示例） |
| --- | --- |
| `ENV` | `prod` |
| `SECRET_KEY` | 用 `openssl rand -hex 64 生成一串 |
| `DATABASE_URL` | （可选）Render Postgres 连接串；不填则自动用 SQLite（适合演示） |
| `CORS_ORIGINS` | `https://<你的前端>.onrender.com`（或 `*`） |

⚠️ **初始化数据：第一次部署完，在 Shell 里执行 `python -m app.init_db`。SQLite 会丢失，请用 Postgres 持久化）

### 9.2 部署前端（New → Static Site）

| 字段 | 填写 |
| --- | --- |
| **Root Directory** | `earthwork-balance-system/frontend` |
| **Build Command** | `npm install && npm run build` |
| **Publish Directory** | `rebuild-dist` |
| **Environment Variables** | `VITE_API_BASE=https://<你的后端域名>/api` |

注意：因为用了 hash 路由 `createWebHashHistory`，Static Site 不需要 Rewrite rules，直接即可刷新无 404。

### 9.3 （可选）模型缓存单独存对象存储

如果 model_cache 太大 > 500MB → 放 S3 / Cloudflare R2 / 阿里云 OSS，然后改：
- `VITE_MODEL_CACHE_BASE=https://cdn.xxx.com/model_cache`
- 前端 VtkViewer.vue 里的 URL 前缀从 `/model_cache/` 改成该变量即可。

---

## 十、扩展开发建议

1. **更多工况**：在 `frontend/public/model_cache/` 新建 `exac_24/` 目录放 156 VTP，然后在 `index.json` 加条目，页面自动识别。
2. **真实传感器接入**：在 `backend/app/api/routes/monitoring.py` 写 MQTT / WebSocket 消费者，把实时消息写进 `monitoring_readings` 表即可，前端图表就会刷新。
3. **权限细化**：在 `backend/app/api/deps.py` 的 `require_role` 改造成 RBAC 权限点粒度（按模块/按操作）。
4. **升级数据库**：SQLite → PostgreSQL，`DATABASE_URL` 换连接串，无需改代码，SQLAlchemy 全兼容。
5. **土石方案调度归类**：表单 `form_type = "schedule_plan" 和 "earthwork_allocation" 两种，在 data 里存详细的调配明细（弃渣场、取土场、运距、车辆），首页 `earthwork-balance` 接口从已审批表单自动合计。

---

## 十一、数据真实性说明

- **三维模型数据（VTP）**：来源于工程真实数值模拟结果，含 14 个物理量场，范围、`RangeMin/Max` 由 `init_db` 从文件头部 XML 正则提取，入库到 `model_stage_metrics`，前端仪表盘的最大位移/最大应力/工况趋势全部来自数据库，非手写。
- **土石方平衡指标**：由 `backend/app/api/routes/dashboard.py` 汇总 `forms` 表中 `status=approved` 的调度表单计算得到；无数据时提供默认演示值（古贤工程规模）。
- **参数繁衍结果**：由 `calculate_derived_params` 基于 Taylor 稳定估算 + 沉降公式 + 方量几何模型，输入改变输入参数改变结果，输出可复现；稳定系数和沉降结果，仅用于工程方案比选参考，非替代专项设计值。
- **传感器读数**：种子数据提供按 14 天、每 6 小时、14 个物理量的时序模拟数据，可在「监测信息 → 读数录入」中追加真实数据，自动联动预警规则触发真实告警。

---

## 十二、联系方式

如果部署/开发问题：优先查看后端日志 / 前端控制台 → 打开 F12 网络面板，401 说明 token 过期需重新登录，500 看 FastAPI 日志里 Python 栈
