#!/bin/bash

# Gateway + Prometheus + Grafana 一键启动脚本

GATEWAY_HOME="/Users/xujian/Athena工作平台/gateway-unified"
PROMETHEUS_CONFIG="$GATEWAY_HOME/configs/prometheus-gateway.yml"

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

# 检查命令是否存在
check_command() {
    if ! command -v $1 &> /dev/null; then
        log_error "$1 未安装"
        echo ""
        echo "安装方法："
        case $1 in
            prometheus)
                echo "  brew install prometheus"
                ;;
            grafana)
                echo "  brew install grafana"
                ;;
            *)
                echo "  请使用 brew install $1 安装"
                ;;
        esac
        return 1
    fi
    return 0
}

# 停止所有服务
stop_all() {
    log_info "停止所有服务..."

    # 停止Gateway
    pkill -f "gateway-unified" 2>/dev/null

    # 停止Prometheus
    pkill -f "prometheus" 2>/dev/null

    # 停止Grafana
    pkill -f "grafana" 2>/dev/null

    sleep 2

    log_info "✅ 所有服务已停止"
}

# 启动Gateway
start_gateway() {
    log_info "启动Gateway..."

    cd "$GATEWAY_HOME"
    nohup ./bin/gateway-unified -config config.yaml > /tmp/gateway.log 2>&1 &

    sleep 2

    if lsof -i :8005 &> /dev/null; then
        log_info "✅ Gateway已启动 (端口8005)"
    else
        log_error "Gateway启动失败"
        return 1
    fi

    if lsof -i :9091 &> /dev/null; then
        log_info "✅ Gateway监控已启动 (端口9091)"
    else
        log_error "Gateway监控启动失败"
        return 1
    fi
}

# 启动Prometheus
start_prometheus() {
    log_info "启动Prometheus..."

    nohup prometheus --config.file="$PROMETHEUS_CONFIG" \
        --storage.tsdb.path="$GATEWAY_HOME/data/prometheus" \
        > /tmp/prometheus.log 2>&1 &

    sleep 3

    if lsof -i :9090 &> /dev/null; then
        log_info "✅ Prometheus已启动 (端口9090)"
    else
        log_error "Prometheus启动失败"
        return 1
    fi
}

# 启动Grafana
start_grafana() {
    log_info "启动Grafana..."

    # 检查Grafana配置目录
    GRAFANA_DATA="$GATEWAY_HOME/data/grafana"
    mkdir -p "$GRAFANA_DATA"

    nohup grafana-server \
        --config="$GATEWAY_HOME/configs/grafana.ini" \
        --homepath="$GRAFANA_DATA" \
        > /tmp/grafana.log 2>&1 &

    sleep 3

    if lsof -i :3000 &> /dev/null; then
        log_info "✅ Grafana已启动 (端口3000)"
    else
        log_error "Grafana启动失败"
        return 1
    fi
}

# 显示状态
show_status() {
    echo ""
    log_info "服务状态："
    echo "----------------------------------------"

    # Gateway
    if lsof -i :8005 &> /dev/null; then
        echo "✅ Gateway:      运行中 (http://localhost:8005)"
    else
        echo "❌ Gateway:      未运行"
    fi

    if lsof -i :9091 &> /dev/null; then
        echo "✅ Gateway监控:  运行中 (http://localhost:9091/metrics)"
    else
        echo "❌ Gateway监控:  未运行"
    fi

    # Prometheus
    if lsof -i :9090 &> /dev/null; then
        echo "✅ Prometheus:   运行中 (http://localhost:9090)"
    else
        echo "❌ Prometheus:   未运行"
    fi

    # Grafana
    if lsof -i :3000 &> /dev/null; then
        echo "✅ Grafana:      运行中 (http://localhost:3000)"
    else
        echo "❌ Grafana:      未运行"
    fi

    echo "----------------------------------------"
    echo ""
}

# 显示访问信息
show_access_info() {
    log_info "访问地址："
    echo ""
    echo "🌐 Gateway主页面:"
    echo "   http://localhost:8005"
    echo ""
    echo "📊 Prometheus指标:"
    echo "   http://localhost:9090"
    echo ""
    echo "📈 Grafana仪表板:"
    echo "   http://localhost:3000"
    echo "   默认用户名: admin"
    echo "   默认密码: admin"
    echo ""
    echo "📋 Gateway指标端点:"
    echo "   http://localhost:9091/metrics"
    echo ""
}

# 主程序
case "$1" in
    start)
        log_info "启动监控服务..."
        check_command prometheus || exit 1
        check_command grafana || exit 1

        start_gateway
        start_prometheus
        start_grafana

        show_status
        show_access_info
        ;;

    stop)
        stop_all
        ;;

    restart)
        stop_all
        sleep 2
        $0 start
        ;;

    status)
        show_status
        ;;

    logs)
        echo "=== Gateway日志 ==="
        tail -20 /tmp/gateway.log 2>/dev/null || echo "无日志"

        echo ""
        echo "=== Prometheus日志 ==="
        tail -20 /tmp/prometheus.log 2>/dev/null || echo "无日志"

        echo ""
        echo "=== Grafana日志 ==="
        tail -20 /tmp/grafana.log 2>/dev/null || echo "无日志"
        ;;

    *)
        echo "用法: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "命令:"
        echo "  start    - 启动所有服务（Gateway + Prometheus + Grafana）"
        echo "  stop     - 停止所有服务"
        echo "  restart  - 重启所有服务"
        echo "  status   - 查看服务状态"
        echo "  logs     - 查看日志"
        echo ""
        exit 1
        ;;
esac

exit 0
