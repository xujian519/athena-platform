#!/bin/bash
# ============================================================
# AI伦理框架 - 容器启动脚本
# AI Ethics Framework - Container Entrypoint
# ============================================================

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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

# 检查环境变量
check_env_vars() {
    log_info "检查环境变量..."

    required_vars=(
        "ENVIRONMENT"
        "DATABASE_URL"
        "REDIS_URL"
    )

    optional_vars=(
        "ETHICS_CONFIG_PATH"
        "PROMETHEUS_PORT"
        "API_PORT"
        "LOG_LEVEL"
    )

    # 检查必需的环境变量
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "必需的环境变量 $var 未设置"
            exit 1
        fi
    done

    # 设置可选的环境变量默认值
    export ETHICS_CONFIG_PATH="${ETHICS_CONFIG_PATH:-/app/config/ethics_config.production.yaml}"
    export PROMETHEUS_PORT="${PROMETHEUS_PORT:-9091}"
    export API_PORT="${API_PORT:-8080}"
    export LOG_LEVEL="${LOG_LEVEL:-INFO}"

    log_info "环境变量检查完成"
}

# 等待依赖服务
wait_for_dependencies() {
    log_info "等待依赖服务..."

    # 等待PostgreSQL
    if [ -n "$DATABASE_URL" ]; then
        log_info "等待 PostgreSQL..."
        until python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')" 2>/dev/null; do
            log_warn "PostgreSQL 不可用，等待重试..."
            sleep 2
        done
        log_info "PostgreSQL 已就绪"
    fi

    # 等待Redis
    if [ -n "$REDIS_URL" ]; then
        log_info "等待 Redis..."
        until python -c "import redis; redis.from_url('$REDIS_URL').ping()" 2>/dev/null; do
            log_warn "Redis 不可用，等待重试..."
            sleep 2
        done
        log_info "Redis 已就绪"
    fi

    log_info "所有依赖服务已就绪"
}

# 初始化应用
initialize_app() {
    log_info "初始化应用..."

    # 创建必要的目录
    mkdir -p /var/log/athena
    mkdir -p /var/run/athena

    # 检查配置文件
    if [ ! -f "$ETHICS_CONFIG_PATH" ]; then
        log_error "配置文件不存在: $ETHICS_CONFIG_PATH"
        exit 1
    fi

    log_info "使用配置文件: $ETHICS_CONFIG_PATH"

    # 运行数据库迁移（如果需要）
    # log_info "运行数据库迁移..."
    # python -m core.ethics.migrations upgrade

    log_info "应用初始化完成"
}

# 启动应用
start_app() {
    log_info "启动 AI伦理框架..."
    log_info "环境: $ENVIRONMENT"
    log_info "API端口: $API_PORT"
    log_info "Prometheus端口: $PROMETHEUS_PORT"

    # 启动Prometheus监控器
    log_info "启动 Prometheus 监控器..."
    python -m core.ethics.monitoring_prometheus &
    PROMETHEUS_PID=$!

    # 启动API服务
    log_info "启动 API 服务..."
    exec python -m uvicorn core.api.main:app \
        --host 0.0.0.0 \
        --port $API_PORT \
        --workers 4 \
        --log-level $LOG_LEVEL \
        --access-log \
        --proxy-headers
}

# 优雅关闭
graceful_shutdown() {
    log_info "接收到关闭信号，执行优雅关闭..."

    if [ -n "$PROMETHEUS_PID" ]; then
        log_info "停止 Prometheus 监控器..."
        kill $PROMETHEUS_PID 2>/dev/null || true
    fi

    log_info "应用已停止"
    exit 0
}

# 信号处理
trap graceful_shutdown SIGTERM SIGINT

# 主流程
main() {
    log_info "=========================================="
    log_info "Athena AI伦理框架启动中..."
    log_info "版本: 1.0.0"
    log_info "=========================================="

    check_env_vars
    wait_for_dependencies
    initialize_app
    start_app
}

# 执行主流程
main "$@"
