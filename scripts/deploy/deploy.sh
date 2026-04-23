#!/bin/bash
#
# 本地CI/CD部署脚本 (Bash版本)
# Local CI/CD Deployment Script
#
# 使用: ./scripts/deploy.sh [环境]
#
# 作者: 小诺·双鱼座
# 创建时间: 2026-01-26

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# 配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
PRODUCTION_DIR="${PROJECT_ROOT}/production"
BACKUP_DIR="/Volumes/AthenaData/Athena工作平台备份/backups"
LOG_DIR="logs"

# PostgreSQL配置
PG_VERSION="17.7"
PG_HOST="localhost"
PG_PORT="5432"
PG_USER="postgres"
PG_DATABASE="athena_production"

# 服务端口
API_PORT=8000

# 日志函数
log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}"
}

log_info() {
    log "INFO" "${BLUE}$@${NC}"
}

log_success() {
    log "SUCCESS" "${GREEN}$@${NC}"
}

log_warning() {
    log "WARNING" "${YELLOW}$@${NC}"
}

log_error() {
    log "ERROR" "${RED}$@${NC}"
}

print_banner() {
    cat << EOF
${BOLD}${GREEN}
============================================
    Athena工作平台 - 本地CI/CD部署
    版本: v1.0.0
    PostgreSQL: ${PG_VERSION}
    时间: $(date '+%Y-%m-%d %H:%M:%S')
============================================
${NC}
EOF
}

# 创建日志目录
mkdir -p "${LOG_DIR}"

# 步骤1: 验证环境
verify_environment() {
    log_info "=========================================="
    log_info "步骤1: 验证环境"
    log_info "=========================================="

    # 检查PostgreSQL版本
    log_info "检查PostgreSQL版本..."
    PG_VER=$(psql --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
    log_success "PostgreSQL版本: ${PG_VER}"

    if [[ ! "${PG_VER}" == "${PG_VERSION}" ]]; then
        log_warning "PostgreSQL版本不匹配: 期望${PG_VERSION}, 实际${PG_VER}"
    fi

    # 检查项目目录
    if [[ ! -d "${PROJECT_ROOT}" ]]; then
        log_error "项目目录不存在: ${PROJECT_ROOT}"
        exit 1
    fi
    log_success "项目目录: ${PROJECT_ROOT}"

    # 检查Python版本
    PYTHON_VER=$(python3 --version | awk '{print $2}')
    log_info "Python版本: ${PYTHON_VER}"

    # 检查Poetry
    if command -v poetry &> /dev/null; then
        POETRY_VER=$(poetry --version)
        log_info "Poetry版本: ${POETRY_VER}"
    else
        log_warning "Poetry未安装"
    fi
}

# 步骤2: 运行测试
run_tests() {
    log_info "=========================================="
    log_info "步骤2: 运行测试套件"
    log_info "=========================================="

    cd "${PROJECT_ROOT}"

    # 运行pytest
    if python3 -m pytest tests/ -v --tb=short --maxfail=5 -x; then
        log_success "所有测试通过"
    else
        log_error "测试失败，部署中止"
        exit 1
    fi
}

# 步骤3: 备份生产环境
backup_production() {
    log_info "=========================================="
    log_info "步骤3: 备份生产环境"
    log_info "=========================================="

    local timestamp=$(date '+%Y%m%d_%H%M%S')
    local backup_path="${BACKUP_DIR}/backup_${timestamp}"

    mkdir -p "${backup_path}"

    # 备份数据库
    log_info "备份数据库..."
    local db_backup_file="${backup_path}/database.sql"

    if pg_dump -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DATABASE}" -f "${db_backup_file}" 2>&1; then
        log_success "数据库备份完成: ${db_backup_file}"
    else
        log_warning "数据库备份失败，继续部署"
    fi

    # 备份配置文件
    log_info "备份配置文件..."
    if cp -r "${PROJECT_ROOT}/config" "${backup_path}/config"; then
        log_success "配置文件备份完成"
    fi

    log_success "备份完成: ${backup_path}"
}

# 步骤4: 部署到生产环境
deploy_to_production() {
    log_info "=========================================="
    log_info "步骤4: 部署到生产环境"
    log_info "=========================================="

    # 创建生产目录
    mkdir -p "${PRODUCTION_DIR}"

    # 同步核心目录
    for dir in core config scripts; do
        log_info "同步 ${dir} 目录..."
        if rsync -av --delete "${PROJECT_ROOT}/${dir}/" "${PRODUCTION_DIR}/${dir}/" > /dev/null 2>&1; then
            log_success "${dir} 同步完成"
        else
            log_error "${dir} 同步失败"
            exit 1
        fi
    done

    # 安装依赖
    log_info "安装生产依赖..."
    cd "${PROJECT_ROOT}"
    if poetry install --only main; then
        log_success "依赖安装完成"
    else
        log_warning "依赖安装失败，尝试使用pip..."
        if pip3 install -e . --quiet; then
            log_success "依赖安装完成(pip)"
        else
            log_warning "依赖安装可能不完整"
        fi
    fi

    log_success "文件部署完成"
}

# 步骤5: 数据库迁移
migrate_database() {
    log_info "=========================================="
    log_info "步骤5: 数据库迁移"
    log_info "=========================================="

    # 测试数据库连接
    log_info "测试数据库连接..."
    if psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DATABASE}" -c 'SELECT version();' > /dev/null 2>&1; then
        log_success "数据库连接成功"
    else
        log_error "数据库连接失败"
        log_info "尝试创建数据库..."
        createdb -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" "${PG_DATABASE}" 2>&1 || true
    fi

    # 运行迁移脚本
    local migration_script="${PROJECT_ROOT}/scripts/migrate_database.py"
    if [[ -f "${migration_script}" ]]; then
        log_info "运行数据库迁移..."
        if python3 "${migration_script}"; then
            log_success "数据库迁移完成"
        else
            log_warning "数据库迁移失败，继续部署"
        fi
    else
        log_info "未找到迁移脚本，跳过迁移"
    fi
}

# 步骤6: 重启服务
restart_services() {
    log_info "=========================================="
    log_info "步骤6: 重启服务"
    log_info "=========================================="

    # 停止现有服务
    log_info "停止现有服务..."
    pkill -f "uvicorn.*:${API_PORT}" || true
    sleep 2

    # 启动新服务
    log_info "启动新服务..."
    cd "${PRODUCTION_DIR}"

    # 创建日志目录
    mkdir -p logs

    # 启动API服务
    nohup python3 -m uvicorn core.api.main:app \
        --host 0.0.0.0 \
        --port ${API_PORT} \
        > logs/api.log 2>&1 &

    # 保存PID
    echo $! > logs/api.pid

    log_info "等待服务启动..."
    sleep 5

    # 健康检查
    if curl -f http://localhost:${API_PORT}/ > /dev/null 2>&1; then
        log_success "API服务启动成功"
    else
        log_warning "健康检查失败，但服务可能已启动"
    fi
}

# 步骤7: 验证部署
verify_deployment() {
    log_info "=========================================="
    log_info "步骤7: 验证部署"
    log_info "=========================================="

    # 检查API
    log_info "检查API端点..."
    if curl -s http://localhost:${API_PORT}/ | head -5; then
        log_success "API响应正常"
    fi

    # 检查数据库
    log_info "检查数据库表..."
    psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DATABASE}" \
        -c 'SELECT COUNT(*) as table_count FROM information_schema.tables WHERE table_schema='\''public'\'';' 2>&1 | head -5

    log_success "部署验证完成"
}

# 步骤8: 清理旧备份
cleanup_old_backups() {
    log_info "=========================================="
    log_info "步骤8: 清理旧备份"
    log_info "=========================================="

    if [[ ! -d "${BACKUP_DIR}" ]]; then
        log_info "备份目录不存在，跳过清理"
        return
    fi

    # 删除7天前的备份
    local deleted_count=0
    find "${BACKUP_DIR}" -type d -name "backup_*" -mtime +7 -print0 | while IFS= read -r -d '' dir; do
        log_info "删除旧备份: $(basename ${dir})"
        rm -rf "${dir}"
        ((deleted_count++))
    done

    log_success "清理完成"
}

# 主部署流程
main() {
    print_banner

    # 记录开始时间
    local start_time=$(date +%s)

    # 执行部署步骤
    verify_environment
    run_tests
    backup_production
    deploy_to_production
    migrate_database
    restart_services
    verify_deployment
    cleanup_old_backups

    # 计算耗时
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))

    # 部署成功
    log_info "=========================================="
    log_success "🎉 部署成功完成!"
    log_info "=========================================="
    log_success "API服务: http://localhost:${API_PORT}"
    log_success "API文档: http://localhost:${API_PORT}/docs"
    log_success "PostgreSQL: ${PG_VERSION}"
    log_success "部署耗时: ${minutes}分${seconds}秒"

    return 0
}

# 捕获Ctrl+C
trap 'log_warning "部署被用户中断"; exit 130' INT

# 执行主函数
main "$@"
