#!/bin/bash
# Athena 感知模块部署脚本
# 使用现有基础设施：本地PostgreSQL 17.7 + Docker服务
# 最后更新: 2026-01-26

set -e  # 遇到错误立即退出

# ========================================
# 颜色输出
# ========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ========================================
# 配置变量
# ========================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
DOCKER_COMPOSE_FILE="${PROJECT_ROOT}/config/docker/docker-compose.perception-module.yml"
ENV_FILE="${PROJECT_ROOT}/.env.perception"

# 数据库配置
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="athena_perception"
DB_USER="athena_perception"
DB_PASSWORD="athena_perception_secure_2024"

# 服务端口
PERCEPTION_PORT="8070"
METRICS_PORT="9070"

# ========================================
# 辅助函数
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

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

# ========================================
# 检查函数
# ========================================

check_postgresql() {
    print_header "检查 PostgreSQL 17.7"

    if command -v psql &> /dev/null; then
        PG_VERSION=$(psql --version | awk '{print $3}')
        log_success "PostgreSQL 已安装: ${PG_VERSION}"

        if pg_isready -h ${DB_HOST} -p ${DB_PORT} &> /dev/null; then
            log_success "PostgreSQL 正在运行"
        else
            log_error "PostgreSQL 未运行，请先启动 PostgreSQL"
            exit 1
        fi
    else
        log_error "未找到 PostgreSQL，请先安装 PostgreSQL 17.7"
        exit 1
    fi
}

check_docker() {
    print_header "检查 Docker"

    if command -v docker &> /dev/null; then
        log_success "Docker 已安装: $(docker --version | awk '{print $3}')"
    else
        log_error "未找到 Docker，请先安装 Docker"
        exit 1
    fi

    if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
        log_success "Docker Compose 已安装"
    else
        log_error "未找到 Docker Compose，请先安装 Docker Compose"
        exit 1
    fi
}

check_networks() {
    print_header "检查 Docker 网络"

    REQUIRED_NETWORKS=("unified-db-network" "athena-network")

    for network in "${REQUIRED_NETWORKS[@]}"; do
        if docker network inspect "${network}" &> /dev/null; then
            log_success "网络 ${network} 已存在"
        else
            log_warning "网络 ${network} 不存在，创建中..."
            docker network create "${network}"
            log_success "网络 ${network} 创建成功"
        fi
    done
}

check_services() {
    print_header "检查 Docker 服务"

    REQUIRED_SERVICES=(
        "athena-redis:Redis"
        "athena_neo4j:Neo4j"
        "athena-qdrant:Qdrant"
    )

    for service in "${REQUIRED_SERVICES[@]}"; do
        SERVICE_NAME="${service%%:*}"
        SERVICE_DISPLAY="${service##*:}"

        if docker ps --format '{{.Names}}' | grep -q "^${SERVICE_NAME}$"; then
            log_success "${SERVICE_DISPLAY} 正在运行"
        else
            log_warning "${SERVICE_DISPLAY} 未运行，尝试启动..."
            # 这里可以添加自动启动逻辑
            log_warning "请手动启动 ${SERVICE_DISPLAY} 后再继续"
        fi
    done
}

check_ports() {
    print_header "检查端口占用"

    PORTS=("${PERCEPTION_PORT}" "${METRICS_PORT}")

    for port in "${PORTS[@]}"; do
        if lsof -i :${port} &> /dev/null; then
            log_warning "端口 ${port} 已被占用"
            read -p "是否继续？(y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "部署已取消"
                exit 0
            fi
        else
            log_success "端口 ${port} 可用"
        fi
    done
}

# ========================================
# 数据库初始化函数
# ========================================

init_database() {
    print_header "初始化数据库"

    log_info "检查数据库是否存在..."
    DB_EXISTS=$(psql -h ${DB_HOST} -p ${DB_PORT} -U $(whoami) -lqt | cut -d \| -f 1 | grep -w ${DB_NAME} | wc -l)

    if [ "${DB_EXISTS}" -eq 0 ]; then
        log_info "创建数据库 ${DB_NAME}..."
        createdb -h ${DB_HOST} -p ${DB_PORT} -U $(whoami) ${DB_NAME}
        log_success "数据库 ${DB_NAME} 创建成功"
    else
        log_info "数据库 ${DB_NAME} 已存在"
    fi

    log_info "执行初始化脚本..."
    psql -h ${DB_HOST} -p ${DB_PORT} -d ${DB_NAME} -f "${SCRIPT_DIR}/init_perception_db.sql"

    log_success "数据库初始化完成"
}

# ========================================
# 环境配置函数
# ========================================

setup_environment() {
    print_header "配置环境变量"

    if [ ! -f "${ENV_FILE}" ]; then
        log_info "创建环境变量文件..."
        cat > "${ENV_FILE}" << EOF
# Athena 感知模块环境变量配置
# 生成时间: $(date)

# ========================================
# 数据库配置
# ========================================
POSTGRES_HOST=host.docker.internal
POSTGRES_PORT=5432
POSTGRES_USER=${DB_USER}
POSTGRES_PASSWORD=${DB_PASSWORD}
POSTGRES_DB=${DB_NAME}
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@host.docker.internal:5432/${DB_NAME}

# ========================================
# Redis配置
# ========================================
REDIS_URL=redis://athena-redis:6379/1
CACHE_TTL=7200
CACHE_MAX_SIZE=1000

# ========================================
# Qdrant配置
# ========================================
QDRANT_URL=http://athena-qdrant:6333
QDRANT_COLLECTION=perception_vectors
QDRANT_VECTOR_SIZE=768

# ========================================
# Neo4j配置
# ========================================
NEO4J_URI=bolt://athena_neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=athena_neo4j_2024

# ========================================
# 感知模块配置
# ========================================
MAX_CONCURRENT_REQUESTS=200
BATCH_SIZE=100
REQUEST_TIMEOUT=30.0
ENABLE_STREAMING=true
ENABLE_COMPRESSION=true

# ========================================
# API配置
# ========================================
PERCEPTION_API_KEY=athena_perception_api_key_$(date +%s)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080,http://localhost:8020
RATE_LIMIT_PER_MINUTE=200

# ========================================
# 监控配置
# ========================================
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
JAEGER_AGENT_HOST=athena-jaeger
JAEGER_AGENT_PORT=6831

# ========================================
# 日志配置
# ========================================
LOG_LEVEL=INFO
LOG_FORMAT=json
EOF
        log_success "环境变量文件创建成功: ${ENV_FILE}"
    else
        log_info "环境变量文件已存在: ${ENV_FILE}"
    fi
}

# ========================================
# 部署函数
# ========================================

deploy_service() {
    print_header "部署感知模块服务"

    cd "${PROJECT_ROOT}"

    log_info "停止旧版本服务（如果存在）..."
    docker-compose -f "${DOCKER_COMPOSE_FILE}" down 2>/dev/null || true

    log_info "构建Docker镜像..."
    docker-compose -f "${DOCKER_COMPOSE_FILE}" build --no-cache

    log_info "启动服务..."
    docker-compose -f "${DOCKER_COMPOSE_FILE}" up -d

    log_success "服务启动成功"
}

# ========================================
# 健康检查函数
# ========================================

health_check() {
    print_header "健康检查"

    log_info "等待服务启动..."
    sleep 10

    MAX_RETRIES=30
    RETRY_COUNT=0

    while [ ${RETRY_COUNT} -lt ${MAX_RETRIES} ]; do
        if curl -f http://localhost:${PERCEPTION_PORT}/health &> /dev/null; then
            log_success "感知模块服务健康检查通过"
            return 0
        fi

        RETRY_COUNT=$((RETRY_COUNT + 1))
        log_info "等待服务就绪... (${RETRY_COUNT}/${MAX_RETRIES})"
        sleep 2
    done

    log_error "服务健康检查失败"
    return 1
}

# ========================================
# 显示信息函数
# ========================================

show_info() {
    print_header "部署信息"

    cat << EOF
${GREEN}✓ Athena 感知模块部署完成！${NC}

${BLUE}服务信息:${NC}
  - API地址:  http://localhost:${PERCEPTION_PORT}
  - 健康检查: http://localhost:${PERCEPTION_PORT}/health
  - API文档:  http://localhost:${PERCEPTION_PORT}/docs
  - 指标端点: http://localhost:${METRICS_PORT}/metrics

${BLUE}数据库信息:${NC}
  - 主机:     ${DB_HOST}
  - 端口:     ${DB_PORT}
  - 数据库:   ${DB_NAME}
  - 用户:     ${DB_USER}

${BLUE}支持的服务:${NC}
  - 图像处理: /api/v1/perception/image
  - OCR识别:  /api/v1/perception/ocr
  - 音频处理: /api/v1/perception/audio
  - 视频处理: /api/v1/perception/video

${BLUE}智能体访问示例:${NC}
  - Athena:  curl -X POST http://localhost:${PERCEPTION_PORT}/api/v1/perception/image \\
             -H "X-Agent-ID: athena" -H "Content-Type: application/json" \\
             -d '{"image_path": "/data/image.png"}'

  - 小诺:     curl -X POST http://localhost:${PERCEPTION_PORT}/api/v1/perception/image \\
             -H "X-Agent-ID: xiaonuo" -H "Content-Type: application/json" \\
             -d '{"image_path": "/data/photo.jpg"}'

${BLUE}常用命令:${NC}
  - 查看日志: docker-compose -f ${DOCKER_COMPOSE_FILE} logs -f perception-service
  - 停止服务: docker-compose -f ${DOCKER_COMPOSE_FILE} down
  - 重启服务: docker-compose -f ${DOCKER_COMPOSE_FILE} restart
  - 查看状态: docker-compose -f ${DOCKER_COMPOSE_FILE} ps

${BLUE}监控面板:${NC}
  - Prometheus: http://localhost:9090
  - Grafana:    http://localhost:3000

${YELLOW}注意:${NC}
  - 请确保所有依赖服务（Redis, Neo4j, Qdrant）正在运行
  - 环境变量文件: ${ENV_FILE}
  - Docker Compose文件: ${DOCKER_COMPOSE_FILE}

EOF
}

# ========================================
# 主函数
# ========================================

main() {
    print_header "Athena 感知模块部署脚本"

    log_info "开始时间: $(date)"

    # 检查环境
    check_postgresql
    check_docker
    check_networks
    check_services
    check_ports

    # 初始化数据库
    init_database

    # 配置环境
    setup_environment

    # 部署服务
    deploy_service

    # 健康检查
    if health_check; then
        show_info
        log_success "部署成功完成！"
    else
        log_error "部署失败，请检查日志"
        docker-compose -f "${DOCKER_COMPOSE_FILE}" logs perception-service
        exit 1
    fi

    log_info "结束时间: $(date)"
}

# ========================================
# 执行主函数
# ========================================

main "$@"
