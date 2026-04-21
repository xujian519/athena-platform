#!/bin/bash
# Athena测试运行脚本
# 用于本地开发和CI/CD

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示帮助信息
show_help() {
    cat << EOF
Athena测试运行脚本

用法: ./scripts/run_tests.sh [选项] [测试路径]

选项:
    -u, --unit              只运行单元测试
    -i, --integration       只运行集成测试
    -c, --coverage          生成覆盖率报告
    -v, --verbose           详细输出
    -f, --fail-fast         遇到失败立即停止
    -k, --keep-going        继续运行所有测试
    -n, --parallel          并行运行测试
    -m, --mark MARK         只运行特定标记的测试
    -h, --help              显示此帮助信息

示例:
    ./scripts/run_tests.sh                    # 运行所有测试
    ./scripts/run_tests.sh -u -c             # 运行单元测试并生成覆盖率
    ./scripts/run_tests.sh -m "not slow"     # 排除慢速测试
    ./scripts/run_tests.sh tests/core/llm/   # 运行特定目录的测试

EOF
}

# 默认参数
UNIT_ONLY=false
INTEGRATION_ONLY=false
COVERAGE=false
VERBOSE=false
FAIL_FAST=false
PARALLEL=false
MARK=""
TEST_PATH=""

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -u|--unit)
            UNIT_ONLY=true
            shift
            ;;
        -i|--integration)
            INTEGRATION_ONLY=true
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -f|--fail-fast)
            FAIL_FAST=true
            shift
            ;;
        -k|--keep-going)
            FAIL_FAST=false
            shift
            ;;
        -n|--parallel)
            PARALLEL=true
            shift
            ;;
        -m|--mark)
            MARK="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
        *)
            TEST_PATH="$1"
            shift
            ;;
    esac
done

# 进入项目根目录
cd "$(dirname "$0")/.." || exit 1

print_info "Athena测试运行脚本"
echo ""

# 检查Poetry是否安装
if ! command -v poetry &> /dev/null; then
    print_error "Poetry未安装，请先安装: pip install poetry"
    exit 1
fi

# 构建pytest命令
PYTEST_CMD="poetry run pytest"

# 添加详细输出
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# 添加失败快速停止
if [ "$FAIL_FAST" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -x"
fi

# 添加并行运行
if [ "$PARALLEL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -n auto"
fi

# 添加覆盖率
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=core --cov-report=term-missing --cov-report=html"
fi

# 添加标记过滤
if [ -n "$MARK" ]; then
    PYTEST_CMD="$PYTEST_CMD -m '$MARK'"
fi

# 根据选项选择测试类型
if [ "$UNIT_ONLY" = true ]; then
    print_info "运行单元测试..."
    PYTEST_CMD="$PYTEST_CMD -m unit"
elif [ "$INTEGRATION_ONLY" = true ]; then
    print_info "运行集成测试..."
    PYTEST_CMD="$PYTEST_CMD -m integration"
fi

# 添加测试路径
if [ -n "$TEST_PATH" ]; then
    print_info "运行测试: $TEST_PATH"
    PYTEST_CMD="$PYTEST_CMD $TEST_PATH"
else
    PYTEST_CMD="$PYTEST_CMD tests/"
fi

# 运行测试
print_info "执行命令: $PYTEST_CMD"
echo ""

eval $PYTEST_CMD
TEST_EXIT_CODE=$?

# 显示结果
echo ""
if [ $TEST_EXIT_CODE -eq 0 ]; then
    print_success "所有测试通过！"

    if [ "$COVERAGE" = true ]; then
        echo ""
        print_info "覆盖率报告已生成:"
        echo "  - 终端: 已在上面显示"
        echo "  - HTML: htmlcov/index.html"
    fi
else
    print_error "测试失败，退出代码: $TEST_EXIT_CODE"
fi

exit $TEST_EXIT_CODE
