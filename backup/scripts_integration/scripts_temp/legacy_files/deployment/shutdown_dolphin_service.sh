#!/bin/bash
# Dolphin文档解析服务停止脚本

echo "🛑 停止Dolphin文档解析服务..."

PID_DIR="/tmp/athena_pids"
DOLPHIN_PID_FILE="$PID_DIR/dolphin_parser.pid"

if [ -f "$DOLPHIN_PID_FILE" ]; then
    DOLPHIN_PID=$(cat "$DOLPHIN_PID_FILE")
    if kill -0 $DOLPHIN_PID 2>/dev/null; then
        echo "停止服务 (PID: $DOLPHIN_PID)..."
        kill $DOLPHIN_PID 2>/dev/null || true

        # 等待进程结束
        sleep 3

        # 强制杀死（如果还在运行）
        if kill -0 $DOLPHIN_PID 2>/dev/null; then
            echo "强制停止服务..."
            kill -9 $DOLPHIN_PID 2>/dev/null || true
        fi

        echo "✅ Dolphin文档解析服务已停止"
    else
        echo "⚠️  服务进程不存在"
    fi

    rm -f "$DOLPHIN_PID_FILE"
else
    echo "⚠️  PID文件不存在，服务可能未运行"
fi

# 清理临时目录
echo "🧹 清理临时目录..."
TEMP_DIRS="/tmp/dolphin_uploads /tmp/dolphin_processed /tmp/dolphin_cache"
for dir in $TEMP_DIRS; do
    if [ -d "$dir" ]; then
        rm -rf "$dir"/*
        echo "✅ 清理 $dir"
    fi
done

echo "🎉 清理完成"
