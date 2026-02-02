#!/bin/bash
# MCP服务器监控守护进程启动脚本
# MCP Server Monitor Daemon Startup Script
#
# 控制者: 小诺 & Athena
# 创建时间: 2025年12月11日
# 版本: 1.0.0

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_ROOT="$(dirname "$SCRIPT_DIR")"
MONITOR_SCRIPT="$PLATFORM_ROOT/tools/mcp/mcp_monitor.py"
PID_FILE="$PLATFORM_ROOT/.pids/mcp_monitor.pid"
LOG_FILE="$PLATFORM_ROOT/logs/mcp_monitor_daemon.log"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

# 检查是否已经运行
check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log_warn "MCP监控守护进程已在运行 (PID: $pid)"
            return 0
        else
            log_warn "PID文件存在但进程不存在，清理PID文件"
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# 启动守护进程
start_daemon() {
    log_header "启动MCP监控守护进程"

    if check_running; then
        return 0
    fi

    # 确保目录存在
    mkdir -p "$(dirname "$PID_FILE")"
    mkdir -p "$(dirname "$LOG_FILE")"

    # 启动守护进程
    log_info "启动MCP监控守护进程..."
    nohup python3 "$MONITOR_SCRIPT" --daemon > "$LOG_FILE" 2>&1 &
    local pid=$!

    # 保存PID
    echo "$pid" > "$PID_FILE"

    # 等待进程启动
    sleep 2

    # 检查进程是否正常运行
    if ps -p "$pid" > /dev/null 2>&1; then
        log_success "MCP监控守护进程启动成功 (PID: $pid)"
        log_info "日志文件: $LOG_FILE"
        log_info "PID文件: $PID_FILE"
    else
        log_error "MCP监控守护进程启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止守护进程
stop_daemon() {
    log_header "停止MCP监控守护进程"

    if ! check_running; then
        log_warn "MCP监控守护进程未运行"
        return 0
    fi

    local pid=$(cat "$PID_FILE")
    log_info "停止MCP监控守护进程 (PID: $pid)..."

    # 发送TERM信号
    kill -TERM "$pid" 2>/dev/null || true

    # 等待进程结束
    local count=0
    while [ $count -lt 10 ]; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            break
        fi
        sleep 1
        count=$((count + 1))
    done

    # 如果进程仍然存在，强制杀死
    if ps -p "$pid" > /dev/null 2>&1; then
        log_warn "进程未响应TERM信号，强制终止..."
        kill -KILL "$pid" 2>/dev/null || true
        sleep 1
    fi

    # 清理PID文件
    rm -f "$PID_FILE"

    log_success "MCP监控守护进程已停止"
}

# 重启守护进程
restart_daemon() {
    log_header "重启MCP监控守护进程"
    stop_daemon
    sleep 2
    start_daemon
}

# 查看状态
show_status() {
    log_header "MCP监控守护进程状态"

    if check_running; then
        local pid=$(cat "$PID_FILE")
        log_success "守护进程正在运行 (PID: $pid)"

        # 显示详细信息
        echo
        echo "进程信息:"
        ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem --no-headers

        echo
        echo "最近的日志 (最后20行):"
        if [ -f "$LOG_FILE" ]; then
            tail -20 "$LOG_FILE"
        else
            log_warn "日志文件不存在"
        fi
    else
        log_error "守护进程未运行"
    fi
}

# 查看服务器状态
show_server_status() {
    log_header "MCP服务器状态"

    python3 "$MONITOR_SCRIPT" --status
}

# 生成健康报告
generate_report() {
    log_header "生成MCP健康报告"

    python3 "$MONITOR_SCRIPT" --report

    if [ $? -eq 0 ]; then
        log_success "健康报告已生成"
    else
        log_error "生成健康报告失败"
    fi
}

# 手动重启服务器
restart_server() {
    local server_name=$1

    if [ -z "$server_name" ]; then
        log_error "请指定服务器名称"
        echo "可用的服务器: jina-ai, bing-cn-search, amap-mcp, academic-search"
        return 1
    fi

    log_header "重启MCP服务器: $server_name"

    python3 "$MONITOR_SCRIPT" --restart "$server_name"

    if [ $? -eq 0 ]; then
        log_success "服务器 $server_name 重启成功"
    else
        log_error "服务器 $server_name 重启失败"
    fi
}

# 启动所有MCP服务器
start_all_servers() {
    log_header "启动所有MCP服务器"

    python3 "$MONITOR_SCRIPT" --start

    if [ $? -eq 0 ]; then
        log_success "所有MCP服务器启动完成"
    else
        log_error "启动MCP服务器失败"
    fi
}

# 停止所有MCP服务器
stop_all_servers() {
    log_header "停止所有MCP服务器"

    python3 "$MONITOR_SCRIPT" --stop

    if [ $? -eq 0 ]; then
        log_success "所有MCP服务器已停止"
    else
        log_error "停止MCP服务器失败"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
MCP监控守护进程管理脚本 v1.0.0

用法: $0 [命令] [参数]

命令:
    start                   启动监控守护进程
    stop                    停止监控守护进程
    restart                 重启监控守护进程
    status                  查看守护进程状态
    servers                 查看MCP服务器状态
    report                  生成健康报告
    restart-server <名称>   重启指定MCP服务器
    start-servers           启动所有MCP服务器
    stop-servers            停止所有MCP服务器
    help                    显示此帮助信息

可用的MCP服务器:
    jina-ai              Jina AI工具服务器
    bing-cn-search       Bing中文搜索服务器
    amap-mcp             高德地图服务器
    academic-search      学术搜索服务器

示例:
    $0 start                   # 启动监控守护进程
    $0 status                  # 查看守护进程状态
    $0 servers                 # 查看MCP服务器状态
    $0 restart-server jina-ai # 重启Jina AI服务器
    $0 report                  # 生成健康报告

控制者: 小诺 & Athena
EOF
}

# 主函数
main() {
    cd "$PLATFORM_ROOT"

    case $1 in
        start)
            start_daemon
            ;;
        stop)
            stop_daemon
            ;;
        restart)
            restart_daemon
            ;;
        status)
            show_status
            ;;
        servers)
            show_server_status
            ;;
        report)
            generate_report
            ;;
        restart-server)
            restart_server "$2"
            ;;
        start-servers)
            start_all_servers
            ;;
        stop-servers)
            stop_all_servers
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 检查依赖
if ! command -v python3 &> /dev/null; then
    log_error "Python3 未安装或不在PATH中"
    exit 1
fi

if ! command -v psutil &> /dev/null; then
    if ! python3 -c "import psutil" &> /dev/null; then
        log_warn "psutil模块未安装，监控功能可能受限"
        log_info "请安装: pip3 install psutil"
    fi
fi

# 执行主函数
main "$@"