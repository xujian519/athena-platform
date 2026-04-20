#!/bin/bash

# 日志轮转配置管理脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GATEWAY_HOME="$(dirname "$SCRIPT_DIR")"
PLIST_FILE="$GATEWAY_HOME/com.athena.gateway.logrotate.plist"
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
SERVICE_LABEL="com.athena.gateway.logrotate"
ROTATE_SCRIPT="$GATEWAY_HOME/scripts/log_rotate.sh"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# 安装日志轮转服务
install_logrotate() {
    log_info "安装日志轮转服务..."

    # 设置脚本执行权限
    chmod +x "$ROTATE_SCRIPT"

    # 复制plist文件
    cp "$PLIST_FILE" "$LAUNCH_AGENT_DIR/"

    # 加载服务
    launchctl load "$LAUNCH_AGENT_DIR/com.athena.gateway.logrotate.plist"

    log_info "✅ 日志轮转服务安装成功！"
    log_info "每天凌晨2点自动运行"
}

# 卸载日志轮转服务
uninstall_logrotate() {
    log_info "卸载日志轮转服务..."

    launchctl unload "$LAUNCH_AGENT_DIR/com.athena.gateway.logrotate.plist" 2>/dev/null
    rm -f "$LAUNCH_AGENT_DIR/com.athena.gateway.logrotate.plist"

    log_info "✅ 日志轮转服务卸载成功！"
}

# 手动运行日志轮转
run_now() {
    log_info "手动运行日志轮转..."
    "$ROTATE_SCRIPT"
}

# 查看日志轮转日志
show_logs() {
    if [ -f "$GATEWAY_HOME/logs/logrotate.log" ]; then
        tail -20 "$GATEWAY_HOME/logs/logrotate.log"
    else
        log_warn "日志轮转日志文件不存在"
    fi
}

# 显示状态
show_status() {
    log_info "日志轮转服务状态:"

    # 检查服务是否加载
    if launchctl list | grep -q "$SERVICE_LABEL"; then
        log_info "✅ 服务已加载"
    else
        log_warn "⚠️  服务未加载"
    fi

    # 显示日志目录大小
    if [ -d "$GATEWAY_HOME/logs" ]; then
        local size=$(du -sh "$GATEWAY_HOME/logs" 2>/dev/null | cut -f1)
        log_info "日志目录大小: $size"
    fi
}

# 显示帮助
show_help() {
    cat << EOF
Gateway日志轮转管理脚本

用法: $0 <command>

命令:
    install     安装日志轮转服务（每天凌晨2点运行）
    uninstall   卸载日志轮转服务
    run         立即运行一次日志轮转
    status      查看服务状态
    logs        查看日志轮转日志
    help        显示此帮助信息

配置说明:
    - 单个日志文件最大: 100MB
    - 保留天数: 30天
    - 最多归档数: 10个
    - 自动压缩: gzip

示例:
    $0 install     # 安装服务
    $0 run         # 立即运行
    $0 status      # 查看状态

EOF
}

case "$1" in
    install)
        install_logrotate
        ;;
    uninstall)
        uninstall_logrotate
        ;;
    run)
        run_now
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo "未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

exit 0
