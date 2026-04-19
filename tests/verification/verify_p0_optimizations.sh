#!/bin/bash

# P0优化验证脚本
# 用于快速验证连接池、日志格式和限流功能

set -e

GATEWAY_URL="${GATEWAY_URL:-https://localhost:8005}"
GATEWAY_BIN="${GATEWAY_BIN:-./gateway-unified/bin/gateway-unified}"

echo "======================================"
echo "Athena Gateway - P0优化验证"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查Gateway是否运行
check_gateway() {
    echo -n "检查Gateway状态..."
    if pgrep -f "gateway-unified" > /dev/null; then
        echo -e "${GREEN}✓ 运行中${NC}"
        return 0
    else
        echo -e "${RED}✗ 未运行${NC}"
        echo ""
        echo "请先启动Gateway:"
        echo "  cd gateway-unified"
        echo "  ./bin/gateway-unified --config config.yaml"
        return 1
    fi
}

# 验证连接池
verify_connection_pool() {
    echo ""
    echo "======================================"
    echo "测试1: 连接池集成"
    echo "======================================"

    echo "发送10个连续请求，观察响应时间..."

    total_time=0
    for i in {1..10}; do
        start=$(date +%s%3N)
        response=$(curl -sk "${GATEWAY_URL}/health" || echo "failed")
        end=$(date +%s%3N)
        duration=$((end - start))
        total_time=$((total_time + duration))

        if [[ "$response" == *"status"* ]]; then
            echo -e "  请求 $i: ${GREEN}${duration}ms${NC}"
        else
            echo -e "  请求 $i: ${RED}失败${NC}"
        fi
    done

    avg_time=$((total_time / 10))
    echo ""
    echo "平均响应时间: ${avg_time}ms"

    if [ $avg_time -lt 150 ]; then
        echo -e "连接池测试: ${GREEN}✓ 通过 (平均响应时间 < 150ms)${NC}"
    else
        echo -e "连接池测试: ${YELLOW}⚠ 警告 (平均响应时间 >= 150ms)${NC}"
    fi
}

# 验证日志格式
verify_logging() {
    echo ""
    echo "======================================"
    echo "测试2: 统一日志格式"
    echo "======================================"

    echo "发送测试请求并检查日志格式..."
    curl -sk "${GATEWAY_URL}/health" > /dev/null

    # 检查日志文件是否存在
    if [ -f "/usr/local/athena-gateway/logs/gateway.log" ]; then
        last_log=$(tail -1 /usr/local/athena-gateway/logs/gateway.log)

        echo "最新日志条目:"
        echo "  $last_log"
        echo ""

        # 检查是否包含追踪字段
        if echo "$last_log" | grep -q "trace_id"; then
            echo -e "日志格式测试: ${GREEN}✓ 通过 (包含trace_id)${NC}"
        else
            echo -e "日志格式测试: ${YELLOW}⚠ 警告 (缺少trace_id)${NC}"
        fi

        if echo "$last_log" | grep -q "request_id"; then
            echo -e "日志格式测试: ${GREEN}✓ 通过 (包含request_id)${NC}"
        else
            echo -e "日志格式测试: ${YELLOW}⚠ 警告 (缺少request_id)${NC}"
        fi
    else
        echo -e "日志格式测试: ${YELLOW}⚠ 警告 (日志文件不存在)${NC}"
        echo "日志路径: /usr/local/athena-gateway/logs/gateway.log"
    fi
}

# 验证限流功能
verify_rate_limiting() {
    echo ""
    echo "======================================"
    echo "测试3: 滑动窗口限流"
    echo "======================================"

    echo "快速发送20个请求（限流阈值: 10次/分钟）..."

    success_count=0
    rate_limited_count=0

    for i in {1..20}; do
        response=$(curl -sk "${GATEWAY_URL}/api/test" 2>&1 || echo "error")

        if echo "$response" | grep -q "过于频繁"; then
            rate_limited_count=$((rate_limited_count + 1))
            echo -e "  请求 $i: ${YELLOW}限流${NC}"
        elif echo "$response" | grep -q "error\|Error\|ERROR"; then
            echo -e "  请求 $i: ${RED}错误${NC}"
        else
            success_count=$((success_count + 1))
            echo -e "  请求 $i: ${GREEN}成功${NC}"
        fi

        # 小延迟避免瞬间完成
        sleep 0.05
    done

    echo ""
    echo "成功: $success_count"
    echo "限流: $rate_limited_count"

    if [ $rate_limited_count -gt 0 ]; then
        echo -e "限流测试: ${GREEN}✓ 通过 (限流生效)${NC}"
    else
        echo -e "限流测试: ${YELLOW}⚠ 警告 (未触发限流，可能需要调整测试参数)${NC}"
    fi
}

# 性能基准测试
run_benchmark() {
    echo ""
    echo "======================================"
    echo "测试4: 性能基准"
    echo "======================================"

    echo "运行100个并发请求..."

    if command -v ab > /dev/null; then
        # 使用Apache Bench
        result=$(ab -n 100 -c 10 -k "${GATEWAY_URL}/health" 2>&1 | grep "Requests per second" | awk '{print $4}')
        echo "吞吐量: ${result} requests/sec"

        if (( $(echo "$result > 50" | bc -l) )); then
            echo -e "性能基准测试: ${GREEN}✓ 通过 (>50 req/s)${NC}"
        else
            echo -e "性能基准测试: ${YELLOW}⚠ 警告 (<=50 req/s)${NC}"
        fi
    else
        echo -e "性能基准测试: ${YELLOW}⚠ 跳过 (Apache Bench未安装)${NC}"
        echo "安装: brew install apr-util"
    fi
}

# 生成报告
generate_report() {
    echo ""
    echo "======================================"
    echo "验证完成"
    echo "======================================"
    echo ""
    echo "详细报告: docs/reports/P0_OPTIMIZATION_IMPLEMENTATION_REPORT.md"
    echo ""
    echo "如需回滚，执行:"
    echo "  git checkout backup-before-p0-optimization"
    echo "  cd gateway-unified && go build -o bin/gateway-unified ./cmd/gateway"
    echo "  sudo bash quick-deploy-macos.sh"
}

# 主函数
main() {
    check_gateway || exit 1
    verify_connection_pool
    verify_logging
    verify_rate_limiting
    run_benchmark
    generate_report
}

# 运行
main
