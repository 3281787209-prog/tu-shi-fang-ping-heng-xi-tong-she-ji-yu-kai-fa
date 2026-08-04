# 土石方平衡协同系统 - Windows 一键启动脚本 (PowerShell)
# 双击本文件或在 PowerShell 中执行: .\start-earthwork.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Write-Host "================================================" -ForegroundColor Cyan
Write-Host " 土石方平衡协同系统 - 启动 (Windows)" -ForegroundColor Cyan
Write-Host " 项目目录: $ProjectRoot" -ForegroundColor Gray
Write-Host "================================================" -ForegroundColor Cyan

# =====================================================
# STEP 1: 后端
# =====================================================
Write-Host "`n[1/4] 检查后端依赖..." -ForegroundColor Yellow
$BackendDir = Join-Path $ProjectRoot "backend"
Set-Location $BackendDir

# 安装依赖（仅首次或 requirements.txt 更新后需要）
if (-not (Test-Path (Join-Path $BackendDir ".venv\Scripts\python.exe"))) {
    # 不用 venv，直接使用系统 python
    Write-Host "    安装 Python 依赖 (pip install -r requirements.txt)..." -ForegroundColor Gray
    python -m pip install -r requirements.txt | Out-Null
} else {
    Write-Host "    虚拟环境已存在，跳过依赖安装" -ForegroundColor Gray
}

Write-Host "`n[2/4] 初始化数据库（首次运行自动注入种子数据）..." -ForegroundColor Yellow
python -c "from app.init_db import main; main()"

Write-Host "`n[3/4] 启动后端 FastAPI (端口 8000)..." -ForegroundColor Green
$BackendJob = Start-Process -FilePath "python" -ArgumentList "-m","uvicorn","app.main:app","--host","0.0.0.0","--port","8000" -WorkingDirectory $BackendDir -PassThru -NoNewWindow
Start-Sleep -Seconds 3
if ($BackendJob.HasExited) {
    Write-Host "    后端启动失败！请检查上面的日志" -ForegroundColor Red
    exit 1
}
Write-Host "    后端启动成功 ->  http://localhost:8000/docs" -ForegroundColor Green

# =====================================================
# STEP 2: 前端
# =====================================================
Write-Host "`n[4/4] 启动前端 Vite Dev Server (端口 5173)..." -ForegroundColor Green
$FrontendDir = Join-Path $ProjectRoot "frontend"
Set-Location $FrontendDir

if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
    Write-Host "    首次运行，安装 npm 依赖（可能需要 3-5 分钟）..." -ForegroundColor Gray
    npm install --no-audit --no-fund
}

# 打开浏览器
Start-Sleep -Seconds 1
Start-Process "http://localhost:5173/"

$FrontendJob = Start-Process -FilePath "npm" -ArgumentList "run","dev" -WorkingDirectory $FrontendDir -PassThru -NoNewWindow

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host " 启动完成！" -ForegroundColor Green
Write-Host " 前端地址:  http://localhost:5173/   (已自动打开浏览器)" -ForegroundColor White
Write-Host " 后端 API:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host " 默认账号：" -ForegroundColor Yellow
Write-Host "   admin    / admin123    超级管理员" -ForegroundColor Gray
Write-Host "   manager  / manager123  项目经理" -ForegroundColor Gray
Write-Host "   engineer / engineer123 技术工程师" -ForegroundColor Gray
Write-Host "   user01   / user123     普通用户" -ForegroundColor Gray
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "`n按 Ctrl+C 或关闭此窗口以停止前后端服务" -ForegroundColor DarkGray

# 等待进程
try {
    Wait-Process -Id $FrontendJob.Id -ErrorAction Stop
} finally {
    Write-Host "`n正在停止后端进程..." -ForegroundColor Yellow
    Stop-Process -Id $BackendJob.Id -Force -ErrorAction SilentlyContinue
    Write-Host "已停止。" -ForegroundColor Gray
}
