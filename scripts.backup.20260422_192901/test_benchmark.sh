#!/bin/bash
# =============================================================================
# 性能基准测试脚本
# 运行性能测试并生成基准报告
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
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

print_benchmark() {
    echo -e "${MAGENTA}[BENCHMARK]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${MAGENTA}========================================${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}========================================${NC}"
    echo ""
}

# 检查pytest-benchmark
check_benchmark() {
    if ! python3 -c "import pytest_benchmark" 2>/dev/null; then
        print_warning "pytest-benchmark未安装，正在安装..."
        pip install pytest-benchmark
    fi
}

# 记录开始时间
START_TIME=$(date +%s)

print_header "性能基准测试"

check_benchmark

# 创建基准测试结果目录
BENCHMARK_DIR=".benchmarks"
mkdir -p "${BENCHMARK_DIR}"

print_info "基准测试结果将保存到: ${BENCHMARK_DIR}"
echo ""

# 运行性能基准测试
print_info "执行性能基准测试..."
echo ""

pytest \
    -m "performance or benchmark" \
    --benchmark-only \
    --benchmark-autosave \
    --benchmark-save-data \
    --benchmark-columns=min,max,mean,stddev,median,ops,rounds \
    --benchmark-sort=name \
    --benchmark-group-by=name \
    -v \
    tests/ "$@"

# 生成HTML报告
if [ -d "${BENCHMARK_DIR}" ]; then
    print_info "生成基准测试报告..."

    # 检查是否有基准数据
    if ls ${BENCHMARK_DIR}/*.json 1> /dev/null 2>&1; then
        pytest-benchmark compare \
            --benchmark-columns=min,max,mean,stddev,median,ops \
            --benchmark-sort=name \
            "${BENCHMARK_DIR}"/*.json || true

        print_success "基准测试报告已生成"
        print_info "位置: ${BENCHMARK_DIR}"
    fi
fi

# 计算执行时间
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
print_success "性能基准测试完成！耗时: ${DURATION}秒"

# 显示性能分析建议
echo ""
print_info "性能分析建议:"
echo "  1. 查看基准测试结果: cat ${BENCHMARK_DIR}/latest.json"
echo "  2. 生成对比报告: pytest-benchmark compare ${BENCHMARK_DIR}/*.json"
echo "  3. 可视化图表: pytest-benchmark histogram ${BENCHMARK_DIR}/*.json"
