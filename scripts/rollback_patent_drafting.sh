#!/bin/bash
###############################################################################
# PatentDraftingProxy回滚脚本
# PatentDraftingProxy Rollback Script
#
# 功能: 回滚PatentDraftingProxy到上一个版本
# 使用: bash scripts/rollback_patent_drafting.sh [environment]
# 参数:
#   environment - 环境名称(dev/test/prod)，默认prod
#
# 示例:
#   bash scripts/rollback_patent_drafting.sh prod
###############################################################################

set -e
set -u
set -o pipefail

# ==================== 配置 ====================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENVIRONMENT="${1:-prod}"
COMPOSE_FILE="${PROJECT_ROOT}/docker-compose.patent-drafting.yml"
BACKUP_DIR="${PROJECT_ROOT}/backup"
LOG_DIR="${PROJECT_ROOT}/logs"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# ==================== 确认函数 ====================
confirm_rollback() {
    echo ""
    log_warning "⚠️  警告: 即将回滚PatentDraftingProxy到上一个版本"
    echo ""
    read -p "确认要继续吗? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        log_info "回滚已取消"
        exit 0
    fi
}

# ==================== 停止服务函数 ====================
stop_services() {
    log_info "停止当前服务..."
    
    cd "${PROJECT_ROOT}"
    
    if docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" ps | grep -q "Up"; then
        docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" down
        log_success "服务已停止"
    else
        log_info "没有运行中的服务"
    fi
}

# ==================== 恢复数据库函数 ====================
restore_database() {
    log_info "查找最近的数据库备份..."
    
    local latest_backup=$(ls -t "${BACKUP_DIR}"/postgres_backup_*.sql 2>/dev/null | head -1)
    
    if [ -z "${latest_backup}" ]; then
        log_error "未找到数据库备份"
        return 1
    fi
    
    log_info "找到备份: ${latest_backup}"
    log_info "恢复数据库..."
    
    # 启动PostgreSQL容器
    cd "${PROJECT_ROOT}"
    docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" up -d postgres
    
    # 等待PostgreSQL就绪
    sleep 10
    
    # 恢复数据
    docker exec -i patent-drafting-postgres psql \
        -U "${POSTGRES_USER:-athena}" \
        -d "${POSTGRES_DB:-athena}" \
        < "${latest_backup}"
    
    log_success "数据库恢复完成"
}

# ==================== 恢复配置函数 ====================
restore_config() {
    log_info "查找最近的配置备份..."
    
    local latest_backup=$(ls -t "${BACKUP_DIR}"/config_backup_*.tar.gz 2>/dev/null | head -1)
    
    if [ -z "${latest_backup}" ]; then
        log_warning "未找到配置备份"
        return 0
    fi
    
    log_info "找到备份: ${latest_backup}"
    log_info "恢复配置..."
    
    # 备份当前配置
    if [ -d "${PROJECT_ROOT}/config" ]; then
        mv "${PROJECT_ROOT}/config" "${PROJECT_ROOT}/config.before_rollback"
    fi
    
    # 恢复配置
    tar -xzf "${latest_backup}" -C "${PROJECT_ROOT}"
    
    log_success "配置恢复完成"
}

# ==================== 切换到上一个版本函数 ====================
switch_to_previous_version() {
    log_info "切换到上一个Docker镜像版本..."
    
    # 查找所有镜像版本
    local images=$(docker images | grep patent-drafting-proxy | awk '{print $2}')
    local current_image=$(docker ps --filter "name=patent-drafting-api" --format "{{.Image}}" || echo "")
    
    if [ -z "${current_image}" ]; then
        log_error "无法确定当前镜像版本"
        return 1
    fi
    
    log_info "当前镜像: ${current_image}"
    
    # 这里需要根据实际的镜像管理策略来实现
    # 例如: 使用docker tag切换到上一个版本的镜像
    
    log_warning "请手动切换Docker镜像到上一个版本"
    log_warning "然后重新运行此脚本的其余部分"
}

# ==================== 启动服务函数 ====================
start_services() {
    log_info "启动服务..."
    
    cd "${PROJECT_ROOT}"
    
    docker compose -f "${COMPOSE_FILE}" --profile "${ENVIRONMENT}" up -d
    
    log_success "服务启动完成"
}

# ==================== 验证回滚函数 ====================
verify_rollback() {
    log_info "验证回滚..."
    
    local max_wait=120
    local wait_time=0
    
    while [ $wait_time -lt $max_wait ]; do
        if curl -sf http://localhost:8010/health > /dev/null 2>&1; then
            log_success "回滚成功，服务已恢复"
            return 0
        fi
        
        sleep 5
        wait_time=$((wait_time + 5))
        echo -n "."
    done
    
    log_error "回滚验证失败，服务未正常启动"
    return 1
}

# ==================== 显示回滚信息函数 ====================
show_rollback_info() {
    echo ""
    log_info "回滚信息:"
    echo "  回滚时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "  环境: ${ENVIRONMENT}"
    echo ""
    log_warning "如果回滚失败，请检查日志:"
    echo "  docker logs patent-drafting-api"
    echo "  docker compose -f ${COMPOSE_FILE} logs"
}

# ==================== 主流程 ====================
main() {
    log_info "开始回滚PatentDraftingProxy [环境: ${ENVIRONMENT}]"
    echo ""
    
    # 确认回滚
    confirm_rollback
    echo ""
    
    # 停止服务
    stop_services
    echo ""
    
    # 恢复数据库
    if ! restore_database; then
        log_error "数据库恢复失败"
        exit 1
    fi
    echo ""
    
    # 恢复配置
    restore_config
    echo ""
    
    # 切换版本(需要手动完成)
    switch_to_previous_version
    echo ""
    
    # 启动服务
    start_services
    echo ""
    
    # 验证回滚
    if ! verify_rollback; then
        log_error "回滚失败"
        show_rollback_info
        exit 1
    fi
    echo ""
    
    log_success "PatentDraftingProxy回滚完成！"
    show_rollback_info
}

# ==================== 错误处理 ====================
trap 'log_error "回滚失败，请检查日志"; exit 1' ERR

# ==================== 执行 ====================
main "$@"
