#!/bin/bash
###############################################################################
# Athena快速停止脚本
#
# 一键停止所有Athena服务
#
# 使用: ./stop_athena.sh
###############################################################################

set -e

echo "=============================================="
echo "  Athena快速停止"
echo "=============================================="
echo ""

# 1. 停止应用服务
echo "1. 停止应用服务..."
cd /Users/xujian/Athena工作平台
production/deploy/athena_services.sh stop
echo ""

# 2. 停止Docker容器（可选）
echo "2. 停止Docker容器？"
read -p "   是否停止Docker容器？(y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "   正在停止Docker容器（开发环境）..."
    docker-compose -f docker-compose.unified.yml --profile dev down
    echo "   ✅ Docker容器已停止"
else
    echo "   ⏭️  Docker容器保持运行"
fi

echo ""
echo "=============================================="
echo "  停止完成！"
echo "=============================================="
echo ""
