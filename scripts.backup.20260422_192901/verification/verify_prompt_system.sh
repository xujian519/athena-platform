#!/usr/bin/env bash
# 动态提示词系统验证脚本
# Verify Athena Prompt System

set -e

ATHENA_API_HOST="${ATHENA_API_HOST:-http://localhost:8000}"
API_ENDPOINT="${ATHENA_API_HOST}/api/v1/prompt-system"

echo "🔍 开始验证动态提示词系统..."
echo "   API地址: $API_ENDPOINT"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_api() {
    local test_name="$1"
    local endpoint="$2"
    local method="${3:-GET}"
    local data="${4:-}"

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -n "测试 $TOTAL_TESTS: $test_name ... "

    if [ "$method" = "GET" ]; then
        response=$(curl -s -X GET "$API_ENDPOINT$endpoint" \
            -H "Content-Type: application/json" \
            --max-time 30 2>&1)
    else
        response=$(curl -s -X "$method" "$API_ENDPOINT$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" \
            --max-time 30 2>&1)
    fi

    # 检查curl是否成功
    if echo "$response" | grep -q "status.*healthy\|success.*true"; then
        echo -e "${GREEN}✓ PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
        echo "   响应: $(echo "$response" | jq -r '.status // .message // .' | head -c 100)..."
    elif echo "$response" | grep -qi "error\|failed\|timeout"; then
        echo -e "${RED}✗ FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        echo "   错误: $(echo "$response" | head -c 200)..."
    else
        echo -e "${YELLOW}? UNKNOWN${NC}"
        echo "   响应: $(echo "$response" | head -c 200)..."
    fi

    echo ""
}

echo "=========================================="
echo " 动态提示词系统验证"
echo "=========================================="
echo ""

# 测试1: 健康检查
test_api "健康检查" "/health"

# 测试2: 场景识别
test_api "场景识别" "/scenario/identify" "POST" \
    '{"user_input": "分析这个化学合成药物的创造性", "additional_context": {"compound_structure": "C15H12N2O"}}'

# 测试3: 规则检索
test_api "规则检索" "/rules/retrieve" "POST" \
    '{"domain": "patent", "task_type": "creativity_analysis", "phase": "examination"}'

# 测试4: 提示词生成
test_api "提示词生成" "/prompt/generate" "POST" \
    '{"user_input": "检索激光雷达相关专利", "additional_context": {"IPC分类": "H04L"}}'

# 测试5: 能力列表
test_api "能力列表" "/capabilities/list"

# 测试6: 缓存统计
test_api "缓存统计" "/cache/stats"

# 总结
echo "=========================================="
echo " 验证总结"
echo "=========================================="
echo "总测试数: $TOTAL_TESTS"
echo -e "通过: ${GREEN}$PASSED_TESTS${NC}"
echo -e "失败: ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ 所有测试通过！动态提示词系统验证成功。${NC}"
    echo ""
    echo "下一步: 可以开始开发 athena-legal 核心技能"
    exit 0
else
    echo -e "${RED}✗ 有 $FAILED_TESTS 个测试失败${NC}"
    echo ""
    echo "请检查:"
    echo "1. Athena服务是否运行: cd /Users/xujian/Athena工作平台/core/api && python main.py"
    echo "2. 端口是否正确: lsof -i :8000"
    echo "3. 依赖服务状态: Neo4j(7687), PostgreSQL(15432), Redis(6379)"
    exit 1
fi
