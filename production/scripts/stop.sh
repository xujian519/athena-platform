#!/bin/bash
###############################################################################
# 停止生产环境服务
###############################################################################

set -e

echo "=== 停止生产环境服务 ==="

# 停止执行引擎
if [ -f "production/pids/execution_engine.pid" ]; then
    PID=$(cat production/pids/execution_engine.pid)
    echo "停止执行引擎 (PID: $PID)..."

    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        sleep 2

        # 如果还在运行，强制停止
        if ps -p $PID > /dev/null 2>&1; then
            echo "强制停止..."
            kill -9 $PID
        fi
    fi

    rm -f production/pids/execution_engine.pid
    echo "✅ 执行引擎已停止"
else
    echo "⚠️  执行引擎未运行"
fi

echo ""
echo "所有服务已停止"
