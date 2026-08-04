#!/usr/bin/env bash
# 土石方平衡协同系统 - Linux/macOS 一键启动脚本
# 用法: chmod +x start-earthwork.sh && ./start-earthwork.sh

set -e
PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"

echo -e "\033[36m================================================\033[0m"
echo -e "\033[36m 土石方平衡协同系统 - 启动 (Linux/macOS)\033[0m"
echo -e "\033[36m================================================\033[0m"

# ---------- 后端 ----------
cd "$PROJECT_ROOT/backend"
echo -e "\n\033[33m[1/3] 安装后端依赖 + 初始化数据库...\033[0m"
python3 -m pip install -r requirements.txt >/dev/null 2>&1 || python -m pip install -r requirements.txt
python3 -c "from app.init_db import main; main()" || python -c "from app.init_db import main; main()"

echo -e "\033[32m[2/3] 启动后端 (端口 8000)...\033[0m"
if command -v python3 >/dev/null 2>&1; then PY=python3; else PY=python; fi
$PY -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
sleep 3
if ! kill -0 $BACKEND_PID 2>/dev/null; then
  echo -e "\033[31m后端启动失败，请检查日志\033[0m"; exit 1
fi
echo -e "\033[32m  后端 OK ->  http://localhost:8000/docs\033[0m"

# ---------- 前端 ----------
cd "$PROJECT_ROOT/frontend"
echo -e "\n\033[33m[3/3] 启动前端 (端口 5173)...\033[0m"
[ ! -d node_modules ] && echo -e "\033[90m  首次运行，安装 npm 依赖 (可能 3-5 分钟)...\033[0m" && npm install --no-audit --no-fund
npm run dev &
FRONTEND_PID=$!
sleep 4

echo -e "\n\033[36m================================================\033[0m"
echo -e "\033[32m 启动完成！\033[0m"
echo -e " 前端地址:  http://localhost:5173/"
echo -e " 后端 API:  http://localhost:8000/docs"
echo -e ""
echo -e "\033[33m 默认账号：\033[0m"
echo -e "   admin    / admin123    超级管理员"
echo -e "   manager  / manager123  项目经理"
echo -e "   engineer / engineer123 技术工程师"
echo -e "   user01   / user123     普通用户"
echo -e "\033[36m================================================\033[0m"
echo -e "\n按 Ctrl+C 停止前后端服务"

cleanup() {
  echo -e "\n\033[33m正在停止服务...\033[0m"
  kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
  wait 2>/dev/null
  echo -e "\033[90m已停止。\033[0m"
}
trap cleanup EXIT INT TERM
wait
