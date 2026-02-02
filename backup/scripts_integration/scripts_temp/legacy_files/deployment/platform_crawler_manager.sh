#!/bin/bash
# -*- coding: utf-8 -*-
# Athena工作平台 - 爬虫系统管理脚本
# Platform Crawler Management Script - 由Athena和小诺全量控制

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# 平台标识
PLATFORM_NAME="Athena工作平台"
PLATFORM_OWNER="Athena & 小诺"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 配置文件
PLATFORM_CONFIG="$PROJECT_ROOT/config/platform_crawler_config.json"
ENV_FILE="$PROJECT_ROOT/.env.platform"

# 服务路径
SERVICE_DIR="$PROJECT_ROOT/services/crawler"
API_FILE="$SERVICE_DIR/api/hybrid_crawler_api.py"
CONFIG_DIR="$PROJECT_ROOT/services/crawler/config"

# 运行时目录
PID_DIR="$PROJECT_ROOT/tmp/crawler"
RUN_DIR="$PROJECT_ROOT/run/crawler"
LOG_DIR="$PROJECT_ROOT/logs/crawler"
CACHE_DIR="$PROJECT_ROOT/cache/crawler"
TEMP_DIR="$PROJECT_ROOT/temp/crawler"

# 创建必要目录
create_directories() {
    local dirs=("$PID_DIR" "$RUN_DIR" "$LOG_DIR" "$CACHE_DIR" "$TEMP_DIR")
    for dir in "${dirs[@]}"; do
        mkdir -p "$dir"
    done
}

# 打印平台标识
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ${WHITE}$PLATFORM_NAME${PURPLE}                       ║"
    echo "║                 混合爬虫系统管理脚本                          ║"
    echo "║                控制者: ${CYAN}$PLATFORM_OWNER${PURPLE}                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 打印彩色信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_platform() {
    echo -e "${PURPLE}[PLATFORM]${NC} $1"
}

# 检查环境
check_environment() {
    print_info "检查平台环境..."

    # 检查项目根目录
    if [[ ! -d "$PROJECT_ROOT" ]]; then
        print_error "项目根目录不存在: $PROJECT_ROOT"
        exit 1
    fi

    # 检查配置文件
    if [[ ! -f "$PLATFORM_CONFIG" ]]; then
        print_error "平台配置文件不存在: $PLATFORM_CONFIG"
        exit 1
    fi

    # 检查环境变量文件
    if [[ ! -f "$ENV_FILE" ]]; then
        print_warning "环境变量文件不存在: $ENV_FILE"
        print_info "将使用默认配置"
    fi

    # 检查服务文件
    if [[ ! -f "$API_FILE" ]]; then
        print_error "爬虫API文件不存在: $API_FILE"
        exit 1
    fi

    print_success "环境检查通过"
}

# 加载环境变量
load_environment() {
    print_info "加载平台环境变量..."

    if [[ -f "$ENV_FILE" ]]; then
        # 安全地加载环境变量
        while IFS='=' read -r key value; do
            # 跳过注释和空行
            [[ $key =~ ^[[:space:]]*# ]] && continue
            [[ -z $key ]] && continue

            # 移除引号和空格
            key=$(echo "$key" | xargs)
            value=$(echo "$value" | sed 's/^["'\'']//' | sed 's/["'\'']$//' | xargs)

            # 导出环境变量
            export "$key=$value"
        done < <(grep -E '^[A-Za-z_][A-Za-z0-9_]*=' "$ENV_FILE")

        print_success "环境变量加载完成"
    else
        print_warning "未找到环境变量文件，使用系统默认值"
    fi
}

# 获取服务配置
get_service_config() {
    local key="$1"
    local default="$2"

    # 优先从环境变量获取
    local env_var="CRAWLER_$(echo "$key" | tr '[:lower:]' '[:upper:]')"
    if [[ -n "${!env_var}" ]]; then
        echo "${!env_var}"
        return
    fi

    # 从配置文件获取
    if command -v jq &> /dev/null; then
        local value=$(jq -r ".$key // empty" "$PLATFORM_CONFIG" 2>/dev/null)
        if [[ -n "$value" && "$value" != "null" ]]; then
            echo "$value"
            return
        fi
    fi

    # 返回默认值
    echo "$default"
}

# 获取服务端口
get_service_port() {
    echo "$(get_service_config "service.port" "8002")"
}

# 获取PID
get_service_pid() {
    local port=$(get_service_port)
    local pid=$(lsof -ti:"$port" 2>/dev/null)
    echo "$pid"
}

# 检查服务状态
check_service_status() {
    local pid=$(get_service_pid)
    if [[ -n "$pid" ]]; then
        echo "running"
        return 0
    else
        echo "stopped"
        return 1
    fi
}

# 健康检查
health_check() {
    local port=$(get_service_port)
    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        if curl -s "http://localhost:$port/health" | grep -q "healthy"; then
            return 0
        fi
        sleep 2
        ((attempt++))
    done

    return 1
}

# 启动服务
start_service() {
    print_platform "启动爬虫服务..."

    # 检查服务状态
    if [[ "$(check_service_status)" == "running" ]]; then
        print_warning "服务已在运行中"
        return 0
    fi

    # 创建目录
    create_directories

    # 加载环境变量
    load_environment

    # 设置Python路径
    export PYTHONPATH="$SERVICE_DIR:$PROJECT_ROOT:$PYTHONPATH"

    # 获取服务配置
    local port=$(get_service_port)
    local host=$(get_service_config "service.host" "0.0.0.0")
    local workers=$(get_service_config "service.workers" "4")

    print_info "服务配置:"
    print_info "  - 端口: $port"
    print_info "  - 主机: $host"
    print_info "  - 工作进程: $workers"

    # 启动服务
    print_platform "正在启动爬虫服务..."

    # 使用uvicorn启动
    nohup uvicorn crawler.api.hybrid_crawler_api:app \
        --host "$host" \
        --port "$port" \
        --workers "$workers" \
        --access-log \
        --log-level info \
        > "$LOG_DIR/crawler_service.log" 2>&1 &

    local pid=$!
    echo "$pid" > "$PID_DIR/crawler_service.pid"

    print_info "服务进程ID: $pid"

    # 等待服务启动
    print_info "等待服务启动..."
    if health_check; then
        print_success "爬虫服务启动成功！"
        print_info "API文档: http://localhost:$port/docs"
        print_info "健康检查: http://localhost:$port/health"
        return 0
    else
        print_error "服务启动失败或健康检查失败"
        print_info "查看日志: tail -f $LOG_DIR/crawler_service.log"
        return 1
    fi
}

# 停止服务
stop_service() {
    print_platform "停止爬虫服务..."

    local pid=$(get_service_pid)
    if [[ -z "$pid" ]]; then
        print_warning "服务未运行"
        return 0
    fi

    print_info "正在停止服务 (PID: $pid)..."

    # 优雅停止
    kill "$pid"

    # 等待进程结束
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [[ $count -lt 10 ]]; do
        sleep 1
        ((count++))
    done

    # 强制停止
    if ps -p "$pid" > /dev/null 2>&1; then
        print_warning "服务未正常停止，强制终止..."
        kill -9 "$pid"
    fi

    # 清理PID文件
    rm -f "$PID_DIR/crawler_service.pid"

    print_success "爬虫服务已停止"
}

# 重启服务
restart_service() {
    print_platform "重启爬虫服务..."
    stop_service
    sleep 2
    start_service
}

# 显示服务状态
show_status() {
    print_platform "爬虫服务状态"
    echo "================================"

    local status=$(check_service_status)
    local pid=$(get_service_pid)
    local port=$(get_service_port)

    echo -e "状态: $([ "$status" == "running" ] && echo -e "${GREEN}运行中${NC}" || echo -e "${RED}已停止${NC}")"
    [[ -n "$pid" ]] && echo "进程ID: $pid"
    echo "服务端口: $port"

    if [[ "$status" == "running" ]]; then
        # 获取详细状态
        print_info "正在获取详细状态..."
        if curl -s "http://localhost:$port/health" &> /dev/null; then
            local health_data=$(curl -s "http://localhost:$port/health")
            echo "健康检查: 通过"
            echo "API文档: http://localhost:$port/docs"
        else
            print_warning "健康检查失败"
        fi
    fi

    echo ""
    echo "服务目录:"
    echo "  PID文件: $PID_DIR"
    echo "  日志目录: $LOG_DIR"
    echo "  缓存目录: $CACHE_DIR"
    echo "  配置文件: $PLATFORM_CONFIG"
    echo "  环境变量: $ENV_FILE"
}

# 显示日志
show_logs() {
    local follow=false
    local lines=50

    while [[ $# -gt 0 ]]; do
        case $1 in
            -f|--follow)
                follow=true
                shift
                ;;
            -n|--lines)
                lines="$2"
                shift 2
                ;;
            *)
                print_error "未知参数: $1"
                exit 1
                ;;
        esac
    done

    local log_file="$LOG_DIR/crawler_service.log"

    if [[ ! -f "$log_file" ]]; then
        print_error "日志文件不存在: $log_file"
        return 1
    fi

    print_info "显示爬虫服务日志..."

    if [[ "$follow" == "true" ]]; then
        tail -f "$log_file"
    else
        tail -n "$lines" "$log_file"
    fi
}

# 测试服务
test_service() {
    print_platform "测试爬虫服务..."

    local port=$(get_service_port)
    local base_url="http://localhost:$port"

    # 检查服务是否运行
    if [[ "$(check_service_status)" != "running" ]]; then
        print_error "服务未运行，无法测试"
        return 1
    fi

    print_info "执行健康检查..."
    if curl -s "$base_url/health" | jq . 2>/dev/null; then
        print_success "健康检查通过"
    else
        print_error "健康检查失败"
        return 1
    fi

    print_info "检查API文档..."
    if curl -s "$base_url/docs" | grep -q "swagger"; then
        print_success "API文档可访问"
    else
        print_warning "API文档访问异常"
    fi

    print_info "检查系统配置..."
    if curl -s "$base_url/config" | jq . 2>/dev/null; then
        print_success "系统配置正常"
    else
        print_warning "系统配置检查失败"
    fi

    print_info "检查系统统计..."
    if curl -s "$base_url/stats" | jq . 2>/dev/null; then
        print_success "系统统计正常"
    else
        print_warning "系统统计检查失败"
    fi

    print_success "服务测试完成"
}

# 清理缓存
cleanup_cache() {
    print_platform "清理爬虫缓存..."

    if [[ -d "$CACHE_DIR" ]]; then
        local cache_size=$(du -sh "$CACHE_DIR" 2>/dev/null | cut -f1)
        print_info "当前缓存大小: $cache_size"

        rm -rf "$CACHE_DIR"/*
        print_success "缓存清理完成"
    else
        print_info "缓存目录不存在，无需清理"
    fi
}

# 备份配置
backup_config() {
    print_platform "备份爬虫配置..."

    local backup_dir="$PROJECT_ROOT/backup/crawler"
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="$backup_dir/crawler_config_$timestamp.tar.gz"

    mkdir -p "$backup_dir"

    tar -czf "$backup_file" \
        -C "$PROJECT_ROOT" \
        config/platform_crawler_config.json \
        .env.platform \
        services/crawler/config/ \
        2>/dev/null

    if [[ -f "$backup_file" ]]; then
        local backup_size=$(du -sh "$backup_file" | cut -f1)
        print_success "配置备份完成: $backup_file ($backup_size)"
    else
        print_error "配置备份失败"
    fi
}

# 显示帮助信息
show_help() {
    print_banner
    echo -e "${CYAN}用法:${NC} $0 [命令] [选项]"
    echo ""
    echo -e "${CYAN}命令:${NC}"
    echo "  start              启动爬虫服务"
    echo "  stop               停止爬虫服务"
    echo "  restart            重启爬虫服务"
    echo "  status             显示服务状态"
    echo "  logs               显示服务日志"
    echo "  test               测试服务功能"
    echo "  health             健康检查"
    echo "  cleanup            清理缓存"
    echo "  backup             备份配置"
    echo ""
    echo -e "${CYAN}选项:${NC}"
    echo "  -f, --follow       跟踪日志输出"
    echo "  -n, --lines NUM    显示最后N行日志"
    echo "  -h, --help         显示帮助信息"
    echo ""
    echo -e "${CYAN}示例:${NC}"
    echo "  $0 start           # 启动服务"
    echo "  $0 logs -f         # 跟踪日志"
    echo "  $0 test            # 测试服务"
    echo ""
    echo -e "${PURPLE}控制者: $PLATFORM_OWNER${NC}"
}

# 主函数
main() {
    # 检查是否提供了参数
    if [[ $# -eq 0 ]]; then
        show_help
        exit 1
    fi

    # 显示平台标识
    print_banner

    # 检查环境
    check_environment

    # 解析命令
    case "$1" in
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            shift
            show_logs "$@"
            ;;
        test)
            test_service
            ;;
        health)
            if health_check; then
                print_success "健康检查通过"
                exit 0
            else
                print_error "健康检查失败"
                exit 1
            fi
            ;;
        cleanup)
            cleanup_cache
            ;;
        backup)
            backup_config
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主程序
main "$@"