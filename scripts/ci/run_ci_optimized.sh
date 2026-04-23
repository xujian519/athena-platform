#!/bin/bash
# =============================================================================
# 优化的本地CI/CD脚本
# 模拟GitHub Actions工作流，在本地执行完整的CI/CD检查
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# 打印函数
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_stage() {
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

# 统计变量
TOTAL_STAGES=0
PASSED_STAGES=0
FAILED_STAGES=0

# 记录开始时间
CI_START_TIME=$(date +%s)

# 清理函数
cleanup() {
    print_info "清理临时文件..."
    rm -f /tmp/ci_stage_*.txt
}

# 捕获中断
trap cleanup EXIT
trap 'print_error "CI被中断"; cleanup; exit 1' INT

# 检查依赖
check_dependencies() {
    print_stage "检查依赖"

    local missing_deps=()

    # 检查必要的命令
    for cmd in python3 pip pytest; do
        if ! command -v $cmd &> /dev/null; then
            missing_deps+=($cmd)
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        print_error "缺少依赖: ${missing_deps[*]}"
        exit 1
    fi

    # 检查pytest插件
    print_info "检查pytest插件..."

    if ! python3 -c "import xdist" 2>/dev/null; then
        print_warning "pytest-xdist未安装，正在安装..."
        pip install pytest-xdist
    fi

    if ! python3 -c "import pytest_timeout" 2>/dev/null; then
        print_warning "pytest-timeout未安装，正在安装..."
        pip install pytest-timeout
    fi

    print_success "所有依赖已就绪"
}

# 阶段1: 快速检查
stage_quick_check() {
    print_stage "阶段1: 快速检查 (<2分钟)"

    TOTAL_STAGES=$((TOTAL_STAGES + 1))
    STAGE_START=$(date +%s)

    # 代码格式检查
    print_info "检查代码格式..."
    if black --check core/cache/ core/agents/ --diff > /tmp/ci_stage_format.txt 2>&1; then
        print_success "代码格式检查通过"
    else
        cat /tmp/ci_stage_format.txt
        print_warning "代码格式需要调整"
    fi

    # 快速测试
    print_info "运行快速测试..."
    if pytest tests/core/ -m "fast and unit" -v --tb=short -x -q > /tmp/ci_stage_quick.txt 2>&1; then
        print_success "快速测试通过"
        PASSED_STAGES=$((PASSED_STAGES + 1))
    else
        print_error "快速测试失败"
        cat /tmp/ci_stage_quick.txt | tail -20
        FAILED_STAGES=$((FAILED_STAGES + 1))
        return 1
    fi

    STAGE_END=$(date +%s)
    STAGE_DURATION=$((STAGE_END - STAGE_START))
    print_info "阶段1耗时: ${STAGE_DURATION}秒"
}

# 阶段2: 并行单元测试
stage_parallel_unit() {
    print_stage "阶段2: 并行单元测试"

    TOTAL_STAGES=$((TOTAL_STAGES + 1))
    STAGE_START=$(date +%s)

    # 获取CPU核心数
    if [[ "$OSTYPE" == "darwin"* ]]; then
        CPU_COUNT=$(sysctl -n hw.ncpu)
    else
        CPU_COUNT=$(nproc)
    fi

    print_info "使用 ${CPU_COUNT} 个worker进程"

    if pytest tests/unit/ tests/core/ \
        -n "${CPU_COUNT}" \
        --dist=loadscope \
        -m "unit and not slow" \
        -v \
        --tb=short \
        -q > /tmp/ci_stage_unit.txt 2>&1; then
        print_success "并行单元测试通过"
        PASSED_STAGES=$((PASSED_STAGES + 1))
    else
        print_error "并行单元测试失败"
        cat /tmp/ci_stage_unit.txt | tail -30
        FAILED_STAGES=$((FAILED_STAGES + 1))
        return 1
    fi

    STAGE_END=$(date +%s)
    STAGE_DURATION=$((STAGE_END - STAGE_START))
    print_info "阶段2耗时: ${STAGE_DURATION}秒"
}

# 阶段3: 边缘情况测试
stage_edge_cases() {
    print_stage "阶段3: 边缘情况测试"

    TOTAL_STAGES=$((TOTAL_STAGES + 1))
    STAGE_START=$(date +%s)

    if pytest tests/core/test_edge_cases.py \
        -n auto \
        -v \
        --tb=short \
        -q > /tmp/ci_stage_edge.txt 2>&1; then
        print_success "边缘情况测试通过"
        PASSED_STAGES=$((PASSED_STAGES + 1))
    else
        print_error "边缘情况测试失败"
        cat /tmp/ci_stage_edge.txt | tail -20
        FAILED_STAGES=$((FAILED_STAGES + 1))
        return 1
    fi

    STAGE_END=$(date +%s)
    STAGE_DURATION=$((STAGE_END - STAGE_START))
    print_info "阶段3耗时: ${STAGE_DURATION}秒"
}

# 阶段4: 代码质量检查
stage_code_quality() {
    print_stage "阶段4: 代码质量检查"

    TOTAL_STAGES=$((TOTAL_STAGES + 1))
    STAGE_START=$(date +%s)

    local quality_passed=true

    # Ruff检查
    print_info "运行Ruff检查..."
    if ruff check core/cache/ core/agents/ > /tmp/ci_stage_ruff.txt 2>&1; then
        print_success "Ruff检查通过"
    else
        cat /tmp/ci_stage_ruff.txt
        print_warning "Ruff发现问题"
        quality_passed=false
    fi

    # Black检查
    print_info "运行Black检查..."
    if black --check core/cache/ core/agents/ > /tmp/ci_stage_black.txt 2>&1; then
        print_success "Black检查通过"
    else
        print_warning "Black发现问题"
        quality_passed=false
    fi

    if [ "$quality_passed" = true ]; then
        PASSED_STAGES=$((PASSED_STAGES + 1))
        print_success "代码质量检查通过"
    else
        FAILED_STAGES=$((FAILED_STAGES + 1))
        print_error "代码质量检查失败"
        return 1
    fi

    STAGE_END=$(date +%s)
    STAGE_DURATION=$((STAGE_END - STAGE_START))
    print_info "阶段4耗时: ${STAGE_DURATION}秒"
}

# 生成CI报告
generate_ci_report() {
    print_stage "CI执行报告"

    # 计算总耗时
    CI_END_TIME=$(date +%s)
    CI_DURATION=$((CI_END_TIME - CI_START_TIME))
    MINUTES=$((CI_DURATION / 60))
    SECONDS=$((CI_DURATION % 60))

    echo ""
    echo -e "${MAGENTA}╔═══════════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║            CI/CD 执行摘要                             ║${NC}"
    echo -e "${MAGENTA}╚═══════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "总耗时: ${MINUTES}分${SECONDS}秒"
    echo ""
    echo -e "阶段统计:"
    echo -e "  总阶段数: ${TOTAL_STAGES}"
    echo -e "  ${GREEN}通过: ${PASSED_STAGES}${NC}"
    echo -e "  ${RED}失败: ${FAILED_STAGES}${NC}"
    echo ""

    # 判断总体结果
    if [ $FAILED_STAGES -eq 0 ]; then
        echo -e "${GREEN}✅ 所有CI阶段通过！${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}❌ CI检查失败，请修复问题后重试${NC}"
        echo ""
        return 1
    fi
}

# 主函数
main() {
    print_info "开始本地CI/CD流程..."
    echo ""

    # 检查依赖
    check_dependencies

    # 执行各阶段
    stage_quick_check || true
    stage_parallel_unit || true
    stage_edge_cases || true
    stage_code_quality || true

    # 生成报告
    generate_ci_report
}

# 显示帮助
show_help() {
    cat << EOF
用法: $0 [选项]

优化的本地CI/CD脚本，模拟GitHub Actions工作流。

选项:
  -h, --help     显示此帮助信息
  -q, --quick    仅运行快速检查
  -u, --unit     仅运行单元测试
  -e, --edge     仅运行边缘情况测试
  -c, --quality  仅运行代码质量检查
  --no-cleanup   保留临时文件

示例:
  $0              # 运行完整CI/CD流程
  $0 --quick      # 仅运行快速检查
  $0 --unit       # 仅运行单元测试

EOF
}

# 处理命令行参数
RUN_QUICK=false
RUN_UNIT=false
RUN_EDGE=false
RUN_QUALITY=false
NO_CLEANUP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -q|--quick)
            RUN_QUICK=true
            shift
            ;;
        -u|--unit)
            RUN_UNIT=true
            shift
            ;;
        -e|--edge)
            RUN_EDGE=true
            shift
            ;;
        -c|--quality)
            RUN_QUALITY=true
            shift
            ;;
        --no-cleanup)
            NO_CLEANUP=true
            shift
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
done

# 设置清理陷阱
if [ "$NO_CLEANUP" = false ]; then
    trap cleanup EXIT
fi

# 根据选项执行相应阶段
if [ "$RUN_QUICK" = true ]; then
    check_dependencies
    stage_quick_check
    exit $?
elif [ "$RUN_UNIT" = true ]; then
    check_dependencies
    stage_parallel_unit
    exit $?
elif [ "$RUN_EDGE" = true ]; then
    check_dependencies
    stage_edge_cases
    exit $?
elif [ "$RUN_QUALITY" = true ]; then
    check_dependencies
    stage_code_quality
    exit $?
else
    main
    exit $?
fi
