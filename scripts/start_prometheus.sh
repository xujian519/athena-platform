#!/bin/bash
###############################################################################
# Prometheus启动脚本
# Prometheus Startup Script for Athena Execution Module Monitoring
#
# 用途: 启动Prometheus监控服务，加载Athena执行模块的配置和告警规则
# 使用: ./start_prometheus.sh [--local|--prod]
#
# 作者: Athena AI系统
# 版本: 2.0.0
# 创建时间: 2026-01-27
###############################################################################

set -e

# 配置变量
ATHENA_HOME=${ATHENA_HOME:-"$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"}
CONFIG_DIR="$ATHENA_HOME/config/monitoring"
PROMETHEUS_PORT=${PROMETHEUS_PORT:-9090}
DATA_DIR="$ATHENA_HOME/data/prometheus"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# 检查Prometheus是否安装
check_prometheus() {
    if ! command -v prometheus &> /dev/null; then
        log_error "Prometheus未安装"
        echo ""
        echo "请安装Prometheus："
        echo "  macOS:   brew install prometheus"
        echo "  Linux:   参考官方文档 https://prometheus.io/docs/prometheus/latest/getting_started/"
        echo "  Docker:  docker run -p 9090:9090 prom/prometheus"
        exit 1
    fi
    log_info "Prometheus已安装: $(which prometheus)"
}

# 创建必要的目录
create_directories() {
    mkdir -p "$DATA_DIR"
    log_info "Prometheus数据目录: $DATA_DIR"
}

# 检查配置文件
check_config() {
    local config_file="$CONFIG_DIR/prometheus.yml"
    
    if [ ! -f "$config_file" ]; then
        log_error "配置文件不存在: $config_file"
        exit 1
    fi
    
    log_info "配置文件: $config_file"
    
    # 验证配置文件
    log_info "验证Prometheus配置..."
    if promtool check config "$config_file"; then
        log_info "配置文件验证通过"
    else
        log_error "配置文件验证失败"
        exit 1
    fi
}

# 检查告警规则
check_rules() {
    local rules_file="$CONFIG_DIR/prometheus_alerts.yml"
    
    if [ ! -f "$rules_file" ]; then
        log_warn "告警规则文件不存在: $rules_file"
        return
    fi
    
    log_info "告警规则: $rules_file"
    
    # 验证告警规则
    log_info "验证告警规则..."
    if promtool check rules "$rules_file"; then
        log_info "告警规则验证通过"
    else
        log_error "告警规则验证失败"
        exit 1
    fi
}

# 检查端口是否可用
check_port() {
    if lsof -i :$PROMETHEUS_PORT &> /dev/null; then
        log_error "端口 $PROMETHEUS_PORT 已被占用"
        echo ""
        lsof -i :$PROMETHEUS_PORT
        echo ""
        echo "请停止占用该端口的进程或使用其他端口："
        echo "  PROMETHEUS_PORT=9091 $0"
        exit 1
    fi
    log_info "端口 $PROMETHEUS_PORT 可用"
}

# 启动Prometheus
start_prometheus() {
    log_info "启动Prometheus..."
    
    prometheus \
        --config.file="$CONFIG_DIR/prometheus.yml" \
        --storage.tsdb.path="$DATA_DIR" \
        --web.console.libraries=/etc/prometheus/console_libraries \
        --web.console.templates=/etc/prometheus/consoles \
        --web.listen-address=:"$PROMETHEUS_PORT" \
        --log.level=info
}

# 显示使用说明
show_usage() {
    cat << EOF
Prometheus已启动！

访问地址:
  - Web UI:    http://localhost:$PROMETHEUS_PORT
  - Metrics:   http://localhost:$PROMETHEUS_PORT/metrics
  - Targets:   http://localhost:$PROMETHEUS_PORT/targets
  - Rules:     http://localhost:$PROMETHEUS_PORT/rules
  - Alerts:    http://localhost:$PROMETHEUS_PORT/alerts

监控的端点:
  - Athena执行模块: http://localhost:9091/metrics

常用查询:
  - 任务总数: athena_execution_tasks_total
  - 队列大小: athena_execution_queue_size
  - 工作线程: athena_execution_workers_active
  - 内存使用: athena_execution_memory_usage_bytes

停止Prometheus: Ctrl+C 或关闭终端

日志查看: tail -f $DATA_DIR/*.log
EOF
}

# 主函数
main() {
    echo "========================================"
    echo " Prometheus启动脚本"
    echo "========================================"
    echo ""
    
    check_prometheus
    create_directories
    check_config
    check_rules
    check_port
    
    echo ""
    log_info "所有检查通过，准备启动Prometheus..."
    echo ""
    
    # 设置陷阱，在退出时显示信息
    trap show_usage EXIT
    
    start_prometheus
}

# 执行主函数
main "$@"
