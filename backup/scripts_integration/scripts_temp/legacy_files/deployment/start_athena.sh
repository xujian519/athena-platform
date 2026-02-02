#!/bin/bash
# Athena平台一键启动脚本
# One-click startup script for Athena Platform

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_msg() {
    echo -e "${2}${1}${NC}"
}

# 显示logo
show_logo() {
    echo -e "${BLUE}"
    echo "    _______ __     __ ___    __  __          "
    echo "   / ____(_) /_   / //   |  / / / /___  ____ "
    echo "  / / __/ / __/ / // /| | / / / / __ \/ __ \\"
    echo " / /_/ / / /_  / // ___ |/ /_/ / /_/ / / / /"
    echo " \____/_/\__/ /_//_/  |_/_____/ \____/_/ /_/ "
    echo -e "${NC}"
    print_msg "智能平台启动脚本 v1.0" "$YELLOW"
    echo ""
}

# 检查Python和Node.js
check_dependencies() {
    print_msg "检查依赖..." "$BLUE"

    if ! command -v python3 &> /dev/null; then
        print_msg "错误: 未找到Python3" "$RED"
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        print_msg "警告: 未找到Node.js (API网关需要)" "$YELLOW"
    fi

    if ! command -v npm &> /dev/null; then
        print_msg "警告: 未找到npm (API网关需要)" "$YELLOW"
    fi

    print_msg "依赖检查完成" "$GREEN"
}

# 检查端口占用
check_ports() {
    print_msg "检查端口占用..." "$BLUE"

    local ports=(8000 8001 8002 8003 8004 8005 8006 9000 9001 9002 3000)
    local occupied=()

    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
            occupied+=($port)
        fi
    done

    if [ ${#occupied[@]} -ne 0 ]; then
        print_msg "警告: 以下端口已被占用: ${occupied[*]}" "$YELLOW"
        read -p "是否继续? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    print_msg "端口检查完成" "$GREEN"
}

# 安装Python依赖
install_python_deps() {
    print_msg "安装Python依赖..." "$BLUE"

    # 检查虚拟环境
    if [ ! -d "venv" ]; then
        print_msg "创建虚拟环境..." "$YELLOW"
        python3 -m venv venv
    fi

    # 激活虚拟环境
    source venv/bin/activate

    # 安装通用依赖
    pip install --upgrade pip
    pip install fastapi uvicorn psutil rich httpx

    print_msg "Python依赖安装完成" "$GREEN"
}

# 安装Node.js依赖
install_node_deps() {
    if [ -d "services/api-gateway" ]; then
        print_msg "安装API网关依赖..." "$BLUE"
        cd services/api-gateway
        if [ ! -d "node_modules" ]; then
            npm install
        fi
        cd ../..
        print_msg "API网关依赖安装完成" "$GREEN"
    fi
}

# 启动服务
start_services() {
    print_msg "启动Athena平台服务..." "$BLUE"

    # 使用部署管理器启动所有服务
    python3 scripts/deployment_manager.py start-all

    if [ $? -eq 0 ]; then
        print_msg "所有服务启动成功!" "$GREEN"
    else
        print_msg "部分服务启动失败，请检查日志" "$YELLOW"
    fi
}

# 显示服务状态
show_status() {
    echo ""
    print_msg "服务状态:" "$BLUE"
    python3 scripts/deployment_manager.py health
}

# 显示访问地址
show_access_info() {
    echo ""
    print_msg "服务访问地址:" "$BLUE"
    echo "====================================="
    echo "🚀 Athena主平台:      http://localhost:8001"
    echo "🤖 YunPat智能体:       http://localhost:8000"
    echo "🔌 API网关:           http://localhost:3000"
    echo "🧠 AI模型服务:        http://localhost:9000"
    echo "🕷️  智能爬虫服务:      http://localhost:8003"
    echo "🎨 数据可视化:        http://localhost:8005"
    echo "====================================="
    echo ""
    print_msg "查看API文档:" "$YELLOW"
    echo "- Athena平台:        http://localhost:8001/docs"
    echo "- YunPat智能体:       http://localhost:8000/docs"
    echo "- AI模型服务:        http://localhost:9000/docs"
    echo ""
}

# 主函数
main() {
    # 切换到项目根目录
    cd "$(dirname "$0")/.."

    show_logo

    # 解析命令行参数
    case "${1:-start}" in
        "start")
            check_dependencies
            check_ports
            install_python_deps
            install_node_deps
            start_services
            show_status
            show_access_info
            ;;
        "stop")
            print_msg "停止所有服务..." "$BLUE"
            python3 scripts/deployment_manager.py stop-all
            ;;
        "restart")
            print_msg "重启所有服务..." "$BLUE"
            python3 scripts/deployment_manager.py stop-all
            sleep 2
            python3 scripts/deployment_manager.py start-all
            show_status
            show_access_info
            ;;
        "status")
            show_status
            ;;
        "monitor")
            print_msg "启动监控仪表板..." "$BLUE"
            python3 scripts/monitor_dashboard.py
            ;;
        "help"|"-h"|"--help")
            echo "Athena平台启动脚本"
            echo ""
            echo "用法: $0 [命令]"
            echo ""
            echo "命令:"
            echo "  start    启动所有服务 (默认)"
            echo "  stop     停止所有服务"
            echo "  restart  重启所有服务"
            echo "  status   查看服务状态"
            echo "  monitor  启动监控仪表板"
            echo "  help     显示此帮助信息"
            ;;
        *)
            print_msg "未知命令: $1" "$RED"
            print_msg "使用 '$0 help' 查看帮助" "$YELLOW"
            exit 1
            ;;
    esac
}

# 捕获Ctrl+C
trap 'print_msg "\n操作已取消" "$YELLOW"; exit 1' INT

# 执行主函数
main "$@"