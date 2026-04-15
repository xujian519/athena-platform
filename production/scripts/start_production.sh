#!/bin/bash
# Athena生产环境启动脚本
# Production Environment Startup Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║        🚀 Athena生产环境启动脚本 🚀                            ║"
echo "║        Production Environment Startup                         ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 显示启动菜单
show_menu() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}🎯 请选择要启动的服务:${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${GREEN}1)${NC} 统一记忆系统 (Unified Memory System) - 端口8900"
    echo -e "  ${GREEN}2)${NC} 小诺统一网关 (Xiaonuo Gateway) - 端口8100"
    echo -e "  ${GREEN}3)${NC} 完整启动 (全部服务)"
    echo -e "  ${GREEN}4)${NC} 安装开机自启"
    echo -e "  ${GREEN}5)${NC} 查看服务状态"
    echo -e "  ${GREEN}6)${NC} 停止所有服务"
    echo ""
    echo -e "  ${YELLOW}0)${NC} 退出"
    echo ""
}

# 启动统一记忆系统
start_unified_memory() {
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo -e "${PURPLE}🧠 启动统一记忆系统...${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"

    # 使用管理脚本启动
    bash production/scripts/manage_unified_memory.sh install
}

# 启动小诺服务
start_xiaonuo() {
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo -e "${PURPLE}🌸 启动小诺统一网关...${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"

    # 检查是否已运行
    if lsof -ti:8100 > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  小诺服务已在运行${NC}"
        return 0
    fi

    # 启动小诺
    cd apps/xiaonuo
    python3 xiaonuo_unified_gateway_v5.py > /tmp/xiaonuo_production.log 2>&1 &
    XIAONUO_PID=$!

    echo -e "${GREEN}✅ 小诺服务已启动 (PID: $XIAONUO_PID)${NC}"
    echo -e "${BLUE}   日志: tail -f /tmp/xiaonuo_production.log${NC}"
    echo -e "${BLUE}   访问: http://localhost:8100${NC}"

    cd "$PROJECT_ROOT"
}

# 完整启动
start_all() {
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo -e "${PURPLE}🚀 完整启动Athena生产环境...${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo ""

    # 1. 启动统一记忆系统
    echo -e "${GREEN}[1/3] 启动统一记忆系统...${NC}"
    bash production/scripts/manage_unified_memory.sh start
    sleep 3

    # 2. 等待记忆系统就绪
    echo -e "${GREEN}[2/3] 等待服务就绪...${NC}"
    for i in {1..10}; do
        if curl -sf http://localhost:8900/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ 记忆系统就绪${NC}"
            break
        fi
        echo -e "${YELLOW}⏳ 等待中... ($i/10)${NC}"
        sleep 2
    done

    # 3. 启动小诺
    echo -e "${GREEN}[3/3] 启动小诺服务...${NC}"
    start_xiaonuo

    echo ""
    echo -e "${GREEN}🎉 所有服务启动完成！${NC}"
    show_status
}

# 安装开机自启
install_autostart() {
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo -e "${PURPLE}🔧 配置开机自启...${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"

    # 安装统一记忆系统
    echo -e "${GREEN}安装统一记忆系统开机自启...${NC}"
    bash production/scripts/manage_unified_memory.sh install

    # 小诺的开机自启
    echo -e "${GREEN}配置小诺开机自启...${NC}"

    # 检查是否已有配置
    if [ -f "$HOME/Library/LaunchAgents/com.athena.xiaonuo.plist" ]; then
        echo -e "${YELLOW}⚠️  小诺LaunchAgent已存在${NC}"
    else
        # 创建小诺LaunchAgent配置
        cat > "$HOME/Library/LaunchAgents/com.athena.xiaonuo.production.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.athena.xiaonuo.production</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/xujian/Athena工作平台/apps/xiaonuo/xiaonuo_unified_gateway_v5.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/xujian/Athena工作平台/apps/xiaonuo</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONPATH</key>
        <string>/Users/xujian/Athena工作平台</string>
        <key>XIAONUO_PORT</key>
        <string>8100</string>
        <key>XIAONUO_ENV</key>
        <string>production</string>
        <key>XIAONUO_MEMORY_ENABLED</key>
        <string>true</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/xujian/Athena工作平台/production/logs/xiaonuo.stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/xujian/Athena工作平台/production/logs/xiaonuo.stderr.log</string>
    <key>UserName</key>
    <string>xujian</string>
</dict>
</plist>
EOF

        launchctl load "$HOME/Library/LaunchAgents/com.athena.xiaonuo.production.plist"
        echo -e "${GREEN}✅ 小诺LaunchAgent已安装${NC}"
    fi

    echo ""
    echo -e "${GREEN}✅ 开机自启配置完成！${NC}"
    echo -e "${BLUE}   服务将在下次登录时自动启动${NC}"
}

# 查看服务状态
show_status() {
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo -e "${PURPLE}📊 服务状态${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo ""

    # 统一记忆系统
    echo -e "${GREEN}统一记忆系统 (端口8900):${NC}"
    if curl -sf http://localhost:8900/health > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ 运行中${NC}"
        response=$(curl -s http://localhost:8900/health)
        echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'   版本: {d.get(\"version\", \"unknown\")}')" 2>/dev/null || true
    else
        echo -e "   ${RED}❌ 未运行${NC}"
    fi

    echo ""

    # 小诺服务
    echo -e "${GREEN}小诺统一网关 (端口8100):${NC}"
    if curl -sf http://localhost:8100/health > /dev/null 2>&1; then
        echo -e "   ${GREEN}✅ 运行中${NC}"
        response=$(curl -s http://localhost:8100/health)
        echo "$response" | python3 -c "import sys, json; d=json.load(sys.stdin); print(f'   版本: {d.get(\"version\", \"unknown\")}')" 2>/dev/null || true
    else
        echo -e "   ${RED}❌ 未运行${NC}"
    fi

    echo ""

    # PostgreSQL
    echo -e "${GREEN}PostgreSQL数据库:${NC}"
    if brew services list | grep postgresql@17 | grep -q started; then
        echo -e "   ${GREEN}✅ 运行中${NC}"
    else
        echo -e "   ${RED}❌ 未运行${NC}"
    fi

    echo ""

    # Redis
    echo -e "${GREEN}Redis缓存:${NC}"
    if docker ps | grep -qi "redis"; then
        # 获取Redis容器名称和版本
        REDIS_CONTAINER=$(docker ps --format "{{.Names}}" | grep -i redis | head -1)
        REDIS_VERSION=$(docker exec ${REDIS_CONTAINER} redis-cli INFO server 2>/dev/null | grep "redis_version" | cut -d: -f2 | tr -d '\r')
        echo -e "   ${GREEN}✅ 运行中 (Docker)${NC}"
        echo -e "   ${BLUE}   容器: ${REDIS_CONTAINER}${NC}"
        echo -e "   ${BLUE}   版本: ${REDIS_VERSION}${NC}"
    else
        echo -e "   ${RED}❌ 未运行${NC}"
    fi

    echo ""

    # Qdrant
    echo -e "${GREEN}Qdrant向量库:${NC}"
    if docker ps | grep -q "qdrant"; then
        echo -e "   ${GREEN}✅ 运行中 (Docker)${NC}"
    else
        echo -e "   ${RED}❌ 未运行${NC}"
    fi

    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
}

# 停止所有服务
stop_all() {
    echo ""
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"
    echo -e "${PURPLE}🛑 停止所有Athena服务...${NC}"
    echo -e "${BLUE}───────────────────────────────────────────────────────────${NC}"

    # 停止小诺
    echo -e "${YELLOW}停止小诺服务...${NC}"
    pkill -f "xiaonuo_unified_gateway" || echo -e "${YELLOW}   小诺未运行${NC}"

    # 停止统一记忆系统
    echo -e "${YELLOW}停止统一记忆系统...${NC}"
    bash production/scripts/manage_unified_memory.sh stop

    echo -e "${GREEN}✅ 所有服务已停止${NC}"
}

# 主循环
main() {
    while true; do
        show_menu
        read -p "请选择 [0-6]: " choice

        case $choice in
            1)
                start_unified_memory
                ;;
            2)
                start_xiaonuo
                ;;
            3)
                start_all
                ;;
            4)
                install_autostart
                ;;
            5)
                show_status
                ;;
            6)
                stop_all
                ;;
            0)
                echo -e "${GREEN}👋 再见！${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ 无效选择，请重试${NC}"
                ;;
        esac

        echo ""
        read -p "按Enter继续..."
    done
}

# 如果有命令行参数，直接执行
if [ $# -gt 0 ]; then
    case "$1" in
        memory)
            start_unified_memory
            ;;
        xiaonuo)
            start_xiaonuo
            ;;
        all|start)
            start_all
            ;;
        autostart|install)
            install_autostart
            ;;
        status)
            show_status
            ;;
        stop)
            stop_all
            ;;
        *)
            echo "用法: $0 [memory|xiaonuo|all|autostart|status|stop]"
            exit 1
            ;;
    esac
else
    main
fi
