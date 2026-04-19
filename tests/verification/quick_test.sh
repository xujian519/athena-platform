#!/bin/bash
# ============================================================================
# Athena平台验证测试 - 快速测试脚本
#
# 功能: 一键执行所有连通性测试,生成测试报告摘要
# 作者: 徐健
# 日期: 2026-04-18
# ============================================================================

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
GATEWAY_URL="http://localhost:8005"
KG_SERVICE="http://localhost:8100"
QDRANT_URL="http://localhost:6333"
REDIS_HOST="localhost"
REDIS_PORT=6379
PG_HOST="localhost"
PG_PORT=5432
PG_USER="athena"
PG_DB="athena"

# 计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNED_TESTS=0

# 测试结果数组
declare -a FAILED_TESTS_LIST
declare -a WARNED_TESTS_LIST

# ============================================================================
# 辅助函数
# ============================================================================

print_header() {
    echo -e "${BLUE}============================================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================================================${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

test_pass() {
    local test_name="$1"
    local details="$2"
    echo -e "${GREEN}✅ PASS${NC} [$test_name] $details"
    ((TOTAL_TESTS++))
    ((PASSED_TESTS++))
}

test_fail() {
    local test_name="$1"
    local details="$2"
    echo -e "${RED}❌ FAIL${NC} [$test_name] $details"
    ((TOTAL_TESTS++))
    ((FAILED_TESTS++))
    FAILED_TESTS_LIST+=("$test_name: $details")
}

test_warn() {
    local test_name="$1"
    local details="$2"
    echo -e "${YELLOW}⚠️  WARN${NC} [$test_name] $details"
    ((TOTAL_TESTS++))
    ((WARNED_TESTS++))
    WARNED_TESTS_LIST+=("$test_name: $details")
}

# ============================================================================
# 知识库连通性测试 (KB-CONN-01~08)
# ============================================================================

test_knowledge_base_connectivity() {
    print_section "知识库连通性测试 (KB-CONN-01~08)"

    # KB-CONN-01: 知识图谱HTTP连通性
    echo -n "KB-CONN-01: 知识图谱服务 ... "
    if http_code=$(curl -s -o /dev/null -w "%{http_code}" "$KG_SERVICE/health" 2>/dev/null); then
        if [ "$http_code" = "200" ]; then
            test_pass "KB-CONN-01" "知识图谱服务 (HTTP $http_code)"
        else
            test_fail "KB-CONN-01" "知识图谱服务返回HTTP $http_code"
        fi
    else
        test_fail "KB-CONN-01" "无法连接到知识图谱服务"
    fi

    # KB-CONN-02: Qdrant向量库连通性
    echo -n "KB-CONN-02: Qdrant向量库 ... "
    if response=$(curl -s "$QDRANT_URL/collections" 2>/dev/null); then
        collection_count=$(echo "$response" | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('result',{}).get('collections',[])))" 2>/dev/null || echo "0")
        if [ "$collection_count" -ge 7 ]; then
            test_pass "KB-CONN-02" "Qdrant向量库 ($collection_count 个集合)"
        else
            test_warn "KB-CONN-02" "Qdrant向量库仅找到 $collection_count 个集合 (预期≥7)"
        fi
    else
        test_fail "KB-CONN-02" "无法连接到Qdrant向量库"
    fi

    # KB-CONN-03: PostgreSQL连通性
    echo -n "KB-CONN-03: PostgreSQL ... "
    if docker-compose exec -T postgres pg_isready -U "$PG_USER" 2>/dev/null | grep -q "accepting"; then
        test_pass "KB-CONN-03" "PostgreSQL (accepting connections)"
    else
        test_fail "KB-CONN-03" "PostgreSQL未就绪"
    fi

    # KB-CONN-04: Redis连通性
    echo -n "KB-CONN-04: Redis ... "
    if docker-compose exec -T redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
        test_pass "KB-CONN-04" "Redis (PONG)"
    else
        test_fail "KB-CONN-04" "Redis未就绪"
    fi

    # KB-CONN-06: 统一网关健康检查
    echo -n "KB-CONN-06: 统一网关(8005) ... "
    if http_code=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL/health" 2>/dev/null); then
        if [ "$http_code" = "200" ]; then
            test_pass "KB-CONN-06" "统一网关 (HTTP $http_code)"
        else
            test_fail "KB-CONN-06" "统一网关返回HTTP $http_code"
        fi
    else
        test_fail "KB-CONN-06" "无法连接到统一网关"
    fi

    # KB-CONN-07: 网关→知识图谱路由
    echo -n "KB-CONN-07: 网关→知识图谱路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/api/v1/kg/query" \
        -H "Content-Type: application/json" \
        -d '{"cypher": "MATCH (n) RETURN count(n) LIMIT 1"}' 2>/dev/null)
    if [[ "$http_code" =~ ^(200|201|204|401|422|400)$ ]]; then
        test_pass "KB-CONN-07" "网关→知识图谱路由 (HTTP $http_code)"
    else
        test_fail "KB-CONN-07" "网关→知识图谱路由返回HTTP $http_code"
    fi

    # KB-CONN-08: 网关→向量搜索路由
    echo -n "KB-CONN-08: 网关→向量搜索路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/api/v1/vector/search" \
        -H "Content-Type: application/json" \
        -d '{"collection_name": "test", "query_text": "测试", "limit": 5}' 2>/dev/null)
    if [[ "$http_code" =~ ^(200|201|204|401|422|400)$ ]]; then
        test_pass "KB-CONN-08" "网关→向量搜索路由 (HTTP $http_code)"
    else
        test_fail "KB-CONN-08" "网关→向量搜索路由返回HTTP $http_code"
    fi
}

# ============================================================================
# 工具库连通性测试 (TOOL-CONN-01~10)
# ============================================================================

test_tool_connectivity() {
    print_section "工具库连通性测试 (TOOL-CONN-01~10)"

    # TOOL-CONN-08: 本地搜索引擎
    echo -n "TOOL-CONN-08: 本地搜索引擎(3003) ... "
    if http_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:3003/health" 2>/dev/null); then
        if [ "$http_code" = "200" ]; then
            test_pass "TOOL-CONN-08" "本地搜索引擎 (HTTP $http_code)"
        else
            test_fail "TOOL-CONN-08" "本地搜索引擎返回HTTP $http_code"
        fi
    else
        test_warn "TOOL-CONN-08" "本地搜索引擎未启动 (可选服务)"
    fi

    # Mineru文档解析器
    echo -n "Mineru解析器(7860) ... "
    if http_code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:7860/health" 2>/dev/null); then
        if [ "$http_code" = "200" ]; then
            test_pass "Mineru解析器" "Mineru文档解析器 (HTTP $http_code)"
        else
            test_fail "Mineru解析器" "Mineru解析器返回HTTP $http_code"
        fi
    else
        test_warn "Mineru解析器" "Mineru解析器未启动 (可选服务)"
    fi

    # TOOL-CONN-09: 网关→工具API路由
    echo -n "TOOL-CONN-09: 网关→工具API路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL/api/v1/tools" 2>/dev/null)
    if [ "$http_code" = "200" ]; then
        test_pass "TOOL-CONN-09" "网关→工具API路由 (HTTP $http_code)"
    else
        test_fail "TOOL-CONN-09" "网关→工具API路由返回HTTP $http_code"
    fi
}

# ============================================================================
# 网关兼容性测试 (GW-ROUTE-01~10)
# ============================================================================

test_gateway_compatibility() {
    print_section "网关兼容性测试 (GW-ROUTE-01~10)"

    # GW-ROUTE-01: 法律API路由
    echo -n "GW-ROUTE-01: 法律API路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/api/legal/analyze" \
        -H "Content-Type: application/json" \
        -d '{"query": "测试"}' 2>/dev/null)
    if [[ "$http_code" =~ ^(200|201|204|401|422|400)$ ]]; then
        test_pass "GW-ROUTE-01" "法律API路由 (HTTP $http_code)"
    else
        test_fail "GW-ROUTE-01" "法律API路由返回HTTP $http_code"
    fi

    # GW-ROUTE-02: 统一搜索路由
    echo -n "GW-ROUTE-02: 统一搜索路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/api/search" \
        -H "Content-Type: application/json" \
        -d '{"query": "专利检索", "limit": 10}' 2>/dev/null)
    if [[ "$http_code" =~ ^(200|201|204|401|422|400)$ ]]; then
        test_pass "GW-ROUTE-02" "统一搜索路由 (HTTP $http_code)"
    else
        test_fail "GW-ROUTE-02" "统一搜索路由返回HTTP $http_code"
    fi

    # GW-ROUTE-03: 知识图谱路由
    echo -n "GW-ROUTE-03: 知识图谱路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/api/v1/kg/query" \
        -H "Content-Type: application/json" \
        -d '{"cypher": "MATCH (n) RETURN count(n) LIMIT 1"}' 2>/dev/null)
    if [[ "$http_code" =~ ^(200|201|204|401|422|400)$ ]]; then
        test_pass "GW-ROUTE-03" "知识图谱路由 (HTTP $http_code)"
    else
        test_fail "GW-ROUTE-03" "知识图谱路由返回HTTP $http_code"
    fi

    # GW-ROUTE-04: 向量搜索路由
    echo -n "GW-ROUTE-04: 向量搜索路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/api/v1/vector/search" \
        -H "Content-Type: application/json" \
        -d '{"collection_name": "test", "query_text": "测试", "limit": 5}' 2>/dev/null)
    if [[ "$http_code" =~ ^(200|201|204|401|422|400)$ ]]; then
        test_pass "GW-ROUTE-04" "向量搜索路由 (HTTP $http_code)"
    else
        test_fail "GW-ROUTE-04" "向量搜索路由返回HTTP $http_code"
    fi

    # GW-ROUTE-05: 法律搜索路由
    echo -n "GW-ROUTE-05: 法律搜索路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/api/v1/legal/search" \
        -H "Content-Type: application/json" \
        -d '{"query": "专利法", "limit": 10}' 2>/dev/null)
    if [[ "$http_code" =~ ^(200|201|204|401|422|400)$ ]]; then
        test_pass "GW-ROUTE-05" "法律搜索路由 (HTTP $http_code)"
    else
        test_fail "GW-ROUTE-05" "法律搜索路由返回HTTP $http_code"
    fi

    # GW-ROUTE-06: 工具服务路由
    echo -n "GW-ROUTE-06: 工具服务路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL/api/v1/tools" 2>/dev/null)
    if [ "$http_code" = "200" ]; then
        test_pass "GW-ROUTE-06" "工具服务路由 (HTTP $http_code)"
    else
        test_fail "GW-ROUTE-06" "工具服务路由返回HTTP $http_code"
    fi

    # GW-ROUTE-07: 服务管理路由
    echo -n "GW-ROUTE-07: 服务管理路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" "$GATEWAY_URL/api/v1/services/instances" 2>/dev/null)
    if [[ "$http_code" =~ ^(200|201|204|401|422|400)$ ]]; then
        test_pass "GW-ROUTE-07" "服务管理路由 (HTTP $http_code)"
    else
        test_fail "GW-ROUTE-07" "服务管理路由返回HTTP $http_code"
    fi

    # GW-ROUTE-10: 认证服务路由
    echo -n "GW-ROUTE-10: 认证服务路由 ... "
    http_code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$GATEWAY_URL/api/v1/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username": "test", "password": "test"}' 2>/dev/null)
    if [[ "$http_code" =~ ^(200|201|204|401|422|400)$ ]]; then
        test_pass "GW-ROUTE-10" "认证服务路由 (HTTP $http_code)"
    else
        test_fail "GW-ROUTE-10" "认证服务路由返回HTTP $http_code"
    fi
}

# ============================================================================
# 生成测试报告摘要
# ============================================================================

generate_summary() {
    print_header "测试报告摘要"

    echo "测试时间: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""

    # 总体统计
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "总体统计"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "总测试数: ${BLUE}$TOTAL_TESTS${NC}"
    echo -e "通过:    ${GREEN}$PASSED_TESTS${NC} (${GREEN}$(awk "BEGIN {printf \"%.1f\", $PASSED_TESTS*100/$TOTAL_TESTS}")%${NC})"
    echo -e "失败:    ${RED}$FAILED_TESTS${NC} (${RED}$(awk "BEGIN {printf \"%.1f\", $FAILED_TESTS*100/$TOTAL_TESTS}")%${NC})"
    echo -e "警告:    ${YELLOW}$WARNED_TESTS${NC} (${YELLOW}$(awk "BEGIN {printf \"%.1f\", $WARNED_TESTS*100/$TOTAL_TESTS}")%${NC})"
    echo ""

    # 失败测试列表
    if [ $FAILED_TESTS -gt 0 ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${RED}失败测试详情${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        for test in "${FAILED_TESTS_LIST[@]}"; do
            echo -e "${RED}✗${NC} $test"
        done
        echo ""
    fi

    # 警告测试列表
    if [ $WARNED_TESTS -gt 0 ]; then
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo -e "${YELLOW}警告测试详情${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        for test in "${WARNED_TESTS_LIST[@]}"; do
            echo -e "${YELLOW}⚠${NC}  $test"
        done
        echo ""
    fi

    # 最终结果
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    if [ $FAILED_TESTS -eq 0 ]; then
        if [ $WARNED_TESTS -eq 0 ]; then
            echo -e "${GREEN}✓ 所有测试通过!${NC}"
        else
            echo -e "${YELLOW}⚠ 所有核心测试通过, 有 $WARNED_TESTS 个警告${NC}"
        fi
    else
        echo -e "${RED}✗ 有 $FAILED_TESTS 个测试失败${NC}"
    fi
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# ============================================================================
# 主函数
# ============================================================================

main() {
    print_header "Athena平台验证测试 - 快速测试"

    # 检查Docker是否运行
    echo "检查Docker环境..."
    if ! docker-compose ps >/dev/null 2>&1; then
        echo -e "${RED}错误: Docker服务未启动${NC}"
        echo "请先运行: docker-compose up -d"
        exit 1
    fi
    echo "Docker环境正常"
    echo ""

    # 执行测试
    test_knowledge_base_connectivity
    test_tool_connectivity
    test_gateway_compatibility

    # 生成报告
    generate_summary

    # 退出码
    if [ $FAILED_TESTS -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# 执行主函数
main "$@"
