#!/bin/bash
# Gateway性能基准测试脚本
# 用于测试gateway-unified的性能表现

set -e

GATEWAY_URL="http://localhost:8005"
RESULTS_DIR="benchmark_results"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="$RESULTS_DIR/benchmark_$TIMESTAMP.txt"

# 创建结果目录
mkdir -p "$RESULTS_DIR"

echo "=== Athena Gateway 性能基准测试 ===" | tee "$RESULTS_FILE"
echo "测试时间: $(date)" | tee -a "$RESULTS_FILE"
echo "Gateway地址: $GATEWAY_URL" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# 检查gateway是否运行
echo "1. 检查Gateway状态..." | tee -a "$RESULTS_FILE"
HEALTH=$(curl -s "$GATEWAY_URL/health")
if echo "$HEALTH" | grep -q '"status":"UP"'; then
    echo "✅ Gateway运行正常" | tee -a "$RESULTS_FILE"
else
    echo "❌ Gateway未运行或异常" | tee -a "$RESULTS_FILE"
    exit 1
fi
echo "" | tee -a "$RESULTS_FILE"

# 测试1: 健康检查性能
echo "2. 健康检查端点性能测试..." | tee -a "$RESULTS_FILE"
echo "执行100次请求，统计延迟..." | tee -a "$RESULTS_FILE"
ab -n 100 -c 10 "$GATEWAY_URL/health" > "$RESULTS_DIR/health_test.txt" 2>&1
HEALTH_RPS=$(grep "Requests per second" "$RESULTS_DIR/health_test.txt" | awk '{print $4}')
HEALTH_P95=$(grep "95%" "$RESULTS_DIR/health_test.txt" | awk '{print $2}')
echo "  - QPS: $HEALTH_RPS" | tee -a "$RESULTS_FILE"
echo "  - P95延迟: $HEALTH_P95 ms" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# 测试2: 服务列表查询性能
echo "3. 服务列表查询性能测试..." | tee -a "$RESULTS_FILE"
echo "执行100次请求，统计延迟..." | tee -a "$RESULTS_FILE"
ab -n 100 -c 10 "$GATEWAY_URL/api/services/instances" > "$RESULTS_DIR/services_test.txt" 2>&1
SERVICES_RPS=$(grep "Requests per second" "$RESULTS_DIR/services_test.txt" | awk '{print $4}')
SERVICES_P95=$(grep "95%" "$RESULTS_DIR/services_test.txt" | awk '{print $2}')
echo "  - QPS: $SERVICES_RPS" | tee -a "$RESULTS_FILE"
echo "  - P95延迟: $SERVICES_P95 ms" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# 测试3: 路由查询性能
echo "4. 路由查询性能测试..." | tee -a "$RESULTS_FILE"
echo "执行100次请求，统计延迟..." | tee -a "$RESULTS_FILE"
ab -n 100 -c 10 "$GATEWAY_URL/api/routes" > "$RESULTS_DIR/routes_test.txt" 2>&1
ROUTES_RPS=$(grep "Requests per second" "$RESULTS_DIR/routes_test.txt" | awk '{print $4}')
ROUTES_P95=$(grep "95%" "$RESULTS_DIR/routes_test.txt" | awk '{print $2}')
echo "  - QPS: $ROUTES_RPS" | tee -a "$RESULTS_FILE"
echo "  - P95延迟: $ROUTES_P95 ms" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# 测试4: 并发性能测试
echo "5. 并发性能测试..." | tee -a "$RESULTS_FILE"
echo "测试不同并发级别下的性能表现" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

for CONCURRENCY in 10 50 100 200; do
    echo "  并发级别: $CONCURRENCY" | tee -a "$RESULTS_FILE"
    ab -n 1000 -c $CONCURRENCY "$GATEWAY_URL/health" > "$RESULTS_DIR/concurrent_${CONCURRENCY}.txt" 2>&1
    RPS=$(grep "Requests per second" "$RESULTS_DIR/concurrent_${CONCURRENCY}.txt" | awk '{print $4}')
    P95=$(grep "95%" "$RESULTS_DIR/concurrent_${CONCURRENCY}.txt" | awk '{print $2}')
    P99=$(grep "99%" "$RESULTS_DIR/concurrent_${CONCURRENCY}.txt" | awk '{print $2}')
    FAILED=$(grep "Failed requests" "$RESULTS_DIR/concurrent_${CONCURRENCY}.txt" | awk '{print $3}')
    echo "    - QPS: $RPS, P95: ${P95}ms, P99: ${P99}ms, 失败: ${FAILED}" | tee -a "$RESULTS_FILE"
done
echo "" | tee -a "$RESULTS_FILE"

# 测试5: 持久负载测试
echo "6. 持久负载测试（30秒）..." | tee -a "$RESULTS_FILE"
echo "模拟真实负载场景" | tee -a "$RESULTS_FILE"
ab -t 30 -c 50 "$GATEWAY_URL/api/services/instances" > "$RESULTS_DIR/sustained_test.txt" 2>&1
SUSTAINED_RPS=$(grep "Requests per second" "$RESULTS_DIR/sustained_test.txt" | awk '{print $4}')
SUSTAINED_P95=$(grep "95%" "$RESULTS_DIR/sustained_test.txt" | awk '{print $2}')
echo "  - QPS: $SUSTAINED_RPS" | tee -a "$RESULTS_FILE"
echo "  - P95延迟: $SUSTAINED_P95 ms" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# 生成总结报告
echo "=== 性能测试总结 ===" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"
echo "核心指标:" | tee -a "$RESULTS_FILE"
echo "  - 健康检查QPS: $HEALTH_RPS" | tee -a "$RESULTS_FILE"
echo "  - 服务查询QPS: $SERVICES_RPS" | tee -a "$RESULTS_FILE"
echo "  - 路由查询QPS: $ROUTES_RPS" | tee -a "$RESULTS_FILE"
echo "  - 持久负载QPS: $SUSTAINED_RPS" | tee -a "$RESULTS_FILE"
echo "" | tee -a "$RESULTS_FILE"

# 性能评估
echo "性能评估:" | tee -a "$RESULTS_FILE"
if [ "$SERVICES_RPS" -gt 500 ]; then
    echo "  ✅ QPS表现优秀 (>500)" | tee -a "$RESULTS_FILE"
elif [ "$SERVICES_RPS" -gt 300 ]; then
    echo "  ⚠️  QPS表现良好 (>300)" | tee -a "$RESULTS_FILE"
else
    echo "  ❌ QPS需要优化 (<300)" | tee -a "$RESULTS_FILE"
fi

if [ "$SERVICES_P95" != "" ]; then
    P95_INT=$(echo $SERVICES_P95 | cut -d'm' -f1)
    if [ "$P95_INT" -lt 100 ]; then
        echo "  ✅ P95延迟优秀 (<100ms)" | tee -a "$RESULTS_FILE"
    elif [ "$P95_INT" -lt 200 ]; then
        echo "  ⚠️  P95延迟良好 (<200ms)" | tee -a "$RESULTS_FILE"
    else
        echo "  ❌ P95延迟需要优化 (>200ms)" | tee -a "$RESULTS_FILE"
    fi
fi

echo "" | tee -a "$RESULTS_FILE"
echo "详细结果保存在: $RESULTS_FILE" | tee -a "$RESULTS_FILE"
echo "完整测试数据: $RESULTS_DIR/" | tee -a "$RESULTS_FILE"
