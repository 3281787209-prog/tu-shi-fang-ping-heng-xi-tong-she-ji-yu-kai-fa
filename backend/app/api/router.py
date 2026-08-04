from fastapi import APIRouter

from app.api.routes import auth, dashboard, forms, models, projects, monitoring, alerts, interactive3d


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["认证与用户"])
api_router.include_router(projects.router, prefix="/projects", tags=["项目管理"])
api_router.include_router(forms.router, prefix="/forms", tags=["表单审批"])
api_router.include_router(models.router, prefix="/models", tags=["三维模型与地质参数"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["监测信息"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["安全预警"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["业务首页"])
api_router.include_router(interactive3d.router, prefix="/interactive3d", tags=["三维交互联动"])
