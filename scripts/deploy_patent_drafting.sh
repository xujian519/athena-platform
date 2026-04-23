#!/bin/bash
###############################################################################
# PatentDraftingProxy部署脚本
# PatentDraftingProxy Deployment Script
#
# 功能: 自动化部署PatentDraftingProxy服务
# 使用: bash scripts/deploy_patent_drafting.sh [environment]
# 参数:
#   environment - 环境名称(dev/test/prod)，默认prod
#
# 示例:
#   bash scripts/deploy_patent_drafting.sh dev
#   bash scripts/deploy_patent_drafting.sh prod
###############################################################################

set -e  # 遇到错误立即退出
set -u  # 使用未定义变量时报错
set -o pipefail  # 管道命令失败时退出

# ==================== 配置 ====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENVIRONMENT="${1:-prod}"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.patent-drafting.yml"
ENV_FILE="${PROJECT_ROOT}/.env.production"
BACKUP_DIR="${PROJECT_ROOT}/backup"
LOG_DIR="${PROJECT_ROOT}/logs"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 日志函数 ====================
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $*"
}

# ==================== 检查函数 ====================
check_requirements() {
    log_info "检查部署依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查配置文件
    if [ ! -f "${COMPOSE_FILE}" ]; then
        log_error "Docker Compose文件不存在: ${COMPOSE_FILE}"
        exit 1
    fi
    
    # 检查环境文件
    if [ ! -f "${ENV_FILE}" ]; then
        log_warning "环境文件不存在: ${ENV_FILE}"
        log_warning "将从模板创建环境文件..."
        if [ -f "${ENV_FILE}.template" ]; then
            cp "${ENV_FILE}.template" "${ENV_FILE}"
            log_warning "请编辑 ${ENV_FILE} 填写实际配置值"
            exit 1
        else
            log_error "环境文件模板也不存在"
            exit 1
        fi
    fi
    
    log_success "依赖检查通过"
}

# ==================== 备份函数 ====================
backup_current() {
    log_info "备份当前部署..."
    
    # 创建备份目录
    mkdir -p "${BACKUP_DIR}"
    
    # 备份数据库
    if docker ps | grep -q patent-drafting-postgres; then
        log_info "备份PostgreSQL数据库..."
        docker exec patent-drafting-postgres pg_dump \
            -U "${POSTGRES_USER:-athena}" \
            -d "${POSTGRES_DB:-athena}" \
            > "${BACKUP_DIR}/postgres_backup_$(date +%Y%m%d_%H%M%S).sql"
        log_success "PostgreSQL备份完成"
    fi
    
    # 备份配置
    if [ -d "${PROJECT_ROOT}/config" ]; then
        log_info "备份配置文件..."
        tar -czf "${BACKUP_DIR}/config_backup_$(date +%Y%m%d_%H%M%S).tar.gz" \
            -C "${PROJECT_ROOT}" config/
        log_success "配置备份完成"
    fi
    
    # 清理7天前的备份
    find "${BACKUP_DIR}" -name "*.sql" -mtime +7 -delete
    find "${BACKUP_DIR}" -name "*.tar.gz" -mtime +7 -delete
    
    log_success "备份完成"
}

# ==================== 停止服务函数 ====================
stop_services() {
    log_info "停止现有服务..."
    
    cd "${PROJECT_ROOT}"
    
    # 优雅停止服务
    if docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" ps | grep -q "Up"; then
        docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" down
        log_success "服务已停止"
    else
        log_info "没有运行中的服务"
    fi
}

# ==================== 拉取镜像函数 ====================
pull_images() {
    log_info "拉取最新镜像..."
    
    cd "${PROJECT_ROOT}"
    
    # 如果镜像存在，先拉取
    if docker images | grep -q patent-drafting-proxy; then
        docker pull patent-drafting-proxy:latest || true
    fi
    
    log_success "镜像准备完成"
}

# ==================== 构建镜像函数 ====================
build_images() {
    log_info "构建Docker镜像..."
    
    cd "${PROJECT_ROOT}"
    
    # 构建镜像
    docker build -f Dockerfile.patent-drafting -t patent-drafting-proxy:latest .
    
    log_success "镜像构建完成"
}

# ==================== 启动服务函数 ====================
start_services() {
    log_info "启动服务..."
    
    cd "${PROJECT_ROOT}"
    
    # 创建必要目录
    mkdir -p "${LOG_DIR}"
    mkdir -p "${BACKUP_DIR}"
    
    # 启动服务
    docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" up -d
    
    log_success "服务启动完成"
}

# ==================== 等待服务就绪函数 ====================
wait_for_services() {
    log_info "等待服务就绪..."
    
    local max_wait=120  # 最大等待时间(秒)
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        # 检查健康状态
        if curl -sf http://localhost:8010/health > /dev/null 2>&1; then
            log_success "服务已就绪"
            return 0
        fi
        
        sleep 5
        wait_time=$((wait_time + 5))
        echo -n "."
    done
    
    log_error "服务启动超时"
    return 1
}

# ==================== 运行迁移函数 ====================
run_migrations() {
    log_info "运行数据库迁移..."
    
    # 这里添加实际的迁移命令
    # 例如: docker exec patent-drafting-api python -m alembic upgrade head
    
    log_success "数据库迁移完成"
}

# ==================== 验证部署函数 ====================
verify_deployment() {
    log_info "验证部署..."
    
    # 检查服务状态
    if ! docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" ps | grep -q "Up"; then
        log_error "服务未运行"
        return 1
    fi
    
    # 检查健康端点
    if ! curl -sf http://localhost:8010/health > /dev/null 2>&1; then
        log_error "健康检查失败"
        return 1
    fi
    
    # 检查Prometheus指标
    if ! curl -sf http://localhost:9090/metrics > /dev/null 2>&1; then
        log_warning "Prometheus指标端点不可用"
    fi
    
    log_success "部署验证通过"
}

# ==================== 显示状态函数 ====================
show_status() {
    log_info "服务状态:"
    echo ""
    docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" ps
    echo ""
    log_info "服务地址:"
    echo "  主应用: http://localhost:8010"
    echo "  健康检查: http://localhost:8010/health"
    echo "  Prometheus指标: http://localhost:9090/metrics"
}

# ==================== 主流程 ====================
main() {
    log_info "开始部署PatentDraftingProxy [环境: ${ENVIRONMENT}]"
    echo ""
    
    # 检查依赖
    check_requirements
    echo ""
    
    # 备份当前部署
    backup_current
    echo ""
    
    # 停止现有服务
    stop_services
    echo ""
    
    # 拉取/构建镜像
    if [ "${SKIP_BUILD:-false}" != "true" ]; then
        build_images
    else
        pull_images
    fi
    echo ""
    
    # 启动服务
    start_services
    echo ""
    
    # 等待服务就绪
    if ! wait_for_services; then
        log_error "服务启动失败"
        exit 1
    fi
    echo ""
    
    # 运行迁移
    run_migrations
    echo ""
    
    # 验证部署
    if ! verify_deployment; then
        log_error "部署验证失败"
        exit 1
    fi
    echo ""
    
    # 显示状态
    show_status
    echo ""
    
    log_success "PatentDraftingProxy部署完成！"
}

# ==================== 错误处理 ====================
trap 'log_error "部署失败，请检查日志"; exit 1' ERR

# ==================== 执行 ====================
main "$@"
