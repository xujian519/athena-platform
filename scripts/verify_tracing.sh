#!/bin/bash
# OpenTelemetry 追踪环境验证脚本
# 验证所有追踪服务是否正常运行
#
# 使用方法:
#   ./scripts/verify_tracing.sh
#   ./scripts/verify_tracing.sh --verbose  # 详细输出

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 详细模式
VERBOSE=false
if [[ "$1" == "--verbose" ]]; then
    VERBOSE=true
fi

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  Athena 追踪环境验证${NC}"
echo -e "${BLUE}================================================${NC}"
echo ""

# 检查函数
check_service() {
    local name=$1
    local url=$2
    local pattern=$3

    echo -e "检查 $name..."

    if curl -s "$url" > /dev/null 2>&1; then
        if [ -n "$pattern" ]; then
            if curl -s "$url" | grep -q "$pattern"; then
                echo -e "  ${GREEN}✅ 正常${NC}"
                return 0
            else
                echo -e "  ${YELLOW}⚠️  响应不符合预期${NC}"
                if [ "$VERBOSE" = true ]; then
                    echo -e "  期望模式: $pattern"
                fi
                return 1
            fi
        else
            echo -e "  ${GREEN}✅ 正常${NC}"
            return 0
        fi
    else
        echo -e "  ${RED}❌ 无法连接${NC}"
        return 1
    fi
}

# 检查Docker容器状态
echo -e "${BLUE}📦 Docker容器状态:${NC}"
docker-compose -f docker-compose.tracing.yml ps --format json 2>/dev/null | \
    jq -r '.[] | "\(.Service): \(.State)"' 2>/dev/null || \
    docker-compose -f docker-compose.tracing.yml ps 2>/dev/null
echo ""

# 服务健康检查
PASSED=0
FAILED=0

echo -e "${BLUE}🔍 服务健康检查:${NC}"
echo ""

# OTEL Collector
if check_service "OTEL Collector" "http://localhost:13133" "ServerInfo"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Jaeger UI
if check_service "Jaeger UI" "http://localhost:16686" "Jaeger"; then
    ((PASSED++))
else
    ((FAILED++))
fi

# Elasticsearch
if check_service "Elasticsearch" "http://localhost:9200/_cluster/health" "green\|yellow"; then
    ((PASSED++))
    # 显示集群信息
    if [ "$VERBOSE" = true ]; then
        echo -e "  集群信息:"
        curl -s http://localhost:9200/_cluster/health | jq '.' 2>/dev/null || echo "    无法获取详细信息"
    fi
else
    ((FAILED++))
fi

# Grafana
if check_service "Grafana" "http://localhost:3001/api/health" "commit"; then
    ((PASSED++))
else
    ((FAILED++))
fi

echo ""

# 端口检查
echo -e "${BLUE}🔌 端口检查:${NC}"
PORTS=(
    "4317:OTLP gRPC"
    "4318:OTLP HTTP"
    "13133:Collector Health"
    "16686:Jaeger UI"
    "9200:Elasticsearch"
    "3001:Grafana"
)

for port_info in "${PORTS[@]}"; do
    port=$(echo $port_info | cut -d: -f1)
    name=$(echo $port_info | cut -d: -f2)

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅${NC} $port - $name"
    else
        echo -e "  ${RED}❌${NC} $port - $name (未监听)"
    fi
done
echo ""

# 容量检查
echo -e "${BLUE}💾 存储状态:${NC}"
ES_HEALTH=$(curl -s http://localhost:9200/_cluster/health 2>/dev/null || echo '{}')
if echo "$ES_HEALTH" | jq -e '.status' > /dev/null 2>&1; then
    echo -e "  Elasticsearch状态: $(echo $ES_HEALTH | jq -r '.status // \"unknown\"')"
    echo -e "  节点数量: $(echo $ES_HEALTH | jq -r '.number_of_nodes // 0')"
    echo -e "  数据节点: $(echo $ES_HEALTH | jq -r '.number_of_data_nodes // 0')"
else
    echo -e "  ${YELLOW}⚠️  无法获取Elasticsearch状态${NC}"
fi
echo ""

# 汇总
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  验证结果汇总${NC}"
echo -e "${BLUE}================================================${NC}"
echo -e "  ${GREEN}通过: $PASSED${NC}"
echo -e "  ${RED}失败: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 所有服务验证通过！${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠️  部分服务验证失败，请检查日志${NC}"
    echo ""
    echo -e "查看日志命令:"
    echo -e "  ${YELLOW}docker-compose -f docker-compose.tracing.yml logs -f [service_name]${NC}"
    exit 1
fi
