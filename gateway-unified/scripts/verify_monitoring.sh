#!/bin/bash

# Athena Gateway 监控告警系统验证脚本
# 文档: docs/monitoring_setup_guide.md

set -e

echo "========================================"
echo "Athena Gateway 监控系统验证"
echo "时间: $(date)"
echo "========================================"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 验证结果统计
PASS=0
FAIL=0
WARN=0

# 打印结果函数
print_result() {
    local test_name="$1"
    local result="$2"
    local message="$3"

    if [ "$result" = "PASS" ]; then
        echo -e "${GREEN}✅ PASS${NC} [$test_name] $message"
        ((PASS++))
    elif [ "$result" = "FAIL" ]; then
        echo -e "${RED}❌ FAIL${NC} [$test_name] $message"
        ((FAIL++))
    else
        echo -e "${YELLOW}⚠️  WARN${NC} [$test_name] $message"
        ((WARN++))
    fi
}

# HTTP状态检查函数
check_http() {
    local url="$1"
    local expected_code="${2:-200}"
    local response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
    if [ "$response_code" = "$expected_code" ]; then
        return 0
    else
        return 1
    fi
}

echo "========================================"
echo "1. Prometheus验证"
echo "========================================"

# 1.1 Prometheus服务状态
echo -n "[MON-01] Prometheus服务 (9090): "
if check_http "http://localhost:9090" "200"; then
    print_result "Prometheus服务" "PASS" "HTTP 200"
else
    print_result "Prometheus服务" "FAIL" "无法连接 (预期HTTP 200)"
fi

# 1.2 网关metrics端点
echo -n "[MON-02] 网关metrics端点 (9090/metrics): "
if check_http "http://localhost:9090/metrics" "200"; then
    print_result "Metrics端点" "PASS" "HTTP 200"
else
    print_result "Metrics端点" "FAIL" "无法访问"
fi

# 1.3 检查指标数据
echo -n "[MON-03] Prometheus指标数据: "
metric_count=$(curl -s http://localhost:9090/metrics 2>/dev/null | grep -c "athena_gateway_" || echo "0")
if [ "$metric_count" -gt 0 ]; then
    print_result "指标数据" "PASS" "发现 $metric_count 个Athena指标"
else
    print_result "指标数据" "FAIL" "未发现Athena指标"
fi

# 1.4 告警规则加载
echo -n "[MON-04] 告警规则加载: "
if command -v promtool &> /dev/null; then
    if promtool check rules /Users/xujian/Athena工作平台/gateway-unified/configs/prometheus/alerts/athena_alerts.yml &> /dev/null; then
        print_result "告警规则" "PASS" "规则语法正确"
    else
        print_result "告警规则" "FAIL" "规则语法错误"
    fi
else
    print_result "告警规则" "WARN" "promtool未安装，跳过验证"
fi

echo ""
echo "========================================"
echo "2. Grafana验证"
echo "========================================"

# 2.1 Grafana服务状态
echo -n "[GRA-01] Grafana服务 (3000): "
if check_http "http://localhost:3000" "200"; then
    print_result "Grafana服务" "PASS" "HTTP 200"
else
    print_result "Grafana服务" "FAIL" "无法连接"
fi

# 2.2 Prometheus数据源
echo -n "[GRA-02] Prometheus数据源: "
# 需要Grafana API token或默认密码验证，这里仅做基础检查
if check_http "http://localhost:3000/api/datasources" "401" || check_http "http://localhost:3000/api/datasources" "200"; then
    print_result "数据源API" "PASS" "Grafana API可访问"
else
    print_result "数据源API" "WARN" "无法验证数据源（需手动检查）"
fi

echo ""
echo "========================================"
echo "3. Alertmanager验证"
echo "========================================"

# 3.1 Alertmanager服务状态
echo -n "[ALE-01] Alertmanager服务 (9093): "
if check_http "http://localhost:9093" "200"; then
    print_result "Alertmanager服务" "PASS" "HTTP 200"
else
    print_result "Alertmanager服务" "WARN" "未运行（可选组件）"
fi

# 3.2 Alertmanager配置
echo -n "[ALE-02] Alertmanager配置: "
if check_http "http://localhost:9093/api/v1/status" "200"; then
    print_result "Alertmanager配置" "PASS" "配置API可访问"
else
    print_result "Alertmanager配置" "WARN" "无法验证配置"
fi

echo ""
echo "========================================"
echo "4. 链路追踪验证"
echo "========================================"

# 4.1 Jaeger服务状态
echo -n "[TRC-01] Jaeger服务 (16686): "
if check_http "http://localhost:16686" "200"; then
    print_result "Jaeger服务" "PASS" "HTTP 200"
else
    print_result "Jaeger服务" "WARN" "未运行（可选组件）"
fi

# 4.2 检查网关OpenTelemetry初始化
echo -n "[TRC-02] OpenTelemetry初始化: "
if docker ps | grep -q "gateway-unified"; then
    if docker logs gateway-unified 2>&1 | grep -q "OpenTelemetry初始化成功"; then
        print_result "OTel初始化" "PASS" "已找到初始化日志"
    else
        print_result "OTel初始化" "WARN" "未找到初始化日志"
    fi
else
    print_result "OTel初始化" "WARN" "网关未运行"
fi

echo ""
echo "========================================"
echo "5. 日志格式验证"
echo "========================================"

# 5.1 JSON结构化日志
echo -n "[LOG-01] JSON日志格式: "
if docker logs gateway-unified 2>&1 | grep -q '"timestamp"'; then
    print_result "JSON格式" "PASS" "日志为JSON结构化"
else
    print_result "JSON格式" "WARN" "日志格式可能不是JSON"
fi

# 5.2 必填字段检查
echo -n "[LOG-02] 日志必填字段: "
if docker logs gateway-unified 2>&1 | grep -q '"level".*"service".*"timestamp"'; then
    print_result "必填字段" "PASS" "包含level/service/timestamp"
else
    print_result "必填字段" "WARN" "缺少必填字段"
fi

echo ""
echo "========================================"
echo "验证总结"
echo "========================================"
echo "✅ PASS: $PASS"
echo "❌ FAIL: $FAIL"
echo "⚠️  WARN: $WARN"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}🎉 所有关键验证通过！${NC}"
    exit 0
else
    echo -e "${RED}⚠️  存在 $FAIL 个失败项，请检查配置${NC}"
    exit 1
fi
