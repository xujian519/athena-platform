#!/bin/bash
# 记忆系统服务启动脚本

PROJECT_ROOT="/Users/xujian/Athena工作平台"
PYTHONPATH="${PROJECT_ROOT}"

# 激活虚拟环境（如果有的话）
if [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# 设置环境变量
export MEMORY_SYSTEM_CONFIG="${PROJECT_ROOT}/config/memory_system_config.json"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5438"
export POSTGRES_DB="memory_module"

# 启动记忆系统API服务
cd "${PROJECT_ROOT}"
python3 scripts/memory/simple_memory_api.py
