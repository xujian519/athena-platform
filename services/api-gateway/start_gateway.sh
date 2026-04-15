#!/bin/bash
# Athena API Gateway 启动脚本

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
SERVICE_NAME="athena-api-gateway"
LOG_DIR="$PROJECT_ROOT/logs"
DATA_DIR="$PROJECT_ROOT/data"
CONFIG_DIR="$PROJECT_ROOT/configs"

# 端口配置
GATEWAY_PORT=${GATEWAY_PORT:-8080}

# 日志函数
log_info() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [INFO] $1"
}

log_error() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [ERROR] $1" >&2
}

# 创建目录
create_directories() {
    log_info "创建必要的目录..."
    mkdir -p "$LOG_DIR" "$DATA_DIR" "$CONFIG_DIR"
}

# 检查Python环境
check_python() {
    log_info "检查Python环境..."
    
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    python_version=$(python3 --version | awk '{print $2}')
    log_info "Python版本: $python_version"
}

# 安装依赖
install_dependencies() {
    log_info "安装Python依赖包..."
    
    cd "$SCRIPT_DIR"
    if [[ -f "requirements.txt" ]]; then
        python3 -m pip install -r requirements.txt
        log_info "依赖安装完成"
    else
        log_error "requirements.txt 文件不存在"
        exit 1
    fi
}

# 检查服务是否运行
check_service() {
    if pgrep -f "athena_gateway.py" > /dev/null; then
        log_info "Athena API Gateway 已在运行"
        return 0
    else
        return 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止 Athena API Gateway..."
    
    if pgrep -f "athena_gateway.py" > /dev/null; then
        pkill -f "athena_gateway.py"
        sleep 2
        
        # 强制停止
        if pgrep -f "athena_gateway.py" > /dev/null; then
            pkill -9 -f "athena_gateway.py"
        fi
        
        log_info "Athena API Gateway 已停止"
    else
        log_info "Athena API Gateway 未在运行"
    fi
}

# 启动服务
start_service() {
    log_info "启动 Athena API Gateway..."
    
    cd "$SCRIPT_DIR"
    
    # 设置环境变量
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
    export GATEWAY_PORT="$GATEWAY_PORT"
    
    # 启动服务
    nohup python3 athena_gateway.py > "$LOG_DIR/gateway_stdout.log" 2> "$LOG_DIR/gateway_stderr.log" &
    
    local pid=$!
    echo "$pid" > "$DATA_DIR/gateway.pid"
    
    # 等待服务启动
    sleep 3
    
    if ps -p "$pid" > /dev/null; then
        log_info "Athena API Gateway 启动成功 (PID: $pid)"
        log_info "服务地址: http://localhost:$GATEWAY_PORT"
        log_info "API文档: http://localhost:$GATEWAY_PORT/docs"
        return 0
    else
        log_error "Athena API Gateway 启动失败"
        return 1
    fi
}

# 重启服务
restart_service() {
    log_info "重启 Athena API Gateway..."
    stop_service
    sleep 2
    start_service
}

# 查看服务状态
show_status() {
    if check_service; then
        local pid=$(pgrep -f "athena_gateway.py")
        log_info "Athena API Gateway 运行中 (PID: $pid)"
        log_info "服务地址: http://localhost:$GATEWAY_PORT"
        
        # 检查端口占用
        if command -v lsof &> /dev/null; then
            local port_info=$(lsof -i ":$GATEWAY_PORT" | grep LISTEN)
            if [[ -n "$port_info" ]]; then
                log_info "端口占用情况:"
                echo "$port_info"
            fi
        fi
    else
        log_info "Athena API Gateway 未运行"
    fi
}

# 查看日志
show_logs() {
    if [[ -f "$LOG_DIR/gateway.log" ]]; then
        log_info "显示最近的日志:"
        tail -f "$LOG_DIR/gateway.log"
    else
        log_error "日志文件不存在: $LOG_DIR/gateway.log"
    fi
}

# 运行健康检查
health_check() {
    log_info "执行健康检查..."
    
    if command -v curl &> /dev/null; then
        local response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$GATEWAY_PORT/health" || echo "000")
        
        if [[ "$response" == "200" ]]; then
            log_info "健康检查通过 (HTTP 200)"
            return 0
        else
            log_error "健康检查失败 (HTTP $response)"
            return 1
        fi
    else
        log_error "curl 命令未安装，无法执行健康检查"
        return 1
    fi
}

# 清理函数
cleanup() {
    log_info "清理资源..."
    # 清理临时文件等
}

# 主函数
main() {
    local command=${1:-"start"}
    
    case "$command" in
        "start")
            create_directories
            check_python
            install_dependencies
            
            if check_service; then
                log_info "服务已在运行，使用 'restart' 重启服务"
                exit 0
            fi
            
            start_service
            ;;
        "stop")
            stop_service
            ;;
        "restart")
            create_directories
            check_python
            restart_service
            ;;
        "status")
            show_status
            ;;
        "logs")
            show_logs
            ;;
        "health")
            health_check
            ;;
        "install")
            create_directories
            check_python
            install_dependencies
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            echo "用法: $0 {start|stop|restart|status|logs|health|install|cleanup}"
            echo ""
            echo "命令说明:"
            echo "  start    - 启动服务"
            echo "  stop     - 停止服务"
            echo "  restart  - 重启服务"
            echo "  status   - 查看状态"
            echo "  logs     - 查看日志"
            echo "  health   - 健康检查"
            echo "  install  - 仅安装依赖"
            echo "  cleanup  - 清理资源"
            echo ""
            echo "环境变量:"
            echo "  GATEWAY_PORT - 服务端口 (默认: 8080)"
            exit 1
            ;;
    esac
}

# 信号处理
trap cleanup EXIT INT TERM

# 执行主函数
main "$@"