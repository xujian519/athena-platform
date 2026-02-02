#!/bin/bash
# Athena平台Docker镜像拉取脚本
# 重新拉取项目所需的所有Docker镜像

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

echo "🐳 Athena平台 - Docker镜像拉取工具"
echo "===================================="
echo ""

# 检查Docker是否运行
if ! docker info >/dev/null 2>&1; then
    log_error "Docker未运行，请先启动Docker Desktop"
    exit 1
fi

log_success "Docker服务检查通过"

# 定义需要拉取的镜像
declare -A IMAGES=(
    # 基础数据库
    ["postgres:15-alpine"]="PostgreSQL数据库"
    ["redis:7-alpine"]="Redis缓存"
    ["qdrant/qdrant:latest"]="Qdrant向量数据库"

    # 监控服务
    ["prom/prometheus:latest"]="Prometheus监控"
    ["grafana/grafana:latest"]="Grafana仪表板"

    # Web服务器
    ["nginx:alpine"]="Nginx反向代理"

    # AI/ML相关镜像
    ["python:3.11-slim"]="Python基础镜像"
    ["python:3.9-slim"]="Python 3.9基础镜像"
    ["node:18-alpine"]="Node.js运行时"
    ["ubuntu:22.04"]="Ubuntu基础镜像"

    # 专用工具镜像
    ["elasticsearch:8.11.0"]="Elasticsearch搜索引擎"
    ["kibana:8.11.0"]="Kibana日志分析"
    ["mongodb:6.0"]="MongoDB文档数据库"
    ["mysql:8.0"]="MySQL关系数据库"

    # 容器编排工具
    ["deployment/docker/compose:latest"]="Docker Compose"
    ["portainer/portainer:latest"]="Portainer容器管理"

    # 其他工具镜像
    ["redis:6-alpine"]="Redis 6.x版本"
    ["postgres:14-alpine"]="PostgreSQL 14版本"
    ["nginx:1.21-alpine"]="Nginx 1.21版本"
)

# 统计信息
total_images=${#IMAGES[@]}
pulled_count=0
failed_count=0

log_info "准备拉取 ${total_images} 个Docker镜像..."
echo ""

# 拉取镜像
for image in "${!IMAGES[@]}"; do
    description="${IMAGES[$image]}"
    log_info "拉取镜像: ${image} (${description})"

    if docker pull "${image}" >/dev/null 2>&1; then
        log_success "✓ ${image} 拉取成功"
        ((pulled_count++))
    else
        log_warning "✗ ${image} 拉取失败，将跳过"
        ((failed_count++))
    fi

    # 显示进度
    progress=$((pulled_count + failed_count))
    percentage=$((progress * 100 / total_images))
    echo -e "进度: ${progress}/${total_images} (${percentage}%)"
    echo ""
done

# 显示最终结果
echo "===================================="
log_info "镜像拉取完成！"
echo ""

echo "📊 统计信息:"
echo "   总镜像数: ${total_images}"
echo "   成功拉取: ${pulled_count}"
echo "   拉取失败: ${failed_count}"
echo ""

if [ $pulled_count -eq $total_images ]; then
    log_success "🎉 所有镜像拉取成功！"
elif [ $pulled_count -gt 0 ]; then
    log_warning "⚠️ 部分镜像拉取成功，系统基本可用"
else
    log_error "❌ 所有镜像拉取失败，请检查网络连接"
fi

echo ""
echo "📋 当前可用镜像列表:"
docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo "🚀 下一步操作建议:"
echo "1. 启动基础服务: docker-compose up -d postgres redis qdrant"
echo "2. 启动监控系统: docker-compose up -d prometheus grafana"
echo "3. 启动应用服务: docker-compose up -d"
echo ""
echo "📖 查看镜像详情: docker images"
echo "📖 查看容器状态: docker ps -a"

# 清理无用镜像（可选）
echo ""
read -p "是否清理无用镜像和容器？(y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    log_info "正在清理无用资源..."
    docker system prune -f
    log_success "清理完成"
fi

echo ""
log_success "脚本执行完成！"