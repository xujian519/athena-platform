#!/bin/bash
# -*- coding: utf-8 -*-
# Athena工作平台 - 公共爬虫服务启动脚本
# Public Crawler Service Startup Script for Athena Platform

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
CRAWLER_DIR="$PROJECT_ROOT/services/crawler"
PID_FILE="$PROJECT_ROOT/.crawler_api.pid"
LOG_FILE="$PROJECT_ROOT/logs/crawler_api.log"

# 服务信息
SERVICE_NAME="Athena公共爬虫服务"
SERVICE_VERSION="1.0.0"
API_PORT="8001"

# 打印横幅
print_banner() {
    echo -e "${CYAN}========================================================${NC}"
    echo -e "${CYAN}    Athena工作平台 - 公共爬虫服务${NC}"
    echo -e "${CYAN}    Public Crawler Service for Athena${NC}"
    echo -e "${CYAN}========================================================${NC}"
    echo -e "${BLUE}服务版本: ${SERVICE_VERSION}${NC}"
    echo -e "${BLUE}API端口: ${API_PORT}${NC}"
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

    # 检查爬虫目录
    if [ ! -d "$CRAWLER_DIR" ]; then
        echo -e "${RED}[错误]${NC} 爬虫服务目录不存在: $CRAWLER_DIR"
        exit 1
    fi

    # 检查必要文件
    if [ ! -f "$CRAWLER_DIR/api/crawler_api.py" ]; then
        echo -e "${RED}[错误]${NC} 爬虫API文件不存在"
        exit 1
    fi

    # 检查依赖
    echo -e "${YELLOW}[检查]${NC} 检查Python依赖..."
    cd "$CRAWLER_DIR"

    # 检查FastAPI
    python3 -c "import fastapi" 2>/dev/null || {
        echo -e "${YELLOW}[警告]${NC} FastAPI未安装，正在安装..."
        pip3 install fastapi uvicorn
    }

    # 检查aiohttp
    python3 -c "import aiohttp" 2>/dev/null || {
        echo -e "${YELLOW}[警告]${NC} aiohttp未安装，正在安装..."
        pip3 install aiohttp beautifulsoup4 pandas
    }

    # 创建日志目录
    mkdir -p "$(dirname "$LOG_FILE")"
    mkdir -p "$PROJECT_ROOT/data/crawler/results"
    mkdir -p "$PROJECT_ROOT/data/crawler/cache"

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
    export PYTHONPATH="$CRAWLER_DIR:$PYTHONPATH"

    # 启动服务
    cd "$CRAWLER_DIR"
    nohup python3 -m uvicorn api.crawler_api:app \
        --host 0.0.0.0 \
        --port $API_PORT \
        --log-level info \
        --access-log > "$LOG_FILE" 2>&1 &

    local pid=$!
    echo "$pid" > "$PID_FILE"

    # 等待启动
    sleep 3

    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${GREEN}[成功]${NC} $SERVICE_NAME 启动成功 (PID: $pid)"
        echo -e "${BLUE}[信息]${NC} API服务地址: http://localhost:$API_PORT"
        echo -e "${BLUE}[信息]${NC} API文档: http://localhost:$API_PORT/docs"

        # 测试API连接
        sleep 2
        if curl -s "http://localhost:$API_PORT/" > /dev/null; then
            echo -e "${GREEN}[成功]${NC} API服务连接正常"
        else
            echo -e "${YELLOW}[警告]${NC} API服务可能还在启动中"
        fi
    else
        echo -e "${RED}[失败]${NC} $SERVICE_NAME 启动失败"
        rm -f "$PID_FILE"
        exit 1
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

# 测试服务
test_service() {
    echo -e "${BLUE}[测试]${NC} 测试爬虫API服务..."

    if ! check_status > /dev/null 2>&1; then
        echo -e "${RED}[错误]${NC} 服务未运行，请先启动服务"
        return 1
    fi

    # 测试API端点
    endpoints=(
        "/"
        "/health"
        "/presets"
        "/stats"
    )

    for endpoint in "${endpoints[@]}"; do
        echo -e "${BLUE}[测试]${NC} http://localhost:$API_PORT$endpoint"
        if response=$(curl -s "http://localhost:$API_PORT$endpoint"); then
            echo -e "${GREEN}[成功]${NC} 响应正常"
        else
            echo -e "${RED}[失败]${NC} 无响应"
        fi
    done
}

# 显示帮助
show_help() {
    echo -e "${BLUE}用法:${NC} $0 [命令]"
    echo ""
    echo -e "${BLUE}命令:${NC}"
    echo "  start     启动爬虫API服务"
    echo "  stop      停止爬虫API服务"
    echo "  restart   重启爬虫API服务"
    echo "  status    查看服务状态"
    echo "  logs      显示服务日志"
    echo "  test      测试API服务"
    echo "  help      显示帮助信息"
    echo ""
    echo -e "${BLUE}API端点:${NC}"
    echo "  GET  /                     服务根路径"
    echo "  POST /crawl               爬取URL列表"
    echo "  GET  /task/{task_id}        查询任务状态"
    echo "  GET  /tasks                 列出所有任务"
    echo "  GET  /presets               获取预定义配置"
    echo "  GET  /stats                 获取统计信息"
    echo "  GET  /health                健康检查"
    echo "  GET  /docs                   API文档"
    echo ""
    echo -e "${BLUE}示例:${NC}"
    echo "  $0 start          # 启动服务"
    echo "  $0 restart        # 重启服务"
    echo "  $0 test           # 测试服务"
    echo "  curl http://localhost:$API_PORT/presets"
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