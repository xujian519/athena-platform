#!/bin/bash

# Athena API Gateway - 开发环境快速启动脚本

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    local deps=("docker" "docker-compose" "go" "make")
    for dep in "${deps[@]}"; do
        if ! command -v "$dep" &> /dev/null; then
            log_error "$dep 未安装，请先安装 $dep"
            exit 1
        fi
    done
    
    log_success "依赖检查完成"
}

# 环境准备
prepare_environment() {
    log_info "准备环境..."
    
    # 创建必要的目录
    mkdir -p logs
    mkdir -p bin
    mkdir -p tmp
    
    # 复制环境配置文件
    if [[ ! -f .env ]]; then
        cp .env.dev .env
        log_info "已复制 .env.dev 到 .env"
    fi
    
    # 检查Go模块
    if [[ ! -f go.mod ]]; then
        go mod init github.com/athena-workspace/core/gateway
        log_info "已初始化 Go 模块"
    fi
    
    # 下载依赖
    go mod download
    
    log_success "环境准备完成"
}

# 启动基础服务
start_infrastructure() {
    log_info "启动基础服务..."
    
    # 启动Redis和其他基础服务
    docker-compose -f docker-compose.dev.yml up -d redis jaeger prometheus
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    log_success "基础服务启动完成"
}

# 启动模拟服务
start_mock_services() {
    log_info "启动模拟服务..."
    
    # 启动用户服务、订单服务等模拟服务
    docker-compose -f docker-compose.dev.yml up -d user-service order-service payment-service notification-service
    
    # 等待服务启动
    sleep 5
    
    log_success "模拟服务启动完成"
}

# 启动网关
start_gateway() {
    log_info "启动API网关..."
    
    # 选择启动方式
    local start_mode=${1:-local}
    
    case $start_mode in
        local)
            log_info "本地启动模式..."
            make run-dev
            ;;
        docker)
            log_info "Docker启动模式..."
            docker-compose -f docker-compose.dev.yml up gateway
            ;;
        *)
            log_error "未知的启动模式: $start_mode"
            log_info "支持的启动模式: local, docker"
            exit 1
            ;;
    esac
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查网关健康状态
    for i in {1..30}; do
        if curl -f http://localhost:8080/health &>/dev/null; then
            log_success "网关健康检查通过"
            return 0
        fi
        sleep 2
    done
    
    log_error "网关健康检查失败"
    return 1
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    echo ""
    echo "🌐 API Gateway:     http://localhost:8080"
    echo "📊 Metrics:        http://localhost:9090"
    echo "🔍 Jaeger:         http://localhost:16686"
    echo "📈 Prometheus:     http://localhost:9091"
    echo "🔑 Redis:          localhost:6379"
    echo ""
    echo "👤 User Service:    http://localhost:8001"
    echo "📦 Order Service:   http://localhost:8002"
    echo "💳 Payment Service: http://localhost:8003"
    echo "📬 Notification:    http://localhost:8004"
    echo ""
}

# 清理函数
cleanup() {
    log_info "清理资源..."
    docker-compose -f docker-compose.dev.yml down
    log_success "清理完成"
}

# 信号处理
trap cleanup EXIT INT TERM

# 主函数
main() {
    echo "🚀 Athena API Gateway - 开发环境启动脚本"
    echo ""
    
    local command=${1:-start}
    local start_mode=${2:-local}
    
    case $command in
        start)
            check_dependencies
            prepare_environment
            start_infrastructure
            start_mock_services
            
            log_info "启动网关服务..."
            start_gateway "$start_mode"
            
            # 健康检查
            sleep 5
            if health_check; then
                show_status
            fi
            ;;
        
        stop)
            cleanup
            ;;
        
        status)
            show_status
            ;;
        
        restart)
            cleanup
            sleep 2
            main start "$start_mode"
            ;;
        
        help)
            echo "用法: $0 [command] [mode]"
            echo ""
            echo "命令:"
            echo "  start    启动开发环境 (默认)"
            echo "  stop     停止开发环境"
            echo "  status   显示服务状态"
            echo "  restart  重启开发环境"
            echo "  help     显示帮助信息"
            echo ""
            echo "启动模式:"
            echo "  local    本地启动模式 (默认)"
            echo "  docker   Docker启动模式"
            echo ""
            echo "示例:"
            echo "  $0 start local     # 本地启动"
            echo "  $0 start docker    # Docker启动"
            echo "  $0 stop           # 停止服务"
            echo "  $0 status         # 查看状态"
            ;;
        
        *)
            log_error "未知命令: $command"
            main help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"