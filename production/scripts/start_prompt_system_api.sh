#!/bin/bash
# ===================================================================
# 独立提示词系统API启动脚本
# Standalone Prompt System API Startup Script
# ===================================================================
# 用途: 启动动态提示词系统API服务
# 端口: 8002 (避免与法律世界模型8000冲突)
# ===================================================================

set -e

# 项目路径
PROJECT_ROOT="/Users/xujian/Athena工作平台"
SRC_DIR="${PROJECT_ROOT}/core/api"
LOG_DIR="${PROJECT_ROOT}/logs"
PID_FILE="${LOG_DIR}/prompt_system_api.pid"

# 服务配置
SERVICE_NAME="prompt-system-api"
SERVICE_HOST="0.0.0.0"
SERVICE_PORT=8002

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

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

# 等待服务启动
wait_for_service() {
    local url=$1
    local max_wait=${2:-30}
    local count=0

    log_info "等待服务启动: $url"

    while [ $count -lt $max_wait ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            log_info "✅ 服务已就绪!"
            return 0
        fi
        sleep 1
        count=$((count + 1))
        echo -n "."
    done

    echo ""
    log_error "服务启动超时"
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
    log_info "启动独立提示词系统API..."

    cd "$SRC_DIR"

    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export API_PORT="$SERVICE_PORT"
    export API_HOST="$SERVICE_HOST"
    export LOG_LEVEL="INFO"

    # 启动服务
    nohup /opt/homebrew/bin/python3.11 main.py \
        > "${LOG_DIR}/${SERVICE_NAME}.log" 2>&1 &

    LOCAL_PID=$!
    echo "$LOCAL_PID" > "$PID_FILE"

    # 等待服务启动
    if wait_for_service "http://${SERVICE_HOST}:${SERVICE_PORT}/api/v1/prompt-system/health" 30; then
        log_info "✅ 独立提示词系统API启动成功 (PID: $LOCAL_PID)"
        return 0
    else
        log_error "❌ 服务启动失败，查看日志: ${LOG_DIR}/${SERVICE_NAME}.log"
        return 1
    fi
}

# 显示服务信息
show_service_info() {
    echo ""
    echo "============================================================"
    echo "  独立提示词系统API"
    echo "============================================================"
    echo ""
    echo "服务名称: $SERVICE_NAME"
    echo "服务地址: http://${SERVICE_HOST}:${SERVICE_PORT}"
    echo "PID文件: $PID_FILE"
    echo ""
    echo "📋 API端点:"
    echo "  - 健康检查: http://${SERVICE_HOST}:${SERVICE_PORT}/api/v1/prompt-system/health"
    echo "  - 场景识别: http://${SERVICE_HOST}:${SERVICE_PORT}/api/v1/prompt-system/scenario/identify"
    echo "  - 规则检索: http://${SERVICE_HOST}:${SERVICE_PORT}/api/v1/prompt-system/rules/retrieve"
    echo "  - 能力调用: http://${SERVICE_HOST}:${SERVICE_PORT}/api/v1/prompt-system/capabilities/invoke"
    echo "  - 提示词生成: http://${SERVICE_HOST}:${SERVICE_PORT}/api/v1/prompt-system/prompt/generate"
    echo "  - 能力列表: http://${SERVICE_HOST}:${SERVICE_PORT}/api/v1/prompt-system/capabilities/list"
    echo "  - 缓存统计: http://${SERVICE_HOST}:${SERVICE_PORT}/api/v1/prompt-system/cache/stats"
    echo "  - API文档: http://${SERVICE_HOST}:${SERVICE_PORT}/docs"
    echo ""
    echo "日志文件: ${LOG_DIR}/${SERVICE_NAME}.log"
    echo ""
    echo "============================================================"
    echo ""
}

# 主程序
main() {
    echo ""
    echo "============================================================"
    echo "  启动独立提示词系统API"
    echo "============================================================"
    echo ""

    # 停止旧服务
    stop_old_service

    # 启动服务
    if ! start_service; then
        log_error "启动失败"
        exit 1
    fi

    # 显示服务信息
    show_service_info

    log_info "启动完成！"
}

# 执行主程序
main "$@"
