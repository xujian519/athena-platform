#!/bin/bash
# 记忆系统完整启动脚本
# Complete Memory System Startup Script

PROJECT_ROOT="/Users/xujian/Athena工作平台"
PYTHONPATH="${PROJECT_ROOT}"
export PYTHONPATH

echo "🧠 启动 Athena 记忆系统..."

# 1. 检查并启动 PostgreSQL
echo "📊 检查 PostgreSQL 数据库..."
if ! pg_isready -h localhost -p 5438 > /dev/null 2>&1; then
    echo "⚠️ PostgreSQL (端口5438) 未运行，正在启动..."
    # 启动 PostgreSQL 的命令需要根据实际安装方式调整
fi

# 2. 检查记忆数据库
echo "🔍 检查记忆数据库..."
PSQL_PATH="/opt/homebrew/Cellar/postgresql@17/17.7/bin/psql"
DB_EXISTS=$($PSQL_PATH -h localhost -p 5438 -lqt 2>/dev/null | cut -d \| -f 1 | grep -w memory_module)
if [ -z "$DB_EXISTS" ]; then
    echo "⚠️ 记忆数据库不存在，请先创建数据库"
    echo "可以运行: /opt/homebrew/Cellar/postgresql@17/17.7/bin/createdb -h localhost -p 5438 memory_module"
    exit 1
fi

# 3. 激活虚拟环境（如果有的话）
if [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
    echo "🐍 激活虚拟环境..."
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# 4. 检查必要的Python包
echo "📦 检查必要的Python包..."
python3 -c "import fastapi, uvicorn, psycopg2" 2>/dev/null || {
    echo "⚠️ 缺少必要的Python包，正在安装..."
    pip3 install fastapi uvicorn psycopg2-binary
}

# 5. 设置环境变量
export MEMORY_SYSTEM_CONFIG="${PROJECT_ROOT}/config/memory_system_config.json"
export POSTGRES_HOST="localhost"
export POSTGRES_PORT="5438"
export POSTGRES_DB="memory_module"

# 6. 停止可能正在运行的记忆系统服务
echo "🔄 清理现有进程..."
pkill -f "simple_memory_api.py" 2>/dev/null || true
sleep 1

# 7. 启动记忆系统API服务
echo "🚀 启动记忆系统API服务..."
cd "${PROJECT_ROOT}"
nohup python3 scripts/memory/simple_memory_api.py > logs/memory_system.log 2>&1 &
MEMORY_PID=$!

# 等待服务启动
sleep 3

# 8. 验证服务是否启动成功
if curl -s http://localhost:8003/api/health > /dev/null 2>&1; then
    echo "✅ 记忆系统API服务启动成功！"
    echo "   - API地址: http://localhost:8003"
    echo "   - 健康检查: http://localhost:8003/api/health"
    echo "   - 统计信息: http://localhost:8003/api/memory/stats"
    echo "   - 进程PID: $MEMORY_PID"

    # 显示记忆统计
    echo ""
    echo "📊 记忆系统统计："
    sleep 1
    curl -s http://localhost:8003/api/memory/stats | python3 -m json.tool 2>/dev/null || echo "   无法获取统计信息"
else
    echo "❌ 记忆系统API服务启动失败！"
    echo "请检查日志文件: logs/memory_system.log"
    exit 1
fi

echo ""
echo "💡 使用示例："
echo "   # 存储记忆:"
echo "   curl -X POST http://localhost:8003/api/memory/store \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"agent_id\":\"your_agent\",\"content\":\"记忆内容\",\"memory_type\":\"conversation\"}'"
echo ""
echo "   # 检索记忆:"
echo "   curl -X POST http://localhost:8003/api/memory/recall \\"
echo "        -H 'Content-Type: application/json' \\"
echo "        -d '{\"agent_id\":\"your_agent\",\"query\":\"关键词\"}'"