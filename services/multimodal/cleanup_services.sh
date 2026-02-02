#!/bin/bash
# -*- coding: utf-8 -*-
"""
清理多余的多模态服务
Clean up Redundant Multimodal Services
"""

echo "🧹 清理多模态后台服务"
echo "=================="

# 函数：安全停止服务
safe_stop() {
    local pid=$1
    local name=$2

    if [ -z "$pid" ]; then
        echo "⚠️ 未找到进程: $name"
        return 1
    fi

    # 检查进程是否存在
    if ! ps -p $pid > /dev/null 2>&1; then
        echo "✅ 进程已停止: $name"
        return 0
    fi

    echo "🛑 停止服务: $name (PID: $pid)"

    # 优雅停止
    kill $pid 2>/dev/null

    # 等待最多5秒
    for i in {1..5}; do
        if ! ps -p $pid > /dev/null 2>&1; then
            echo "✅ 服务已优雅停止: $name"
            return 0
        fi
        sleep 1
        echo "  等待停止... ($i/5)"
    done

    # 强制停止
    echo "⚡ 强制停止服务: $name"
    kill -9 $pid 2>/dev/null

    if ps -p $pid > /dev/null 2>&1; then
        echo "❌ 无法停止服务: $name"
        return 1
    else
        echo "✅ 服务已强制停止: $name"
        return 0
    fi
}

# 获取进程ID
get_pid() {
    local pattern=$1
    ps aux | grep "$pattern" | grep -v grep | awk '{print $2}' | head -1
}

echo ""
echo "🔍 查找运行中的服务..."

# 定义要保留的服务
declare -A keep_services=(
    ["hybrid_api_gateway"]="混合API网关 (主入口)"
    ["xiaonuo_gui_controller"]="小诺GUI控制器"
    ["zai-mcp-server"]="MCP工具服务"
)

# 定义可清理的服务
declare -A clean_services=(
    ["multimodal_api_server"]="基础版多模态API (8088) - 已被增强版和混合网关替代"
    ["multimodal_api_enhanced"]="增强版多模态API (8089) - 如果只使用混合网关可停止"
)

echo ""
echo "📋 服务清单："
echo "============"

# 检查所有服务
all_services=("${!keep_services[@]}" "${!clean_services[@]}")

for service in "${all_services[@]}"; do
    pid=$(get_pid "$service")
    if [ ! -z "$pid" ]; then
        if [[ -n "${keep_services[$service]}" ]]; then
            echo "✅ 保留: $service (PID: $pid) - ${keep_services[$service]}"
        else
            echo "⚠️  可清理: $service (PID: $pid) - ${clean_services[$service]}"
        fi
    else
        echo "⭕ 未运行: $service"
    fi
done

echo ""
echo "🎯 清理选项："
echo "============"
echo "1) 最小化 - 只保留混合网关和小诺GUI (推荐)"
echo "2) 保守 - 停止基础版，保留增强版"
echo "3) 查看详细 - 显示所有进程详情"
echo "4) 手动选择 - 自定义要停止的服务"
echo "0) 退出"
echo ""

read -p "请选择 (0-4): " choice

case $choice in
    1)
        echo ""
        echo "🚀 最小化清理..."
        echo "将保留："
        echo "  - hybrid_api_gateway (PID: $(get_pid 'hybrid_api_gateway'))"
        echo "  - xiaonuo_gui_controller (PID: $(get_pid 'xiaonuo_gui_controller'))"
        echo "  - zai-mcp-server (PID: $(get_pid 'zai-mcp-server'))"
        echo ""
        read -p "确认继续？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # 停止基础版
            safe_stop $(get_pid 'multimodal_api_server') "multimodal_api_server"
            # 停止增强版
            safe_stop $(get_pid 'multimodal_api_enhanced') "multimodal_api_enhanced"
        fi
        ;;
    2)
        echo ""
        echo "🔧 保守清理..."
        echo "将停止基础版，保留增强版"
        echo ""
        read -p "确认停止基础版？(y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            safe_stop $(get_pid 'multimodal_api_server') "multimodal_api_server"
        fi
        ;;
    3)
        echo ""
        echo "📊 详细进程信息："
        echo "=================="
        ps aux | grep -E "(xiaonuo_gui_controller|multimodal_api|hybrid_api_gateway|zai-mcp-server)" | grep -v grep | \
        awk 'BEGIN{printf "%-8s %-6s %-40s %-10s\n","PID","端口","命令","状态"}
             {pid=$2; cmd=$11; for(i=12;i<=NF;i++) cmd=cmd" "$i;
              port="";
              if(cmd ~ "xiaonuo_gui") port="8001";
              else if(cmd ~ "multimodal_api_server") port="8088";
              else if(cmd ~ "multimodal_api_enhanced") port="8089";
              else if(cmd ~ "hybrid_api_gateway") port="8090";
              port=(substr(port,1,5));
              printf "%-8s %-6s %-40s %-10s\n",pid,port,substr(cmd,1,40),"RUNNING"}'
        ;;
    4)
        echo ""
        echo "🎮 手动选择要停止的服务："
        echo "可停止的服务："
        echo "1) multimodal_api_server (基础版)"
        echo "2) multimodal_api_enhanced (增强版)"
        echo "0) 返回"
        echo ""
        read -p "选择要停止的服务 (0-2): " sub_choice
        case $sub_choice in
            1)
                safe_stop $(get_pid 'multimodal_api_server') "multimodal_api_server"
                ;;
            2)
                safe_stop $(get_pid 'multimodal_api_enhanced') "multimodal_api_enhanced"
                ;;
            0)
                echo "返回"
                ;;
            *)
                echo "无效选择"
                ;;
        esac
        ;;
    0)
        echo "👋 退出"
        exit 0
        ;;
    *)
        echo "❌ 无效选择"
        ;;
esac

echo ""
echo "✅ 清理完成！"
echo ""
echo "当前运行的服务："
echo "=================="

# 显示最终状态
for service in "${!keep_services[@]}"; do
    pid=$(get_pid "$service")
    if [ ! -z "$pid" ]; then
        echo "✅ $service (PID: $pid)"
    else
        echo "❌ $service (未运行)"
    fi
done

echo ""
echo "💡 提示："
echo "- 使用 './manage_services.sh status' 查看详细状态"
echo "- 使用 'curl http://localhost:8090/api/health' 检查服务健康"