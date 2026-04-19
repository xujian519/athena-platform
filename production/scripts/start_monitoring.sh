#!/bin/bash
# 启动监控系统

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DAEMON_SCRIPT="$SCRIPT_DIR/infrastructure/infrastructure/monitoring/monitoring_daemon.py"

echo "🚀 启动Athena监控系统..."

# 创建日志目录
mkdir -p /Users/xujian/Athena工作平台/production/logs/monitoring
mkdir -p /Users/xujian/Athena工作平台/production/logs/alerts

# 启动监控守护进程
nohup python3 "$DAEMON_SCRIPT" > /Users/xujian/Athena工作平台/production/logs/infrastructure/infrastructure/monitoring/daemon.log 2>&1 &
echo $! > /Users/xujian/Athena工作平台/production/logs/infrastructure/infrastructure/monitoring/daemon.pid

echo "✅ 监控系统已启动"
echo "📋 PID文件: /Users/xujian/Athena工作平台/production/logs/infrastructure/infrastructure/monitoring/daemon.pid"
echo "📋 日志文件: /Users/xujian/Athena工作平台/production/logs/infrastructure/infrastructure/monitoring/daemon.log"
echo "📋 告警日志: /Users/xujian/Athena工作平台/production/logs/alerts/alerts.log"
echo ""
echo "🛑 停止监控: ./dev/scripts/stop_monitoring.sh"
echo "📊 健康检查: python3 dev/scripts/infrastructure/infrastructure/monitoring/comprehensive_health_check.py"
