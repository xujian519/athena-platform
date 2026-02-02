#!/bin/bash

# 认知决策层服务停止脚本
# Cognitive Decision Layer Stop Script
# Created by Athena + 小诺
# Date: 2025-12-05

set -e

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

# 项目配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
PID_DIR="${PROJECT_ROOT}/pids"

# 停止服务
stop_services() {
    log_info "正在停止认知决策层服务..."

    # 停止认知集成层服务
    if [ -f "${PID_DIR}/cognitive_integration.pid" ]; then
        PID=$(cat "${PID_DIR}/cognitive_integration.pid")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            log_success "认知集成层服务已停止 (PID: $PID)"
        else
            log_warning "认知集成层服务进程不存在"
        fi
        rm -f "${PID_DIR}/cognitive_integration.pid"
    fi

    # 停止增强API服务
    if [ -f "${PID_DIR}/enhanced_api.pid" ]; then
        PID=$(cat "${PID_DIR}/enhanced_api.pid")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            log_success "增强API服务已停止 (PID: $PID)"
        else
            log_warning "增强API服务进程不存在"
        fi
        rm -f "${PID_DIR}/enhanced_api.pid"
    fi

    # 停止前端服务
    if [ -f "${PID_DIR}/frontend.pid" ]; then
        PID=$(cat "${PID_DIR}/frontend.pid")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID"
            log_success "前端服务已停止 (PID: $PID)"
        else
            log_warning "前端服务进程不存在"
        fi
        rm -f "${PID_DIR}/frontend.pid"
    fi

    # 强制停止所有相关进程
    pkill -f "cognitive_integration_layer.py" || true
    pkill -f "enhanced_patent_api.py" || true
    pkill -f "python3 -m http.server 3000" || true

    log_success "所有服务已停止"
}

# 清理端口
cleanup_ports() {
    log_info "清理占用端口..."

    # 清理端口 8080
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true

    # 清理端口 8000
    lsof -ti:8000 | xargs kill -9 2>/dev/null || true

    # 清理端口 3000
    lsof -ti:3000 | xargs kill -9 2>/dev/null || true

    log_success "端口清理完成"
}

# 主函数
main() {
    echo -e "${BLUE}"
    echo "=================================================="
    echo "    🛑 认知决策层服务停止脚本"
    echo "    Cognitive Decision Layer Stop Script"
    echo "    Created by Athena + 小诺"
    echo "    Date: 2025-12-05"
    echo "=================================================="
    echo -e "${NC}"

    stop_services
    cleanup_ports

    echo -e "${GREEN}🎉 认知决策层服务已完全停止！${NC}"
}

# 执行主函数
main "$@"