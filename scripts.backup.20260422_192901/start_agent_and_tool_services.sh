#!/bin/bash
# 启动所有智能体和工具服务
# Start All Agent and Tool Services

echo "🚀 Athena智能体和工具服务启动脚本"
echo "======================================"

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 进入项目目录
cd "$PROJECT_DIR"

# 检查网关是否运行
echo ""
echo "📡 检查网关状态..."
if curl -s http://localhost:8005/health > /dev/null 2>&1; then
    echo "✅ 网关正在运行 (Port 8005)"
else
    echo "❌ 网关未运行，请先启动网关:"
    echo "   sudo /usr/local/athena-gateway/start.sh"
    echo "   或"
    echo "   cd gateway-unified && ./start.sh"
    exit 1
fi

# 启动服务函数
start_service() {
    local service_name=$1
    local service_dir=$2
    local log_file=$3

    echo ""
    echo "🔧 启动 $service_name..."

    # 检查服务目录
    if [ ! -d "$service_dir" ]; then
        echo "❌ 服务目录不存在: $service_dir"
        return 1
    fi

    # 检查是否已经运行
    if [ -f "$log_file" ]; then
        pid=$(pgrep -f "python3.*$service_dir/main.py")
        if [ -n "$pid" ]; then
            echo "⚠️ $service_name 已经在运行 (PID: $pid)"
            return 0
        fi
    fi

    # 启动服务
    cd "$service_dir"
    nohup python3 main.py > "$log_file" 2>&1 &
    local pid=$!

    # 等待服务启动
    sleep 3

    # 检查是否启动成功
    if ps -p $pid > /dev/null; then
        echo "✅ $service_name 启动成功 (PID: $pid)"
        echo "   日志文件: $log_file"
        return 0
    else
        echo "❌ $service_name 启动失败，查看日志: $log_file"
        return 1
    fi
}

# 创建日志目录
mkdir -p logs

# 启动工具注册表API
start_service \
    "工具注册表API" \
    "$PROJECT_DIR/services/tool-registry-api" \
    "$PROJECT_DIR/logs/tool-registry-api.log"

# 启动小娜智能体API
start_service \
    "小娜智能体API" \
    "$PROJECT_DIR/services/xiaona-agent-api" \
    "$PROJECT_DIR/logs/xiaona-agent-api.log"

# 启动小诺智能体API
start_service \
    "小诺智能体API" \
    "$PROJECT_DIR/services/xiaonuo-agent-api" \
    "$PROJECT_DIR/logs/xiaonuo-agent-api.log"

echo ""
echo "======================================"
echo "⏳ 等待服务完全启动..."
sleep 5

# 健康检查
echo ""
echo "🔍 服务健康检查:"

check_service() {
    local service_name=$1
    local health_url=$2

    if curl -s "$health_url" > /dev/null 2>&1; then
        echo "   ✅ $service_name"
        return 0
    else
        echo "   ❌ $service_name"
        return 1
    fi
}

check_service "工具注册表API (Port 8021)" "http://localhost:8021/health"
check_service "小娜智能体API (Port 8023)" "http://localhost:8023/health"
check_service "小诺智能体API (Port 8024)" "http://localhost:8024/health"

echo ""
echo "======================================"
echo "📝 注册服务到网关..."

# 注册服务到网关
if python3 gateway-unified/scripts/register_agent_and_tool_services.py; then
    echo "✅ 服务注册成功"
else
    echo "⚠️ 服务注册失败，请手动运行:"
    echo "   python3 gateway-unified/scripts/register_agent_and_tool_services.py"
fi

echo ""
echo "======================================"
echo "✅ 所有服务启动完成！"
echo ""
echo "📖 快速测试:"
echo ""
echo "  # 测试工具注册表"
echo "  curl http://localhost:8021/health"
echo "  curl http://localhost:8021/api/v1/tools"
echo ""
echo "  # 测试小娜"
echo "  curl http://localhost:8023/health"
echo "  curl http://localhost:8023/api/v1/xiaona/capabilities"
echo ""
echo "  # 测试小诺"
echo "  curl http://localhost:8024/health"
echo "  curl http://localhost:8024/api/v1/xiaonuo/agents"
echo ""
echo "  # 通过网关访问"
echo "  curl http://localhost:8005/api/tools"
echo "  curl http://localhost:8005/api/agents/xiaona/capabilities"
echo "  curl http://localhost:8005/api/agents/xiaonuo/agents"
echo ""
echo "📊 查看日志:"
echo "  tail -f logs/tool-registry-api.log"
echo "  tail -f logs/xiaona-agent-api.log"
echo "  tail -f logs/xiaonuo-agent-api.log"
echo ""
