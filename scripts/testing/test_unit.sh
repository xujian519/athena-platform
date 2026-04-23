#!/bin/bash
# =============================================================================
# 单元测试脚本
# 运行所有单元测试，使用并行化加速执行
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

print_header "单元测试执行"

# 检查pytest-xdist
if python3 -c "import xdist" 2>/dev/null; then
    # 获取CPU核心数
    if [[ "$OSTYPE" == "darwin"* ]]; then
        CPU_COUNT=$(sysctl -n hw.ncpu)
    else
        CPU_COUNT=$(nproc)
    fi

    print_info "使用并行模式 (${CPU_COUNT} workers)..."
    echo ""

    pytest \
        -n "${CPU_COUNT}" \
        -m "unit and not slow" \
        --dist=loadscope \
        -v \
        --tb=short \
        tests/unit/ tests/core/ "$@"
else
    print_warning "pytest-xdist未安装，使用串行模式..."
    echo ""

    pytest \
        -m "unit and not slow" \
        -v \
        --tb=short \
        tests/unit/ tests/core/ "$@"
fi

# 计算执行时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
print_success "单元测试完成！耗时: ${DURATION}秒"
