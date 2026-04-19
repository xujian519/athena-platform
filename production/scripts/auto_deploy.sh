#!/bin/bash
###############################################################################
# 生产环境自动部署脚本（非交互式）
# Automated Production Deployment
#
# 功能：自动执行生产环境部署，无需人工干预
#   - 生成安全密钥
#   - 创建目录结构
#   - 验证配置
#   - 启动服务
#
# 使用: ./production/scripts/auto_deploy.sh
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
echo "Athena平台生产环境自动部署"
echo "=========================================="
echo ""

# ============================================================================
# 1. 验证环境
# ============================================================================
log_info "步骤 1/7: 验证部署环境..."

# 检查Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker未安装，请先安装Docker"
    exit 1
fi
log_success "Docker已安装: $(docker --version | head -1)"

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose未安装，请先安装Docker Compose"
    exit 1
fi
log_success "Docker Compose已就绪"

# 检查配置文件
if [ ! -f "${PROJECT_ROOT}/.env.production" ]; then
    log_error ".env.production配置文件不存在"
    exit 1
fi
log_success "配置文件存在"

# ============================================================================
# 2. 检查并更新配置文件
# ============================================================================
log_info "步骤 2/7: 检查配置文件..."

# 检查是否还有占位符
if grep -q "CHANGE_ME" "${PROJECT_ROOT}/.env.production" 2>/dev/null; then
    log_warning "发现配置占位符，正在生成安全密钥..."

    # 生成强密码
    POSTGRES_PASSWORD=$(openssl rand -hex 16)
    REDIS_PASSWORD=$(openssl rand -hex 16)
    NEO4J_PASSWORD=$(openssl rand -hex 16)
    QDRANT_API_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)

    # 备份原配置
    cp "${PROJECT_ROOT}/.env.production" "${PROJECT_ROOT}/.env.production.backup"

    # 更新配置
    sed -i.bak "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=${POSTGRES_PASSWORD}/" "${PROJECT_ROOT}/.env.production"
    sed -i.bak "s/DB_PASSWORD=.*/DB_PASSWORD=${POSTGRES_PASSWORD}/" "${PROJECT_ROOT}/.env.production"
    sed -i.bak "s/REDIS_PASSWORD=.*/REDIS_PASSWORD=${REDIS_PASSWORD}/" "${PROJECT_ROOT}/.env.production"
    sed -i.bak "s/NEO4J_PASSWORD=.*/NEO4J_PASSWORD=${NEO4J_PASSWORD}/" "${PROJECT_ROOT}/.env.production"
    sed -i.bak "s|QDRANT_API_KEY=.*|QDRANT_API_KEY=${QDRANT_API_KEY}|" "${PROJECT_ROOT}/.env.production"

    log_success "安全密钥已生成并更新"

    # 保存密钥信息
    cat > "${PROJECT_ROOT}/production/SECRET_KEYS.txt" <<EOF
# Athena平台生产环境密钥信息
# 生成时间: $(date)
# ⚠️ 请妥善保管此文件，不要提交到Git仓库

PostgreSQL密码: ${POSTGRES_PASSWORD}
Redis密码: ${REDIS_PASSWORD}
Neo4j密码: ${NEO4J_PASSWORD}
Qdrant API Key: ${QDRANT_API_KEY}
JWT Secret: ${JWT_SECRET}

数据库连接字符串:
- PostgreSQL: postgresql://athena:${POSTGRES_PASSWORD}@localhost:5432/athena_production
- Redis: redis://:${REDIS_PASSWORD}@localhost:6379
- Neo4j: bolt://neo4j:${NEO4J_PASSWORD}@localhost:7687
EOF

    log_warning "密钥已保存到: production/SECRET_KEYS.txt"
    log_warning "请将此文件保存到安全位置"
else
    log_success "配置文件检查通过，无占位符"
fi

# ============================================================================
# 3. 创建目录结构
# ============================================================================
log_info "步骤 3/7: 创建目录结构..."

mkdir -p "${PROJECT_ROOT}/logs/production"
mkdir -p "${PROJECT_ROOT}/data/production"
mkdir -p "${PROJECT_ROOT}/backups/production"
mkdir -p "${PROJECT_ROOT}/models"
mkdir -p "${PROJECT_ROOT}/monitoring/data"

log_success "目录结构已创建"

# ============================================================================
# 4. 设置文件权限
# ============================================================================
log_info "步骤 4/7: 设置文件权限..."

chmod 600 "${PROJECT_ROOT}/.env.production" 2>/dev/null || true
chmod +x "${PROJECT_ROOT}/production/scripts/"*.sh 2>/dev/null || true
chmod -R 755 "${PROJECT_ROOT}/production/scripts/" 2>/dev/null || true

log_success "文件权限已设置"

# ============================================================================
# 5. 验证Docker Compose配置
# ============================================================================
log_info "步骤 5/7: 验证Docker Compose配置..."

if [ -f "${PROJECT_ROOT}/docker-compose.production.yml" ]; then
    cd "${PROJECT_ROOT}"
    docker-compose -f docker-compose.production.yml config > /dev/null
    log_success "Docker Compose配置验证通过"
else
    log_warning "docker-compose.production.yml不存在，跳过验证"
fi

# ============================================================================
# 6. 停止现有服务（如存在）
# ============================================================================
log_info "步骤 6/7: 停止现有服务..."

if [ -f "${PROJECT_ROOT}/docker-compose.production.yml" ]; then
    cd "${PROJECT_ROOT}"
    docker-compose -f docker-compose.production.yml down 2>/dev/null || true
    log_success "现有服务已停止"
fi

# ============================================================================
# 7. 启动生产服务
# ============================================================================
log_info "步骤 7/7: 启动生产服务..."

if [ -f "${PROJECT_ROOT}/docker-compose.production.yml" ]; then
    cd "${PROJECT_ROOT}"
    docker-compose -f docker-compose.production.yml up -d

    log_success "服务启动完成"
    echo ""
    log_info "等待服务就绪..."
    sleep 10

    # 显示服务状态
    echo ""
    echo "=========================================="
    echo "服务状态"
    echo "=========================================="
    docker-compose -f docker-compose.production.yml ps
else
    log_error "docker-compose.production.yml不存在"
    exit 1
fi

# ============================================================================
# 完成
# ============================================================================
echo ""
echo "=========================================="
echo -e "${GREEN}部署完成！${NC}"
echo "=========================================="
echo ""
echo "服务访问地址："
echo "  - Gateway: http://localhost:8005"
echo "  - Grafana: http://localhost:3000 (admin/admin123)"
echo "  - Prometheus: http://localhost:9090"
echo "  - Alertmanager: http://localhost:9093"
echo ""
echo "数据库访问："
echo "  - PostgreSQL: localhost:5432"
echo "  - Redis: localhost:6379"
echo "  - Qdrant: http://localhost:6333"
echo "  - Neo4j: http://localhost:7474"
echo ""
echo "常用命令："
echo "  - 查看日志: docker-compose -f docker-compose.production.yml logs -f"
echo "  - 健康检查: ./production/scripts/health_check.sh"
echo "  - 停止服务: docker-compose -f docker-compose.production.yml down"
echo "  - 重启服务: docker-compose -f docker-compose.production.yml restart"
echo ""
if [ -f "${PROJECT_ROOT}/production/SECRET_KEYS.txt" ]; then
    log_warning "重要：请查看并保存密钥信息: production/SECRET_KEYS.txt"
fi
echo ""
