#!/bin/bash
# -*- coding: utf-8 -*-
# Athena工作平台 - 公共高德地图MCP服务器启动脚本
# Public Gaode Maps MCP Server Startup Script for Athena Platform

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_DIR="$PROJECT_ROOT/amap-mcp-server"
PID_FILE="$PROJECT_ROOT/.amap_mcp.pid"
LOG_FILE="$PROJECT_ROOT/logs/amap_mcp.log"

# 服务信息
SERVICE_NAME="高德地图MCP服务"
SERVICE_VERSION="1.0.0"
MCP_PORT="8899"  # MCP通信使用stdio，这里只是标识

# 打印横幅
print_banner() {
    echo -e "${CYAN}========================================================${NC}"
    echo -e "${CYAN}    Athena工作平台 - 高德地图MCP公共服务${NC}"
    echo -e "${CYAN}    Gaode Maps MCP Public Service for Athena${NC}"
    echo -e "${CYAN}========================================================${NC}"
    echo -e "${BLUE}服务版本: ${SERVICE_VERSION}${NC}"
    echo -e "${BLUE}服务端口: ${MCP_PORT}${NC}"
    echo -e "${BLUE}日志文件: ${LOG_FILE}${NC}"
    echo -e "${BLUE}PID文件: ${PID_FILE}${NC}"
    echo -e "${CYAN}========================================================${NC}"
}

# 检查环境
check_environment() {
    echo -e "${YELLOW}[检查]${NC} 检查运行环境..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}[错误]${NC} Python3 未安装"
        exit 1
    fi

    # 检查MCP服务器目录
    if [ ! -d "$MCP_DIR" ]; then
        echo -e "${RED}[错误]${NC} MCP服务器目录不存在: $MCP_DIR"
        exit 1
    fi

    # 检查必要文件
    if [ ! -f "$MCP_DIR/src/amap_mcp_server/server.py" ]; then
        echo -e "${RED}[错误]${NC} MCP服务器主文件不存在"
        exit 1
    fi

    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"

    echo -e "${GREEN}[成功]${NC} 环境检查通过"
}

# 检查服务状态
check_status() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${GREEN}[运行中]${NC} $SERVICE_NAME (PID: $pid)"
            return 0
        else
            echo -e "${YELLOW}[已停止]${NC} PID文件存在但进程不存在"
            rm -f "$PID_FILE"
            return 1
        fi
    else
        echo -e "${YELLOW}[已停止]${NC} $SERVICE_NAME 未运行"
        return 1
    fi
}

# 启动服务
start_service() {
    echo -e "${YELLOW}[启动]${NC} 启动 $SERVICE_NAME..."

    if check_status > /dev/null 2>&1; then
        echo -e "${YELLOW}[警告]${NC} 服务已在运行中"
        return 0
    fi

    # 设置环境变量
    export PYTHONPATH="$MCP_DIR:$PYTHONPATH"
    export AMAP_API_KEY="4c98d375577d64cfce0d4d0dfee25fb9"
    export AMAP_SECRET_KEY=""
    export MCP_LOG_LEVEL="INFO"

    # MCP服务器使用stdio协议，不适合作为后台服务运行
    echo -e "${BLUE}[信息]${NC} MCP服务器通过stdio协议与AI客户端通信"
    echo -e "${BLUE}[信息]${NC} 请在AI客户端中配置以下参数启动MCP服务"
    echo ""
    echo -e "${GREEN}AI客户端配置:${NC}"
    echo "  命令: python3 $MCP_DIR/run_server.py"
    echo "  工作目录: $MCP_DIR"
    echo ""
    echo -e "${BLUE}[信息]${NC} MCP工具列表:"
    echo "   - gaode_geocode: 地理编码工具"
    echo "   - gaode_poi_search: POI搜索工具"
    echo "   - gaode_route_planning: 路径规划工具"
    echo "   - gaode_map_service: 地图服务工具"
    echo "   - gaode_traffic_service: 交通服务工具"
    echo "   - gaode_geofence: 地理围栏工具"
    echo ""
    echo -e "${BLUE}[测试]${NC} 运行测试验证MCP服务可用性..."

    # 运行测试来验证服务配置
    if [ -f "$PROJECT_ROOT/scripts/test_all_amap_services.py" ]; then
        python3 "$PROJECT_ROOT/scripts/test_all_amap_services.py"
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}[成功]${NC} MCP服务配置验证通过"
            # 创建一个标记文件表示服务已配置
            touch "$PROJECT_ROOT/.amap_mcp_configured"
        else
            echo -e "${YELLOW}[警告]${NC} 服务配置验证失败，请检查配置"
        fi
    else
        echo -e "${YELLOW}[警告]${NC} 测试脚本不存在"
    fi
}

# 停止服务
stop_service() {
    echo -e "${YELLOW}[停止]${NC} 停止 $SERVICE_NAME..."

    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid"
            sleep 2

            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid"
                echo -e "${YELLOW}[强制]${NC} 强制终止进程"
            fi

            rm -f "$PID_FILE"
            echo -e "${GREEN}[成功]${NC} $SERVICE_NAME 已停止"
        else
            echo -e "${YELLOW}[警告]${NC} 进程不存在"
            rm -f "$PID_FILE"
        fi
    else
        echo -e "${YELLOW}[信息]${NC} 服务未运行"
    fi
}

# 重启服务
restart_service() {
    stop_service
    sleep 1
    start_service
}

# 显示日志
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}[日志]${NC} 显示最近的日志:"
        tail -n 50 "$LOG_FILE"
    else
        echo -e "${YELLOW}[警告]${NC} 日志文件不存在"
    fi
}

# 显示帮助
show_help() {
    echo -e "${BLUE}用法:${NC} $0 [命令]"
    echo ""
    echo -e "${BLUE}命令:${NC}"
    echo "  start     启动高德地图MCP服务"
    echo "  stop      停止高德地图MCP服务"
    echo "  restart   重启高德地图MCP服务"
    echo "  status    查看服务状态"
    echo "  logs      显示服务日志"
    echo "  help      显示帮助信息"
    echo ""
    echo -e "${BLUE}示例:${NC}"
    echo "  $0 start          # 启动服务"
    echo "  $0 restart        # 重启服务"
    echo "  $0 status         # 查看状态"
    echo ""
    echo -e "${GREEN}AI客户端配置:${NC}"
    echo "  MCP命令: python3 -m amap_mcp_server.server"
    echo "  工作目录: $MCP_DIR"
}

# 测试服务
test_service() {
    echo -e "${BLUE}[测试]${NC} 测试高德地图MCP服务..."

    if ! check_status > /dev/null 2>&1; then
        echo -e "${RED}[错误]${NC} 服务未运行，请先启动服务"
        return 1
    fi

    # 运行测试脚本
    if [ -f "$PROJECT_ROOT/scripts/test_all_amap_services.py" ]; then
        python3 "$PROJECT_ROOT/scripts/test_all_amap_services.py"
    else
        echo -e "${YELLOW}[警告]${NC} 测试脚本不存在"
    fi
}

# 主逻辑
main() {
    print_banner

    # 检查环境
    check_environment

    # 处理命令
    case "${1:-start}" in
        "start")
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            restart_service
            ;;
        "status")
            check_status
            ;;
        "logs")
            show_logs
            ;;
        "test")
            test_service
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}[错误]${NC} 未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 信号处理
trap 'echo -e "\n${RED}[中断]${NC} 正在停止服务..."; stop_service; exit 130' INT TERM

# 执行主函数
main "$@"