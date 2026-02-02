#!/bin/bash

# 停止优化版Athena工作平台
# 停止所有优化服务

echo "🛑 停止优化版Athena工作平台"
echo "=========================="

# 设置工作目录
cd "$(dirname "$0")/.."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

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
    local pid_file="logs/${service_name}/${service_name}.pid"

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

            # 强制杀死如果仍在运行
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

# 停止所有优化服务
stop_all_services() {
    log_info "停止所有优化服务..."

    # 从PID文件停止
    stop_service "unified-identity"
    stop_service "intelligent-collaboration"
    stop_service "websocket-server"
    stop_service "api-gateway-enhanced"
    stop_service "https-server"
    stop_service "custom-ai"

    # 监控服务
    stop_service "prometheus"
    stop_service "alerting"

    # 清理端口占用
    log_info "清理端口占用..."
    stop_process_by_port 8000 "HTTP服务"
    stop_process_by_port 8080 "API网关"
    stop_process_by_port 8090 "统一身份服务"
    stop_process_by_port 8091 "协作中枢"
    stop_process_by_port 8092 "WebSocket服务"
    stop_process_by_port 8093 "告警服务"
    stop_process_by_port 8094 "自定义AI服务"
    stop_process_by_port 8443 "HTTPS服务"
    stop_process_by_port 9090 "Prometheus"

    # 额外清理
    log_info "清理相关进程..."
    pkill -f "api_server.py" 2>/dev/null || true
    pkill -f "websocket_server.py" 2>/dev/null || true
    pkill -f "main_enhanced.py" 2>/dev/null || true
    pkill -f "collaboration_controller.py" 2>/dev/null || true
    pkill -f "alerting_system.py" 2>/dev/null || true
    pkill -f "custom_ai_manager.py" 2>/dev/null || true
    pkill -f "learning_system.py" 2>/dev/null || true

    # 停止Redis（如果由我们启动）
    if pgrep -f "redis-server.*:6379" > /dev/null; then
        log_info "停止Redis服务..."
        pkill -f "redis-server.*:6379"
    fi
}

# 验证服务已停止
verify_services_stopped() {
    log_info "验证服务已停止..."

    local ports=(8000 8080 8090 8091 8092 8093 8094 8443 9090)
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
        find logs -name "*.log" -type f -delete 2>/dev/null || true
        find logs -name "*.pid" -type f -delete 2>/dev/null || true
        log_info "日志文件已清理"
    fi
}

# 生成停止报告
generate_stop_report() {
    log_info "生成停止报告..."

    report_file="logs/stop_report_$(date +%Y%m%d_%H%M%S).txt"
    {
        echo "Athena工作平台停止报告"
        echo "======================="
        echo "停止时间: $(date)"
        echo ""
        echo "停止的服务:"
        echo "- 统一身份服务 (端口 8090)"
        echo "- 协作中枢 (端口 8091)"
        echo "- WebSocket通信 (端口 8092)"
        echo "- API网关 (端口 8080)"
        echo "- HTTPS服务 (端口 8443)"
        echo "- 自定义AI服务 (端口 8094)"
        echo "- 告警系统 (端口 8093)"
        echo "- Prometheus监控 (端口 9090)"
        echo ""
        echo "优化功能已停止:"
        echo "- 连接池管理"
        echo "- 响应缓存"
        echo "- 消息序列化优化"
        echo "- 性能监控"
        echo "- 智能告警"
        echo "- API认证"
        echo "- 自定义AI角色"
        echo "- 学习系统"
    } > "$report_file"

    log_info "停止报告已保存: $report_file"
}

# 主函数
main() {
    echo -e "${RED}停止Athena工作平台优化版${NC}"
    echo "========================="
    echo

    # 停止服务
    stop_all_services
    echo

    # 验证
    verify_services_stopped
    echo

    # 生成报告
    generate_stop_report
    echo

    # 清理日志（如果指定）
    cleanup_logs "$1"

    echo -e "\n${GREEN}✅ 优化版平台已停止${NC}"
    echo -e "\n提示:"
    echo "1. 使用 'bash scripts/start_optimized_platform.sh' 重新启动"
    echo "2. 使用 '--clean-logs' 参数清理日志"
    echo "3. 查看 'logs/' 目录获取更多信息"
}

# 执行主函数
main "$@"