#!/bin/bash

# Docker监控服务启动脚本

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否运行
check_docker() {
    if ! docker ps > /dev/null 2>&1; then
        log_error "Docker daemon未运行"
        echo ""
        echo "请先启动Docker Desktop："
        echo "  1. 打开Docker Desktop应用"
        echo "  2. 等待Docker引擎启动"
        echo "  3. 运行 'docker ps' 验证"
        echo ""
        return 1
    fi
    return 0
}

# 启动监控服务
start_monitoring() {
    log_info "启动Prometheus和Grafana..."

    cd /Users/xujian/Athena工作平台

    docker-compose -f docker-compose.unified.yml --profile dev up -d prometheus grafana

    log_info "等待服务启动..."
    sleep 5

    # 检查服务状态
    if docker-compose -f docker-compose.unified.yml --profile dev ps | grep -q "athena-prometheus.*Up"; then
        log_info "✅ Prometheus已启动 (http://localhost:9090)"
    else
        log_error "Prometheus启动失败"
        return 1
    fi

    if docker-compose -f docker-compose.unified.yml --profile dev ps | grep -q "athena-grafana.*Up"; then
        log_info "✅ Grafana已启动 (http://localhost:3000)"
    else
        log_error "Grafana启动失败"
        return 1
    fi

    echo ""
    log_info "监控服务已启动！"
    echo ""
    echo "访问地址："
    echo "  📊 Prometheus: http://localhost:9090"
    echo "  📈 Grafana:    http://localhost:3000 (admin/admin)"
    echo ""
    echo "Gateway指标: http://localhost:9091/metrics"
    echo ""
}

# 停止监控服务
stop_monitoring() {
    log_info "停止Prometheus和Grafana..."

    cd /Users/xujian/Athena工作平台

    docker-compose stop prometheus grafana

    log_info "✅ 监控服务已停止"
}

# 查看服务状态
show_status() {
    log_info "监控服务状态："
    echo ""

    cd /Users/xujian/Athena工作平台

    docker-compose -f docker-compose.unified.yml --profile dev ps prometheus grafana
}

# 查看日志
show_logs() {
    SERVICE=$1

    cd /Users/xujian/Athena工作平台

    case $SERVICE in
        prometheus)
            docker-compose -f docker-compose.unified.yml --profile dev logs -f prometheus
            ;;
        grafana)
            docker-compose -f docker-compose.unified.yml --profile dev logs -f grafana
            ;;
        *)
            echo "用法: $0 logs [prometheus|grafana]"
            exit 1
            ;;
    esac
}

# 显示帮助
show_help() {
    cat << EOF
Docker监控服务管理脚本

用法: $0 <command> [options]

命令:
    start       启动Prometheus和Grafana
    stop        停止监控服务
    restart     重启监控服务
    status      查看服务状态
    logs        查看服务日志
    help        显示此帮助信息

日志命令:
    $0 logs prometheus   查看Prometheus日志
    $0 logs grafana      查看Grafana日志

示例:
    $0 start              # 启动监控服务
    $0 status             # 查看状态
    $0 logs prometheus    # 查看Prometheus日志

注意：
    - 需要先启动Docker Desktop
    - Gateway必须运行在端口9091（监控端口）
    - Prometheus配置: config/docker/prometheus/prometheus.yml
    - Grafana仪表板: config/docker/grafana/dashboards/

详细文档:
    docs/DOCKER_MONITORING_SETUP.md

EOF
}

# 主程序
case "$1" in
    start)
        check_docker || exit 1
        start_monitoring
        ;;
    stop)
        stop_monitoring
        ;;
    restart)
        stop_monitoring
        sleep 2
        check_docker || exit 1
        start_monitoring
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs $2
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
