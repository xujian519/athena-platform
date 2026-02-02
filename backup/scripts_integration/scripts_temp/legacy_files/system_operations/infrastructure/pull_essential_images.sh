#!/bin/bash
# Athena平台核心Docker镜像快速拉取脚本
# 只拉取项目运行所需的核心镜像

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }

echo "⚡ Athena平台 - 核心镜像快速拉取"
echo "==============================="
echo ""

# 核心镜像列表（按优先级排序）
CORE_IMAGES=(
    "postgres:15-alpine"
    "redis:7-alpine"
    "qdrant/qdrant:latest"
    "prom/prometheus:latest"
    "grafana/grafana:latest"
    "nginx:alpine"
    "python:3.11-slim"
    "node:18-alpine"
)

log_info "开始拉取 ${#CORE_IMAGES[@]} 个核心镜像..."
echo ""

# 拉取核心镜像
for image in "${CORE_IMAGES[@]}"; do
    log_info "正在拉取: ${image}"
    if docker pull "${image}" >/dev/null 2>&1; then
        log_success "✓ ${image} 拉取成功"
    else
        echo "❌ ${image} 拉取失败，跳过..."
    fi
    echo ""
done

log_success "核心镜像拉取完成！"
echo ""

echo "🚀 现在可以启动Athena服务："
echo "   docker-compose up -d postgres redis qdrant"
echo "   docker-compose up -d prometheus grafana"
echo ""
echo "📖 查看已拉取的镜像："
echo "   docker images