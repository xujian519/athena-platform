#!/bin/bash

# Athena Gateway 服务管理脚本（macOS launchd）

GATEWAY_HOME="/Users/xujian/Athena工作平台/gateway-unified"
PLIST_FILE="$GATEWAY_HOME/com.athena.gateway.plist"
LAUNCH_AGENT_DIR="$HOME/Library/LaunchAgents"
SERVICE_LABEL="com.athena.gateway"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查plist文件是否存在
check_plist() {
    if [ ! -f "$PLIST_FILE" ]; then
        log_error "plist文件不存在: $PLIST_FILE"
        return 1
    fi
    return 0
}

# 安装服务
install_service() {
    log_info "安装Athena Gateway服务..."

    if ! check_plist; then
        return 1
    fi

    # 复制plist文件到LaunchAgents目录
    cp "$PLIST_FILE" "$LAUNCH_AGENT_DIR/"
    if [ $? -ne 0 ]; then
        log_error "复制plist文件失败"
        return 1
    fi

    # 加载服务
    launchctl load "$LAUNCH_AGENT_DIR/com.athena.gateway.plist"
    if [ $? -eq 0 ]; then
        log_info "✅ 服务安装成功！"
        log_info "服务将在系统启动时自动运行"
        return 0
    else
        log_error "服务加载失败"
        return 1
    fi
}

# 卸载服务
uninstall_service() {
    log_info "卸载Athena Gateway服务..."

    # 先停止服务
    stop_service

    # 卸载服务
    launchctl unload "$LAUNCH_AGENT_DIR/com.athena.gateway.plist" 2>/dev/null

    # 删除plist文件
    rm -f "$LAUNCH_AGENT_DIR/com.athena.gateway.plist"

    log_info "✅ 服务卸载成功！"
}

# 启动服务
start_service() {
    log_info "启动Athena Gateway服务..."

    launchctl start "$SERVICE_LABEL"
    if [ $? -eq 0 ]; then
        log_info "✅ 服务启动成功！"
        sleep 2
        show_status
        return 0
    else
        log_error "服务启动失败"
        return 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止Athena Gateway服务..."

    launchctl stop "$SERVICE_LABEL" 2>/dev/null
    if [ $? -eq 0 ]; then
        log_info "✅ 服务停止成功！"
        return 0
    else
        log_warn "服务可能未运行"
        return 0
    fi
}

# 重启服务
restart_service() {
    log_info "重启Athena Gateway服务..."
    stop_service
    sleep 2
    start_service
}

# 显示服务状态
show_status() {
    log_info "Athena Gateway服务状态:"

    # 检查进程
    PID=$(pgrep -f "gateway-unified")
    if [ -n "$PID" ]; then
        log_info "✅ 服务正在运行 (PID: $PID)"
    else
        log_warn "⚠️  服务未运行"
    fi

    # 检查端口
    PORT=$(lsof -i :8005 -t -sTCP:LISTEN 2>/dev/null)
    if [ -n "$PORT" ]; then
        log_info "✅ 端口8005正在监听"
    else
        log_warn "⚠️  端口8005未监听"
    fi

    # 显示日志
    echo ""
    log_info "最近的日志："
    if [ -f "$GATEWAY_HOME/logs/gateway-error.log" ]; then
        tail -5 "$GATEWAY_HOME/logs/gateway-error.log"
    fi
}

# 查看日志
show_logs() {
    if [ -f "$GATEWAY_HOME/logs/gateway-error.log" ]; then
        tail -f "$GATEWAY_HOME/logs/gateway-error.log"
    else
        log_error "日志文件不存在"
    fi
}

# 显示帮助
show_help() {
    cat << EOF
Athena Gateway 服务管理脚本

用法: $0 <command> [options]

命令:
    install     安装并启动服务（开机自动运行）
    uninstall   卸载服务
    start       启动服务
    stop        停止服务
    restart     重启服务
    status      显示服务状态
    logs        查看实时日志
    help        显示此帮助信息

示例:
    $0 install     # 首次安装服务
    $0 start       # 启动服务
    $0 stop        # 停止服务
    $0 restart     # 重启服务
    $0 status      # 查看状态
    $0 logs        # 查看日志

注意：
    - 服务安装后会配置为开机自动启动
    - 配置文件修改后会自动重启服务
    - 服务崩溃后会自动重启

EOF
}

# 主程序
case "$1" in
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
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
        log_error "未知命令: $1"
        echo ""
        show_help
        exit 1
        ;;
esac

exit 0
