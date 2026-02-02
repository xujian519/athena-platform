#!/bin/bash

# Athena平台一键启动脚本
# Athena Platform One-Click Startup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Logo
print_logo() {
    echo -e "${PURPLE}"
    echo "    __     __    __     __   __     ______  "
    echo "   /  \   /  \  /  \   /  \ /  \   /      \\ "
    echo "  /    \/    \/    \/    \/    \ |  ,----' "
    echo "  |  |\__/|  |\__/|  |\__/|  |\__/|  |      "
    echo "  |  |    |  |    |  |    |  |    |  `----. "
    echo "   \  \__/ \  \__/ \  \__/ \  \__/ \______| "
    echo -e "    ${CYAN}云熙专利管理AI平台 v2.0${NC}"
    echo ""
}

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

log_step() {
    echo -e "\n${CYAN}[STEP]${NC} $1"
}

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# 检查系统要求
check_requirements() {
    log_step "检查系统要求..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        echo "  安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi

    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        echo "  安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi

    # 检查内存
    TOTAL_MEM=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$TOTAL_MEM" -lt 8 ]; then
        log_warn "系统内存少于8GB，可能影响性能"
    fi

    # 检查磁盘空间
    AVAILABLE_SPACE=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [ "$AVAILABLE_SPACE" -lt 20 ]; then
        log_warn "可用磁盘空间少于20GB，可能影响运行"
    fi

    log_info "✓ 系统要求检查通过"
}

# 检查配置文件
check_configs() {
    log_step "检查配置文件..."

    # 检查环境配置文件
    if [ ! -f ".env.production" ]; then
        log_error "未找到 .env.production 文件"
        log_info "请复制 .env.example 到 .env.production 并配置相关参数"
        exit 1
    fi

    # 检查Docker Compose文件
    if [ ! -f "docker-compose.production.yml" ]; then
        log_error "未找到 docker-compose.production.yml 文件"
        exit 1
    fi

    # 检查监控配置
    if [ ! -d "config/monitoring" ]; then
        log_warn "监控配置目录不存在，将跳过监控服务"
    fi

    log_info "✓ 配置文件检查通过"
}

# 创建必要的目录
create_directories() {
    log_step "创建必要的目录..."

    # 数据目录
    mkdir -p data/{postgres,redis,qdrant,neo4j,elasticsearch,mongodb,rabbitmq}
    mkdir -p data/{vectors_qdrant,knowledge_graph_sqlite}

    # 日志目录
    mkdir -p logs/{services,monitoring,deployment}

    # 临时目录
    mkdir -p tmp/cache

    # 设置权限
    chmod 755 data logs tmp

    log_info "✓ 目录创建完成"
}

# 启动基础设施服务
start_infrastructure() {
    log_step "启动基础设施服务..."

    # 加载环境变量
    source .env.production

    # 启动数据库和中间件
    docker-compose -f docker-compose.production.yml up -d \
        postgres \
        redis \
        qdrant \
        neo4j \
        elasticsearch \
        rabbitmq

    log_info "等待基础设施服务启动..."
    sleep 30

    # 检查服务状态
    log_info "检查基础设施服务状态..."

    # PostgreSQL
    if docker-compose -f docker-compose.production.yml exec -T postgres pg_isready -U ${POSTGRES_USER:-athena_admin} > /dev/null 2>&1; then
        log_info "✓ PostgreSQL 运行正常"
    else
        log_error "✗ PostgreSQL 启动失败"
    fi

    # Redis
    if docker-compose -f docker-compose.production.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_info "✓ Redis 运行正常"
    else
        log_error "✗ Redis 启动失败"
    fi

    # Qdrant
    if curl -s http://localhost:${QDRANT_PORT:-6333}/health > /dev/null; then
        log_info "✓ Qdrant 运行正常"
    else
        log_error "✗ Qdrant 启动失败"
    fi

    # Neo4j
    if curl -s http://localhost:${NEO4J_PORT:-7474} > /dev/null; then
        log_info "✓ Neo4j 运行正常"
    else
        log_error "✗ Neo4j 启动失败"
    fi

    # Elasticsearch
    if curl -s http://localhost:${ELASTICSEARCH_PORT:-9200}/_cluster/health > /dev/null; then
        log_info "✓ Elasticsearch 运行正常"
    else
        log_error "✗ Elasticsearch 启动失败"
    fi
}

# 启动核心服务
start_core_services() {
    log_step "启动核心服务..."

    # 启动API网关
    docker-compose -f docker-compose.production.yml up -d api-gateway

    # 启动业务服务
    docker-compose -f docker-compose.production.yml up -d \
        patent-service \
        user-service \
        search-service \
        crawler-service

    log_info "等待核心服务启动..."
    sleep 20

    # 检查服务状态
    log_info "检查核心服务状态..."

    services=(
        "API网关:8080"
        "专利服务:8001"
        "用户服务:8002"
        "搜索服务:8003"
        "爬虫服务:8300"
    )

    for service in "${services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)

        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            log_info "✓ $name 运行正常 (http://localhost:$port)"
        else
            log_warn "⚠ $name 可能还在启动中..."
        fi
    done
}

# 启动监控服务
start_monitoring() {
    log_step "启动监控服务..."

    # 检查是否配置了监控
    if [ -d "config/monitoring" ] && [ -f "config/monitoring/prometheus.yml" ]; then
        # 启动监控服务
        docker-compose -f docker-compose.production.yml up -d \
            prometheus \
            grafana \
            jaeger \
            health-checker

        log_info "等待监控服务启动..."
        sleep 15

        # 检查监控服务
        if curl -s http://localhost:${PROMETHEUS_PORT:-9090}/-/healthy > /dev/null; then
            log_info "✓ Prometheus 运行正常 (http://localhost:${PROMETHEUS_PORT:-9090})"
        fi

        if curl -s http://localhost:${GRAFANA_PORT:-3000}/api/health > /dev/null; then
            log_info "✓ Grafana 运行正常 (http://localhost:${GRAFANA_PORT:-3000})"
        fi

        if curl -s http://localhost:${JAEGER_PORT:-16686}/ > /dev/null; then
            log_info "✓ Jaeger 运行正常 (http://localhost:${JAEGER_PORT:-16686})"
        fi
    else
        log_warn "监控配置未找到，跳过监控服务启动"
    fi
}

# 显示服务状态
show_status() {
    log_step "服务运行状态..."

    echo ""
    docker-compose -f docker-compose.production.yml ps
    echo ""
}

# 显示访问信息
show_access_info() {
    echo -e "\n${CYAN}========================================${NC}"
    echo -e "${GREEN}Athena平台启动完成！${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}📋 服务访问地址：${NC}"
    echo ""
    echo -e "  ${BLUE}API网关:${NC}        http://localhost:${API_GATEWAY_PORT:-8080}"
    echo -e "  ${BLUE}专利服务:${NC}        http://localhost:${PATENT_SERVICE_PORT:-8001}"
    echo -e "  ${BLUE}用户服务:${NC}        http://localhost:${USER_SERVICE_PORT:-8002}"
    echo -e "  ${BLUE}搜索服务:${NC}        http://localhost:${SEARCH_SERVICE_PORT:-8003}"
    echo -e "  ${BLUE}爬虫服务:${NC}        http://localhost:${CRAWLER_SERVICE_PORT:-8300}"
    echo ""
    echo -e "${YELLOW}🔧 管理工具：${NC}"
    echo ""
    echo -e "  ${BLUE}Grafana监控:${NC}     http://localhost:${GRAFANA_PORT:-3000} (admin/athena_grafana_2024!)"
    echo -e "  ${BLUE}Prometheus:${NC}      http://localhost:${PROMETHEUS_PORT:-9090}"
    echo -e "  ${BLUE}Jaeger追踪:${NC}      http://localhost:${JAEGER_PORT:-16686}"
    echo -e "  ${BLUE}健康检查:${NC}        http://localhost:9999"
    echo ""
    echo -e "${YELLOW}🗄️  数据库管理：${NC}"
    echo ""
    echo -e "  ${BLUE}PostgreSQL:${NC}      localhost:${POSTGRES_PORT:-5432}"
    echo -e "  ${BLUE}Redis:${NC}           localhost:${REDIS_PORT:-6379}"
    echo -e "  ${BLUE}Qdrant:${NC}          localhost:${QDRANT_PORT:-6333}"
    echo -e "  ${BLUE}Neo4j:${NC}           localhost:${NEO4J_PORT:-7474} (neo4j/athena_neo4j_2024!)"
    echo -e "  ${BLUE}Elasticsearch:${NC}    localhost:${ELASTICSEARCH_PORT:-9200}"
    echo ""
    echo -e "${YELLOW}📝 常用命令：${NC}"
    echo ""
    echo -e "  查看所有服务状态: ${BLUE}docker-compose -f docker-compose.production.yml ps${NC}"
    echo -e "  查看服务日志:     ${BLUE}docker-compose -f docker-compose.production.yml logs -f [服务名]${NC}"
    echo -e "  重启服务:         ${BLUE}docker-compose -f docker-compose.production.yml restart [服务名]${NC}"
    echo -e "  停止所有服务:     ${BLUE}docker-compose -f docker-compose.production.yml down${NC}"
    echo ""
    echo -e "${YELLOW}📚 文档地址：${NC}"
    echo ""
    echo -e "  ${BLUE}API文档:${NC}          http://localhost:${API_GATEWAY_PORT:-8080}/docs"
    echo -e "  ${BLUE}项目文档:${NC}          ./documentation/"
    echo ""
    echo -e "${CYAN}========================================${NC}"
}

# 错误处理
handle_error() {
    log_error "启动过程中发生错误，正在清理..."
    docker-compose -f docker-compose.production.yml down
    exit 1
}

# 主函数
main() {
    # 设置错误处理
    trap handle_error ERR

    # 打印Logo
    print_logo

    # 检查要求
    check_requirements

    # 检查配置
    check_configs

    # 创建目录
    create_directories

    # 启动基础设施
    start_infrastructure

    # 启动核心服务
    start_core_services

    # 启动监控（可选）
    if [ "$1" != "--no-monitoring" ]; then
        start_monitoring
    fi

    # 显示状态
    show_status

    # 显示访问信息
    show_access_info
}

# 显示帮助信息
show_help() {
    echo "Athena平台启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --no-monitoring    不启动监控服务"
    echo "  --help             显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0                启动所有服务"
    echo "  $0 --no-monitoring 启动核心服务，不启动监控"
}

# 处理命令行参数
case "$1" in
    --help|-h)
        show_help
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac