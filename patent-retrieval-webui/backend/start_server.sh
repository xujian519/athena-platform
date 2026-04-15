#!/bin/bash

cd "$(dirname "$0")"

echo "🚀 启动专利检索WebUI后端服务..."

if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "📥 安装依赖..."
pip install -r requirements.txt

echo "🔧 启动FastAPI服务..."
python api_server.py
