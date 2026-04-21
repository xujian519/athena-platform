#!/bin/bash
# Agent代理启动脚本
# 用于启动Python智能体代理服务
#
# 作者: Athena平台团队
# 创建时间: 2026-04-21
# 版本: v1.0.0

set -e

# ==================== 配置 ====================

# 项目根目录
PROJECT_ROOT="${ATHENA_PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

# Gateway WebSocket URL
GATEWAY_URL="${GATEWAY_URL:-ws://localhost:8005/ws}"

# 日志目录
LOG_DIR="${LOG_DIR:-${PROJECT_ROOT}/logs}"

# Agent类型
AGENT_TYPE="${1:-xiaona}"

# Python解释器
PYTHON="${PYTHON:-python3}"

# ==================== 颜色输出 ====================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==================== 函数 ====================

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

# ==================== 检查环境 ====================

check_environment() {
    log_info "检查运行环境..."

    # 检查Python
    if ! command -v "$PYTHON" &> /dev/null; then
        log_error "Python未找到: $PYTHON"
        exit 1
    fi

    # 检查项目目录
    if [ ! -d "$PROJECT_ROOT/core" ]; then
        log_error "无效的项目根目录: $PROJECT_ROOT"
        exit 1
    fi

    # 创建日志目录
    mkdir -p "$LOG_DIR"

    log_success "环境检查通过"
}

# ==================== 启动代理 ====================

start_agent() {
    local agent_type="$1"

    log_info "启动${agent_type}代理..."

    # 设置PYTHONPATH
    export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH}"

    # 日志文件
    local log_file="${LOG_DIR}/${agent_type}_proxy.log"

    # 根据Agent类型选择启动脚本
    case "$agent_type" in
        xiaona)
            local script="core.orchestration.xiaona_agent_proxy"
            ;;
        xiaonuo)
            local script="core.orchestration.xiaonuo_agent_proxy"
            ;;
        yunxi)
            local script="core.orchestration.yunxi_agent_proxy"
            ;;
        all)
            log_info "启动所有代理..."
            start_agent xiaona &
            start_agent xiaonuo &
            wait
            return
            ;;
        *)
            log_error "未知的Agent类型: $agent_type"
            echo ""
            echo "用法: $0 [AGENT_TYPE]"
            echo ""
            echo "Agent类型:"
            echo "  xiaona  - 法律专家"
            echo "  xiaonuo - 调度官"
            echo "  yunxi   - IP管理"
            echo "  all     - 启动所有代理"
            echo ""
            exit 1
            ;;
    esac

    # 启动代理
    log_info "Gateway URL: $GATEWAY_URL"
    log_info "日志文件: $log_file"

    "$PYTHON" -m "$script" "$GATEWAY_URL" 2>&1 | tee -a "$log_file"
}

# ==================== 主程序 ====================

main() {
    echo ""
    echo "🤖 Athena Agent代理启动脚本"
    echo "============================="
    echo ""

    # 检查环境
    check_environment

    # 显示配置
    log_info "配置:"
    log_info "  项目根目录: $PROJECT_ROOT"
    log_info "  Gateway URL: $GATEWAY_URL"
    log_info "  日志目录: $LOG_DIR"
    log_info "  Python: $PYTHON"
    echo ""

    # 启动代理
    start_agent "$AGENT_TYPE"
}

# ==================== 信号处理 ====================

trap 'log_warning "收到中断信号，正在停止..."; exit 0' INT TERM

# ==================== 执行 ====================

main "$@"
