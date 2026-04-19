#!/bin/bash
# ===================================================================
# Athena记忆服务启动脚本
# Athena Memory Service Startup Script
# ===================================================================
# 用途: 启动Athena迭代搜索服务 (端口8008)
# ===================================================================

set -e

PROJECT_ROOT="/Users/xujian/Athena工作平台"
SRC_DIR="${PROJECT_ROOT}/services/athena_iterative_search"
LOG_DIR="${PROJECT_ROOT}/logs"
PID_FILE="${LOG_DIR}/athena_memory.pid"

# 服务配置
SERVICE_NAME="athena-memory"
SERVICE_PORT=8008

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"; }

# 检查服务是否运行
is_service_running() {
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

# 停止旧服务
stop_old_service() {
    if is_service_running; then
        OLD_PID=$(cat "$PID_FILE")
        log_warn "检测到旧服务运行中 (PID: $OLD_PID)，正在停止..."
        kill "$OLD_PID" 2>/dev/null || true
        sleep 2
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            kill -9 "$OLD_PID" 2>/dev/null || true
        fi
        rm -f "$PID_FILE"
    fi
}

# 启动服务
start_service() {
    log_info "启动Athena记忆服务..."

    cd "$SRC_DIR"

    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"

    # 启动服务
    nohup /opt/homebrew/bin/python3.11 -m uvicorn main:app \
        --host 0.0.0.0 \
        --port $SERVICE_PORT \
        --reload \
        > "${LOG_DIR}/${SERVICE_NAME}.log" 2>&1 &

    LOCAL_PID=$!
    echo "$LOCAL_PID" > "$PID_FILE"

    # 等待启动
    sleep 5

    # 检查进程
    if ps -p "$LOCAL_PID" > /dev/null 2>&1; then
        log_info "✅ Athena记忆服务启动成功 (PID: $LOCAL_PID)"
        log_info "   端口: $SERVICE_PORT"
        log_info "   日志: ${LOG_DIR}/${SERVICE_NAME}.log"
        return 0
    else
        log_error "❌ 服务启动失败，查看日志"
        tail -20 "${LOG_DIR}/${SERVICE_NAME}.log"
        return 1
    fi
}

# 显示服务信息
show_service_info() {
    echo ""
    echo "============================================================"
    echo "  Athena记忆服务"
    echo "============================================================"
    echo ""
    echo "服务地址: http://localhost:$SERVICE_PORT"
    echo "API文档: http://localhost:$SERVICE_PORT/docs"
    echo "健康检查: http://localhost:$SERVICE_PORT/health"
    echo ""
    echo "主要端点:"
    echo "  - POST /api/v2/search/iterative - 迭代搜索"
    echo "  - POST /api/v2/search/enhanced - 增强搜索"
    echo "  - GET  /api/v2/config - 获取配置"
    echo "  - POST /api/v2/config - 更新配置"
    echo ""
    echo "============================================================"
    echo ""
}

# 主程序
main() {
    echo ""
    echo "============================================================"
    echo "  启动Athena记忆服务"
    echo "============================================================"
    echo ""

    stop_old_service

    if ! start_service; then
        log_error "启动失败"
        exit 1
    fi

    show_service_info
    log_info "启动完成！"
}

main "$@"
