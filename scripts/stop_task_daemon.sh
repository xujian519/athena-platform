#!/bin/bash
# Athena任务管理系统守护进程停止脚本

PID_FILE="/Users/xujian/Athena工作平台/logs/task_daemon.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "🛑 停止任务管理系统守护进程 (PID: $PID)"
        kill $PID
        rm -f "$PID_FILE"
        echo "✅ 任务管理系统已停止"
    else
        echo "⚠️ 任务管理系统未在运行"
    fi
else
    echo "⚠️ PID文件不存在"
fi
