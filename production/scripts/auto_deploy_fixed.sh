#!/bin/bash
###############################################################################
# 生产环境自动部署脚本（增强版）
# Automated Production Deployment (Enhanced)
#
# 功能：自动执行生产环境部署，处理镜像构建
#   - 加载环境变量
#   - 构建Gateway镜像
#   - 启动所有服务
#
# 使用: ./production/scripts/auto_deploy_fixed.sh
#
# 作者: Athena AI系统
# 创建时间: 2026-04-18
###############################################################################

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

# 颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[⚠]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

echo "=========================================="
echo "Athena平台生产环境自动部署（增强版）"
echo "=========================================="
echo ""

# 加载环境变量
if [ -f "${PROJECT_ROOT}/.env.production" ]; then
    log_info "加载环境变量..."
    set -a
    source "${PROJECT_ROOT}/.env.production"
    set +a
    log_success "环境变量已加载"
fi

# 设置默认值
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-athena_prod_pass_$(openssl rand -hex 8)}
export REDIS_PASSWORD=${REDIS_PASSWORD:-redis_prod_pass_$(openssl rand -hex 8)}
export NEO4J_PASSWORD=${NEO4J_PASSWORD:-neo4j_prod_pass_$(openssl rand -hex 8)}
export GRAFANA_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin123}
export QDRANT_API_KEY=${QDRANT_API_KEY:-$(openssl rand -hex 32)}

# ============================================================================
# 步骤 1: 创建目录结构
# ============================================================================
log_info "步骤 1/5: 创建目录结构..."
mkdir -p "${PROJECT_ROOT}/logs/production"
mkdir -p "${PROJECT_ROOT}/data/production"
mkdir -p "${PROJECT_ROOT}/backups/production"
mkdir -p "${PROJECT_ROOT}/models"
mkdir -p "${PROJECT_ROOT}/monitoring/data"
log_success "目录结构已创建"

# ============================================================================
# 步骤 2: 构建Gateway镜像
# ============================================================================
log_info "步骤 2/5: 构建Gateway镜像..."

if [ -d "${PROJECT_ROOT}/gateway-unified" ]; then
    cd "${PROJECT_ROOT}/gateway-unified"

    if [ -f "Makefile" ]; then
        log_info "使用Makefile构建..."
        make docker-build 2>/dev/null || {
            log_warning "Makefile构建失败，尝试手动构建..."
            docker build -t athena-gateway:latest . 2>&1 | tail -5
        }
    else
        log_info "手动构建Gateway镜像..."
        docker build -t athena-gateway:latest . 2>&1 | tail -5
    fi

    log_success "Gateway镜像构建完成"
    cd "${PROJECT_ROOT}"
else
    log_warning "gateway-unified目录不存在，跳过Gateway构建"
fi

# ============================================================================
# 步骤 3: 停止现有服务
# ============================================================================
log_info "步骤 3/5: 停止现有服务..."
docker-compose -f docker-compose.production.yml down 2>/dev/null || true
log_success "现有服务已停止"

# ============================================================================
# 步骤 4: 启动生产服务
# ============================================================================
log_info "步骤 4/5: 启动生产服务..."
docker-compose -f docker-compose.production.yml up -d

log_success "服务启动完成"
echo ""
log_info "等待服务就绪..."
sleep 15

# ============================================================================
# 步骤 5: 显示服务状态
# ============================================================================
log_info "步骤 5/5: 检查服务状态..."

echo ""
echo "=========================================="
echo "服务状态"
echo "=========================================="
docker-compose -f docker-compose.production.yml ps

# ============================================================================
# 完成
# ============================================================================
echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "📊 服务访问地址："
echo "  - Gateway: http://localhost:8005"
echo "  - Grafana: http://localhost:3000 (admin/admin123)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Alertmanager: http://localhost:9093"
echo ""
echo "🗄️  数据库访问："
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Qdrant: http://localhost:6333"
echo "  - Neo4j: http://localhost:7474"
echo ""
echo "🔧 常用命令："
echo "  - 查看日志: docker-compose -f docker-compose.production.yml logs -f"
echo "  - 健康检查: ./production/scripts/health_check.sh"
echo "  - 停止服务: docker-compose -f docker-compose.production.yml down"
echo "  - 重启服务: docker-compose -f docker-compose.production.yml restart"
echo ""
