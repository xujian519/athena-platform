#!/bin/bash
# =============================================================================
# Athena记忆系统 - 本地PostgreSQL生产部署脚本
# =============================================================================
# 使用本地PostgreSQL 17.7 + Docker (Qdrant, Neo4j, Redis)

set -e

PROJECT_ROOT="/Users/xujian/Athena工作平台"
LOG_DIR="${PROJECT_ROOT}/logs"
BACKUP_DIR="${PROJECT_ROOT}/backups"
DEPLOY_LOG="${LOG_DIR}/local_deploy_$(date +%Y%m%d_%H%M%S).log"

# 创建必要目录
mkdir -p "${LOG_DIR}" "${BACKUP_DIR}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    local level=$1
    shift
    local message="$@"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "${timestamp} [${level}] ${message}" | tee -a "${DEPLOY_LOG}"
}

log_info() { log "INFO" "${BLUE}$@${NC}"; }
log_success() { log "SUCCESS" "${GREEN}$@${NC}"; }
log_warning() { log "WARNING" "${YELLOW}$@${NC}"; }
log_error() { log "ERROR" "${RED}$@${NC}"; }

# 检查本地PostgreSQL状态
check_postgresql() {
    log_info "检查本地PostgreSQL服务..."
    
    if ! command -v psql &> /dev/null; then
        log_error "PostgreSQL客户端未安装"
        return 1
    fi
    
    local pg_version=$(psql --version | grep -oP '\d+\.\d+')
    log_info "PostgreSQL版本: ${pg_version}"
    
    # 检查PostgreSQL服务状态
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        log_success "PostgreSQL服务运行正常"
        return 0
    else
        log_warning "PostgreSQL服务未运行，尝试启动..."
        brew services start postgresql@17.7 || {
            log_error "无法启动PostgreSQL服务"
            return 1
        }
        sleep 3
        if pg_isready -h localhost -p 5432 &> /dev/null; then
            log_success "PostgreSQL服务已启动"
            return 0
        else
            log_error "PostgreSQL启动失败"
            return 1
        fi
    fi
}

# 配置PostgreSQL数据库
setup_postgresql() {
    log_info "配置PostgreSQL数据库..."
    
    # 检查并创建数据库
    if ! psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw athena_memory; then
        log_info "创建数据库 athena_memory..."
        psql -h localhost -U postgres -c "CREATE DATABASE athena_memory ENCODING 'UTF8';"
        log_success "数据库创建成功"
    else
        log_info "数据库 athena_memory 已存在"
    fi
    
    # 安装pgvector扩展（如果未安装）
    log_info "检查pgvector扩展..."
    if ! psql -h localhost -U postgres -d athena_memory -c "CREATE EXTENSION IF NOT EXISTS vector;" &> /dev/null; then
        log_warning "pgvector扩展未安装，请手动安装"
        log_info "安装命令: git clone https://github.com/pgvector/pgvector.git /tmp/pgvector && cd /tmp/pgvector && make install"
    else
        log_success "pgvector扩展已就绪"
    fi
}

# 启动Docker服务（Qdrant, Neo4j, Redis）
start_docker_services() {
    log_info "启动Docker基础设施服务..."
    
    cd "${PROJECT_ROOT}/config/docker"
    
    # 启动Qdrant和Neo4j（不启动PostgreSQL）
    log_info "启动Qdrant向量数据库..."
    docker-compose -f docker-compose.unified-databases.yml up -d athena-qdrant
    
    log_info "启动Neo4j图数据库..."
    docker-compose -f docker-compose.unified-databases.yml up -d neo4j
    
    log_info "启动Redis缓存..."
    docker-compose -f docker-compose.unified-databases.yml --profile cache up -d athena-redis
    
    log_success "Docker服务启动完成"
}

# 部署记忆系统代码
deploy_memory_system() {
    log_info "部署记忆系统代码..."
    
    cd "${PROJECT_ROOT}"
    
    # 检查Python虚拟环境
    if [ ! -d "venv" ]; then
        log_info "创建Python虚拟环境..."
        python3 -m venv venv
    fi
    
    # 激活虚拟环境并安装依赖
    source venv/bin/activate
    log_info "安装Python依赖..."
    pip install -e . --quiet
    
    log_success "记忆系统代码部署完成"
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    local all_ok=true
    
    # 检查PostgreSQL
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        log_success "✓ PostgreSQL (本地 17.7)"
    else
        log_error "✗ PostgreSQL 不可用"
        all_ok=false
    fi
    
    # 检查Qdrant
    if curl -s http://localhost:6333/health &> /dev/null; then
        log_success "✓ Qdrant (Docker)"
    else
        log_error "✗ Qdrant 不可用"
        all_ok=false
    fi
    
    # 检查Neo4j
    if curl -s http://localhost:7474 &> /dev/null; then
        log_success "✓ Neo4j (Docker)"
    else
        log_error "✗ Neo4j 不可用"
        all_ok=false
    fi
    
    # 检查Redis
    if redis-cli -h localhost -p 6379 ping &> /dev/null; then
        log_success "✓ Redis (Docker)"
    else
        log_warning "✗ Redis 不可用（可选）"
    fi
    
    if [ "$all_ok" = true ]; then
        log_success "所有核心服务健康检查通过"
        return 0
    else
        log_error "部分服务健康检查失败"
        return 1
    fi
}

# 主部署流程
main() {
    log_info "=========================================="
    log_info "Athena记忆系统 - 本地生产环境部署"
    log_info "=========================================="
    
    # 1. 检查PostgreSQL
    check_postgresql || exit 1
    
    # 2. 配置数据库
    setup_postgresql || exit 1
    
    # 3. 启动Docker服务
    start_docker_services || exit 1
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 4. 部署应用代码
    deploy_memory_system || exit 1
    
    # 5. 健康检查
    health_check || exit 1
    
    log_success "=========================================="
    log_success "部署完成！"
    log_success "=========================================="
    log_info "部署日志: ${DEPLOY_LOG}"
    log_info ""
    log_info "服务访问地址:"
    log_info "  - PostgreSQL: localhost:5432 (本地 17.7)"
    log_info "  - Qdrant: http://localhost:6333"
    log_info "  - Neo4j: http://localhost:7474"
    log_info "  - Redis: localhost:6379"
}

# 执行主流程
main "$@"
