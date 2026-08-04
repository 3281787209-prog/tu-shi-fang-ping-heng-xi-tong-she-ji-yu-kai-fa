"""
FastAPI 应用入口
运行: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.api.router import api_router

# 创建所有数据表（首次启动自动建表）
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="土石方平衡与工程数字化协同系统",
    description=(
        "古贤黄河水利枢纽 - 坝肩左岸边坡开挖土石方平衡协同平台。\n"
        "包含：业务首页看板、表单审批、地质信息、监测信息、参数繁衍、安全预警、系统管理 七大模块。"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
# 生产部署时追加 Render / 静态站点域名，同时也允许任意来源通过（前端静态站场景）
origins += ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态资源：三维模型 VTP 文件
from pathlib import Path
from fastapi.responses import FileResponse

model_cache_dir = Path(settings.MODEL_CACHE_DIR)
if model_cache_dir.exists():
    # 自定义静态目录响应，正确设置 VTP 的 MIME 类型
    from fastapi import HTTPException, Request

    @app.get("/model_cache/{full_path:path}", include_in_schema=False)
    async def serve_model_cache(full_path: str, request: Request):
        target = (model_cache_dir / full_path).resolve()
        # 防目录穿越
        if not str(target).startswith(str(model_cache_dir.resolve())):
            raise HTTPException(403)
        if not target.is_file():
            raise HTTPException(404)
        media = "application/octet-stream"
        if target.suffix == ".json":
            media = "application/json"
        elif target.suffix == ".vtp":
            media = "application/x-vtk-poly-data"
        return FileResponse(target, media_type=media)


# 健康检查
@app.get("/health", tags=["系统"])
def health():
    return {"status": "ok", "env": settings.ENV}


# 业务 API
app.include_router(api_router, prefix="/api")

# ============================================================
# 生产模式：同源部署 - 后端同时托管前端静态站 (SPA fallback)
# 将前端构建产物 rebuild-dist/ 拷贝到 backend/webroot/ 即可启用
# 或者设置 VITE_API_BASE_URL=/api 即可同源无跨域访问
# ============================================================
_root = Path(__file__).resolve().parents[2]  # backend/
_webroot = _root / "webroot"
_alt_webroot = _root.parent / "frontend" / "rebuild-dist"
if not _webroot.exists():
    pass
elif _alt_webroot.exists():
    _webroot = _alt_webroot

if _webroot.exists() and (_webroot / "index.html").exists():
    from fastapi.responses import FileResponse, HTMLResponse
    import os

    # 静态子目录（assets / model_cache 等
    app.mount("/assets", StaticFiles(directory=str(_webroot / "assets")), name="web_assets")
    if (_webroot / "model_cache").exists():
        app.mount("/model_cache", StaticFiles(directory=str(_webroot / "model_cache")), name="web_model_cache")

    @app.get("/", include_in_schema=False)
    async def serve_index():
        return HTMLResponse((_webroot / "index.html").read_text(encoding="utf-8"))

    @app.get("/index.html", include_in_schema=False)
    async def serve_index_html():
        return HTMLResponse((_webroot / "index.html").read_text(encoding="utf-8"))

    # SPA: 所有非 API/静态/API路由都返回 index.html
    @app.api_route("/{path_name:path}", methods=["GET"], include_in_schema=False)
    async def spa_fallback(path_name: str, request: Request):
        # 如果请求路径属于 API 或已知静态文件则不处理
        if path_name.startswith("api/") or path_name.startswith("docs") or path_name.startswith("redoc"):
            from fastapi import HTTPException
            raise HTTPException(status_code=404)
        idx = _webroot / "index.html"
        if idx.exists():
            return HTMLResponse(idx.read_text(encoding="utf-8"))
        from fastapi import HTTPException
        raise HTTPException(status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
