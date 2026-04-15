#!/bin/bash
# Athena浏览器自动化服务启动脚本
# Browser Automation Service Startup Script

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 服务信息
SERVICE_NAME="Athena浏览器自动化服务"
SERVICE_DIR="/Users/xujian/Athena工作平台/services/browser_automation_service"
PORT=8030

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}  ${SERVICE_NAME} 启动脚本${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# 检查端口是否被占用
check_port() {
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${YELLOW}⚠️  端口 $PORT 已被占用${NC}"
        echo -e "${YELLOW}尝试关闭现有服务...${NC}"
        pkill -f "browser_automation_service" 2>/dev/null
        sleep 2
    fi
}

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}🔍 检查依赖...${NC}"

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python3 未安装${NC}"
        exit 1
    fi

    # 检查pip
    if ! python3 -m pip --version &> /dev/null; then
        echo -e "${RED}❌ pip 未安装${NC}"
        exit 1
    fi

    echo -e "${GREEN}✅ 依赖检查通过${NC}"
}

# 安装依赖
install_dependencies() {
    echo -e "${BLUE}📦 安装Python依赖...${NC}"
    cd "$SERVICE_DIR"

    # 检查是否需要安装依赖
    if ! python3 -c "import fastapi" 2>/dev/null; then
        echo -e "${YELLOW}安装依赖包...${NC}"
        python3 -m pip install -r requirements.txt -q
    fi

    echo -e "${GREEN}✅ 依赖安装完成${NC}"
}

# 检查Playwright浏览器
check_playwright() {
    echo -e "${BLUE}🌐 检查Playwright浏览器...${NC}"

    if ! python3 -c "from playwright.sync_api import sync_playwright; sync_playwright().start().chromium.launch(headless=True).close()" 2>/dev/null; then
        echo -e "${YELLOW}安装Playwright浏览器...${NC}"
        cd "$SERVICE_DIR"
        python3 -m playwright install chromium
    fi

    echo -e "${GREEN}✅ Playwright浏览器就绪${NC}"
}

# 启动服务
start_service() {
    echo ""
    echo -e "${BLUE}======================================${NC}"
    echo -e "${BLUE}  启动 ${SERVICE_NAME}${NC}"
    echo -e "${BLUE}======================================${NC}"
    echo ""

    cd "$SERVICE_DIR"

    # 创建日志目录
    mkdir -p logs

    # 启动服务
    echo -e "${GREEN}🚀 服务启动中...${NC}"
    echo -e "${GREEN}📍 地址: http://localhost:${PORT}${NC}"
    echo -e "${GREEN}📖 文档: http://localhost:${PORT}/docs${NC}"
    echo ""
    echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
    echo ""

    python3 main.py
}

# 主流程
main() {
    check_port
    check_dependencies
    install_dependencies
    check_playwright
    start_service
}

# 运行主流程
main
