#!/bin/bash

# Athena平台监控系统部署脚本
# Monitoring System Deployment Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_debug() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# 配置
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.production.yml"
PROMETHEUS_CONFIG="$PROJECT_ROOT/config/monitoring/prometheus.yml"
ALERT_RULES="$PROJECT_ROOT/config/monitoring/alert_rules.yml"
GRAFANA_DATASOURCES="$PROJECT_ROOT/config/monitoring/grafana/datasources"

log_info "========================================"
log_info "Athena平台监控系统部署"
log_info "========================================"

# 检查Docker和Docker Compose
if ! command -v docker &> /dev/null; then
    log_error "Docker 未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose 未安装"
    exit 1
fi

# 检查配置文件
if [ ! -f "$COMPOSE_FILE" ]; then
    log_error "Docker Compose 文件不存在: $COMPOSE_FILE"
    exit 1
fi

if [ ! -f "$PROMETHEUS_CONFIG" ]; then
    log_error "Prometheus 配置文件不存在: $PROMETHEUS_CONFIG"
    exit 1
fi

if [ ! -f "$ALERT_RULES" ]; then
    log_error "告警规则文件不存在: $ALERT_RULES"
    exit 1
fi

# 创建必要的目录
log_info "创建监控数据目录..."
mkdir -p "$PROJECT_ROOT/data/prometheus"
mkdir -p "$PROJECT_ROOT/data/grafana"
mkdir -p "$PROJECT_ROOT/logs/monitoring"

# 设置权限
chmod 755 "$PROJECT_ROOT/data/prometheus"
chmod 755 "$PROJECT_ROOT/data/grafana"
chmod 755 "$PROJECT_ROOT/logs/monitoring"

# 加载环境变量
if [ -f "$PROJECT_ROOT/.env.production" ]; then
    log_info "加载环境变量..."
    source "$PROJECT_ROOT/.env.production"
else
    log_warn "未找到 .env.production 文件，将使用默认配置"
fi

# 启动监控服务
log_info "启动监控服务..."
cd "$PROJECT_ROOT"

# 只启动监控相关的服务
docker-compose -f "$COMPOSE_FILE" up -d \
    prometheus \
    grafana \
    jaeger \
    health-checker

# 等待服务启动
log_info "等待服务启动..."
sleep 10

# 检查服务状态
log_info "检查服务状态..."

# Prometheus
if curl -s http://localhost:${PROMETHEUS_PORT:-9090}/-/healthy > /dev/null; then
    log_info "✓ Prometheus 运行正常 (http://localhost:${PROMETHEUS_PORT:-9090})"
else
    log_error "✗ Prometheus 启动失败"
fi

# Grafana
if curl -s http://localhost:${GRAFANA_PORT:-3000}/api/health > /dev/null; then
    log_info "✓ Grafana 运行正常 (http://localhost:${GRAFANA_PORT:-3000})"
    log_info "  用户名: admin"
    log_info "  密码: athena_grafana_2024!"
else
    log_error "✗ Grafana 启动失败"
fi

# Jaeger
if curl -s http://localhost:${JAEGER_PORT:-16686}/ > /dev/null; then
    log_info "✓ Jaeger 运行正常 (http://localhost:${JAEGER_PORT:-16686})"
else
    log_error "✗ Jaeger 启动失败"
fi

# 健康检查服务
if curl -s http://localhost:9999/health > /dev/null; then
    log_info "✓ 健康检查服务运行正常 (http://localhost:9999)"
else
    log_error "✗ 健康检查服务启动失败"
fi

# 配置Grafana数据源（如果Grafana已启动）
if curl -s http://localhost:${GRAFANA_PORT:-3000}/api/health > /dev/null; then
    log_info "配置Grafana数据源..."

    # 等待Grafana完全启动
    sleep 5

    # 使用API配置数据源
    curl -X POST \
        http://admin:athena_grafana_2024!@localhost:${GRAFANA_PORT:-3000}/api/datasources \
        -H 'Content-Type: application/json' \
        -d '{
            "name": "Prometheus",
            "type": "prometheus",
            "url": "http://prometheus:9090",
            "access": "proxy",
            "isDefault": true
        }' > /dev/null 2>&1 || log_warn "Grafana数据源配置可能失败，请手动配置"
fi

# 显示访问信息
log_info "========================================"
log_info "监控系统部署完成！"
log_info "========================================"
log_info ""
log_info "访问地址："
log_info "  Prometheus: http://localhost:${PROMETHEUS_PORT:-9090}"
log_info "  Grafana:    http://localhost:${GRAFANA_PORT:-3000}"
log_info "  Jaeger:     http://localhost:${JAEGER_PORT:-16686}"
log_info "  Health:     http://localhost:9999"
log_info ""
log_info "Grafana登录信息："
log_info "  用户名: admin"
log_info "  密码:   athena_grafana_2024!"
log_info ""
log_info "常用命令："
log_info "  查看监控服务状态: docker-compose -f $COMPOSE_FILE ps"
log_info "  查看Prometheus日志: docker-compose -f $COMPOSE_FILE logs prometheus"
log_info "  重启监控服务: docker-compose -f $COMPOSE_FILE restart"
log_info ""
log_info "告警规则位置："
log_info "  $ALERT_RULES"
log_info ""
log_info "如需停止监控系统："
log_info "  docker-compose -f $COMPOSE_FILE down prometheus grafana jaeger health-checker"
log_info "========================================"