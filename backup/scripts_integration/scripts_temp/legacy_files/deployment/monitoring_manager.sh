#!/bin/bash
# -*- coding: utf-8 -*-
# 监控系统管理脚本
# Monitoring System Management Script - Controlled by Athena & 小诺

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 平台信息
PLATFORM_NAME="Athena工作平台"
PLATFORM_OWNER="Athena & 小诺"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
MONITORING_DIR="$PROJECT_ROOT/monitoring"

# 服务配置
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
ALERTMANAGER_PORT=9093

# 打印平台标识
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ${PLATFORM_NAME}                       ║"
    echo "║                  监控系统管理脚本                           ║"
    echo "║                 控制者: ${PLATFORM_OWNER}                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 打印彩色信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_platform() {
    echo -e "${PURPLE}[PLATFORM]${NC} $1"
}

# 检查依赖
check_dependencies() {
    print_info "检查监控服务依赖..."

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        print_warning "Docker未安装，将使用本地安装方式"
        USE_DOCKER=false
    else
        USE_DOCKER=true
    fi

    # 检查配置文件
    local required_files=(
        "$MONITORING_DIR/prometheus.yml"
        "$MONITORING_DIR/crawler_alerts.yml"
        "$MONITORING_DIR/grafana/crawler_dashboard.json"
    )

    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "配置文件不存在: $file"
            return 1
        fi
    done

    print_success "依赖检查通过"
}

# 获取服务状态
get_service_status() {
    local service="$1"
    local port="$2"

    if command -v lsof &> /dev/null; then
        if lsof -i ":$port" &> /dev/null; then
            echo "running"
        else
            echo "stopped"
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tln | grep -q ":$port "; then
            echo "running"
        else
            echo "stopped"
        fi
    else
        echo "unknown"
    fi
}

# 启动Prometheus
start_prometheus() {
    print_platform "启动Prometheus..."

    if [[ "$(get_service_status prometheus $PROMETHEUS_PORT)" == "running" ]]; then
        print_warning "Prometheus已在运行中"
        return 0
    fi

    if [[ "$USE_DOCKER" == "true" ]]; then
        print_info "使用Docker启动Prometheus..."
        docker run -d \
            --name prometheus \
            -p "$PROMETHEUS_PORT:9090" \
            -v "$MONITORING_DIR/prometheus.yml:/etc/prometheus/prometheus.yml" \
            -v "$MONITORING_DIR/crawler_alerts.yml:/etc/prometheus/crawler_alerts.yml" \
            prom/prometheus:latest
    else
        print_info "使用本地方式启动Prometheus..."
        prometheus --config.file="$MONITORING_DIR/prometheus.yml" \
            --storage.tsdb.path="$MONITORING_DIR/data" \
            --web.console.templates="$MONITORING_DIR/console_templates" \
            --web.console.libraries="$MONITORING_DIR/console_libraries" \
            --web.enable-admin-api &
    fi

    # 等待启动
    sleep 3

    if [[ "$(get_service_status prometheus $PROMETHEUS_PORT)" == "running" ]]; then
        print_success "Prometheus启动成功！"
        print_info "访问地址: http://localhost:$PROMETHEUS_PORT"
    else
        print_error "Prometheus启动失败"
        return 1
    fi
}

# 停止Prometheus
stop_prometheus() {
    print_platform "停止Prometheus..."

    if [[ "$USE_DOCKER" == "true" ]]; then
        docker stop prometheus 2>/dev/null || true
        docker rm prometheus 2>/dev/null || true
    else
        pkill -f prometheus 2>/dev/null || true
    fi

    print_success "Prometheus已停止"
}

# 启动Grafana
start_grafana() {
    print_platform "启动Grafana..."

    if [[ "$(get_service_status grafana $GRAFANA_PORT)" == "running" ]]; then
        print_warning "Grafana已在运行中"
        return 0
    fi

    if [[ "$USE_DOCKER" == "true" ]]; then
        print_info "使用Docker启动Grafana..."
        docker run -d \
            --name grafana \
            -p "$GRAFANA_PORT:3000" \
            -e "GF_SECURITY_ADMIN_PASSWORD=admin" \
            -e "GF_INSTALL_PLUGINS=grafana-piechart-panel" \
            -v "$MONITORING_DIR/grafana:/etc/grafana/provisioning" \
            grafana/grafana:latest
    else
        print_info "使用本地方式启动Grafana..."
        # 创建配置目录
        mkdir -p "$MONITORING_DIR/grafana/provisioning/datasources"
        mkdir -p "$MONITORING_DIR/grafana/provisioning/dashboards"

        # 创建数据源配置
        cat > "$MONITORING_DIR/grafana/provisioning/datasources/prometheus.yml" << 'EOF'
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
EOF

        # 创建仪表板配置
        cat > "$MONITORING_DIR/grafana/provisioning/dashboards/dashboard.yml" << 'EOF'
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

        # 复制仪表板文件
        cp "$MONITORING_DIR/grafana/crawler_dashboard.json" \
           "$MONITORING_DIR/grafana/provisioning/dashboards/" 2>/dev/null || true

        # 启动Grafana
        grafana-server \
            --config="$MONITORING_DIR/grafana/grafana.ini" \
            --home-path="$MONITORING_DIR/grafana/data" &
    fi

    # 等待启动
    sleep 5

    if [[ "$(get_service_status grafana $GRAFANA_PORT)" == "running" ]]; then
        print_success "Grafana启动成功！"
        print_info "访问地址: http://localhost:$GRAFANA_PORT"
        print_info "用户名: admin"
        print_info "密码: admin"
    else
        print_error "Grafana启动失败"
        return 1
    fi
}

# 停止Grafana
stop_grafana() {
    print_platform "停止Grafana..."

    if [[ "$USE_DOCKER" == "true" ]]; then
        docker stop grafana 2>/dev/null || true
        docker rm grafana 2>/dev/null || true
    else
        pkill -f grafana-server 2>/dev/null || true
    fi

    print_success "Grafana已停止"
}

# 启动AlertManager
start_alertmanager() {
    print_platform "启动AlertManager..."

    if [[ "$(get_service_status alertmanager $ALERTMANAGER_PORT)" == "running" ]]; then
        print_warning "AlertManager已在运行中"
        return 0
    fi

    if [[ "$USE_DOCKER" == "true" ]]; then
        print_info "使用Docker启动AlertManager..."
        docker run -d \
            --name alertmanager \
            -p "$ALERTMANAGER_PORT:9093" \
            -v "$MONITORING_DIR/alertmanager.yml:/etc/alertmanager/alertmanager.yml" \
            prom/alertmanager:latest
    else
        alertmanager --config.file="$MONITORING_DIR/alertmanager.yml" &
    fi

    # 等待启动
    sleep 3

    if [[ "$(get_service_status alertmanager $ALERTMANAGER_PORT)" == "running" ]]; then
        print_success "AlertManager启动成功！"
        print_info "访问地址: http://localhost:$ALERTMANAGER_PORT"
    else
        print_error "AlertManager启动失败"
        return 1
    fi
}

# 停止AlertManager
stop_alertmanager() {
    print_platform "停止AlertManager..."

    if [[ "$USE_DOCKER" == "true" ]]; then
        docker stop alertmanager 2>/dev/null || true
        docker rm alertmanager 2>/dev/null || true
    else
        pkill -f alertmanager 2>/dev/null || true
    fi

    print_success "AlertManager已停止"
}

# 显示状态
show_status() {
    print_platform "监控系统状态"
    echo "================================"

    local prometheus_status=$(get_service_status prometheus $PROMETHEUS_PORT)
    local grafana_status=$(get_service_status grafana $GRAFANA_PORT)
    local alertmanager_status=$(get_service_status alertmanager $ALERTMANAGER_PORT)

    echo "Prometheus: $([ "$prometheus_status" == "running" ] && echo -e "${GREEN}运行中${NC}" || echo -e "${RED}已停止${NC}")"
    echo "  访问地址: http://localhost:$PROMETHEUS_PORT"
    echo ""
    echo "Grafana: $([ "$grafana_status" == "running" ] && echo -e "${GREEN}运行中${NC}" || echo -e "${RED}已停止${NC}")"
    echo "  访问地址: http://localhost:$GRAFANA_PORT"
    echo "  用户名: admin"
    echo "  密码: admin"
    echo ""
    echo "AlertManager: $([ "$alertmanager_status" == "running" ] && echo -e "${GREEN}运行中${NC}" || echo -e "${RED}已停止${NC}")"
    echo "  访问地址: http://localhost:$ALERTMANAGER_PORT"
    echo ""
    echo "配置文件:"
    echo "  Prometheus配置: $MONITORING_DIR/prometheus.yml"
    echo "  告警规则: $MONITORING_DIR/crawler_alerts.yml"
    echo "  Grafana仪表板: $MONITORING_DIR/grafana/"
    echo ""
    echo "监控指标:"
    echo "  请求速率、响应时间、错误率"
    echo "  系统资源使用情况"
    echo "  成本统计和分析"
    echo "  外部API状态"
}

# 测试监控
test_monitoring() {
    print_platform "测试监控系统..."

    # 测试Prometheus
    if curl -s http://localhost:$PROMETHEUS_PORT/api/v1/query?query=up &> /dev/null; then
        print_success "Prometheus API测试通过"
    else
        print_error "Prometheus API测试失败"
    fi

    # 测试Grafana
    if curl -s http://localhost:$GRAFANA_PORT/api/health &> /dev/null; then
        print_success "Grafana API测试通过"
    else
        print_error "Grafana API测试失败"
    fi

    # 测试爬虫指标
    if curl -s http://localhost:8002/metrics &> /dev/null; then
        print_success "爬虫服务指标测试通过"
    else
        print_warning "爬虫服务指标测试失败"
    fi
}

# 重载配置
reload_config() {
    print_platform "重载监控配置..."

    # 重载Prometheus配置
    if [[ "$(get_service_status prometheus $PROMETHEUS_PORT)" == "running" ]]; then
        curl -X POST http://localhost:$PROMETHEUS_PORT/-/reload &> /dev/null
        if [[ $? -eq 0 ]]; then
            print_success "Prometheus配置重载成功"
        else
            print_error "Prometheus配置重载失败"
        fi
    else
        print_warning "Prometheus未运行，请先启动服务"
    fi

    # 重载AlertManager配置
    if [[ "$(get_service_status alertmanager $ALERTMANAGER_PORT)" == "running" ]]; then
        curl -X POST http://localhost:$ALERTMANAGER_PORT/-/reload &> /dev/null
        if [[ $? -eq 0 ]]; then
            print_success "AlertManager配置重载成功"
        else
            print_error "AlertManager配置重载失败"
        fi
    else
        print_warning "AlertManager未运行，请先启动服务"
    fi
}

# 显示帮助信息
show_help() {
    print_banner
    echo -e "${CYAN}用法:${NC} $0 [命令]"
    echo ""
    echo -e "${CYAN}命令:${NC}"
    echo "  start              启动所有监控服务"
    echo "  stop               停止所有监控服务"
    echo "  restart            重启所有监控服务"
    echo "  status             显示服务状态"
    echo "  test               测试监控功能"
    echo "  reload             重载配置"
    echo ""
    echo -e "${CYAN}单独控制:${NC}"
    echo "  prometheus         启动/停止Prometheus"
    echo "  grafana             启动/停止Grafana"
    echo "  alertmanager       启动/停止AlertManager"
    echo ""
    echo -e "${CYAN}示例:${NC}"
    echo "  $0 start           # 启动所有服务"
    echo "  $0 stop            # 停止所有服务"
    echo "  $0 prometheus stop # 停止Prometheus"
    echo ""
    echo -e "${PURPLE}控制者: $PLATFORM_OWNER${NC}"
}

# 主函数
main() {
    # 检查参数
    if [[ $# -eq 0 ]]; then
        show_help
        exit 1
    fi

    # 显示平台标识
    print_banner

    # 检查依赖
    check_dependencies

    # 解析命令
    case "$1" in
        start)
            start_prometheus
            start_grafana
            start_alertmanager
            print_success "所有监控服务启动完成！"
            ;;
        stop)
            stop_alertmanager
            stop_grafana
            stop_prometheus
            print_success "所有监控服务已停止！"
            ;;
        restart)
            stop_alertmanager
            stop_grafana
            stop_prometheus
            sleep 2
            start_prometheus
            start_grafana
            start_alertmanager
            print_success "所有监控服务重启完成！"
            ;;
        status)
            show_status
            ;;
        test)
            test_monitoring
            ;;
        reload)
            reload_config
            ;;
        prometheus)
            if [[ "$2" == "stop" ]]; then
                stop_prometheus
            else
                start_prometheus
            fi
            ;;
        grafana)
            if [[ "$2" == "stop" ]]; then
                stop_grafana
            else
                start_grafana
            fi
            ;;
        alertmanager)
            if [[ "$2" == "stop" ]]; then
                stop_alertmanager
            else
                start_alertmanager
            fi
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"