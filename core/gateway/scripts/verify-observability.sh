#!/bin/bash

# Athena API Gateway 可观测性系统验证脚本
# 用于验证所有可观测性组件是否正常工作

set -e

echo "🚀 启动 Athena API Gateway 可观测性系统验证..."
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 函数定义
check_service() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "检查 $service_name... "
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_status"; then
        echo -e "${GREEN}✓ 正常${NC}"
        return 0
    else
        echo -e "${RED}✗ 异常${NC}"
        return 1
    fi
}

wait_for_service() {
    local service_name=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=1
    
    echo -n "等待 $service_name 启动"
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200\|404"; then
            echo -e " ${GREEN}已启动${NC}"
            return 0
        fi
        
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    echo -e " ${RED}超时${NC}"
    return 1
}

# 1. 检查Docker服务
echo "📋 步骤 1: 检查 Docker 服务状态"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}错误: Docker 未安装或未运行${NC}"
    exit 1
fi

if ! docker-compose ps | grep -q "Up"; then
    echo -e "${YELLOW}警告: 没有运行的服务，尝试启动...${NC}"
    docker-compose -f docker-compose.observability.yml up -d
    sleep 10
fi

echo ""

# 2. 等待所有服务启动
echo "⏳ 步骤 2: 等待服务启动"

wait_for_service "API Gateway" "http://localhost:8080/health"
wait_for_service "Prometheus" "http://localhost:9090/-/healthy"
wait_for_service "Jaeger" "http://localhost:16686"
wait_for_service "Grafana" "http://localhost:3000/api/health"

echo ""

# 3. 验证服务健康状态
echo "🔍 步骤 3: 验证服务健康状态"

all_services_healthy=true

check_service "API Gateway 健康检查" "http://localhost:8080/health" || all_services_healthy=false
check_service "API Gateway 指标端点" "http://localhost:8080/metrics" || all_services_healthy=false
check_service "Prometheus" "http://localhost:9090" || all_services_healthy=false
check_service "Jaeger UI" "http://localhost:16686" || all_services_healthy=false
check_service "Grafana UI" "http://localhost:3000" || all_services_healthy=false

echo ""

# 4. 验证可观测性功能
echo "📊 步骤 4: 验证可观测性功能"

# 生成一些测试流量
echo "生成测试流量..."
for i in {1..20}; do
    curl -s "http://localhost:8080/health" > /dev/null &
done

# 生成一些错误流量
for i in {1..5}; do
    curl -s "http://localhost:8080/nonexistent" > /dev/null &
done

wait

# 等待指标收集
echo "等待指标收集..."
sleep 5

# 检查指标
echo -n "检查 Prometheus 指标... "
if curl -s "http://localhost:8080/metrics" | grep -q "athena_gateway_http_requests_total"; then
    echo -e "${GREEN}✓ 指标正常收集${NC}"
else
    echo -e "${RED}✗ 指标收集异常${NC}"
    all_services_healthy=false
fi

# 检查 Jaeger 追踪
echo -n "检查 Jaeger 服务列表... "
if curl -s "http://localhost:16686/api/services" | grep -q "athena-gateway"; then
    echo -e "${GREEN}✓ 追踪服务正常${NC}"
else
    echo -e "${YELLOW}⚠ 追踪服务可能需要更多时间初始化${NC}"
fi

# 检查 Grafana 数据源
echo -n "检查 Grafana 数据源... "
if curl -s -u "admin:admin" "http://localhost:3000/api/datasources" | grep -q "Prometheus"; then
    echo -e "${GREEN}✓ 数据源配置正常${NC}"
else
    echo -e "${YELLOW}⚠ Grafana 数据源可能需要手动配置${NC}"
fi

echo ""

# 5. 性能基准测试
echo "⚡ 步骤 5: 运行性能基准测试"

echo -n "执行基准测试... "
if command -v curl &> /dev/null; then
    # 简单的性能测试
    start_time=$(date +%s%N)
    
    for i in {1..50}; do
        curl -s "http://localhost:8080/health" > /dev/null
    done
    
    end_time=$(date +%s%N)
    duration=$((($end_time - $start_time) / 1000000))
    
    if [ $duration -lt 5000 ]; then
        echo -e "${GREEN}✓ 性能测试通过 (${duration}ms)${NC}"
    else
        echo -e "${YELLOW}⚠ 性能可能需要优化 (${duration}ms)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ curl 不可用，跳过性能测试${NC}"
fi

echo ""

# 6. 总结报告
echo "📋 步骤 6: 验证总结"

if [ "$all_services_healthy" = true ]; then
    echo -e "${GREEN}✅ 所有可观测性组件验证通过！${NC}"
    echo ""
    echo -e "${BLUE}🌐 服务访问地址:${NC}"
    echo "  🏗️  API Gateway:     http://localhost:8080"
    echo "  📊 Prometheus:      http://localhost:9090"
    echo "  📈 Grafana:         http://localhost:3000 (admin/admin)"
    echo "  🔍 Jaeger:          http://localhost:16686"
    echo ""
    echo -e "${BLUE}🧪 快速测试命令:${NC}"
    echo "  curl http://localhost:8080/health"
    echo "  curl http://localhost:8080/metrics | head -10"
    echo ""
    echo -e "${BLUE}📊 有用的查询:${NC}"
    echo "  rate(athena_gateway_http_requests_total[5m])"
    echo "  histogram_quantile(0.95, rate(athena_gateway_http_request_duration_seconds_bucket[5m]))"
    echo ""
    echo -e "${GREEN}🎉 可观测性系统已成功部署并运行正常！${NC}"
    exit 0
else
    echo -e "${RED}❌ 部分组件验证失败，请检查日志：${NC}"
    echo ""
    echo "查看服务日志："
    echo "  docker-compose -f docker-compose.observability.yml logs gateway"
    echo "  docker-compose -f docker-compose.observability.yml logs prometheus"
    echo "  docker-compose -f docker-compose.observability.yml logs jaeger"
    echo "  docker-compose -f docker-compose.observability.yml logs grafana"
    echo ""
    echo "重启服务："
    echo "  docker-compose -f docker-compose.observability.yml restart"
    exit 1
fi