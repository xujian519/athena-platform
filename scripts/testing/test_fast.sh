#!/bin/bash
# =============================================================================
# 快速测试脚本
# 仅运行快速单元测试，用于开发过程中的快速验证
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# 记录开始时间
START_TIME=$(date +%s)

print_header "快速测试执行"

# 执行快速单元测试
print_info "运行标记为 @fast 的单元测试..."
echo ""

pytest \
    -m "fast and unit and not slow" \
    -v \
    --tb=short \
    tests/unit/ tests/core/ "$@"

# 计算执行时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
print_success "快速测试完成！耗时: ${DURATION}秒"

# 显示后续建议
echo ""
print_info "后续测试建议:"
echo "  • 运行所有单元测试: ./scripts/test_unit.sh"
echo "  • 运行并行测试: ./scripts/test_parallel.sh"
echo "  • 运行完整测试: ./scripts/test_all.sh"
