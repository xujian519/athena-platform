#!/bin/bash
# Athena Gateway 停止脚本

echo "🛑 停止 Athena Gateway..."

# 查找并停止进程
GATEWAY_PID=$(pgrep -f "bin/gateway|athena-gateway" || true)

if [ -n "$GATEWAY_PID" ]; then
    echo "找到进程 PID: $GATEWAY_PID"
    kill $GATEWAY_PID 2>/dev/null || true
    sleep 1

    # 如果进程仍在运行，强制停止
    if pgrep -f "bin/gateway|athena-gateway" > /dev/null 2>&1; then
        echo "强制停止进程..."
        pkill -9 -f "bin/gateway" 2>/dev/null || true
        pkill -9 -f "athena-gateway" 2>/dev/null || true
    fi

    echo "✅ Gateway 已停止"
else
    echo "ℹ️  Gateway 未运行"
fi
