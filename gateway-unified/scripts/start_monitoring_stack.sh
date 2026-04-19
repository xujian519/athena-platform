#!/bin/bash

# Athena Gateway 监控堆栈快速启动脚本
# 一键启动 Prometheus + Grafana + Alertmanager + Jaeger

set -e

echo "========================================"
echo "Athena Gateway 监控堆栈启动"
echo "时间: $(date)"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"
MONITORING_DIR="$PROJECT_ROOT/monitoring"

# 创建必要目录
echo "📁 创建监控配置目录..."
mkdir -p "$MONITORING_DIR/prometheus"
mkdir -p "$MONITORING_DIR/alertmanager"
mkdir -p "$MONITORING_DIR/grafana"
mkdir -p "$MONITORING_DIR/jaeger"

# 复制配置文件
echo "📝 复制配置文件..."
cp "$PROJECT_ROOT/gateway-unified/configs/prometheus/prometheus.yml" \
   "$MONITORING_DIR/prometheus/" 2>/dev/null || echo "⚠️  Prometheus配置文件不存在"

# 创建Alertmanager配置
cat > "$MONITORING_DIR/alertmanager/alertmanager.yml" <<EOF
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:5001/webhook'
EOF

echo ""
echo "========================================"
echo "启动监控服务"
echo "========================================"

# 1. 启动Prometheus
echo ""
echo "🔥 启动 Prometheus (9090)..."
if docker ps | grep -q "prometheus"; then
    echo -e "${YELLOW}⚠️  Prometheus已运行${NC}"
else
    docker run -d \
      --name prometheus \
      --network host \
      -v "$MONITORING_DIR/prometheus:/etc/prometheus" \
      -v "$PROJECT_ROOT/gateway-unified/configs/prometheus:/etc/prometheus-configs" \
      prom/prometheus:latest \
      --config.file=/etc/prometheus/prometheus.yml \
      --web.listen-address=:9090 \
      --web.enable-lifecycle \
      2>/dev/null && echo -e "${GREEN}✅ Prometheus启动成功${NC}" || echo -e "${RED}❌ Prometheus启动失败${NC}"
fi

# 2. 启动Grafana
echo ""
echo "🔥 启动 Grafana (3000)..."
if docker ps | grep -q "grafana"; then
    echo -e "${YELLOW}⚠️  Grafana已运行${NC}"
else
    docker run -d \
      --name grafana \
      --network host \
      -e GF_SECURITY_ADMIN_PASSWORD=admin123 \
      -e GF_INSTALL_PLUGINS= \
      grafana/grafana:latest \
      2>/dev/null && echo -e "${GREEN}✅ Grafana启动成功${NC}" || echo -e "${RED}❌ Grafana启动失败${NC}"
fi

# 3. 启动Alertmanager
echo ""
echo "🔥 启动 Alertmanager (9093)..."
if docker ps | grep -q "alertmanager"; then
    echo -e "${YELLOW}⚠️  Alertmanager已运行${NC}"
else
    docker run -d \
      --name alertmanager \
      --network host \
      -v "$MONITORING_DIR/alertmanager:/etc/alertmanager" \
      prom/alertmanager:latest \
      --config.file=/etc/alertmanager/alertmanager.yml \
      --web.listen-address=:9093 \
      2>/dev/null && echo -e "${GREEN}✅ Alertmanager启动成功${NC}" || echo -e "${RED}❌ Alertmanager启动失败${NC}"
fi

# 4. 启动Jaeger
echo ""
echo "🔥 启动 Jaeger (16686)..."
if docker ps | grep -q "jaeger"; then
    echo -e "${YELLOW}⚠️  Jaeger已运行${NC}"
else
    docker run -d \
      --name jaeger \
      --network host \
      -e COLLECTOR_OTLP_ENABLED=true \
      jaegertracing/all-in-one:latest \
      2>/dev/null && echo -e "${GREEN}✅ Jaeger启动成功${NC}" || echo -e "${RED}❌ Jaeger启动失败${NC}"
fi

echo ""
echo "========================================"
echo "监控服务启动完成"
echo "========================================"
echo ""
echo "📍 访问地址:"
echo "  - Prometheus:  http://localhost:9090"
echo "  - Grafana:     http://localhost:3000 (admin/admin123)"
echo "  - Alertmanager: http://localhost:9093"
echo "  - Jaeger:      http://localhost:16686"
echo ""
echo "🔧 下一步操作:"
echo "  1. 配置Grafana数据源: Configuration → Data Sources → Add Prometheus"
echo "  2. 导入仪表板: Create → Import → Upload athena_gateway_dashboard.json"
echo "  3. 运行验证脚本: ./gateway-unified/scripts/verify_monitoring.sh"
echo ""
