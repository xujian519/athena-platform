#!/bin/bash
# 小诺服务启动脚本

export PYTHONPATH="/Users/xujian/Athena工作平台"
export XIAONUO_DATA_DIR="/Users/xujian/Athena工作平台/data/xiaonuo"
export XIAONUO_LOG_DIR="/Users/xujian/Athena工作平台/logs/xiaonuo"

# 启动健康检查服务
cd /Users/xujian/Athena工作平台
python3 production/services/health_check.py &
echo $! > /Users/xujian/Athena工作平台/pids/xiaonuo/health_check.pid

echo "小诺健康检查服务已启动"
echo "监听地址: http://127.0.0.1:8099"
echo "健康检查: http://127.0.0.1:8099/health"
