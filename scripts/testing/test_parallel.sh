#!/bin/bash
# =============================================================================
# 并行测试执行脚本
# 使用pytest-xdist进行并行测试，提升测试执行效率
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 获取CPU核心数
get_cpu_count() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sysctl -n hw.ncpu
    else
        # Linux
        nproc
    fi
}

# 主函数
main() {
    print_info "开始并行测试执行..."
    echo ""

    # 检查pytest-xdist是否安装
    if ! python3 -c "import xdist" 2>/dev/null; then
        print_error "pytest-xdist未安装，正在安装..."
        pip install pytest-xdist pytest-timeout
    fi

    # 获取CPU核心数
    CPU_COUNT=$(get_cpu_count)
    WORKER_COUNT=${1:-$CPU_COUNT}
    print_info "检测到 ${CPU_COUNT} 个CPU核心"
    print_info "使用 ${WORKER_COUNT} 个worker进程"
    echo ""

    # 记录开始时间
    START_TIME=$(date +%s)

    # 执行并行测试
    print_info "执行测试..."
    echo ""

    pytest \
        -n "${WORKER_COUNT}" \
        --dist=loadscope \
        --maxfail=10 \
        --timeout=300 \
        -v \
        tests/ "$@"

    # 计算执行时间
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    MINUTES=$((DURATION / 60))
    SECONDS=$((DURATION % 60))

    echo ""
    print_success "测试完成！"
    print_info "总耗时: ${MINUTES}分${SECONDS}秒"

    # 显示性能建议
    if [ $DURATION -gt 300 ]; then
        print_warning "测试执行时间较长，建议："
        echo "  1. 使用 -m 'not slow' 跳过慢速测试"
        echo "  2. 使用 -m unit 仅运行单元测试"
        echo "  3. 增加worker数量: -n $((CPU_COUNT * 2))"
    fi
}

# 显示帮助信息
show_help() {
    cat << EOF
用法: $0 [worker数量] [pytest选项...]

示例:
  $0              # 自动检测CPU核心数并执行
  $0 4            # 使用4个worker进程
  $0 8 -m unit    # 使用8个worker，仅运行单元测试
  $0 -m "not slow" # 跳过慢速测试

环境变量:
  PYTEST_WORKERS   # 覆盖worker数量

性能提示:
  - 对于CPU密集型测试: worker数 = CPU核心数
  - 对于IO密集型测试: worker数 = CPU核心数 * 2
  - 避免worker数过多，会导致上下文切换开销

EOF
}

# 处理命令行参数
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
    show_help
    exit 0
fi

main "$@"
