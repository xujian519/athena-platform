#!/bin/bash
# 启动所有核心服务

echo "🚀 启动Athena核心服务..."

# 创建日志目录
mkdir -p logs

# 启动健康检查服务
echo "启动健康检查服务..."
cd health-checker
python main.py > ../logs/health-checker.log 2>&1 &
HEALTH_PID=$!
echo "健康检查服务 PID: $HEALTH_PID"

# 启动缓存服务
echo "启动缓存服务..."
cd ../cache
python cache_server.py > ../logs/cache.log 2>&1 &
CACHE_PID=$!
echo "缓存服务 PID: $CACHE_PID"

# 启动平台监控服务
echo "启动平台监控服务..."
cd ../platform-monitor
python main.py > ../logs/platform-monitor.log 2>&1 &
MONITOR_PID=$!
echo "平台监控服务 PID: $MONITOR_PID"

# 保存PID
echo $HEALTH_PID > ../logs/health-checker.pid
echo $CACHE_PID > ../logs/cache.pid
echo $MONITOR_PID > ../logs/platform-monitor.pid

echo "✅ 所有核心服务已启动"
echo "健康检查: http://localhost:9001/health"
echo "缓存服务: http://localhost:9002/status"
echo "平台监控: http://localhost:9003/metrics"