#!/bin/bash
# Athena工作平台 - 生产环境部署脚本
# Production Deployment Script for Athena Platform
#
# 用途: 自动部署执行模块到生产环境
# 使用: ./scripts/deploy_to_production.sh [options]
#
# 选项:
#   --env <environment>  部署环境 (production|staging, 默认: production)
#   --tag <image_tag>     Docker镜像标签 (默认: latest)
#   --skip-tests          跳过测试
#   --force               强制部署（跳过确认）
#   --dry-run             模拟运行（不实际部署）

set -e  # 遇到错误立即退出
set -u  # 使用未定义的变量时退出
set -o pipefail  # 管道中任一命令失败则退出

# ==========================================
# 配置
# ==========================================

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
ENVIRONMENT="${ENVIRONMENT:-production}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
SKIP_TESTS="${SKIP_TESTS:-false}"
FORCE_DEPLOY="${FORCE_DEPLOY:-false}"
DRY_RUN="${DRY_RUN:-false}"

# PostgreSQL配置（本地17.7版本）
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-athena_production}"
POSTGRES_USER="${POSTGRES_USER:-athena}"

# 执行引擎配置
EXECUTION_CONFIG="${EXECUTION_CONFIG:-config/production.yaml}"
EXECUTION_LOG_DIR="${EXECUTION_LOG_DIR:-/var/log/athena/execution}"
EXECUTION_DATA_DIR="${EXECUTION_DATA_DIR:-/var/lib/athena/execution}"
EXECUTION_PID_FILE="${EXECUTION_PID_FILE:-/var/run/athena-execution.pid}"

# ==========================================
# 日志函数
# ==========================================

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
    echo -e "\n${GREEN}==>${NC} $1"
}

# ==========================================
# 工具函数
# ==========================================

# 显示使用说明
show_usage() {
    cat << EOF
使用方法: $0 [options]

选项:
  --env <environment>  部署环境 (production|staging, 默认: production)
  --tag <image_tag>     Docker镜像标签 (默认: latest)
  --skip-tests          跳过测试
  --force               强制部署（跳过确认）
  --dry-run             模拟运行（不实际部署）
  -h, --help            显示此帮助信息

示例:
  $0 --env production --tag v1.0.0
  $0 --env staging --dry-run
  $0 --force --skip-tests

环境变量:
  ENVIRONMENT           部署环境
  IMAGE_TAG             Docker镜像标签
  SKIP_TESTS            跳过测试
  FORCE_DEPLOY          强制部署
  DRY_RUN               模拟运行

EOF
}

# 解析命令行参数
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            --tag)
                IMAGE_TAG="$2"
                shift 2
                ;;
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --force)
                FORCE_DEPLOY=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_usage
                exit 1
                ;;
        esac
    done
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        log_warning "建议使用root用户执行此脚本（需要写入系统目录）"
        if [ "$DRY_RUN" = false ]; then
            read -p "继续执行? (y/N) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                log_info "部署已取消"
                exit 0
            fi
        fi
    fi
}

# 检查PostgreSQL连接
check_postgres() {
    log_step "检查PostgreSQL连接..."
    if ! PGPASSWORD="${POSTGRES_PASSWORD:-athena123}" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" &> /dev/null; then
        log_error "无法连接到PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT"
        log_info "请确保PostgreSQL 17.7正在运行，并且数据库和用户已创建"
        return 1
    fi
    log_success "PostgreSQL连接正常"
    return 0
}

# 创建必要的目录
create_directories() {
    log_step "创建必要的目录..."
    local dirs=(
        "$EXECUTION_LOG_DIR"
        "$EXECUTION_DATA_DIR/tasks"
        "$EXECUTION_DATA_DIR/state"
        "$EXECUTION_DATA_DIR/cache"
        "/var/run/athena"
    )

    for dir in "${dirs[@]}"; do
        if [ "$DRY_RUN" = true ]; then
            log_info "[DRY-RUN] 创建目录: $dir"
        else
            mkdir -p "$dir"
            log_success "创建目录: $dir"
        fi
    done

    # 设置权限
    if [ "$DRY_RUN" = false ]; then
        chmod -R 755 "$EXECUTION_LOG_DIR"
        chmod -R 755 "$EXECUTION_DATA_DIR"
        log_success "目录权限设置完成"
    fi
}

# 停止当前运行的执行引擎
stop_execution_engine() {
    log_step "停止当前运行的执行引擎..."
    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] 停止执行引擎"
        return 0
    fi

    if [ -f "$EXECUTION_PID_FILE" ]; then
        local pid=$(cat "$EXECUTION_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_info "停止进程 $pid..."
            kill "$pid" || true
            sleep 5
            if ps -p "$pid" > /dev/null 2>&1; then
                log_warning "进程未响应，强制停止..."
                kill -9 "$pid" || true
            fi
        fi
        rm -f "$EXECUTION_PID_FILE"
        log_success "执行引擎已停止"
    else
        log_info "未找到运行中的执行引擎"
    fi
}

# 部署新的执行引擎
deploy_execution_engine() {
    log_step "部署新的执行引擎..."

    # 检查配置文件
    if [ ! -f "$EXECUTION_CONFIG" ]; then
        log_error "配置文件不存在: $EXECUTION_CONFIG"
        return 1
    fi

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] 部署执行引擎"
        log_info "[DRY-RUN] 配置文件: $EXECUTION_CONFIG"
        log_info "[DRY-RUN] 日志目录: $EXECUTION_LOG_DIR"
        log_info "[DRY-RUN] 数据目录: $EXECUTION_DATA_DIR"
        return 0
    fi

    # 复制配置文件到系统目录
    local system_config="/etc/athena/execution/production.yaml"
    mkdir -p "$(dirname "$system_config")"
    cp "$EXECUTION_CONFIG" "$system_config"
    log_success "配置文件已安装: $system_config"

    # 创建systemd服务文件（如果使用Linux）
    if [ "$(uname)" = "Linux" ] && command -v systemctl &> /dev/null; then
        local service_file="/etc/systemd/system/athena-execution.service"
        cat > "$service_file" << EOF
[Unit]
Description=Athena Execution Engine
After=network.target postgresql.service

[Service]
Type=simple
User=athena
Group=athena
WorkingDirectory=$PROJECT_ROOT
Environment="PYTHONPATH=$PROJECT_ROOT"
Environment="ATHENA_CONFIG=$system_config"
Environment="DATABASE_URL=postgresql://$POSTGRES_USER:\${POSTGRES_PASSWORD}@localhost:5432/$POSTGRES_DB"
ExecStart=$(which python3) -m athena.execution.engine
Restart=always
RestartSec=10
StandardOutput=append:$EXECUTION_LOG_DIR/execution.log
StandardError=append:$EXECUTION_LOG_DIR/execution-error.log

[Install]
WantedBy=multi-user.target
EOF
        log_success "systemd服务文件已创建: $service_file"
        systemctl daemon-reload
        systemctl enable athena-execution.service
        log_success "执行引擎服务已启用"
    fi

    log_success "执行引擎部署完成"
}

# 初始化数据库
initialize_database() {
    log_step "初始化数据库..."

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] 初始化数据库"
        return 0
    fi

    # 运行数据库迁移脚本
    if [ -f scripts/init_database.sql ]; then
        log_info "执行数据库迁移脚本..."
        PGPASSWORD="${POSTGRES_PASSWORD:-athena123}" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f scripts/init_database.sql
        log_success "数据库迁移完成"
    fi

    # 运行Python初始化脚本
    if [ -f scripts/init_athena_db.py ]; then
        log_info "执行Python初始化脚本..."
        python3 scripts/init_athena_db.py --env "$ENVIRONMENT"
        log_success "数据库初始化完成"
    fi
}

# 启动执行引擎
start_execution_engine() {
    log_step "启动执行引擎..."

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] 启动执行引擎"
        return 0
    fi

    # 使用systemd启动（如果可用）
    if [ "$(uname)" = "Linux" ] && command -v systemctl &> /dev/null; then
        systemctl start athena-execution.service
        log_success "执行引擎已启动（systemd）"
        return 0
    fi

    # macOS或无systemd环境，使用后台进程
    log_info "以后台进程方式启动执行引擎..."
    nohup python3 -m athena.execution.engine \
        --config "$EXECUTION_CONFIG" \
        > "$EXECUTION_LOG_DIR/execution.stdout.log" 2> "$EXECUTION_LOG_DIR/execution.stderr.log" &
    local pid=$!
    echo "$pid" > "$EXECUTION_PID_FILE"
    log_success "执行引擎已启动（PID: $pid）"
}

# 健康检查
health_check() {
    log_step "执行健康检查..."

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] 健康检查"
        return 0
    fi

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10

    # 检查进程
    if [ -f "$EXECUTION_PID_FILE" ]; then
        local pid=$(cat "$EXECUTION_PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_success "执行引擎进程运行正常（PID: $pid）"
        else
            log_error "执行引擎进程未运行"
            return 1
        fi
    fi

    # 检查HTTP健康端点
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8080/health &> /dev/null; then
            log_success "健康检查通过"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done

    log_error "健康检查失败"
    return 1
}

# 运行冒烟测试
run_smoke_tests() {
    if [ "$SKIP_TESTS" = true ]; then
        log_info "跳过测试"
        return 0
    fi

    log_step "运行冒烟测试..."

    if [ "$DRY_RUN" = true ]; then
        log_info "[DRY-RUN] 冒烟测试"
        return 0
    fi

    if [ -f scripts/smoke_tests.py ]; then
        python3 scripts/smoke_tests.py --env "$ENVIRONMENT"
        log_success "冒烟测试通过"
    else
        log_warning "冒烟测试脚本不存在，跳过"
    fi
}

# 显示部署摘要
show_deployment_summary() {
    log_step "部署摘要"
    echo ""
    echo "部署环境: $ENVIRONMENT"
    echo "镜像标签: $IMAGE_TAG"
    echo "配置文件: $EXECUTION_CONFIG"
    echo "日志目录: $EXECUTION_LOG_DIR"
    echo "数据目录: $EXECUTION_DATA_DIR"
    echo "PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        log_warning "DRY-RUN模式: 未实际部署"
    fi
}

# ==========================================
# 主函数
# ==========================================

main() {
    # 解析参数
    parse_args "$@"

    # 显示标题
    echo -e "${BLUE}"
    echo "============================================"
    echo "  Athena工作平台 - 生产环境部署"
    echo "============================================"
    echo -e "${NC}"
    echo "项目根目录: $PROJECT_ROOT"
    echo "部署环境: $ENVIRONMENT"
    echo "镜像标签: $IMAGE_TAG"
    echo ""

    # 确认部署
    if [ "$FORCE_DEPLOY" = false ] && [ "$DRY_RUN" = false ]; then
        log_warning "即将部署到生产环境"
        read -p "确认部署? (y/N) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_info "部署已取消"
            exit 0
        fi
    fi

    # 执行部署步骤
    check_root || exit 1
    check_postgres || exit 1
    create_directories || exit 1
    stop_execution_engine || exit 1
    deploy_execution_engine || exit 1
    initialize_database || exit 1
    start_execution_engine || exit 1
    health_check || exit 1
    run_smoke_tests || exit 1
    show_deployment_summary

    log_success "部署完成"
}

# 执行主函数
main "$@"
