#!/bin/bash

cd "$(dirname "$0")"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║     专利混合检索系统 - 一键启动脚本                      ║"
echo "║     Patent Hybrid Retrieval System - Quick Start        ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

BACKEND_DIR="backend"
FRONTEND_DIR="."

echo "📋 检查依赖..."

if ! command -v node &> /dev/null; then
    echo "❌ Node.js未安装，请先安装Node.js"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python3"
    exit 1
fi

echo ""
echo "🚀 启动后端服务..."
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

if [ -f "requirements.txt" ]; then
    pip install -q -r requirements.txt
fi

python api_server.py &
BACKEND_PID=$!

cd ..
echo "✅ 后端服务已启动 (PID: $BACKEND_PID)"

echo ""
echo "🚀 启动前端服务..."
cd "$FRONTEND_DIR"
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 前端服务已启动 (PID: $FRONTEND_PID)"

echo ""
echo "════════════════════════════════════════════════════════"
echo "🎉 系统启动完成！"
echo ""
echo "📍 访问地址："
echo "   前端界面: http://localhost:3000"
echo "   后端API:  http://localhost:8000"
echo "   API文档:  http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "════════════════════════════════════════════════════════"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo ''; echo '🛑 所有服务已停止'; exit 0" SIGINT SIGTERM

wait
