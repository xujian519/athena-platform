#!/bin/bash
###############################################################################
# Athena快速启动脚本
#
# 一键启动所有Athena服务
#
# 使用: ./start_athena.sh
###############################################################################

set -e

echo "=============================================="
echo "  Athena快速启动"
echo "=============================================="
echo ""

# 1. 检查Docker
echo "1. 检查Docker..."
if ! docker ps > /dev/null 2>&1; then
    echo "   ❌ Docker未运行，请先启动Docker Desktop"
    exit 1
fi
echo "   ✅ Docker运行正常"
echo ""

# 2. 启动Docker容器
echo "2. 启动Docker容器..."
cd /Users/xujian/Athena工作平台
docker-compose -f docker-compose.unified.yml --profile dev up -d > /dev/null 2>&1
echo "   ✅ Docker容器已启动（开发环境）"
echo ""

# 3. 启动应用服务
echo "3. 启动应用服务..."
production/deploy/athena_services.sh start
echo ""

echo "=============================================="
echo "  启动完成！"
echo "=============================================="
echo ""
echo "📍 服务地址："
echo "   Gateway:     http://localhost:8005"
echo "   Prometheus:  http://localhost:9090"
echo "   Grafana:      http://localhost:3005"
echo ""
echo "📝 查看日志："
echo "   ./production/deploy/athena_services.sh logs gateway"
echo "   ./production/deploy/athena_services.sh logs agents"
echo ""
echo "🔍 查看状态："
echo "   ./production/deploy/athena_services.sh status"
echo ""
