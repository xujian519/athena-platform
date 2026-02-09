#!/bin/bash
# =============================================================================
# 小诺·双鱼座 - 生产环境启动脚本
# Xiaonuo Pisces - Production Startup Script
# =============================================================================
#
# 使用说明：
# 1. 确保已配置 .env.production 文件
# 2. 执行: ./start_xiaonuo_production.sh [start|stop|restart|status]
#
# =============================================================================

set -e

# -----------------------------------------------------------------------------
# 配置
# -----------------------------------------------------------------------------

# 服务名称
SERVICE_NAME="xiaonuo-pisces"
DISPLAY_NAME="小诺·双鱼座"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Python虚拟环境
VENV_DIR="${PROJECT_ROOT}/athena_env_py311"
PYTHON="${VENV_DIR}/bin/python"

# PID文件
PID_DIR="/var/run/xiaonuo"
PID_FILE="${PID_DIR}/xiaonuo.pid"

# 日志目录
LOG_DIR="/var/log/xiaonuo"

# 配置文件
CONFIG_FILE="${PROJECT_ROOT}/config/production/xiaonuo_production.yaml"
ENV_FILE="${PROJECT_ROOT}/.env.production.xiaonuo"

# 服务端口
PORT=8005

# -----------------------------------------------------------------------------
# 辅助函数
# -----------------------------------------------------------------------------

# 打印带颜色的消息
print_info() {
    echo -e "\033[0;32m[INFO]\033[0m $1"
}

print_warn() {
    echo -e "\033[0;33m[WARN]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查依赖..."

    # 检查Python
    if [ ! -f "$PYTHON" ]; then
        print_error "Python未找到: $PYTHON"
        exit 1
    fi

    # 检查配置文件
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "配置文件未找到: $CONFIG_FILE"
        exit 1
    fi

    # 检查环境变量文件
    if [ ! -f "$ENV_FILE" ]; then
        print_warn "环境变量文件未找到: $ENV_FILE"
        print_warn "将使用默认配置"
    fi

    # 创建必要目录
    mkdir -p "$PID_DIR"
    mkdir -p "$LOG_DIR"

    print_info "依赖检查完成"
}

# 检查服务是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
            return 1
        fi
    fi
    return 1
}

# 启动服务
start_service() {
    print_info "启动${DISPLAY_NAME}..."

    if is_running; then
        print_warn "${DISPLAY_NAME}已在运行中"
        return 0
    fi

    check_dependencies

    # 加载环境变量
    if [ -f "$ENV_FILE" ]; then
        export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
    fi

    # 启动服务
    nohup "$PYTHON" "${PROJECT_ROOT}/production/services/xiaonuo_service.py" \
        --config "$CONFIG_FILE" \
        --port "$PORT" \
        >> "${LOG_DIR}/xiaonuo.log" 2>&1 &

    PID=$!
    echo $PID > "$PID_FILE"

    # 等待服务启动
    sleep 2

    if is_running; then
        print_info "${DISPLAY_NAME}启动成功 (PID: $PID)"
        print_info "监听地址: http://127.0.0.1:${PORT}"
        print_info "日志文件: ${LOG_DIR}/xiaonuo.log"
        return 0
    else
        print_error "${DISPLAY_NAME}启动失败"
        return 1
    fi
}

# 停止服务
stop_service() {
    print_info "停止${DISPLAY_NAME}..."

    if ! is_running; then
        print_warn "${DISPLAY_NAME}未运行"
        return 0
    fi

    PID=$(cat "$PID_FILE")

    # 发送TERM信号（优雅关闭）
    kill -TERM "$PID"

    # 等待进程退出
    for i in {1..30}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            break
        fi
        sleep 1
    done

    # 如果进程仍在运行，强制终止
    if ps -p "$PID" > /dev/null 2>&1; then
        print_warn "强制终止进程..."
        kill -KILL "$PID"
        sleep 1
    fi

    # 清理PID文件
    rm -f "$PID_FILE"

    print_info "${DISPLAY_NAME}已停止"
}

# 重启服务
restart_service() {
    print_info "重启${DISPLAY_NAME}..."
    stop_service
    sleep 2
    start_service
}

# 显示状态
show_status() {
    echo -e "\033[1;34m${DISPLAY_NAME} 状态\033[0m"
    echo "----------------------------------------"

    if is_running; then
        PID=$(cat "$PID_FILE")
        echo "状态: \033[0;32m运行中\033[0m"
        echo "PID: $PID"
        echo "端口: $PORT"
        echo "配置: $CONFIG_FILE"

        # 显示进程信息
        ps -p "$PID" -o pid,ppid,cmd,etime,pcpu,pmem

        # 显示最近的日志
        echo ""
        echo "最近的日志:"
        tail -n 5 "${LOG_DIR}/xiaonuo.log" 2>/dev/null || echo "日志文件不存在"

    else
        echo "状态: \033[0;31m已停止\033[0m"
    fi
}

# 显示帮助
show_help() {
    echo "用法: $0 [start|stop|restart|status|help]"
    echo ""
    echo "命令:"
    echo "  start   - 启动${DISPLAY_NAME}"
    echo "  stop    - 停止${DISPLAY_NAME}"
    echo "  restart - 重启${DISPLAY_NAME}"
    echo "  status  - 显示${DISPLAY_NAME}状态"
    echo "  help    - 显示此帮助信息"
}

# -----------------------------------------------------------------------------
# 主程序
# -----------------------------------------------------------------------------

main() {
    case "${1:-}" in
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
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: ${1:-}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 运行主程序
main "$@"
