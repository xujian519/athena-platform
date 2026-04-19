#!/bin/bash
# 停止监控系统

PID_FILE="/Users/xujian/Athena工作平台/production/logs/infrastructure/infrastructure/monitoring/daemon.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    echo "🛑 停止监控系统 (PID: $PID)"
    kill $PID
    rm "$PID_FILE"
    echo "✅ 监控系统已停止"
else
    echo "❌ 监控系统未运行"
fi
