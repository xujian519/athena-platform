#!/bin/bash
# 停止所有智能体和工具服务
# Stop All Agent and Tool Services

echo "🛑 停止Athena智能体和工具服务"
echo "======================================"

# 停止函数
stop_service() {
    local service_name=$1
    local pattern=$2

    echo ""
    echo "🛑 停止 $service_name..."

    local pids=$(pgrep -f "$pattern")

    if [ -z "$pids" ]; then
        echo "⚠️ $service_name 未运行"
        return 0
    fi

    # 优雅停止
    for pid in $pids; do
        if kill $pid 2>/dev/null; then
            echo "   ✅ 已停止 $service_name (PID: $pid)"
        else
            echo "   ⚠️ 无法停止 PID $pid"
        fi
    done

    # 等待进程结束
    sleep 2

    # 强制杀死残留进程
    local remaining=$(pgrep -f "$pattern")
    if [ -n "$remaining" ]; then
        echo "   ⚠️ 强制停止残留进程..."
        pkill -9 -f "$pattern"
    fi
}

# 停止工具注册表API
stop_service "工具注册表API" "tool-registry-api/main.py"

# 停止小娜智能体API
stop_service "小娜智能体API" "xiaona-agent-api/main.py"

# 停止小诺智能体API
stop_service "小诺智能体API" "xiaonuo-agent-api/main.py"

echo ""
echo "======================================"
echo "✅ 所有服务已停止"
echo ""
