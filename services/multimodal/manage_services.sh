#!/bin/bash
# -*- coding: utf-8 -*-
"""
多模态服务管理脚本
Manage Multimodal Services
"""

echo "🔧 Athena多模态服务管理"
echo "========================"

# 函数：显示服务状态
show_services() {
    echo ""
    echo "📊 当前运行的服务："
    echo "=================="

    # 查找相关进程
    ps aux | grep -E "(xiaonuo_gui_controller|multimodal_api|hybrid_api_gateway|zai-mcp-server)" | grep -v grep | while read line; do
        pid=$(echo $line | awk '{print $2}')
        cmd=$(echo $line | awk '{for(i=11;i<=NF;i++) printf "%s ", $i; print ""}')
        echo "PID: $pid"
        echo "命令: $cmd"

        # 查找端口
        port=$(lsof -p $pid 2>/dev/null | grep LISTEN | awk '{print $9}' | head -1)
        if [ ! -z "$port" ]; then
            echo "端口: $port"
        fi
        echo "---"
    done
}

# 函数：停止指定服务
stop_service() {
    local service_name=$1
    local pid=$2

    if [ -z "$pid" ]; then
        echo "❌ 未找到 $service_name 的进程ID"
        return 1
    fi

    echo "🛑 停止 $service_name (PID: $pid)..."

    # 优雅停止
    kill $pid 2>/dev/null

    # 等待2秒
    sleep 2

    # 检查是否还在运行
    if ps -p $pid > /dev/null 2>&1; then
        echo "强制停止..."
        kill -9 $pid 2>/dev/null
    fi

    echo "✅ $service_name 已停止"
}

# 函数：检查端口占用
check_ports() {
    echo ""
    echo "🌐 端口占用情况："
    echo "=================="

    ports=(8001 8088 8089 8090)

    for port in "${ports[@]}"; do
        pid=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            cmd=$(ps -p $pid -o comm= 2>/dev/null)
            echo "端口 $port: 被占用 (PID: $pid, 命令: $cmd)"
        else
            echo "端口 $port: 空闲"
        fi
    done
}

# 函数：清理重复服务
cleanup_duplicate() {
    echo ""
    echo "🧹 清理重复服务："
    echo "=================="

    # 检查8088和8089是否同时运行
    port_8088_pid=$(lsof -ti:8088 2>/dev/null)
    port_8089_pid=$(lsof -ti:8089 2>/dev/null)

    if [ ! -z "$port_8088_pid" ] && [ ! -z "$port_8089_pid" ]; then
        echo "⚠️  检测到端口8088和8089都被占用"
        echo "   8088: 基础版multimodal_api"
        echo "   8089: 增强版multimodal_api"
        echo ""
        echo "建议：停止基础版(8088)，使用增强版(8089)或混合网关(8090)"

        read -p "是否停止基础版服务？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            stop_service "multimodal_api_server(基础版)" $port_8088_pid
        fi
    fi
}

# 函数：一键清理
cleanup_all() {
    echo ""
    echo "🗑️  一键清理建议："
    echo "=================="

    echo "可停止的服务（按需选择）："
    echo ""
    echo "1. multimodal_api_server (8088) - 基础版"
    echo "   原因：已被增强版(8089)和混合网关(8090)替代"
    echo ""
    echo "2. 保留的服务："
    echo "   ✅ xiaonuo_gui_controller (8001) - 小诺GUI"
    echo "   ✅ multimodal_api_enhanced (8089) - 增强版API"
    echo "   ✅ hybrid_api_gateway (8090) - 混合网关"
    echo "   ✅ zai-mcp-server - MCP工具服务"
    echo ""

    read -p "是否停止基础版multimodal_api_server？(y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pid_8088=$(lsof -ti:8088 2>/dev/null)
        if [ ! -z "$pid_8088" ]; then
            stop_service "multimodal_api_server(基础版)" $pid_8088
        fi
    fi
}

# 主菜单
main_menu() {
    echo ""
    echo "请选择操作："
    echo "1) 显示所有服务"
    echo "2) 检查端口占用"
    echo "3) 清理重复服务"
    echo "4) 一键清理"
    echo "5) 自定义停止服务"
    echo "0) 退出"
    echo ""
    read -p "请输入选项(0-5): " choice

    case $choice in
        1)
            show_services
            ;;
        2)
            check_ports
            ;;
        3)
            cleanup_duplicate
            ;;
        4)
            cleanup_all
            ;;
        5)
            echo ""
            read -p "输入要停止的PID: " pid
            read -p "输入服务名称: " name
            stop_service "$name" "$pid"
            ;;
        0)
            echo "👋 退出"
            exit 0
            ;;
        *)
            echo "❌ 无效选项"
            ;;
    esac
}

# 直接执行指定功能
case "${1:-}" in
    "show"|"list")
        show_services
        ;;
    "ports")
        check_ports
        ;;
    "cleanup"|"clean")
        cleanup_all
        ;;
    "status"|"")
        show_services
        echo ""
        check_ports
        ;;
    *)
        echo "用法: $0 [show|ports|cleanup|status]"
        echo ""
        echo "选项："
        echo "  show     - 显示所有服务"
        echo "  ports    - 检查端口占用"
        echo "  cleanup  - 清理重复服务"
        echo "  status   - 显示完整状态（默认）"
        ;;
esac