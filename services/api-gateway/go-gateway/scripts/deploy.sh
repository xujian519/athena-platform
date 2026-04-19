#!/bin/bash

# Athena API Gateway 部署脚本
# 用于构建和部署Athena API网关服务

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 检查Go
    if ! command -v go &> /dev/null; then
        log_error "Go未安装，请先安装Go 1.21+"
        exit 1
    fi
    
    log_info "依赖检查通过"
}

# 构建应用
build_app() {
    log_info "构建应用..."
    
    # 检查go.mod
    if [ ! -f "go.mod" ]; then
        log_error "go.mod文件不存在"
        exit 1
    fi
    
    # 下载依赖
    log_info "下载Go模块依赖..."
    go mod download
    
    # 运行测试
    log_info "运行测试..."
    go test -v ./...
    
    # 构建二进制文件
    log_info "构建二进制文件..."
    go build -o build/gateway cmd/gateway/main.go
    
    if [ $? -eq 0 ]; then
        log_info "构建成功"
    else
        log_error "构建失败"
        exit 1
    fi
}

# 构建Docker镜像
build_docker() {
    log_info "构建Docker镜像..."
    
    # 构建镜像
    docker build -t athena-gateway:latest .
    
    if [ $? -eq 0 ]; then
        log_info "Docker镜像构建成功"
    else
        log_error "Docker镜像构建失败"
        exit 1
    fi
}

# 启动服务
start_services() {
    log_info "启动服务..."
    
    # 创建必要的目录
    mkdir -p logs monitoring/grafana/{dashboards,datasources}
    
    # 停止现有服务
    docker-compose down || true
    
    # 启动服务
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        log_info "服务启动成功"
        log_info "API网关: http://localhost:8080"
        log_info "监控指标: http://localhost:9090/metrics"
        log_info "Grafana: http://localhost:3000 (admin/admin123)"
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose down
    log_info "服务已停止"
}

# 查看日志
view_logs() {
    log_info "查看服务日志..."
    docker-compose logs -f athena-gateway
}

# 健康检查
health_check() {
    log_info "执行健康检查..."
    
    # 检查网关健康状态
    if curl -f http://localhost:8080/health > /dev/null 2>&1; then
        log_info "✅ API网关健康"
    else
        log_error "❌ API网关不健康"
    fi
    
    # 检查数据库连接
    if docker-compose exec -T postgres pg_isready -U athena -d athena_gateway > /dev/null 2>&1; then
        log_info "✅ PostgreSQL健康"
    else
        log_error "❌ PostgreSQL不健康"
    fi
    
    # 检查Redis连接
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_info "✅ Redis健康"
    else
        log_error "❌ Redis不健康"
    fi
}

# 清理资源
cleanup() {
    log_info "清理资源..."
    
    # 停止并删除容器
    docker-compose down -v
    
    # 删除未使用的镜像
    docker image prune -f
    
    # 删除未使用的卷
    docker volume prune -f
    
    log_info "清理完成"
}

# 开发环境部署
deploy_dev() {
    log_info "部署开发环境..."
    
    # 设置环境变量
    export ATHENA_GATEWAY_SERVER_MODE=debug
    export ATHENA_GATEWAY_LOGGING_LEVEL=debug
    
    # 启动服务
    start_services
    
    log_info "开发环境部署完成"
}

# 生产环境部署
deploy_prod() {
    log_info "部署生产环境..."
    
    # 设置环境变量
    export ATHENA_GATEWAY_SERVER_MODE=release
    export ATHENA_GATEWAY_LOGGING_LEVEL=info
    export ATHENA_GATEWAY_LOGGING_FORMAT=json
    
    # 构建生产镜像
    build_docker
    
    # 启动服务
    start_services
    
    log_info "生产环境部署完成"
}

# 备份数据
backup_data() {
    log_info "备份数据..."
    
    timestamp=$(date +"%Y%m%d_%H%M%S")
    backup_dir="backups/${timestamp}"
    
    mkdir -p "${backup_dir}"
    
    # 备份PostgreSQL数据
    docker-compose exec -T postgres pg_dump -U athena athena_gateway > "${backup_dir}/postgres_backup.sql"
    
    # 备份Redis数据
    docker-compose exec -T redis redis-cli BGSAVE
    docker cp $(docker-compose ps -q redis):/data/dump.rdb "${backup_dir}/redis_backup.rdb"
    
    # 压缩备份
    tar -czf "${backup_dir}.tar.gz" -C backups "${timestamp}"
    
    # 删除临时目录
    rm -rf "${backup_dir}"
    
    log_info "备份完成: ${backup_dir}.tar.gz"
}

# 显示帮助信息
show_help() {
    echo "Athena API Gateway 部署脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  check      - 检查依赖"
    echo "  build      - 构建应用"
    echo "  docker     - 构建Docker镜像"
    echo "  start      - 启动服务"
    echo "  stop       - 停止服务"
    echo "  restart    - 重启服务"
    echo "  logs       - 查看日志"
    echo "  health     - 健康检查"
    echo "  dev        - 部署开发环境"
    echo "  prod       - 部署生产环境"
    echo "  backup     - 备份数据"
    echo "  cleanup    - 清理资源"
    echo "  help       - 显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 dev          # 部署开发环境"
    echo "  $0 prod         # 部署生产环境"
    echo "  $0 logs         # 查看服务日志"
    echo "  $0 health       # 检查服务健康状态"
}

# 主函数
main() {
    # 检查是否在正确的目录
    if [ ! -f "go.mod" ]; then
        log_error "请在项目根目录运行此脚本"
        exit 1
    fi
    
    # 解析命令行参数
    case "${1:-}" in
        "check")
            check_dependencies
            ;;
        "build")
            check_dependencies
            build_app
            ;;
        "docker")
            check_dependencies
            build_docker
            ;;
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            stop_services
            start_services
            ;;
        "logs")
            view_logs
            ;;
        "health")
            health_check
            ;;
        "dev")
            check_dependencies
            deploy_dev
            ;;
        "prod")
            check_dependencies
            deploy_prod
            ;;
        "backup")
            backup_data
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        "")
            show_help
            ;;
        *)
            log_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"