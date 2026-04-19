#!/bin/bash
# Athena统一记忆系统 - 管理脚本
# Unified Memory System Management Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PLIST_FILE="$PROJECT_ROOT/production/launchd/com.athena.unified-memory.plist"
LAUNCH_AGENT_PATH="$HOME/Library/LaunchAgents/com.athena.unified-memory.plist"
SERVICE_URL="http://localhost:8900/health"

# 显示Logo
show_logo() {
    echo -e "${PURPLE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                                                               ║"
    echo "║        🧠  Athena统一智能体记忆系统  🧠                        ║"
    echo "║           Unified Agent Memory System                          ║"
    echo "║                                                               ║"
    echo "║                    v1.0.0 永恒记忆                              ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查服务状态
check_status() {
    echo -e "${BLUE}🔍 检查服务状态...${NC}"

    # 检查LaunchAgent
    if launchctl list | grep -q "com.athena.unified-memory"; then
        echo -e "${GREEN}✅ LaunchAgent已加载${NC}"
    else
        echo -e "${YELLOW}⚠️  LaunchAgent未加载${NC}"
    fi

    # 检查HTTP服务
    if curl -sf "$SERVICE_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 统一记忆服务运行中 (端口8900)${NC}"

        # 获取详细信息
        response=$(curl -s "$SERVICE_URL")
        echo -e "${BLUE}📊 服务信息:${NC}"
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        echo -e "${RED}❌ 统一记忆服务未运行${NC}"
        return 1
    fi
}

# 安装服务
install_service() {
    echo -e "${GREEN}📦 安装统一记忆系统服务...${NC}"

    # 复制plist文件
    cp "$PLIST_FILE" "$LAUNCH_AGENT_PATH"
    echo -e "${GREEN}✅ 配置文件已复制到 $LAUNCH_AGENT_PATH${NC}"

    # 加载LaunchAgent
    launchctl load "$LAUNCH_AGENT_PATH"
    echo -e "${GREEN}✅ LaunchAgent已加载${NC}"

    # 等待服务启动
    echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
    sleep 5

    # 验证服务
    if check_status; then
        echo -e "${GREEN}🎉 统一记忆系统安装成功！${NC}"
    else
        echo -e "${RED}❌ 服务启动失败，查看日志:${NC}"
        echo "   tail -f $PROJECT_ROOT/production/logs/unified_memory.stderr.log"
    fi
}

# 启动服务
start_service() {
    echo -e "${GREEN}🚀 启动统一记忆系统...${NC}"

    # 如果LaunchAgent未加载，先加载
    if ! launchctl list | grep -q "com.athena.unified-memory"; then
        launchctl load "$LAUNCH_AGENT_PATH"
    fi

    # 启动服务
    launchctl start com.athena.unified-memory 2>/dev/null || true

    sleep 3
    check_status
}

# 停止服务
stop_service() {
    echo -e "${YELLOW}🛑 停止统一记忆系统...${NC}"

    launchctl stop com.athena.unified-memory 2>/dev/null || true
    echo -e "${GREEN}✅ 服务已停止${NC}"
}

# 重启服务
restart_service() {
    echo -e "${YELLOW}🔄 重启统一记忆系统...${NC}"
    stop_service
    sleep 2
    start_service
}

# 卸载服务
uninstall_service() {
    echo -e "${RED}🗑️  卸载统一记忆系统...${NC}"

    # 停止服务
    stop_service

    # 卸载LaunchAgent
    launchctl unload "$LAUNCH_AGENT_PATH" 2>/dev/null || true

    # 删除配置文件
    rm -f "$LAUNCH_AGENT_PATH"
    echo -e "${GREEN}✅ 服务已卸载${NC}"
}

# 查看日志
show_logs() {
    echo -e "${BLUE}📄 显示最近日志...${NC}"
    echo ""

    # 选择日志类型
    echo "选择日志类型:"
    echo "1) 标准输出"
    echo "2) 标准错误"
    echo "3) 服务日志"
    echo ""
    read -p "请选择 (1-3): " log_choice

    case $log_choice in
        1)
            tail -f "$PROJECT_ROOT/production/logs/unified_memory.stdout.log"
            ;;
        2)
            tail -f "$PROJECT_ROOT/production/logs/unified_memory.stderr.log"
            ;;
        3)
            tail -f "$PROJECT_ROOT/production/logs/unified_memory_service.log"
            ;;
        *)
            echo -e "${RED}❌ 无效选择${NC}"
            ;;
    esac
}

# 查看统计信息
show_stats() {
    echo -e "${BLUE}📊 记忆系统统计信息${NC}"
    echo ""

    # 这里可以调用统计API
    curl -s "http://localhost:8900/api/memory/stats" 2>/dev/null | python3 -m json.tool || echo -e "${YELLOW}⚠️  无法获取统计信息${NC}"
}

# 测试服务
test_service() {
    echo -e "${BLUE}🧪 测试统一记忆系统...${NC}"
    echo ""

    # 测试健康检查
    echo "1. 测试健康检查..."
    if curl -sf "$SERVICE_URL" > /dev/null; then
        echo -e "${GREEN}   ✅ 健康检查通过${NC}"
    else
        echo -e "${RED}   ❌ 健康检查失败${NC}"
        return 1
    fi

    # 测试记忆存储
    echo ""
    echo "2. 测试记忆存储..."
    test_result=$(curl -s -X POST "http://localhost:8900/api/memory/store" \
        -H "Content-Type: application/json" \
        -d '{
            "agent_id": "xiaonuo_pisces",
            "content": "测试记忆：自动启动验证",
            "memory_type": "conversation",
            "memory_tier": "warm",
            "importance": 0.5
        }' 2>/dev/null)

    if echo "$test_result" | grep -q "success"; then
        echo -e "${GREEN}   ✅ 记忆存储成功${NC}"
    else
        echo -e "${YELLOW}   ⚠️  记忆存储响应: $test_result${NC}"
    fi

    echo ""
    echo -e "${GREEN}✅ 测试完成${NC}"
}

# 显示帮助
show_help() {
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  status    - 检查服务状态"
    echo "  install   - 安装服务(开机自启)"
    echo "  start     - 启动服务"
    echo "  stop      - 停止服务"
    echo "  restart   - 重启服务"
    echo "  uninstall - 卸载服务"
    echo "  logs      - 查看日志"
    echo "  stats     - 查看统计信息"
    echo "  test      - 测试服务"
    echo "  help      - 显示此帮助"
    echo ""
}

# 主函数
main() {
    show_logo

    # 确保日志目录存在
    mkdir -p "$PROJECT_ROOT/production/logs"

    # 解析命令
    case "${1:-help}" in
        status)
            check_status
            ;;
        install)
            install_service
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            restart_service
            ;;
        uninstall)
            uninstall_service
            ;;
        logs)
            show_logs
            ;;
        stats)
            show_stats
            ;;
        test)
            test_service
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知命令: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
