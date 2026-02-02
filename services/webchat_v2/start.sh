#!/bin/bash
# WebChat V2 Gateway 启动脚本
# 作者: Athena平台团队
# 创建时间: 2025-01-31

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 激活虚拟环境（如果存在）
if [ -f "../../../.venv/bin/activate" ]; then
    echo "激活虚拟环境..."
    source "../../../.venv/bin/activate"
elif [ -f "../../../.venv_opt/bin/activate" ]; then
    echo "激活虚拟环境..."
    source "../../../.venv_opt/bin/activate"
fi

# 安装依赖
echo "检查并安装依赖..."
pip install -q fastapi uvicorn[standard] websockets pydantic-settings

# 启动服务
echo "启动 WebChat V2 Gateway 服务..."
echo ""
echo "WebSocket 端点: ws://localhost:8000/gateway/ws"
echo "健康检查: http://localhost:8000/gateway/health"
echo "模块列表: http://localhost:8000/gateway/modules"
echo ""
echo "按 Ctrl+C 停止服务"
echo ""

cd api
python -m uvicorn app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --reload \
    --log-level info
