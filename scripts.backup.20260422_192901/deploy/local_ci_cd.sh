#!/bin/bash
# -*- coding: utf-8 -*-
"""
Athena本地CI/CD部署脚本

使用本地PostgreSQL 17.7，避免重复下载Docker镜像

作者: Athena平台团队
创建时间: 2026-01-25
版本: v1.0.0
"""

set -e  # 遇到错误立即退出

# ========================================
# 配置
# ========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# 从scripts/deploy目录向上两级到项目根目录
PROJECT_ROOT="$(cd "$(dirname "$(dirname "$SCRIPT_DIR")")" && pwd)"
LOG_DIR="$PROJECT_ROOT/logs/deploy"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 本地PostgreSQL配置
LOCAL_PG_VERSION="17.7"
LOCAL_PG_HOST="localhost"
LOCAL_PG_PORT="5432"
LOCAL_PG_USER="athena"
LOCAL_PG_PASSWORD="athena_password"
LOCAL_PG_DATABASE="athena_prod"

# Docker配置
# 优先使用已有基础设施配置，避免重复下载
DOCKER_COMPOSE_FILE_EXISTING="$PROJECT_ROOT/config/docker/docker-compose.existing-infra.yml"
DOCKER_COMPOSE_FILE_FULL="$PROJECT_ROOT/config/docker/docker-compose.production.yml"
# 检查是否有已有基础设施在运行
DOCKER_COMPOSE_FILE="$DOCKER_COMPOSE_FILE_EXISTING"
COMPOSE_PROJECT_NAME="athena-prod"

# ========================================
# 日志函数
# ========================================

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
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
# 前置检查
# ========================================

check_prerequisites() {
    log_step "前置检查"

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    log_success "Docker已安装: $(docker --version)"

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装，请先安装"
        exit 1
    fi
    log_success "Docker Compose已安装"

    # 检查本地PostgreSQL
    if command -v pg_config &> /dev/null; then
        local_version=$(pg_config --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
        log_success "本地PostgreSQL: $local_version"

        # 检查PostgreSQL服务状态
        if pg_isready -h $LOCAL_PG_HOST -p $LOCAL_PG_PORT &> /dev/null; then
            log_success "PostgreSQL服务运行中"
        else
            log_warning "PostgreSQL服务未运行，将启动服务"
        fi
    else
        log_warning "本地PostgreSQL未找到，将使用Docker PostgreSQL"
    fi

    # 检查项目目录
    if [ ! -d "$PROJECT_ROOT/core" ]; then
        log_error "项目根目录不正确: $PROJECT_ROOT"
        exit 1
    fi
    log_success "项目目录: $PROJECT_ROOT"
}

# ========================================
# 环境准备
# ========================================

prepare_environment() {
    log_step "环境准备"

    # 创建日志目录
    mkdir -p "$LOG_DIR"
    mkdir -p "$PROJECT_ROOT/logs/app"
    mkdir -p "$PROJECT_ROOT/logs/nginx"

    # 创建数据目录
    mkdir -p "$PROJECT_ROOT/data/qdrant"
    mkdir -p "$PROJECT_ROOT/data/nebula/meta"
    mkdir -p "$PROJECT_ROOT/data/nebula/storage"

    log_success "目录结构已创建"

    # 检查.env文件
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        log_warning ".env文件不存在，从.env.example创建"
        if [ -f "$PROJECT_ROOT/.env.example" ]; then
            cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
            log_info "已创建.env文件，请配置必要的环境变量"
        fi
    fi

    # 配置生产环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export ENVIRONMENT=production
    export LOG_LEVEL=INFO
}

# ========================================
# PostgreSQL配置
# ========================================

configure_local_postgresql() {
    log_step "配置本地PostgreSQL 17.7"

    # 检查本地PostgreSQL是否可用
    if command -v pg_isready &> /dev/null; then
        log_info "配置本地PostgreSQL连接..."

        # 创建数据库和用户（如果不存在）
        PGHOST=$LOCAL_PG_HOST PGPORT=$LOCAL_PG_PORT psql -d postgres -c "SELECT 1" &> /dev/null && {
            log_info "PostgreSQL可访问，配置数据库..."

            # 创建用户
            psql -h $LOCAL_PG_HOST -p $LOCAL_PG_PORT -d postgres -c "DO \$\$ \$\$
            CREATE USER $LOCAL_PG_USER WITH PASSWORD '$LOCAL_PG_PASSWORD';
            SELECT 'CREATE USER' as action;
            GRANT ALL PRIVILEGES ON DATABASE $LOCAL_PG_DATABASE TO $LOCAL_PG_USER;
            SELECT 'GRANT PRIVILEGES' as action;
            \$\$ \$\$" || true

            # 创建数据库
            psql -h $LOCAL_PG_HOST -p $LOCAL_PG_PORT -d postgres -c "CREATE DATABASE $LOCAL_PG_DATABASE OWNER $LOCAL_PG_USER;" || true

            log_success "本地PostgreSQL配置完成"
        }

        # 导出PostgreSQL连接信息为环境变量
        export POSTGRES_HOST=$LOCAL_PG_HOST
        export POSTGRES_PORT=$LOCAL_PG_PORT
        export POSTGRES_USER=$LOCAL_PG_USER
        export POSTGRES_PASSWORD=$LOCAL_PG_PASSWORD
        export POSTGRES_DB=$LOCAL_PG_DATABASE
        export DATABASE_URL="postgresql://$LOCAL_PG_USER:$LOCAL_PG_PASSWORD@$LOCAL_PG_HOST:$LOCAL_PG_PORT/$LOCAL_PG_DATABASE"

    else
        log_warning "本地PostgreSQL不可用，将使用容器PostgreSQL"
    fi
}

# ========================================
# Docker镜像优化
# ========================================

optimize_docker_images() {
    log_step "优化Docker镜像（避免重复下载）"

    log_info "检查现有Docker基础设施..."
    docker images | grep -E "athena|qdrant|nebula|neo4j" || echo "无现有镜像"

    # 检查已有运行中的容器
    log_info "检查运行中的Athena服务..."
    if docker ps --format "{{{{.Names}}}}" | grep -q "athena_.*_prod"; then
        log_success "发现已有Athena基础设施:"
        docker ps --format "table {{{{.Names}}}}\t{{{{.Image}}}}\t{{{{.Status}}}}" | grep "athena_.*_prod" || true
        log_info "将使用已有基础设施，无需重复下载"
    fi

    # 使用Docker BuildKit缓存加速构建
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1

    log_success "Docker优化配置已应用"
}

# ========================================
# 运行测试
# ========================================

run_tests() {
    log_step "运行测试套件"

    cd "$PROJECT_ROOT"

    log_info "运行工具库测试..."
    if pytest tests/unit/tools/ tests/integration/tools/ -v --tb=short -m "not slow" > "$LOG_DIR/test_results_$TIMESTAMP.log" 2>&1; then
        log_success "工具库测试通过"
        TEST_RESULT=0
    else
        log_error "工具库测试失败，查看日志: $LOG_DIR/test_results_$TIMESTAMP.log"
        TEST_RESULT=1
    fi

    # 显示测试摘要
    if [ -f "$LOG_DIR/test_results_$TIMESTAMP.log" ]; then
        echo -e "\n${BLUE}测试摘要:${NC}"
        tail -20 "$LOG_DIR/test_results_$TIMESTAMP.log"
    fi

    return $TEST_RESULT
}

# ========================================
# 构建镜像
# ========================================

build_images() {
    log_step "构建Docker镜像"

    cd "$PROJECT_ROOT"

    # 使用缓存和并行构建
    log_info "构建生产镜像（使用缓存）..."
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        docker compose -f "$DOCKER_COMPOSE_FILE" build --parallel 2>&1 | tee "$LOG_DIR/build_$TIMESTAMP.log"

        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            log_success "镜像构建完成"
        else
            log_error "镜像构建失败"
            return 1
        fi
    else
        log_warning "Docker Compose文件不存在: $DOCKER_COMPOSE_FILE"
    fi
}

# ========================================
# 部署服务
# ========================================

deploy_services() {
    log_step "部署服务到生产环境（使用已有基础设施）"

    cd "$PROJECT_ROOT"

    # 检查配置文件
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        log_error "Docker Compose文件不存在: $DOCKER_COMPOSE_FILE"
        return 1
    fi

    # 停止旧容器（如果存在）
    log_info "停止旧容器..."
    docker compose -f "$DOCKER_COMPOSE_FILE" --project-name "$COMPOSE_PROJECT_NAME" down 2>&1 || true

    # 启动新容器（仅启动intelligent-router）
    log_info "启动intelligent-router服务（连接已有基础设施）..."
    docker compose -f "$DOCKER_COMPOSE_FILE" --project-name "$COMPOSE_PROJECT_NAME" up -d 2>&1 | tee "$LOG_DIR/deploy_$TIMESTAMP.log"

    # 等待服务就绪
    log_info "等待服务就绪..."
    sleep 10

    # 检查服务状态
    log_info "检查服务状态..."
    docker compose -f "$DOCKER_COMPOSE_FILE" --project-name "$COMPOSE_PROJECT_NAME" ps

    # 显示服务日志
    echo -e "\n${BLUE}服务日志（最近20行）:${NC}"
    docker compose -f "$DOCKER_COMPOSE_FILE" --project-name "$COMPOSE_PROJECT_NAME" logs --tail=20

    log_success "服务部署完成"
    log_info "✅ 使用已有基础设施：PostgreSQL 17.7 (本地), Qdrant, Redis, Neo4j"
}

# ========================================
# 健康检查
# ========================================

health_check() {
    log_step "健康检查"

    # 等待服务启动
    log_info "等待服务完全启动..."
    sleep 15

    # 检查容器状态
    unhealthy_containers=$(docker compose -f "$DOCKER_COMPOSE_FILE" --project-name "$COMPOSE_PROJECT_NAME" ps | grep -c "Exit" || true)

    if [ $unhealthy_containers -gt 0 ]; then
        log_warning "发现 $unhealthy_containers 个异常容器"
        docker compose -f "$DOCKER_COMPOSE_FILE" --project-name "$COMPOSE_PROJECT_NAME" ps
    else
        log_success "所有容器运行正常"
    fi

    # 检查本地PostgreSQL连接
    if command -v pg_isready &> /dev/null; then
        if pg_isready -h $LOCAL_PG_HOST -p $LOCAL_PG_PORT -U $LOCAL_PG_USER -d $LOCAL_PG_DATABASE &> /dev/null; then
            log_success "本地PostgreSQL连接正常"

            # 显示数据库统计
            psql -h $LOCAL_PG_HOST -p $LOCAL_PG_PORT -U $LOCAL_PG_USER -d $LOCAL_PG_DATABASE -c "
                SELECT
                    version() as pg_version,
                    current_database as database_name,
                    (SELECT count(*) FROM pg_tables WHERE schemaname = 'public') as table_count;
            " || true
        fi
    fi
}

# ========================================
# 回滚
# ========================================

rollback() {
    log_error "部署失败，执行回滚..."

    cd "$PROJECT_ROOT"

    # 使用git回滚到上一个版本
    log_info "回滚到上一个提交..."
    git reset --hard HEAD~1

    # 重新部署
    log_info "重新部署..."
    docker compose -f "$DOCKER_COMPOSE_FILE" --project-name "$COMPOSE_PROJECT_NAME" up -d

    log_success "回滚完成"
}

# ========================================
# 主流程
# ========================================

main() {
    echo -e "${GREEN}"
    echo "========================================"
    echo "  Athena 本地CI/CD部署脚本"
    echo "  版本: v1.0.0"
    echo "  时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "========================================"
    echo -e "${NC}"

    # 解析命令行参数
    SKIP_TESTS=false
    SKIP_BUILD=false
    FORCE_DEPLOY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                echo "用法: $0 [--skip-tests] [--skip-build] [--force]"
                exit 1
                ;;
        esac
    done

    # 执行部署流程
    {
        check_prerequisites
        prepare_environment
        configure_local_postgresql
        optimize_docker_images

        # 运行测试（除非跳过）
        if [ "$SKIP_TESTS" = false ]; then
            if ! run_tests; then
                if [ "$FORCE_DEPLOY" = false ]; then
                    log_error "测试失败，部署中止（使用 --force 强制部署）"
                    exit 1
                else
                    log_warning "测试失败但继续部署（--force）"
                fi
            fi
        fi

        # 构建镜像（除非跳过）
        if [ "$SKIP_BUILD" = false ]; then
            build_images || rollback
        fi

        # 部署服务
        deploy_services

        # 健康检查
        health_check

        log_step "部署完成！"
        log_success "Athena平台已成功部署到生产环境"
        echo ""
        echo -e "${GREEN}服务访问:${NC}"
        echo "  - API服务: http://localhost:8081"
        echo "  - Qdrant:  http://localhost:6335"
        echo "  - NebulaGraph: http://localhost:9670"
        echo ""
        echo -e "${GREEN}管理命令:${NC}"
        echo "  - 查看日志: docker compose -f $DOCKER_COMPOSE_FILE logs -f"
        echo "  - 停止服务: docker compose -f $DOCKER_COMPOSE_FILE down"
        echo "  - 重启服务: docker compose -f $DOCKER_COMPOSE_FILE restart"
        echo ""

    } || {
        log_error "部署过程中出现错误"
        rollback
        exit 1
    }
}

# ========================================
# 信号处理
# ========================================

trap 'log_error "部署被中断"; rollback; exit 1' INT TERM

# ========================================
# 执行主流程
# ========================================

main "$@"
