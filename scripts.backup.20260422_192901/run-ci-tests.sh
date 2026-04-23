#!/bin/bash
# 本地CI/CD测试脚本
# Local CI/CD Test Runner

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 打印函数
print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# 统计变量
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
SKIPPED_TESTS=0

# 解析命令行参数
COVERAGE=false
SKIP_DOCKER=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        *)
            print_error "未知参数: $1"
            echo "用法: $0 [--coverage] [--skip-docker] [--verbose]"
            exit 1
            ;;
    esac
done

# 开始测试流程
print_header "Athena CI/CD 测试流程"

# 1. 代码质量检查
print_header "1. 代码质量检查"

echo "检查核心模块语法..."
if python3 -m py_compile core/cache/ core/agents/ tests/unit/test_config.py tests/core/ tests/integration/test_core_integration.py 2>/dev/null; then
    print_success "核心模块语法检查通过"
else
    print_error "核心模块语法检查失败"
    # 不退出，继续测试
fi

# 2. 安装依赖
print_header "2. 安装测试依赖"

if ! pip3 list | grep -q python3 -m pytest; then
    echo "安装python3 -m pytest和相关依赖..."
    pip3 install python3 -m pytest python3 -m pytest-cov python3 -m pytest-asyncio python3 -m pytest-mock -q
    print_success "依赖安装完成"
else
    print_success "依赖已安装"
fi

# 3. 运行单元测试
print_header "3. 运行单元测试"

echo "运行单元测试..."
if [ "$VERBOSE" = true ]; then
    UNIT_OUTPUT=$(python3 -m pytest tests/unit/test_config.py tests/core/ -v --tb=short 2>&1)
    UNIT_EXIT=$?
else
    UNIT_OUTPUT=$(python3 -m pytest tests/unit/test_config.py tests/core/ -q --tb=no 2>&1)
    UNIT_EXIT=$?
fi

# 解析结果
UNIT_PASSED=$(echo "$UNIT_OUTPUT" | grep -oP '\d+(?= passed)' || echo "0")
UNIT_FAILED=$(echo "$UNIT_OUTPUT" | grep -oP '\d+(?= failed)' || echo "0")
UNIT_SKIPPED=$(echo "$UNIT_OUTPUT" | grep -oP '\d+(?= skipped)' || echo "0")

if [ $UNIT_EXIT -eq 0 ]; then
    print_success "单元测试通过 ($UNIT_PASSED 个测试)"
else
    print_error "单元测试失败 ($UNIT_FAILED 个失败)"
    echo "$UNIT_OUTPUT"
fi

PASSED_TESTS=$((PASSED_TESTS + UNIT_PASSED))
FAILED_TESTS=$((FAILED_TESTS + UNIT_FAILED))
SKIPPED_TESTS=$((SKIPPED_TESTS + UNIT_SKIPPED))

# 4. 运行核心测试
print_header "4. 运行核心模块测试"

echo "核心测试已在单元测试中运行，跳过..."
CORE_PASSED=0
CORE_FAILED=0
CORE_SKIPPED=0
CORE_EXIT=0

if [ $CORE_EXIT -eq 0 ]; then
    print_success "核心测试通过 ($CORE_PASSED 个测试)"
else
    print_error "核心测试失败 ($CORE_FAILED 个失败)"
fi

PASSED_TESTS=$((PASSED_TESTS + CORE_PASSED))
FAILED_TESTS=$((FAILED_TESTS + CORE_FAILED))
SKIPPED_TESTS=$((SKIPPED_TESTS + CORE_SKIPPED))

# 5. 运行集成测试
print_header "5. 运行集成测试"

echo "运行集成测试..."
if [ "$VERBOSE" = true ]; then
    INT_OUTPUT=$(python3 -m pytest tests/integration/test_core_integration.py -v --tb=short 2>&1)
    INT_EXIT=$?
else
    INT_OUTPUT=$(python3 -m pytest tests/integration/test_core_integration.py -q --tb=no 2>&1)
    INT_EXIT=$?
fi

INT_PASSED=$(echo "$INT_OUTPUT" | grep -oP '\d+(?= passed)' || echo "0")
INT_FAILED=$(echo "$INT_OUTPUT" | grep -oP '\d+(?= failed)' || echo "0")
INT_SKIPPED=$(echo "$INT_OUTPUT" | grep -oP '\d+(?= skipped)' || echo "0")

if [ $INT_EXIT -eq 0 ]; then
    print_success "集成测试通过 ($INT_PASSED 个测试)"
else
    print_error "集成测试失败 ($INT_FAILED 个失败)"
fi

PASSED_TESTS=$((PASSED_TESTS + INT_PASSED))
FAILED_TESTS=$((FAILED_TESTS + INT_FAILED))
SKIPPED_TESTS=$((SKIPPED_TESTS + INT_SKIPPED))

# 6. 生成覆盖率报告
if [ "$COVERAGE" = true ]; then
    print_header "6. 生成覆盖率报告"

    echo "生成覆盖率报告..."
    python3 -m pytest tests/unit/test_config.py tests/core/ tests/integration/test_core_integration.py --cov=core.cache --cov=core.agents --cov-report=html --cov-report=term --cov-report=xml -q
    print_success "覆盖率报告已生成: htmlcov/index.html"
fi

# 7. 生成测试报告
print_header "7. 测试结果摘要"

TOTAL_TESTS=$((PASSED_TESTS + FAILED_TESTS + SKIPPED_TESTS))

echo ""
echo "=========================================="
echo "           测试结果摘要"
echo "=========================================="
echo -e "  总测试数:   ${BLUE}$TOTAL_TESTS${NC}"
echo -e "  通过:       ${GREEN}$PASSED_TESTS${NC}"
echo -e "  失败:       ${RED}$FAILED_TESTS${NC}"
echo -e "  跳过:       ${YELLOW}$SKIPPED_TESTS${NC}"
echo "=========================================="

# 计算通过率
if [ $TOTAL_TESTS -gt 0 ]; then
    PASS_RATE=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    echo "  通过率:     ${PASS_RATE}%"
    echo "=========================================="
fi

# 返回适当的退出码
if [ $FAILED_TESTS -gt 0 ]; then
    print_error "存在失败的测试"
    exit 1
elif [ $PASSED_TESTS -eq 0 ]; then
    print_error "没有运行的测试"
    exit 1
else
    print_success "所有测试通过!"
    exit 0
fi
