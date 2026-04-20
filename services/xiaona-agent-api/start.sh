#!/bin/bash
# 小娜智能体API服务启动脚本

cd "$(dirname "$0")"

echo "🌟 启动小娜智能体API服务..."

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# 启动服务
python3 main.py
