#!/bin/bash

# 停止融合服务脚本
# 停止所有融合服务进程

echo "🛑 停止Athena工作平台融合服务"
echo "=============================="

# 设置工作目录
cd "$(dirname "$0")/.."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 停止服务
stop_service() {
    local service_name=$1
    local pid_file="logs/fusion/${service_name}.pid"

    if [ -f $pid_file ]; then
        local pid=$(cat $pid_file)
        if kill -0 $pid 2>/dev/null; then
            log_info "停止 $service_name (PID: $pid)"
            kill $pid

            # 等待进程退出
            local count=0
            while kill -0 $pid 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done

            # 如果进程仍然存在，强制杀死
            if kill -0 $pid 2>/dev/null; then
                log_warn "强制停止 $service_name"
                kill -9 $pid
            fi
        else
            log_warn "$service_name 进程不存在"
        fi
        rm -f $pid_file
    else
        log_warn "$service_name PID文件不存在"
    fi
}

# 查找并停止特定端口的进程
stop_process_by_port() {
    local port=$1
    local service_name=$2

    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ ! -z "$pid" ]; then
        log_info "停止占用端口 $port 的进程 (PID: $pid)"
        kill $pid
        sleep 2
        # 强制杀死如果仍在运行
        if kill -0 $pid 2>/dev/null; then
            kill -9 $pid
        fi
    fi
}

# 停止所有融合服务
stop_all_services() {
    log_info "停止所有融合服务..."

    # 从PID文件停止
    stop_service "unified-identity"
    stop_service "intelligent-collaboration"
    stop_service "websocket-server"
    stop_service "api-gateway-enhanced"

    # 清理端口占用
    log_info "清理端口占用..."
    stop_process_by_port 8090 "统一身份服务"
    stop_process_by_port 8091 "协作中枢"
    stop_process_by_port 8092 "WebSocket服务"
    stop_process_by_port 8080 "API网关"

    # 额外清理可能残留的Python进程
    log_info "清理残留进程..."
    pkill -f "api_server.py" 2>/dev/null || true
    pkill -f "websocket_server.py" 2>/dev/null || true
    pkill -f "main_enhanced.py" 2>/dev/null || true
    pkill -f "collaboration_controller.py" 2>/dev/null || true
}

# 验证服务已停止
verify_services_stopped() {
    log_info "验证服务已停止..."

    local ports=(8090 8091 8092 8080)
    local all_stopped=true

    for port in "${ports[@]}"; do
        local pid=$(lsof -ti:$port 2>/dev/null)
        if [ ! -z "$pid" ]; then
            log_error "端口 $port 仍被进程 $pid 占用"
            all_stopped=false
        fi
    done

    if [ "$all_stopped" = true ]; then
        log_info "所有服务已成功停止"
    else
        log_warn "部分服务可能仍在运行，请手动检查"
    fi
}

# 清理日志（可选）
cleanup_logs() {
    if [ "$1" = "--clean-logs" ]; then
        log_info "清理日志文件..."
        if [ -d logs/fusion ]; then
            rm -f logs/fusion/*.log
            rm -f logs/fusion/*.pid
            log_info "日志文件已清理"
        fi
    fi
}

# 主函数
main() {
    echo -e "${RED}停止Athena工作平台融合服务${NC}"
    echo "============================"
    echo

    # 停止服务
    stop_all_services
    echo

    # 验证
    verify_services_stopped
    echo

    # 清理日志（如果指定）
    cleanup_logs "$1"

    echo -e "\n${GREEN}✅ 融合服务已停止${NC}"
    echo -e "\n提示: 使用 'bash scripts/start_fusion_services.sh' 重新启动服务"
}

# 执行主函数
main "$@"