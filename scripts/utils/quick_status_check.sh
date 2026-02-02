#!/bin/bash

# Athena工作平台快速状态检查脚本
# Quick Status Check for Athena Work Platform

echo "🏛️ Athena工作平台 - 快速状态检查"
echo "=================================="

# 检查时间
echo "🕐 检查时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 服务端口列表
services=(
    "8000:Athena主服务"
    "8008:Athena记忆服务"
    "8083:小诺记忆服务"
    "8010:Athena身份认知服务"
    "8011:记忆集成服务"
)

# 检查服务状态
echo "📊 服务状态:"
healthy_count=0
total_count=${#services[@]}

for service in "${services[@]}"; do
    port="${service%%:*}"
    name="${service##*:}"

    if curl -s "http://localhost:$port/health" > /dev/null 2>&1; then
        echo "  ✅ $name (端口$port): 运行中"
        ((healthy_count++))
    else
        echo "  ❌ $name (端口$port): 停止或异常"
    fi
done

echo ""
echo "📈 服务健康度: $healthy_count/$total_count ($(( healthy_count * 100 / total_count ))%)"

# 系统资源检查
echo ""
echo "💻 系统资源:"
echo "  🖥️  CPU使用率: $(top -l 1 | grep "CPU usage" | awk '{print $3}' | sed 's/%//')%"
echo "  💾 内存使用: $(vm_stat | awk '/Pages free/ {free=$3} /Pages active/ {active=$3} /Pages wired/ {wired=$3} END {printf "%.1f%%", (active+wired)*4096/(active+wired+free)*4096*100}')"

# 磁盘空间
echo "  💿 磁盘使用: $(df -h / | tail -1 | awk '{print $5}')"

# 最近日志
echo ""
echo "📋 最近活动:"
if [ -f "/Users/xujian/Athena工作平台/documentation/logs/latest_health_check.json" ]; then
    echo "  📄 最后健康检查: $(stat -f "%Sm" -t "%Y-%m-%d %H:%M" /Users/xujian/Athena工作平台/documentation/logs/latest_health_check.json)"
else
    echo "  📄 最后健康检查: 无记录"
fi

# 快速操作提示
echo ""
echo "⚡ 快速操作:"
echo "  🔄 重启所有服务: bash scripts/start_core_services.sh"
echo "  🔍 详细监控: python3 scripts/services/service_health_monitor.py --check"
echo "  📊 持续监控: python3 scripts/services/service_health_monitor.py --monitor"

echo ""
echo "✅ 状态检查完成"