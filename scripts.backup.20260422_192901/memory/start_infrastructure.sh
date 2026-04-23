#!/bin/bash
# ============================================================================
# Athena记忆模块 - 基础设施一键启动脚本
# ============================================================================
#
# 此脚本自动启动记忆模块所需的所有基础设施
#
# 使用方法:
#   ./scripts/memory/start_infrastructure.sh
#
# 功能:
#   1. 检查Docker和Docker Compose
#   2. 加载环境配置
#   3. 启动PostgreSQL、Redis、Qdrant
#   4. 等待服务就绪
#   5. 运行健康检查
#   6. 初始化记忆系统
#
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
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

# 打印带边框的标题
print_header() {
    local text="$1"
    local width=60
    local padding=$(( (width - ${#text}) / 2 ))

    echo ""
    echo "===================================="
    printf "%${padding}s%s\n" "" "$text"
    echo "===================================="
    echo ""
}

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装，请先安装"
        exit 1
    fi
}

# 等待服务就绪
wait_for_service() {
    local service_name="$1"
    local check_command="$2"
    local max_attempts=30
    local attempt=1

    log_info "等待 $service_name 启动..."

    while [ $attempt -le $max_attempts ]; do
        if eval "$check_command" &> /dev/null; then
            log_success "$service_name 已就绪"
            return 0
        fi

        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done

    echo ""
    log_error "$service_name 启动超时"
    return 1
}

# 主函数
main() {
    print_header "Athena记忆模块 - 基础设施启动"

    # ============================================================================
    # 1. 环境检查
    # ============================================================================
    print_header "步骤1: 环境检查"

    log_info "检查Docker..."
    check_command docker
    log_success "Docker已安装: $(docker --version)"

    log_info "检查Docker Compose..."
    check_command docker-compose
    log_success "Docker Compose已安装: $(docker-compose --version)"

    # ============================================================================
    # 2. 配置加载
    # ============================================================================
    print_header "步骤2: 配置加载"

    # 查找配置文件
    ENV_FILE=""
    if [ -f ".env.production" ]; then
        ENV_FILE=".env.production"
    elif [ -f ".env" ]; then
        ENV_FILE=".env"
    elif [ -f "config/memory/production.env" ]; then
        ENV_FILE="config/memory/production.env"
    else
        log_warning "未找到配置文件，使用默认配置"
        log_warning "建议创建 .env 文件并配置数据库密码"
    fi

    if [ -n "$ENV_FILE" ]; then
        log_info "加载配置文件: $ENV_FILE"
        export $(cat $ENV_FILE | grep -v '^#' | xargs)
        log_success "配置已加载"
    fi

    # ============================================================================
    # 3. 启动基础设施
    # ============================================================================
    print_header "步骤3: 启动基础设施"

    COMPOSE_FILE="config/docker/docker-compose.memory.yml"

    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "Docker Compose文件不存在: $COMPOSE_FILE"
        exit 1
    fi

    log_info "启动Docker服务..."
    docker-compose -f "$COMPOSE_FILE" up -d

    log_success "Docker服务已启动"

    # ============================================================================
    # 4. 等待服务就绪
    # ============================================================================
    print_header "步骤4: 等待服务就绪"

    # PostgreSQL
    wait_for_service "PostgreSQL" \
        "docker exec athena_memory_postgres pg_isready -U ${MEMORY_DB_USER:-athena_admin}"

    # Redis
    wait_for_service "Redis" \
        "docker exec athena_memory_redis redis-cli -a '${REDIS_PASSWORD:-athena_redis_password}' ping"

    # Qdrant
    wait_for_service "Qdrant" \
        "curl -f http://localhost:${QDRANT_PORT:-6333}/health"

    # ============================================================================
    # 5. 健康检查
    # ============================================================================
    print_header "步骤5: 健康检查"

    log_info "运行服务健康检查..."

    echo ""
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""

    log_success "所有服务运行正常"

    # ============================================================================
    # 6. 数据库初始化
    # ============================================================================
    print_header "步骤6: 数据库初始化"

    log_info "检查数据库表..."

    # 检查memories表是否存在
    TABLE_EXISTS=$(docker exec athena_memory_postgres psql \
        -U ${MEMORY_DB_USER:-athena_admin} \
        -d ${MEMORY_DB_NAME:-athena_memory} \
        -tAc "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'memories')")

    if [ "$TABLE_EXISTS" = "t" ]; then
        log_success "数据库表已存在"
    else
        log_warning "数据库表不存在，将在首次初始化时自动创建"
    fi

    # ============================================================================
    # 7. 初始化记忆系统
    # ============================================================================
    print_header "步骤7: 初始化记忆系统"

    if [ -f "scripts/memory/init_production.py" ]; then
        log_info "运行记忆系统初始化..."

        if [ -n "$ENV_FILE" ]; then
            python scripts/memory/init_production.py --config "$ENV_FILE"
        else
            python scripts/memory/init_production.py
        fi

        if [ $? -eq 0 ]; then
            log_success "记忆系统初始化成功"
        else
            log_warning "记忆系统初始化遇到问题，但基础设施已启动"
        fi
    else
        log_warning "未找到初始化脚本，跳过"
    fi

    # ============================================================================
    # 完成
    # ============================================================================
    print_header "启动完成"

    log_success "所有服务已启动并就绪！"
    echo ""
    echo "📊 服务访问信息:"
    echo "  PostgreSQL: ${MEMORY_DB_HOST:-localhost}:${MEMORY_DB_PORT:-5432}"
    echo "  Redis: ${REDIS_HOST:-localhost}:${REDIS_PORT:-6379}"
    echo "  Qdrant: http://${QDRANT_HOST:-localhost}:${QDRANT_PORT:-6333}"
    echo ""
    echo "📝 管理工具:"
    echo "  pgAdmin: http://localhost:${PGADMIN_PORT:-5050}"
    echo "  Redis Commander: http://localhost:${REDIS_COMMANDER_PORT:-8081}"
    echo ""
    echo "🔧 常用命令:"
    echo "  查看日志: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  停止服务: docker-compose -f $COMPOSE_FILE down"
    echo "  重启服务: docker-compose -f $COMPOSE_FILE restart"
    echo ""
    echo "📖 文档: docs/DEPLOYMENT_MEMORY.md"
    echo ""
}

# 捕获Ctrl+C
trap 'log_warning "启动被中断"; exit 1' INT

# 运行主函数
main "$@"
