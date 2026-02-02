#!/bin/bash

# Athena AI平台 - 容器化部署脚本
# 生成时间: 2025-12-11
# 支持环境: development, staging, production
# 功能: 自动化容器部署、健康检查、回滚机制

set -euo pipefail  # 严格错误处理

# ================================
# 配置变量
# ================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-development}"
COMPOSE_FILE=""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# ================================
# 环境检测和配置
# ================================
detect_environment() {
    log_info "检测部署环境: $ENVIRONMENT"

    case "$ENVIRONMENT" in
        development)
            COMPOSE_FILE="docker-compose.dev.yml"
            ENV_FILE=".env.development"
            ;;
        staging)
            COMPOSE_FILE="docker-compose.staging.yml"
            ENV_FILE=".env.staging"
            ;;
        production)
            COMPOSE_FILE="docker-compose.production.yml"
            ENV_FILE=".env.production"
            ;;
        *)
            log_error "不支持的环境: $ENVIRONMENT"
            echo "支持的环境: development, staging, production"
            exit 1
            ;;
    esac

    if [[ ! -f "$PROJECT_ROOT/deployment/docker/$COMPOSE_FILE" ]]; then
        log_error "配置文件不存在: $PROJECT_ROOT/deployment/docker/$COMPOSE_FILE"
        exit 1
    fi

    if [[ -f "$PROJECT_ROOT/$ENV_FILE" ]]; then
        export $(cat "$PROJECT_ROOT/$ENV_FILE" | grep -v '^#' | xargs)
        log_info "加载环境配置: $ENV_FILE"
    else
        log_warning "环境配置文件不存在: $ENV_FILE，使用默认配置"
    fi

    export COMPOSE_PROJECT_NAME="athena-$ENVIRONMENT"
    export COMPOSE_FILE="$PROJECT_ROOT/deployment/docker/$COMPOSE_FILE"

    log_success "环境配置完成: $ENVIRONMENT"
}

# ================================
# 依赖检查
# ================================
check_dependencies() {
    log_info "检查系统依赖..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装或未运行"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi

    # 检查Docker服务状态
    if ! docker info &> /dev/null; then
        log_error "Docker 服务未运行"
        exit 1
    fi

    # 检查可用磁盘空间 (至少5GB)
    available_space=$(df "$PROJECT_ROOT" | awk 'NR==2 {print $4}')
    if [[ $available_space -lt 5242880 ]]; then  # 5GB in KB
        log_warning "可用磁盘空间不足5GB，建议释放空间"
    fi

    # 检查可用内存
    if [[ "$ENVIRONMENT" == "production" ]]; then
        total_memory=$(free -g | awk 'NR==2{print $2}')
        if [[ $total_memory -lt 8 ]]; then
            log_warning "生产环境建议至少8GB内存，当前: ${total_memory}GB"
        fi
    fi

    log_success "依赖检查通过"
}

# ================================
# 镜像构建
# ================================
build_images() {
    log_info "开始构建Docker镜像..."

    cd "$PROJECT_ROOT"

    # 构建基础镜像
    log_info "构建基础应用镜像..."
    docker build \
        -f deployment/docker/Dockerfile.optimized \
        --target base \
        -t "athena-base:$ENVIRONMENT" \
        --build-arg BUILD_ENV="$ENVIRONMENT" \
        . || {
        log_error "基础镜像构建失败"
        exit 1
    }

    # 构建生产镜像
    log_info "构建生产应用镜像..."
    docker build \
        -f deployment/docker/Dockerfile.optimized \
        --target production \
        -t "athena-app:$ENVIRONMENT" \
        -t "athena-app:latest" \
        --build-arg BUILD_ENV="$ENVIRONMENT" \
        --cache-from "athena-base:$ENVIRONMENT" \
        . || {
        log_error "生产镜像构建失败"
        exit 1
    }

    # 构建AI服务镜像
    if [[ -d "services/ai-services" ]]; then
        log_info "构建AI服务镜像..."
        docker build \
            -f services/ai-services/Dockerfile \
            -t "athena-ai-service:$ENVIRONMENT" \
            -t "athena-ai-service:latest" \
            --build-arg BUILD_ENV="$ENVIRONMENT" \
            services/ai-services/ || {
            log_error "AI服务镜像构建失败"
            exit 1
        }
    fi

    log_success "所有镜像构建完成"
}

# ================================
# 容器部署
# ================================
deploy_containers() {
    log_info "开始部署容器服务..."

    cd "$PROJECT_ROOT"

    # 拉取最新基础镜像
    log_info "拉取最新基础镜像..."
    docker-compose -f "$COMPOSE_FILE" pull

    # 停止现有服务
    log_info "停止现有服务..."
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans || true

    # 启动数据库服务
    log_info "启动数据库服务..."
    docker-compose -f "$COMPOSE_FILE" up -d postgres redis elasticsearch qdrant

    # 等待数据库服务就绪
    wait_for_database

    # 启动应用服务
    log_info "启动应用服务..."
    docker-compose -f "$COMPOSE_FILE" up -d web-app ai-service

    # 启动网关和监控服务
    log_info "启动网关和监控服务..."
    docker-compose -f "$COMPOSE_FILE" up -d api-gateway prometheus grafana

    log_success "所有服务部署完成"
}

# ================================
# 数据库等待和初始化
# ================================
wait_for_database() {
    log_info "等待数据库服务就绪..."

    local max_attempts=30
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        # 检查PostgreSQL
        if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U athena -d athenadb &>/dev/null; then
            log_success "PostgreSQL 已就绪"
            break
        fi

        # 检查Redis
        if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping &>/dev/null; then
            log_success "Redis 已就绪"
        fi

        # 检查Elasticsearch
        if curl -s http://localhost:9200/_cluster/health | grep -q '"status":"green"\|"status":"yellow"'; then
            log_success "Elasticsearch 已就绪"
        fi

        log_info "等待数据库就绪... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    if [[ $attempt -gt $max_attempts ]]; then
        log_error "数据库服务启动超时"
        exit 1
    fi

    # 运行数据库迁移
    log_info "运行数据库迁移..."
    docker-compose -f "$COMPOSE_FILE" exec -T web-app python -m alembic upgrade head || {
        log_warning "数据库迁移失败，可能需要手动处理"
    }
}

# ================================
# 健康检查
# ================================
health_check() {
    log_info "执行服务健康检查..."

    local services=("postgres" "redis" "elasticsearch" "web-app" "ai-service" "api-gateway")
    local unhealthy_services=()

    for service in "${services[@]}"; do
        log_info "检查服务: $service"

        # 等待服务启动
        sleep 10

        # 执行健康检查
        if docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "Up (healthy)"; then
            log_success "✓ $service: 健康"
        else
            log_warning "✗ $service: 不健康"
            unhealthy_services+=("$service")
        fi
    done

    # 检查HTTP端点
    log_info "检查HTTP端点..."

    local endpoints=(
        "http://localhost:80/health"
        "http://localhost:8080/api/v2/health"
        "http://localhost:9090/-/healthy"
        "http://localhost:3000/api/health"
    )

    for endpoint in "${endpoints[@]}"; do
        log_info "检查端点: $endpoint"

        for i in {1..5}; do
            if curl -f -s "$endpoint" >/dev/null 2>&1; then
                log_success "✓ $endpoint: 可访问"
                break
            else
                if [[ $i -eq 5 ]]; then
                    log_warning "✗ $endpoint: 不可访问"
                    unhealthy_services+=("$endpoint")
                else
                    sleep 5
                fi
            fi
        done
    done

    if [[ ${#unhealthy_services[@]} -gt 0 ]]; then
        log_error "以下服务不健康: ${unhealthy_services[*]}"

        if [[ "$ENVIRONMENT" == "production" ]]; then
            log_error "生产环境检测到不健康服务，执行自动回滚..."
            rollback_deployment
            exit 1
        fi
    else
        log_success "所有服务健康检查通过"
    fi
}

# ================================
# 回滚机制
# ================================
rollback_deployment() {
    log_warning "执行部署回滚..."

    # 获取上一个版本的镜像
    local previous_image=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep "athena-app" | head -2 | tail -1)

    if [[ -n "$previous_image" ]]; then
        log_info "回滚到上一个版本: $previous_image"

        # 停止当前服务
        docker-compose -f "$COMPOSE_FILE" down

        # 修改compose文件使用上一个镜像版本
        sed -i.bak "s|athena-app:latest|$previous_image|g" "$COMPOSE_FILE"

        # 重新启动服务
        docker-compose -f "$COMPOSE_FILE" up -d

        # 恢复compose文件
        mv "$COMPOSE_FILE.bak" "$COMPOSE_FILE"

        log_success "回滚完成"
    else
        log_error "无法找到上一个版本的镜像"
    fi
}

# ================================
# 服务监控
# ================================
monitor_services() {
    log_info "启动服务监控..."

    # 显示容器状态
    echo
    log_info "=== 容器状态 ==="
    docker-compose -f "$COMPOSE_FILE" ps

    # 显示资源使用情况
    echo
    log_info "=== 资源使用情况 ==="
    docker stats --no-stream $(docker-compose -f "$COMPOSE_FILE" ps -q)

    # 显示服务日志
    echo
    log_info "=== 最近服务日志 ==="
    docker-compose -f "$COMPOSE_FILE" logs --tail=10
}

# ================================
# 清理函数
# ================================
cleanup() {
    log_info "执行清理操作..."

    # 清理未使用的镜像
    log_info "清理未使用的Docker镜像..."
    docker image prune -f

    # 清理未使用的容器
    log_info "清理未使用的Docker容器..."
    docker container prune -f

    # 清理未使用的网络
    log_info "清理未使用的Docker网络..."
    docker network prune -f

    log_success "清理完成"
}

# ================================
# 主函数
# ================================
main() {
    echo "=============================================="
    echo "🚀 Athena AI平台 容器化部署脚本"
    echo "环境: $ENVIRONMENT"
    echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================="
    echo

    # 执行部署流程
    detect_environment
    check_dependencies

    # 构建镜像
    if [[ "${SKIP_BUILD:-false}" != "true" ]]; then
        build_images
    fi

    deploy_containers
    health_check
    monitor_services

    # 可选清理
    if [[ "${CLEANUP:-false}" == "true" ]]; then
        cleanup
    fi

    echo
    log_success "🎉 部署完成！"
    echo
    echo "=== 服务访问地址 ==="
    echo "Web应用: http://localhost"
    echo "API文档: http://localhost/docs"
    echo "Grafana监控: http://localhost:3000 (admin/admin)"
    echo "Prometheus: http://localhost:9090"
    echo
    echo "=== 管理命令 ==="
    echo "查看日志: docker-compose -f $COMPOSE_FILE logs -f"
    echo "停止服务: docker-compose -f $COMPOSE_FILE down"
    echo "重启服务: docker-compose -f $COMPOSE_FILE restart"
    echo "检查状态: docker-compose -f $COMPOSE_FILE ps"
    echo
}

# ================================
# 信号处理
# ================================
trap 'log_error "脚本被中断"; exit 1' INT TERM

# ================================
# 执行主函数
# ================================
main "$@"