#!/bin/bash
# 小诺服务停止脚本

echo "停止小诺服务..."

# 读取PID文件并终止进程
PID_FILE="/Users/xujian/Athena工作平台/pids/xiaonuo/health_check.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "终止进程 $PID..."
        kill -TERM "$PID"
        sleep 2
        if kill -0 "$PID" 2>/dev/null; then
            echo "强制终止进程 $PID..."
            kill -KILL "$PID"
        fi
    fi
    rm -f "$PID_FILE"
    echo "服务已停止"
else
    echo "服务未运行"
fi
