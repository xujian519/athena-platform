# =============================================================================
# Athena 工作平台命令别名
# 使用方法：source /Users/xujian/Athena工作平台/config/bash_aliases.sh
# =============================================================================

# 基础服务管理别名
alias athena-start='cd /Users/xujian/Athena工作平台 && ./dev/scripts/quick_start.sh'
alias athena-stop='cd /Users/xujian/Athena工作平台 && ./dev/scripts/athena_services_manager.sh stop'
alias athena-restart='cd /Users/xujian/Athena工作平台 && ./dev/scripts/athena_services_manager.sh restart'
alias athena-status='cd /Users/xujian/Athena工作平台 && ./dev/scripts/athena_services_manager.sh status'
alias athena-health='cd /Users/xujian/Athena工作平台 && ./dev/scripts/athena_services_manager.sh health'
alias athena-full='cd /Users/xujian/Athena工作平台 && ./dev/scripts/athena_services_manager.sh start'

# 调试模式别名
alias athena-debug='DEBUG=true cd /Users/xujian/Athena工作平台 && ./dev/scripts/athena_services_manager.sh status'

# 日志查看别名
alias athena-logs='tail -f /Users/xujian/Athena工作平台/logs/athena_services_$(date +%Y%m%d).log'
alias athena-log='cat /Users/xujian/Athena工作平台/logs/athena_services_$(date +%Y%m%d).log | tail -20'

# 端口检查别名
alias athena-ports='netstat -an | grep LISTEN | grep -E "(6379|5432|8080|8081|8082|8083|8084|8085|8086|9200)"'
alias athena-processes='ps aux | grep -E "(redis|postgres|xiaonuo|nlp|vector)"'

# 项目目录跳转别名
alias athena='cd /Users/xujian/Athena工作平台'
alias athena-scripts='cd /Users/xujian/Athena工作平台/dev/scripts'
alias athena-logs-dir='cd /Users/xujian/Athena工作平台/logs'
alias athena-config='cd /Users/xujian/Athena工作平台/config'

# 便捷组合命令
alias athena-check='athena-status && athena-health'
alias athena-reset='athena-stop && sleep 3 && athena-start'

# 显示帮助信息
athena-help() {
    echo "🚀 Athena 工作平台命令别名"
    echo ""
    echo "基础命令："
    echo "  athena-start     - 快速启动核心服务"
    echo "  athena-full      - 完整启动所有服务"
    echo "  athena-stop      - 停止所有服务"
    echo "  athena-restart   - 重启所有服务"
    echo "  athena-status    - 显示服务状态"
    echo "  athena-health    - 执行健康检查"
    echo ""
    echo "调试和监控："
    echo "  athena-debug     - 启用调试模式查看状态"
    echo "  athena-logs      - 实时查看日志"
    echo "  athena-log       - 查看最近20行日志"
    echo "  athena-ports     - 检查服务端口状态"
    echo "  athena-processes - 查看相关进程"
    echo ""
    echo "便捷命令："
    echo "  athena           - 进入项目目录"
    echo "  athena-check     - 检查状态和健康"
    echo "  athena-reset     - 重置服务（停止后重新启动）"
    echo ""
    echo "目录跳转："
    echo "  athena-scripts   - 进入脚本目录"
    echo "  athena-logs-dir  - 进入日志目录"
    echo "  athena-config    - 进入配置目录"
    echo ""
    echo "使用示例："
    echo "  athena-start     # 清理上下文后快速恢复"
    echo "  athena-check     # 全面检查系统状态"
    echo "  athena-reset     # 完全重置服务"
}

echo "✅ Athena 命令别名已加载！"
echo "💡 输入 'athena-help' 查看所有可用命令"