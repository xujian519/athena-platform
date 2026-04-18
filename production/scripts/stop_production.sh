#!/bin/bash
# Rust缓存生产环境停止脚本

PROJECT_ROOT="/Users/xujian/Athena工作平台"
PID_FILE="$PROJECT_ROOT/production/rust_cache.pid"

echo "停止Athena Rust缓存服务..."

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  PID文件不存在，服务可能未运行"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ps -p $PID > /dev/null 2>&1; then
    echo "停止服务 (PID: $PID)..."
    kill $PID

    # 等待进程结束
    for i in {1..10}; do
        if ! ps -p $PID > /dev/null 2>&1; then
            echo "✅ 服务已停止"
            rm -f "$PID_FILE"
            exit 0
        fi
        sleep 1
    done

    # 强制结束
    echo "强制停止服务..."
    kill -9 $PID
    rm -f "$PID_FILE"
    echo "✅ 服务已强制停止"
else
    echo "⚠️  进程不存在 (PID: $PID)"
    rm -f "$PID_FILE"
fi
