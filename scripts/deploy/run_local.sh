#!/bin/bash
# -*- coding: utf-8 -*-
"""
Athena本地部署脚本 - 使用本地Python环境

使用本地Homebrew Python 3.14和已有Docker基础设施

作者: Athena平台团队
创建时间: 2026-01-25
版本: v1.0.0
"""

set -e

# ========================================
# 配置
# ========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 从scripts/deploy目录向上两级到项目根目录
PROJECT_ROOT="$(cd "$(dirname "$(dirname "$SCRIPT_DIR")")" && pwd)"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ========================================
# 日志函数
# ========================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

# ========================================
# 检查本地Python环境
# ========================================

check_python_env() {
    log_step "检查本地Python环境"

    # 检查Python版本
    PYTHON_CMD=$(which python3)
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')

    log_success "Python路径: $PYTHON_CMD"
    log_success "Python版本: $PYTHON_VERSION"

    # 检查Poetry
    if command -v poetry &> /dev/null; then
        POETRY_VERSION=$(poetry --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
        log_success "Poetry已安装: $POETRY_VERSION"
    else
        log_warning "Poetry未安装，将使用pip"
    fi

    # 检查PostgreSQL
    if command -v psql &> /dev/null; then
        PG_VERSION=$(pg_config --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        log_success "本地PostgreSQL: $PG_VERSION"
    else
        log_error "PostgreSQL未找到"
        return 1
    fi
}

# ========================================
# 检查已有基础设施
# ========================================

check_existing_infra() {
    log_step "检查已有Docker基础设施"

    # 检查运行中的容器
    log_info "运行中的Athena服务:"
    docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}" | grep "athena_.*_prod" || echo "无"

    # 检查网络
    if docker network ls | grep -q "athena-prod-network"; then
        log_success "athena-prod-network已存在"
    else
        log_error "athena-prod-network不存在"
        return 1
    fi
}

# ========================================
# 安装Python依赖
# ========================================

install_dependencies() {
    log_step "安装Python依赖"

    cd "$PROJECT_ROOT"

    # 使用Poetry安装依赖
    if command -v poetry &> /dev/null; then
        log_info "使用Poetry安装依赖..."
        poetry install --only main

        # 设置Python路径
        PYTHON_CMD="poetry run python"
    else
        log_info "使用pip安装依赖..."
        $PYTHON_CMD -m pip install -e . --no-deps

        # 安装核心依赖
        $PYTHON_CMD -m pip install \
            fastapi uvicorn[standard] \
            pydantic pydantic-settings \
            qdrant-client \
            redis \
            psycopg2-binary \
            numpy \
            sentence-transformers \
            tenacity \
            prometheus-fastapi-instrumenter \
            slowapi

        PYTHON_CMD=$PYTHON_CMD
    fi

    log_success "依赖安装完成"
}

# ========================================
# 配置环境变量
# ========================================

setup_environment() {
    log_step "配置环境变量"

    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export ENVIRONMENT=production
    export LOG_LEVEL=INFO

    # PostgreSQL配置（本地17.7）
    export POSTGRES_HOST=localhost
    export POSTGRES_PORT=5432
    export POSTGRES_USER=athena
    export POSTGRES_PASSWORD=athena_password
    export POSTGRES_DB=athena_prod
    export DATABASE_URL="postgresql://athena:athena_password@localhost:5432/athena_prod"

    # Redis配置（已有容器）
    export REDIS_URL="redis://athena_redis_prod:6379"

    # Qdrant配置（已有容器）
    export QDRANT_URL="http://athena_qdrant_prod:6333"

    # Neo4j配置（已有容器）
    export NEO4J_URI="bolt://athena_neo4j_prod:7687"
    export NEO4J_USER=neo4j
    export NEO4J_PASSWORD=athena123

    # API配置
    export API_KEY_PROD=74207bed56b28b4faa4a7981d4e0b783f14f2e8a000adae2aa41f56b8ee2f7d6
    export CACHE_MAX_SIZE=1000
    export CACHE_TTL=3600
    export RATE_LIMIT_PER_MINUTE=100

    log_success "环境变量已配置"
}

# ========================================
# 启动服务
# ========================================

start_service() {
    log_step "启动Athena智能路由服务"

    cd "$PROJECT_ROOT"

    # 创建日志目录
    mkdir -p logs/app

    # 检查服务是否已运行
    if pgrep -f "uvicorn.*unified_retrieval_api" > /dev/null; then
        log_info "服务已在运行，停止旧进程..."
        pkill -f "uvicorn.*unified_retrieval_api" || true
        sleep 2
    fi

    # 启动服务
    log_info "启动服务..."
    nohup $PYTHON_CMD -m uvicorn core.search.unified_retrieval_api:app \
        --host 0.0.0.0 \
        --port 8081 \
        --workers 1 \
        --log-level info \
        > logs/app/intelligent-router.log 2>&1 &

    # 保存PID
    echo $! > logs/app/intelligent-router.pid

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 5

    # 检查服务状态
    if curl -sf http://localhost:8081/health > /dev/null 2>&1; then
        log_success "✅ 服务启动成功！"
    else
        log_error "❌ 服务启动失败，查看日志:"
        tail -20 logs/app/intelligent-router.log
        return 1
    fi
}

# ========================================
# 显示服务信息
# ========================================

show_service_info() {
    log_step "服务信息"

    echo -e "${GREEN}🎉 Athena平台已启动！${NC}\n"

    echo -e "${BLUE}服务访问:${NC}"
    echo "  - API服务:     http://localhost:8081"
    echo "  - 健康检查:   http://localhost:8081/health"
    echo "  - API文档:     http://localhost:8081/docs"
    echo ""

    echo -e "${BLUE}基础设施:${NC}"
    echo "  - PostgreSQL: localhost:5432 (本地17.7)"
    echo "  - Qdrant:     athena_qdrant_prod:6333 (Docker)"
    echo "  - Redis:      athena_redis_prod:6379 (Docker)"
    echo "  - Neo4j:      athena_neo4j_prod:7687 (Docker)"
    echo ""

    echo -e "${BLUE}日志文件:${NC}"
    echo "  - 服务日志:   $PROJECT_ROOT/logs/app/intelligent-router.log"
    echo ""

    echo -e "${BLUE}管理命令:${NC}"
    echo "  - 查看日志:   tail -f logs/app/intelligent-router.log"
    echo "  - 停止服务:   kill \$(cat logs/app/intelligent-router.pid)"
    echo "  - 重启服务:   bash scripts/deploy/run_local.sh"
    echo ""
}

# ========================================
# 主流程
# ========================================

main() {
    echo -e "${GREEN}"
    echo "========================================"
    echo "  Athena 本地部署脚本"
    echo "  使用本地Python 3.14 + 已有基础设施"
    echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo -e "${NC}"

    # 解析命令行参数
    SKIP_DEPS=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                echo "用法: $0 [--skip-deps]"
                exit 1
                ;;
        esac
    done

    # 执行部署流程
    check_python_env || exit 1
    check_existing_infra || exit 1

    if [ "$SKIP_DEPS" = false ]; then
        install_dependencies || exit 1
    fi

    setup_environment
    start_service || exit 1
    show_service_info

    log_success "部署完成！"
}

# ========================================
# 信号处理
# ========================================

trap 'log_error "部署被中断"; exit 1' INT TERM

# ========================================
# 执行主流程
# ========================================

main "$@"
