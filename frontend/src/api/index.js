import request from '@/utils/request'

// 原始 axios 实例（命名导出，供 ControlPanel3D.vue / LayerTree3D.vue 直接用）
export const api = request
export default request

// ========== 认证 ==========
export const login = (data) => request.post('/auth/login-json', data)
export const getMe = () => request.get('/auth/me')
export const listUsers = () => request.get('/auth/users')
export const createUser = (data) => request.post('/auth/users', data)
export const updateUser = (id, data) => request.put(`/auth/users/${id}`, data)
export const deleteUser = (id) => request.delete(`/auth/users/${id}`)

// ========== 项目 ==========
export const listProjects = (params) => request.get('/projects', { params })
export const createProject = (data) => request.post('/projects', data)
export const updateProject = (id, data) => request.put(`/projects/${id}`, data)
export const deleteProject = (id) => request.delete(`/projects/${id}`)

// ========== 表单审批 ==========
export const getFormTypes = () => request.get('/forms/types')
export const listForms = (params) => request.get('/forms', { params })
export const getFormStats = () => request.get('/forms/stats')
export const getForm = (id) => request.get(`/forms/${id}`)
export const createForm = (data) => request.post('/forms', data)
export const submitForm = (id) => request.post(`/forms/${id}/submit`)
export const approveForm = (id, data) => request.post(`/forms/${id}/approve`, data)
export const deleteForm = (id) => request.delete(`/forms/${id}`)

// ========== 三维模型 / 地质 / 参数 ==========
export const getModelCatalog = () => request.get('/models/catalog')
export const listStages = () => request.get('/models/stages')
export const getStageMetrics = (stageKey) => request.get(`/models/stages/${stageKey}/metrics`)
export const refreshMetrics = () => request.get('/models/metrics/refresh')

export const listGeologyLayers = (params) => request.get('/models/geology/layers', { params })
export const createGeologyLayer = (data) => request.post('/models/geology/layers', data)
export const updateGeologyLayer = (id, data) => request.put(`/models/geology/layers/${id}`, data)
export const deleteGeologyLayer = (id) => request.delete(`/models/geology/layers/${id}`)

export const listBoreholes = (params) => request.get('/models/geology/boreholes', { params })
export const createBorehole = (data) => request.post('/models/geology/boreholes', data)

export const getParamSchema = () => request.get('/models/params/schema')
export const getParamValues = (params) => request.get('/models/params/values', { params })
export const calculateParams = (data) => request.post('/models/params/calculate', data)

// ========== 监测 ==========
export const getSensorTypes = () => request.get('/monitoring/sensors/types')
export const listSensors = (params) => request.get('/monitoring/sensors', { params })
export const getSensor = (id) => request.get(`/monitoring/sensors/${id}`)
export const createSensor = (data) => request.post('/monitoring/sensors', data)
export const updateSensor = (id, data) => request.put(`/monitoring/sensors/${id}`, data)
export const deleteSensor = (id) => request.delete(`/monitoring/sensors/${id}`)

export const getSensorReadings = (id, params) => request.get(`/monitoring/sensors/${id}/readings`, { params })
export const addSensorReading = (id, data) => request.post(`/monitoring/sensors/${id}/readings`, data)
export const batchReadings = (data) => request.post('/monitoring/readings/batch', data)
export const getMonitoringOverview = (params) => request.get('/monitoring/overview', { params })

// ========== 安全预警 ==========
export const listAlertRules = (params) => request.get('/alerts/rules', { params })
export const createAlertRule = (data) => request.post('/alerts/rules', data)
export const updateAlertRule = (id, data) => request.put(`/alerts/rules/${id}`, data)
export const deleteAlertRule = (id) => request.delete(`/alerts/rules/${id}`)

export const listAlerts = (params) => request.get('/alerts/alerts', { params })
export const getAlertStats = (params) => request.get('/alerts/alerts/stats', { params })
export const ackAlert = (id) => request.post(`/alerts/alerts/${id}/ack`)
export const closeAlert = (id) => request.post(`/alerts/alerts/${id}/close`)
export const runAlertCheck = (params) => request.post('/alerts/alerts/check-all', null, { params })

// ========== 仪表盘 ==========
export const getDashboardSummary = () => request.get('/dashboard/summary')
export const getFormTrend = (params) => request.get('/dashboard/form-trend', { params })
export const getFormByType = () => request.get('/dashboard/form-by-type')
export const getEarthworkBalance = () => request.get('/dashboard/earthwork-balance')
export const getStageDisplacementTrend = () => request.get('/dashboard/stage-displacement-trend')
export const getRecentActivities = (params) => request.get('/dashboard/recent-activities', { params })
