#!/bin/bash
# -*- coding: utf-8 -*-
# 混合爬虫服务启动脚本
# Hybrid Crawler Service Startup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SERVICE_DIR="$PROJECT_ROOT/services/crawler"
HYBRID_API_DIR="$SERVICE_DIR/api/hybrid_crawler_api.py"
LEGACY_API_DIR="$SERVICE_DIR/api/crawler_api.py"
CONFIG_DIR="$PROJECT_ROOT/services/crawler/config"
PID_DIR="$PROJECT_ROOT/tmp/crawler"
LOG_DIR="$PROJECT_ROOT/logs/crawler"

# 创建必要目录
mkdir -p "$PID_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$CONFIG_DIR"

# 默认配置
DEFAULT_PORT=8002
DEFAULT_HOST="0.0.0.0"
DEFAULT_MODE="hybrid"  # hybrid, legacy, both

# 函数：打印彩色信息
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

# 函数：显示帮助信息
show_help() {
    echo "Athena混合爬虫服务启动脚本"
    echo ""
    echo "用法: $0 [选项] [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动爬虫服务"
    echo "  stop      停止爬虫服务"
    echo "  restart   重启爬虫服务"
    echo "  status    查看服务状态"
    echo "  test      测试服务连通性"
    echo "  logs      查看服务日志"
    echo ""
    echo "选项:"
    echo "  -p, --port PORT     服务端口 (默认: $DEFAULT_PORT)"
    echo "  -h, --host HOST     服务主机 (默认: $DEFAULT_HOST)"
    echo "  -m, --mode MODE     运行模式 (hybrid, legacy, both)"
    echo "  -d, --daemon        后台运行"
    echo "  -v, --verbose       详细输出"
    echo "  --config FILE       指定配置文件"
    echo "  --help              显示帮助信息"
    echo ""
    echo "运行模式说明:"
    echo "  hybrid   - 启动增强版混合爬虫API (推荐)"
    echo "  legacy   - 启动传统爬虫API"
    echo "  both     - 同时启动两个API (不同端口)"
    echo ""
    echo "示例:"
    echo "  $0 start                           # 启动混合爬虫服务"
    echo "  $0 start -m legacy -p 8001          # 启动传统爬虫服务在8001端口"
    echo "  $0 start -m both                    # 同时启动两个服务"
    echo "  $0 status                          # 查看服务状态"
    echo "  $0 logs                            # 查看服务日志"
}

# 函数：解析参数
parse_args() {
    PORT=$DEFAULT_PORT
    HOST=$DEFAULT_HOST
    MODE=$DEFAULT_MODE
    DAEMON=false
    VERBOSE=false
    CONFIG_FILE=""
    COMMAND=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--port)
                PORT="$2"
                shift 2
                ;;
            -h|--host)
                HOST="$2"
                shift 2
                ;;
            -m|--mode)
                MODE="$2"
                shift 2
                ;;
            -d|--daemon)
                DAEMON=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            --config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            --help)
                show_help
                exit 0
                ;;
            start|stop|restart|status|test|logs)
                COMMAND="$1"
                shift
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 验证模式
    if [[ ! "$MODE" =~ ^(hybrid|legacy|both)$ ]]; then
        print_error "无效的运行模式: $MODE"
        exit 1
    fi

    # 验证命令
    if [[ -z "$COMMAND" ]]; then
        print_error "请指定命令"
        show_help
        exit 1
    fi
}

# 函数：检查依赖
check_dependencies() {
    print_info "检查依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 未安装"
        exit 1
    fi

    # 检查必要的Python包
    local packages=("fastapi" "uvicorn" "aiohttp" "beautifulsoup4" "crawl4ai")
    for package in "${packages[@]}"; do
        if ! python3 -c "import $package" &> /dev/null; then
            print_error "缺少Python包: $package"
            print_info "请运行: pip3 install $package"
            exit 1
        fi
    done

    # 检查服务文件
    if [[ "$MODE" == "hybrid" || "$MODE" == "both" ]]; then
        if [[ ! -f "$HYBRID_API_DIR" ]]; then
            print_error "混合爬虫API文件不存在: $HYBRID_API_DIR"
            exit 1
        fi
    fi

    if [[ "$MODE" == "legacy" || "$MODE" == "both" ]]; then
        if [[ ! -f "$LEGACY_API_DIR" ]]; then
            print_error "传统爬虫API文件不存在: $LEGACY_API_DIR"
            exit 1
        fi
    fi

    print_success "依赖检查通过"
}

# 函数：获取进程PID
get_pid() {
    local service_name="$1"
    local pid_file="$PID_DIR/${service_name}.pid"

    if [[ -f "$pid_file" ]]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "$pid"
            return 0
        else
            rm -f "$pid_file"
            return 1
        fi
    fi
    return 1
}

# 函数：启动服务
start_service() {
    local service_name="$1"
    local api_file="$2"
    local service_port="$3"
    local log_file="$LOG_DIR/${service_name}.log"

    local pid=$(get_pid "$service_name")
    if [[ -n "$pid" ]]; then
        print_warning "$service_name 服务已在运行 (PID: $pid)"
        return 0
    fi

    print_info "启动 $service_name 服务 (端口: $service_port)..."

    # 设置Python路径
    export PYTHONPATH="$SERVICE_DIR:$PROJECT_ROOT:$PYTHONPATH"

    # 设置环境变量
    if [[ -n "$CONFIG_FILE" ]]; then
        export CRAWLER_CONFIG_FILE="$CONFIG_FILE"
    fi

    # 启动命令
    local cmd="python3 $api_file --host $HOST --port $service_port"

    if [[ "$VERBOSE" == "true" ]]; then
        cmd="$cmd --log-level debug"
    fi

    if [[ "$DAEMON" == "true" ]]; then
        # 后台运行
        nohup $cmd > "$log_file" 2>&1 &
        local pid=$!
        echo "$pid" > "$PID_DIR/${service_name}.pid"
        print_success "$service_name 服务已启动 (PID: $pid, 端口: $service_port)"
        print_info "日志文件: $log_file"
    else
        # 前台运行
        print_info "在前台启动 $service_name 服务..."
        $cmd
    fi
}

# 函数：停止服务
stop_service() {
    local service_name="$1"

    local pid=$(get_pid "$service_name")
    if [[ -z "$pid" ]]; then
        print_warning "$service_name 服务未运行"
        return 0
    fi

    print_info "停止 $service_name 服务 (PID: $pid)..."
    kill "$pid"

    # 等待进程结束
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [[ $count -lt 10 ]]; do
        sleep 1
        count=$((count + 1))
    done

    if ps -p "$pid" > /dev/null 2>&1; then
        print_warning "$service_name 服务未正常结束，强制终止..."
        kill -9 "$pid"
    fi

    rm -f "$PID_DIR/${service_name}.pid"
    print_success "$service_name 服务已停止"
}

# 函数：显示服务状态
show_status() {
    echo "爬虫服务状态:"
    echo "==============="

    # 混合爬虫服务状态
    if [[ "$MODE" == "hybrid" || "$MODE" == "both" ]]; then
        local hybrid_pid=$(get_pid "hybrid_crawler")
        if [[ -n "$hybrid_pid" ]]; then
            echo -e "混合爬虫服务: ${GREEN}运行中${NC} (PID: $hybrid_pid, 端口: $PORT)"
        else
            echo -e "混合爬虫服务: ${RED}未运行${NC}"
        fi
    fi

    # 传统爬虫服务状态
    if [[ "$MODE" == "legacy" || "$MODE" == "both" ]]; then
        local legacy_port=$((PORT + 1))
        local legacy_pid=$(get_pid "legacy_crawler")
        if [[ -n "$legacy_pid" ]]; then
            echo -e "传统爬虫服务: ${GREEN}运行中${NC} (PID: $legacy_pid, 端口: $legacy_port)"
        else
            echo -e "传统爬虫服务: ${RED}未运行${NC}"
        fi
    fi

    echo ""
    echo "PID目录: $PID_DIR"
    echo "日志目录: $LOG_DIR"
    echo "配置目录: $CONFIG_DIR"
}

# 函数：测试服务连通性
test_service() {
    print_info "测试爬虫服务连通性..."

    # 测试混合爬虫服务
    if [[ "$MODE" == "hybrid" || "$MODE" == "both" ]]; then
        print_info "测试混合爬虫服务 (端口: $PORT)..."
        if curl -s "http://$HOST:$PORT/health" > /dev/null; then
            print_success "混合爬虫服务连通正常"
        else
            print_warning "混合爬虫服务连接失败"
        fi
    fi

    # 测试传统爬虫服务
    if [[ "$MODE" == "legacy" || "$MODE" == "both" ]]; then
        local legacy_port=$((PORT + 1))
        print_info "测试传统爬虫服务 (端口: $legacy_port)..."
        if curl -s "http://$HOST:$legacy_port/health" > /dev/null; then
            print_success "传统爬虫服务连通正常"
        else
            print_warning "传统爬虫服务连接失败"
        fi
    fi
}

# 函数：显示日志
show_logs() {
    local follow=false
    if [[ "$1" == "--follow" || "$1" == "-f" ]]; then
        follow=true
        shift
    fi

    # 混合爬虫服务日志
    if [[ "$MODE" == "hybrid" || "$MODE" == "both" ]]; then
        local hybrid_log="$LOG_DIR/hybrid_crawler.log"
        if [[ -f "$hybrid_log" ]]; then
            echo "=== 混合爬虫服务日志 ==="
            if [[ "$follow" == "true" ]]; then
                tail -f "$hybrid_log"
            else
                tail -50 "$hybrid_log"
            fi
        else
            print_warning "混合爬虫服务日志文件不存在"
        fi
    fi

    # 传统爬虫服务日志
    if [[ "$MODE" == "legacy" || "$MODE" == "both" ]]; then
        local legacy_log="$LOG_DIR/legacy_crawler.log"
        if [[ -f "$legacy_log" ]]; then
            echo "=== 传统爬虫服务日志 ==="
            if [[ "$follow" == "true" ]]; then
                tail -f "$legacy_log"
            else
                tail -50 "$legacy_log"
            fi
        else
            print_warning "传统爬虫服务日志文件不存在"
        fi
    fi
}

# 主程序
main() {
    # 解析参数
    parse_args "$@"

    # 设置Python路径
    export PYTHONPATH="$SERVICE_DIR:$PROJECT_ROOT:$PYTHONPATH"

    case "$COMMAND" in
        start)
            check_dependencies
            if [[ "$MODE" == "hybrid" ]]; then
                start_service "hybrid_crawler" "$HYBRID_API_DIR" "$PORT"
            elif [[ "$MODE" == "legacy" ]]; then
                start_service "legacy_crawler" "$LEGACY_API_DIR" "$PORT"
            elif [[ "$MODE" == "both" ]]; then
                start_service "hybrid_crawler" "$HYBRID_API_DIR" "$PORT"
                if [[ "$DAEMON" == "true" ]]; then
                    sleep 2  # 等待第一个服务启动
                    start_service "legacy_crawler" "$LEGACY_API_DIR" $((PORT + 1))
                fi
            fi
            ;;
        stop)
            if [[ "$MODE" == "hybrid" || "$MODE" == "both" ]]; then
                stop_service "hybrid_crawler"
            fi
            if [[ "$MODE" == "legacy" || "$MODE" == "both" ]]; then
                stop_service "legacy_crawler"
            fi
            ;;
        restart)
            if [[ "$MODE" == "hybrid" || "$MODE" == "both" ]]; then
                stop_service "hybrid_crawler"
            fi
            if [[ "$MODE" == "legacy" || "$MODE" == "both" ]]; then
                stop_service "legacy_crawler"
            fi
            sleep 2
            check_dependencies
            if [[ "$MODE" == "hybrid" ]]; then
                start_service "hybrid_crawler" "$HYBRID_API_DIR" "$PORT"
            elif [[ "$MODE" == "legacy" ]]; then
                start_service "legacy_crawler" "$LEGACY_API_DIR" "$PORT"
            elif [[ "$MODE" == "both" ]]; then
                start_service "hybrid_crawler" "$HYBRID_API_DIR" "$PORT"
                if [[ "$DAEMON" == "true" ]]; then
                    sleep 2
                    start_service "legacy_crawler" "$LEGACY_API_DIR" $((PORT + 1))
                fi
            fi
            ;;
        status)
            show_status
            ;;
        test)
            test_service
            ;;
        logs)
            show_logs "$@"
            ;;
        *)
            print_error "未知命令: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# 运行主程序
main "$@"