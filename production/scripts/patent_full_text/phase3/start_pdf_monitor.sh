#!/bin/bash
# PDF监控服务启动脚本
# PDF Monitor Service Startup Script
#
# 作者: Athena平台团队
# 创建时间: 2025-12-25

set -e

# 配置
WATCH_DIR="${WATCH_DIR:-/Users/xujian/patents}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_CMD="${PYTHON_CMD:-python3}"
LOG_DIR="${LOG_DIR:-/Users/xujian/apps/apps/patents/logs}"
PID_FILE="${PID_FILE:-/var/run/pdf_monitor.pid}"

# 颜色输出
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

log_blue() {
    echo -e "${BLUE}[SYSTEM]${NC} $1"
}

# 检查目录
check_directory() {
    if [ ! -d "$WATCH_DIR" ]; then
        log_warn "监控目录不存在: $WATCH_DIR"
        read -p "是否创建? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            mkdir -p "$WATCH_DIR"
            log_info "已创建目录: $WATCH_DIR"
        else
            log_error "取消操作"
            exit 1
        fi
    fi

    # 创建日志目录
    mkdir -p "$LOG_DIR"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    # 检查Python
    if ! command -v $PYTHON_CMD &> /dev/null; then
        log_error "Python未安装: $PYTHON_CMD"
        exit 1
    fi

    # 检查PDF解析库
    log_info "检查PDF解析库..."
    if ! $PYTHON_CMD -c "import PyPDF2" 2>/dev/null && \
       ! $PYTHON_CMD -c "import pdfplumber" 2>/dev/null && \
       ! $PYTHON_CMD -c "import fitz" 2>/dev/null; then
        log_warn "未安装PDF解析库，尝试安装..."
        $PYTHON_CMD -m pip install PyPDF2 pdfplumber PyMuPDF || {
            log_error "PDF解析库安装失败"
            exit 1
        }
    fi

    log_info "✅ 依赖检查通过"
}

# 启动服务
start_service() {
    log_blue "=========================================="
    log_blue "    PDF监控服务启动"
    log_blue "=========================================="
    echo

    log_info "监控目录: $WATCH_DIR"
    log_info "脚本目录: $SCRIPT_DIR"
    log_info "日志目录: $LOG_DIR"

    # 检查是否已运行
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            log_warn "服务已在运行 (PID: $PID)"
            read -p "是否重启? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                stop_service
            else
                exit 0
            fi
        else
            log_warn "清理旧的PID文件"
            rm -f "$PID_FILE"
        fi
    fi

    # 检查目录
    check_directory

    # 检查依赖
    check_dependencies

    # 启动服务
    log_info "启动服务..."

    cd "$SCRIPT_DIR"

    # 后台运行
    nohup $PYTHON_CMD pdf_to_pipeline.py \
        > "$LOG_DIR/pdf_monitor.log" 2>&1 &

    PID=$!
    echo $PID > "$PID_FILE"

    log_info "✅ 服务已启动 (PID: $PID)"
    log_info "日志文件: $LOG_DIR/pdf_monitor.log"

    # 等待启动
    sleep 2

    # 检查服务状态
    if ps -p $PID > /dev/null 2>&1; then
        log_info "✅ 服务运行正常"
    else
        log_error "❌ 服务启动失败，请查看日志"
        cat "$LOG_DIR/pdf_monitor.log" | tail -20
        exit 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止服务..."

    if [ ! -f "$PID_FILE" ]; then
        log_warn "PID文件不存在，服务可能未运行"
        return
    fi

    PID=$(cat "$PID_FILE")

    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        log_info "已发送停止信号 (PID: $PID)"

        # 等待进程结束
        for i in {1..10}; do
            if ! ps -p $PID > /dev/null 2>&1; then
                log_info "✅ 服务已停止"
                rm -f "$PID_FILE"
                return
            fi
            sleep 1
        done

        # 强制停止
        log_warn "强制停止服务..."
        kill -9 $PID 2>/dev/null || true
        rm -f "$PID_FILE"
        log_info "✅ 服务已强制停止"
    else
        log_warn "进程不存在 (PID: $PID)"
        rm -f "$PID_FILE"
    fi
}

# 重启服务
restart_service() {
    log_info "重启服务..."
    stop_service
    sleep 1
    start_service
}

# 查看状态
status_service() {
    log_info "服务状态:"

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            log_info "✅ 服务运行中 (PID: $PID)"

            # 显示进程信息
            ps -p $PID -o pid,ppid,cmd,etime,pcpu,pmem

            # 显示日志尾部
            if [ -f "$LOG_DIR/pdf_monitor.log" ]; then
                echo
                log_info "最近日志:"
                tail -10 "$LOG_DIR/pdf_monitor.log"
            fi
        else
            log_warn "❌ 服务未运行 (PID文件存在但进程不存在)"
            rm -f "$PID_FILE"
        fi
    else
        log_warn "❌ 服务未运行 (无PID文件)"
    fi
}

# 查看日志
logs_service() {
    if [ -f "$LOG_DIR/pdf_monitor.log" ]; then
        tail -f "$LOG_DIR/pdf_monitor.log"
    else
        log_error "日志文件不存在: $LOG_DIR/pdf_monitor.log"
    fi
}

# 清理
cleanup_service() {
    log_info "清理..."

    # 停止服务
    stop_service

    # 清理状态文件
    rm -f "${WATCH_DIR}/.pdf_monitor_state.json"

    log_info "✅ 清理完成"
}

# 主函数
main() {
    case "${1:-start}" in
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
            status_service
            ;;
        logs)
            logs_service
            ;;
        cleanup)
            cleanup_service
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|logs|cleanup}"
            echo
            echo "命令:"
            echo "  start   - 启动服务"
            echo "  stop    - 停止服务"
            echo "  restart - 重启服务"
            echo "  status  - 查看状态"
            echo "  logs    - 查看日志"
            echo "  cleanup - 清理服务"
            echo
            echo "环境变量:"
            echo "  WATCH_DIR - 监控目录 (默认: /Users/xujian/patents)"
            echo "  LOG_DIR   - 日志目录 (默认: /Users/xujian/apps/apps/patents/logs)"
            echo "  PYTHON_CMD - Python命令 (默认: python3)"
            exit 1
            ;;
    esac
}

# 执行
main "$@"
