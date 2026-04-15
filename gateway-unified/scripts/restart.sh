#!/bin/bash
# Athena Gateway 重启脚本

echo "🔄 重启 Athena Gateway..."

# 停止
cd "$(dirname "$0")"
./stop.sh

# 等待进程完全退出
sleep 1

# 启动
./start.sh
