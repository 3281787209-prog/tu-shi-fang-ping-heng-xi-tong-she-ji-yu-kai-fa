#!/usr/bin/env bash
# ============================================================
# 土石方平衡系统设计与开发 - GitHub 初始化 & 上传脚本（Linux / macOS）
# ============================================================
set -euo pipefail

# ================== 请修改这里 ===============================
GITHUB_REPO_URL="https://github.com/你的用户名/tu-shi-fang-ping-heng-xi-tong-she-ji-yu-kai-fa.git"
DEFAULT_BRANCH="main"
COMMIT_MESSAGE="feat: 初始化土石方平衡系统设计与开发（Vue3+FastAPI+VTK三维协同）"
# ============================================================

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "\033[36m================================================\033[0m"
echo -e "\033[36m 土石方平衡系统设计与开发 · GitHub 初始化 & 上传\033[0m"
echo -e "\033[36m 项目目录: $PROJECT_ROOT\033[0m"
echo -e "\033[36m 远程仓库: $GITHUB_REPO_URL\033[0m"
echo -e "\033[36m================================================\033[0m"

command -v git >/dev/null 2>&1 || { echo "请先安装 git"; exit 1; }

echo -e "\n\033[33m[1/6] git init\033[0m"
[ ! -d .git ] && git init -b "$DEFAULT_BRANCH" || echo "   .git 已存在，跳过 init"

echo -e "\n\033[33m[2/6] 启用 Git LFS\033[0m"
(command -v git-lfs >/dev/null 2>&1 && git lfs install) || echo "   git-lfs 未安装，跳过（大文件会被当作普通文件上传）"
git lfs track "*.vtp" 2>/dev/null || true
git lfs track "*.xlsx" 2>/dev/null || true

echo -e "\n\033[33m[3/6] 设置远程 origin\033[0m"
if git remote 2>/dev/null | grep -q '^origin$'; then
  git remote set-url origin "$GITHUB_REPO_URL"
else
  git remote add origin "$GITHUB_REPO_URL"
fi

echo -e "\n\033[33m[4/6] git add\033[0m"
git add -A

echo -e "\n\033[33m[5/6] git commit\033[0m"
git commit -m "$COMMIT_MESSAGE" 2>&1 | tail -5 || echo "   nothing to commit"

echo -e "\n\033[33m[6/6] git push origin $DEFAULT_BRANCH\033[0m"
git push -u origin "$DEFAULT_BRANCH" --progress 2>&1 | tail -8

OWNER_REPO="${GITHUB_REPO_URL#https://github.com/}"; OWNER_REPO="${OWNER_REPO%.git}"
OWNER="${OWNER_REPO%%/*}"; REPO="${OWNER_REPO##*/}"
echo -e "\n\033[32m================================================\033[0m"
echo -e "\033[32m 上传完成！\033[0m"
echo -e " 仓库:   $GITHUB_REPO_URL"
echo -e " Pages:  Settings → Pages → Source 选择『GitHub Actions』"
echo -e " 地址:   https://${OWNER}.github.io/${REPO}/"
echo -e "\033[32m================================================\033[0m"
