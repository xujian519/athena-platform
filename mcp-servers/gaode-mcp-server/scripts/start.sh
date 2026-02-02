#!/bin/bash
# 高德地图MCP服务器启动脚本

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

# 检查Python版本
check_python() {
    log_info "检查Python版本..."

    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi

    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    required_version="3.8"

    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        log_error "Python版本过低，需要 >= 3.8，当前版本: $python_version"
        exit 1
    fi

    log_success "Python版本检查通过: $python_version"
}

# 检查依赖
check_dependencies() {
    log_info "检查项目依赖..."

    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt 文件不存在"
        exit 1
    fi

    # 检查关键依赖是否已安装
    python3 -c "import mcp, httpx, pydantic, structlog" 2>/dev/null || {
        log_warning "依赖未完全安装，正在安装..."
        pip3 install -r requirements.txt
    }

    log_success "依赖检查完成"
}

# 检查配置
check_config() {
    log_info "检查配置文件..."

    if [ ! -f ".env" ]; then
        log_warning ".env 文件不存在，使用默认配置"
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "已从 .env.example 复制配置，请编辑 .env 文件设置API密钥"
        fi
    fi

    # 检查API密钥是否设置
    if [ -f ".env" ]; then
        if grep -q "your_amap_api_key_here" .env; then
            log_warning "请在 .env 文件中设置你的高德地图API密钥"
            log_info "API密钥获取地址: https://lbs.amap.com/dev/"
        fi
    fi

    log_success "配置检查完成"
}

# 创建日志目录
setup_logs() {
    log_info "设置日志目录..."

    mkdir -p logs
    log_success "日志目录已创建"
}

# 启动服务器
start_server() {
    log_info "启动高德地图MCP服务器..."

    # 设置环境变量
    export PYTHONPATH="${PWD}/src:$PYTHONPATH"

    # 启动服务器
    if command -v python3 -m amap_mcp_server &> /dev/null; then
        # 如果包已安装，直接运行
        python3 -m amap_mcp_server.server
    else
        # 否则运行源码
        python3 src/amap_mcp_server/server.py
    fi
}

# 显示帮助信息
show_help() {
    echo "高德地图MCP服务器启动脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -v, --verbose  详细输出"
    echo "  -c, --check    仅检查环境，不启动服务器"
    echo ""
    echo "环境变量:"
    echo "  MCP_LOG_LEVEL  日志级别 (DEBUG, INFO, WARNING, ERROR)"
    echo ""
}

# 主函数
main() {
    echo "🗺️  高德地图MCP服务器启动脚本"
    echo "================================"

    # 解析参数
    VERBOSE=false
    CHECK_ONLY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -c|--check)
                CHECK_ONLY=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 设置详细输出
    if [ "$VERBOSE" = true ]; then
        set -x
    fi

    # 执行检查
    check_python
    check_dependencies
    check_config
    setup_logs

    if [ "$CHECK_ONLY" = true ]; then
        log_success "环境检查完成，所有检查项都通过了！"
        exit 0
    fi

    # 启动服务器
    start_server
}

# 捕获退出信号
trap 'log_info "正在关闭服务器..."; exit 0' SIGINT SIGTERM

# 运行主函数
main "$@"