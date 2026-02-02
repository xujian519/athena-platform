#!/bin/bash
# =============================================================================
# 完整测试套件脚本
# 按分组运行测试，并生成综合报告
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_stage() {
    echo ""
    echo -e "${CYAN}========================================${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}========================================${NC}"
    echo ""
}

# 总计开始时间
TOTAL_START=$(date +%s)

# 统计变量
TOTAL_PASSED=0
TOTAL_FAILED=0
TOTAL_ERRORS=0
TOTAL_SKIPPED=0

# 运行测试组
run_test_group() {
    local group_name=$1
    local group_marker=$2
    local group_desc=$3

    print_stage "阶段: $group_desc"

    # 记录阶段开始时间
    STAGE_START=$(date +%s)

    # 运行测试
    if pytest -m "$group_marker" -v --tb=no --no-header -q "$@" 2>&1 | tee /tmp/test_output_$$.txt; then
        RESULT=$(cat /tmp/test_output_$$.txt | grep -E "passed|failed|error" | tail -1)
        print_success "$group_desc 完成: $RESULT"
    else
        RESULT=$(cat /tmp/test_output_$$.txt | grep -E "passed|failed|error" | tail -1)
        print_error "$group_desc 失败: $RESULT"
    fi

    # 解析结果
    PASSED=$(cat /tmp/test_output_$$.txt | grep -oP '\d+(?= passed)' || echo "0")
    FAILED=$(cat /tmp/test_output_$$.txt | grep -oP '\d+(?= failed)' || echo "0")
    ERRORS=$(cat /tmp/test_output_$$.txt | grep -oP '\d+(?= error)' || echo "0")
    SKIPPED=$(cat /tmp/test_output_$$.txt | grep -oP '\d+(?= skipped)' || echo "0")

    TOTAL_PASSED=$((TOTAL_PASSED + PASSED))
    TOTAL_FAILED=$((TOTAL_FAILED + FAILED))
    TOTAL_ERRORS=$((TOTAL_ERRORS + ERRORS))
    TOTAL_SKIPPED=$((TOTAL_SKIPPED + SKIPPED))

    # 计算阶段耗时
    STAGE_END=$(date +%s)
    STAGE_DURATION=$((STAGE_END - STAGE_START))
    print_info "阶段耗时: ${STAGE_DURATION}秒"

    # 清理临时文件
    rm -f /tmp/test_output_$$.txt
}

# 主测试流程
main() {
    print_info "开始完整测试套件执行..."
    echo ""

    # 阶段1: 快速单元测试
    run_test_group "快速测试" "fast and unit and not slow" "快速单元测试"

    # 阶段2: 边缘情况测试
    run_test_group "边缘测试" "edge" "边缘情况测试"

    # 阶段3: 集成测试
    run_test_group "集成测试" "integration and not slow" "集成测试"

    # 计算总耗时
    TOTAL_END=$(date +%s)
    TOTAL_DURATION=$((TOTAL_END - TOTAL_START))
    MINUTES=$((TOTAL_DURATION / 60))
    SECONDS=$((TOTAL_DURATION % 60))

    # 打印总结
    print_stage "测试总结"
    echo ""
    echo -e "${CYAN}测试结果统计:${NC}"
    echo "  ✅ 通过: ${TOTAL_PASSED}"
    echo "  ❌ 失败: ${TOTAL_FAILED}"
    echo "  ⚠️  错误: ${TOTAL_ERRORS}"
    echo "  ⏭️  跳过: ${TOTAL_SKIPPED}"
    echo ""
    echo -e "${CYAN}总耗时:${NC} ${MINUTES}分${SECONDS}秒"
    echo ""

    # 判断总体结果
    if [ $TOTAL_FAILED -eq 0 ] && [ $TOTAL_ERRORS -eq 0 ]; then
        print_success "所有测试通过！"
        return 0
    else
        print_error "存在失败的测试，请检查日志"
        return 1
    fi
}

# 捕获Ctrl+C
trap 'print_error "测试被中断"; exit 1' INT

# 显示帮助
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    cat << EOF
用法: $0 [pytest选项...]

完整测试套件执行，按分组依次运行：
  1. 快速单元测试
  2. 边缘情况测试
  3. 集成测试

选项:
  -h, --help     显示此帮助信息
  其他选项将传递给pytest

示例:
  $0                    # 运行完整测试套件
  $0 -v                # 详细输出
  $0 -x                # 遇到失败立即停止

EOF
    exit 0
fi

# 执行主函数
main "$@"
