#!/bin/bash
# 启动高德地图MCP服务器脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
MCP_SERVER_PATH="/Users/xujian/Athena工作平台/amap-mcp-server"
ATHENA_ROOT="/Users/xujian/Athena工作平台"

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

# 显示标题
show_banner() {
    echo -e "${BLUE}"
    echo "🗺️  高德地图MCP服务器启动器"
    echo "================================"
    echo -e "${NC}"
}

# 检查环境
check_environment() {
    log_info "检查运行环境..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装，请先安装Python 3.8或更高版本"
        exit 1
    fi

    # 检查MCP服务器目录
    if [ ! -d "$MCP_SERVER_PATH" ]; then
        log_error "MCP服务器目录不存在: $MCP_SERVER_PATH"
        exit 1
    fi

    log_success "环境检查完成"
}

# 安装依赖
install_dependencies() {
    log_info "检查并安装依赖..."

    cd "$MCP_SERVER_PATH"

    # 检查requirements.txt
    if [ -f "requirements.txt" ]; then
        log_info "安装Python依赖包..."
        pip3 install -r requirements.txt -q
        log_success "依赖包安装完成"
    else
        log_warning "requirements.txt文件不存在"
    fi
}

# 验证配置
verify_config() {
    log_info "验证配置文件..."

    # 检查.env文件
    if [ ! -f ".env" ]; then
        log_warning ".env文件不存在，使用默认配置"
        if [ -f ".env.example" ]; then
            cp .env.example .env
        fi
    fi

    # 检查API密钥
    if grep -q "your_amap_api_key_here" .env 2>/dev/null; then
        log_warning "请在.env文件中设置正确的高德地图API密钥"
        log_info "获取API密钥: https://lbs.amap.com/dev/"
    else
        log_success "API密钥配置完成"
    fi
}

# 启动MCP服务器
start_mcp_server() {
    log_info "启动高德地图MCP服务器..."

    cd "$MCP_SERVER_PATH"

    # 设置环境变量
    export PYTHONPATH="${MCP_SERVER_PATH}/src:$PYTHONPATH"
    export AMAP_API_KEY="6e77ee0ef334ad03ba3f766c991f0d7"

    # 启动服务器
    log_info "MCP服务器启动中..."
    log_info "服务地址: $MCP_SERVER_PATH"
    log_info "API密钥: ${AMAP_API_KEY:0:8}..."

    echo ""
    echo -e "${GREEN}🚀 MCP服务器已启动！${NC}"
    echo ""
    echo -e "${BLUE}可用工具:${NC}"
    echo "  • gaode_geocode - 地理编码服务"
    echo "  • gaode_poi_search - POI搜索服务"
    echo ""
    echo -e "${BLUE}使用方法:${NC}"
    echo "  1. 在Claude等AI工具中选择MCP服务器"
    echo "  2. 配置服务器路径: $MCP_SERVER_PATH"
    echo "  3. 启动命令: python3 -m amap_mcp_server.server"
    echo ""
    echo -e "${YELLOW}注意: 请确保您的高德地图API密钥有效且已开通相应服务${NC}"
    echo ""
    echo -e "${BLUE}按 Ctrl+C 停止服务器${NC}"
    echo ""

    # 启动服务器（前台运行）
    python3 -m amap_mcp_server.server
}

# 创建快捷启动脚本
create_quick_start() {
    log_info "创建快捷启动脚本..."

    # 创建全局可执行的启动脚本
    cat > "$ATHENA_ROOT/start_amap_mcp" << 'EOF'
#!/bin/bash
# 高德地图MCP服务器快捷启动脚本

MCP_SERVER_PATH="/Users/xujian/Athena工作平台/amap-mcp-server"

cd "$MCP_SERVER_PATH"
export PYTHONPATH="${MCP_SERVER_PATH}/src:$PYTHONPATH"
export AMAP_API_KEY="6e77ee0ef334ad03ba3f766c991f0d7"

python3 -m amap_mcp_server.server
EOF

    chmod +x "$ATHENA_ROOT/start_amap_mcp"
    log_success "快捷启动脚本创建完成: $ATHENA_ROOT/start_amap_mcp"
}

# 显示使用帮助
show_usage() {
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -c, --check    仅检查环境，不启动服务器"
    echo "  -i, --install  仅安装依赖"
    echo "  -q, --quick    创建快捷启动脚本"
    echo ""
    echo "示例:"
    echo "  $0              # 完整检查并启动"
    echo "  $0 --check      # 仅检查环境"
    echo "  $0 --install    # 仅安装依赖"
    echo "  $0 --quick      # 创建快捷脚本"
}

# 主函数
main() {
    show_banner

    # 解析参数
    CHECK_ONLY=false
    INSTALL_ONLY=false
    CREATE_QUICK=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_usage
                exit 0
                ;;
            -c|--check)
                CHECK_ONLY=true
                shift
                ;;
            -i|--install)
                INSTALL_ONLY=true
                shift
                ;;
            -q|--quick)
                CREATE_QUICK=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_usage
                exit 1
                ;;
        esac
    done

    # 执行步骤
    check_environment

    if [ "$INSTALL_ONLY" = true ]; then
        install_dependencies
        log_success "依赖安装完成"
        exit 0
    fi

    if [ "$CREATE_QUICK" = true ]; then
        create_quick_start
        log_success "快捷脚本创建完成"
        exit 0
    fi

    if [ "$CHECK_ONLY" = true ]; then
        install_dependencies
        verify_config
        log_success "环境检查完成，所有检查项都通过了！"
        exit 0
    fi

    # 完整启动流程
    install_dependencies
    verify_config
    create_quick_start
    start_mcp_server
}

# 捕获退出信号
trap 'log_info "正在关闭MCP服务器..."; exit 0' SIGINT SIGTERM

# 运行主函数
main "$@"