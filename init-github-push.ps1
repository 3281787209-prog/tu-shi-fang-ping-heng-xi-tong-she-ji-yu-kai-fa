# ============================================================
# 土石方平衡系统设计与开发 - GitHub 初始化&上传脚本（Windows PowerShell）
# ============================================================
# 功能说明
#   1. 初始化Git仓库
#   2. 安装并启用Git LFS（追踪.vtp/.vtk/.xlsx等大文件）
#   3. 首次commit并推送到GitHub
#   4. 推送后自动等待GitHub Actions构建GitHub Pages公共网页
# ============================================================
# 使用方法
#   A. 先到github.com 创建仓库，记下你的仓库URL（例如https://github.com/你的用户名/tu-shi-fang-ping-heng-xi-tong-she-ji-yu-kai-fa.git）
#   B. 修改下方$GITHUB_REPO_URL
#   C. PowerShell中运行：.\init-github-push.ps1
# ============================================================
$ErrorActionPreference = "Stop"
# ====================== 请修改这里 ==========================
$GITHUB_REPO_URL = "https://github.com/3281787209-prog/tu-shi-fang-ping-heng-xi-tong-she-ji-yu-kai-fa.git"
$DEFAULT_BRANCH  = "main"
$COMMIT_MESSAGE  = "feat: 初始化土石方平衡系统设计与开发（Vue3""&""FastAPI""&""VTK三维协同"
# ============================================================
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " 土石方平衡系统设计与开发 · GitHub 初始化""&""上传" -ForegroundColor Cyan
Write-Host " 项目目录: $ProjectRoot" -ForegroundColor Gray
Write-Host " 远程仓库: $GITHUB_REPO_URL" -ForegroundColor Gray
Write-Host "================================================================" -ForegroundColor Cyan
# 1) 检测git 与git-lfs
function Check-Cmd($name) {
    $null = Get-Command $name -ErrorAction Stop
}
try { Check-Cmd "git" } catch { Write-Error "未检测到 git，请先安装Git for Windows"; exit 1 }
# 2) 初始化仓库
if (-not (Test-Path (Join-Path $ProjectRoot ".git"))) {
    Write-Host "`n[1/6] git init..." -ForegroundColor Yellow
    git init -b $DEFAULT_BRANCH
} else {
    Write-Host "`n[1/6] .git 已存在，跳过 init" -ForegroundColor Green
}
# 3) 启用 Git LFS
Write-Host "`n[2/6] 启用 Git LFS（追踪VTP/大文件）..." -ForegroundColor Yellow
git lfs install 2>$null | Out-Null
# 应用 .gitattributes（已包含 LFS 模式）
git lfs track "*.vtp" 2>$null | Out-Null
git lfs track "*.vtu" 2>$null | Out-Null
git lfs track "*.xlsx" 2>$null | Out-Null
Write-Host "    LFS 已启用，追踪规则写入.gitattributes" -ForegroundColor Gray
# 4) 设置远程仓库
$remotes = (git remote 2>$null) -join ','
if ($remotes -notmatch 'origin') {
    Write-Host "`n[3/6] 添加远程 origin..." -ForegroundColor Yellow
    git remote add origin $GITHUB_REPO_URL
} else {
    Write-Host "`n[3/6] 更新远程 origin..." -ForegroundColor Yellow
    git remote set-url origin $GITHUB_REPO_URL
}
# 5) 首次提交（排除node_modules/__pycache__/rebuild-dist等，已在.gitignore配置）
Write-Host "`n[4/6] git add 全部文件（首次可能需要几分钟处理 model_cache VTP 文件）.." -ForegroundColor Yellow
git add -A
Write-Host "`n[5/6] git commit..." -ForegroundColor Yellow
git commit -m $COMMIT_MESSAGE 2>&1 | Select-Object -Last 5
# 6) 推送到 GitHub
Write-Host "`n[6/6] git push origin $DEFAULT_BRANCH（上传可能需要几分钟，尤其含 LFS 大文件）..." -ForegroundColor Yellow
git push -u origin $DEFAULT_BRANCH --progress 2>&1 | Select-Object -Last 8
# 7) 提示 Pages 构建
Write-Host "`n================================================================" -ForegroundColor Green
Write-Host " 上传完成" -ForegroundColor Green
Write-Host " 1) 访问仓库地址$GITHUB_REPO_URL"
Write-Host " 2) 点击 Settings -> Pages -> Source 选择""GitHub Actions"""
Write-Host " 3) 打开 Actions 标签页，查看""构建并发布 GitHub Pages 公共网页""工作流"
Write-Host " 4) 构建完成后，公共网页地址为"
Write-Host "    https://$(($GITHUB_REPO_URL -replace 'https://github.com/','' -replace '\.git$','').Split('/')[0]).github.io/$($DEFAULT_BRANCH)/tu-shi-fang-ping-heng-xi-tong-she-ji-yu-kai-fa/"
Write-Host ""
Write-Host " 离线演示模式已启用：GitHub Pages 上无需后端即可完整体验 7 大业务模块""&""3D 交互"
Write-Host "================================================================" -ForegroundColor Green