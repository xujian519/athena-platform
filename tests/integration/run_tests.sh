#!/bin/bash

# Athena工作平台多智能体协作集成测试运行脚本

set -euo pipefail

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TEST_DIR="$PROJECT_ROOT/tests/integration"
LOG_DIR="$PROJECT_DIR/logs/test"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查测试依赖..."
    
    # 检查Go
    if ! command -v go &> /dev/null; then
        log_error "Go未安装，请先安装Go"
        exit 1
    fi
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 准备测试环境
prepare_test_environment() {
    log_info "准备测试环境..."
    
    # 创建日志目录
    mkdir -p "$LOG_DIR"
    
    # 设置测试环境变量
    export TEST_MODE=true
    export TEST_LOG_LEVEL=debug
    export TEST_TIMEOUT=300
    
    # 检查端口占用
    local ports=("8080" "5432" "6379")
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            log_warning "端口 $port 已被占用，可能导致测试失败"
        fi
    done
    
    log_success "测试环境准备完成"
}

# 启动测试服务
start_test_services() {
    log_info "启动测试服务..."
    
    cd "$PROJECT_ROOT"
    
    # 启动测试数据库和缓存
    docker-compose -f docker-compose.unified.yml --profile test up -d
    
    # 等待服务就绪
    log_info "等待服务就绪..."
    sleep 10
    
    # 检查服务状态
    if ! docker-compose -f docker-compose.test.yml ps | grep -q "Up"; then
        log_error "测试服务启动失败"
        exit 1
    fi
    
    log_success "测试服务启动完成"
}

# 运行单元测试
run_unit_tests() {
    log_info "运行单元测试..."
    
    cd "$TEST_DIR"
    
    # 运行Go单元测试
    go test -v -race -cover -timeout 300s ./...
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "单元测试通过"
    else
        log_error "单元测试失败，退出码: $exit_code"
        return $exit_code
    fi
}

# 运行集成测试
run_integration_tests() {
    log_info "运行集成测试..."
    
    cd "$TEST_DIR"
    
    # 运行集成测试
    go test -v -race -timeout 600s -tags=integration ./...
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "集成测试通过"
    else
        log_error "集成测试失败，退出码: $exit_code"
        return $exit_code
    fi
}

# 运行性能测试
run_performance_tests() {
    log_info "运行性能测试..."
    
    cd "$TEST_DIR"
    
    # 运行性能基准测试
    go test -v -race -timeout 900s -bench=. -benchmem ./...
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log_success "性能测试通过"
    else
        log_warning "性能测试出现问题，但不阻止继续执行"
    fi
}

# 生成测试报告
generate_test_report() {
    log_info "生成测试报告..."
    
    local report_file="$LOG_DIR/integration-test-report-$(date +%Y%m%d-%H%M%S).html"
    
    # 生成覆盖率报告
    cd "$TEST_DIR"
    go test -coverprofile=coverage.out ./...
    go tool cover -html=coverage.out -o "$report_file"
    
    # 生成JSON格式的测试结果
    go test -json ./... > "$LOG_DIR/test-results-$(date +%Y%m%d-%H%M%S).json"
    
    log_success "测试报告生成完成: $report_file"
}

# 清理测试环境
cleanup_test_environment() {
    log_info "清理测试环境..."
    
    cd "$PROJECT_ROOT"
    
    # 停止测试服务
    docker-compose -f docker-compose.unified.yml --profile test down
    
    # 清理测试数据
    rm -f "$TEST_DIR/coverage.out"
    rm -f "$TEST_DIR/test.log"
    
    log_success "测试环境清理完成"
}

# 显示帮助信息
show_help() {
    echo "Athena工作平台多智能体协作集成测试脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help      显示帮助信息"
    echo "  -u, --unit      仅运行单元测试"
    echo "  -i, --integration 仅运行集成测试"
    echo "  -p, --performance 仅运行性能测试"
    echo "  -a, --all       运行所有测试（默认）"
    echo "  -c, --cleanup   仅清理测试环境"
    echo ""
    echo "示例:"
    echo "  $0              # 运行所有测试"
    echo "  $0 -u          # 仅运行单元测试"
    echo "  $0 -i          # 仅运行集成测试"
    echo "  $0 -c          # 清理测试环境"
}

# 主函数
main() {
    local run_unit=true
    local run_integration=true
    local run_performance=false
    local cleanup_only=false
    
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -u|--unit)
                run_unit=true
                run_integration=false
                shift
                ;;
            -i|--integration)
                run_unit=false
                run_integration=true
                shift
                ;;
            -p|--performance)
                run_unit=false
                run_integration=false
                run_performance=true
                shift
                ;;
            -a|--all)
                run_unit=true
                run_integration=true
                run_performance=true
                shift
                ;;
            -c|--cleanup)
                cleanup_only=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 仅清理模式
    if [ "$cleanup_only" = true ]; then
        cleanup_test_environment
        exit 0
    fi
    
    # 开始测试流程
    log_info "开始Athena工作平台多智能体协作集成测试"
    
    # 检查依赖
    check_dependencies
    
    # 准备环境
    prepare_test_environment
    
    # 启动服务
    start_test_services
    
    # 设置清理陷阱
    trap cleanup_test_environment EXIT
    
    local exit_code=0
    
    # 运行测试
    if [ "$run_unit" = true ]; then
        run_unit_tests || exit_code=$?
    fi
    
    if [ "$run_integration" = true ] && [ $exit_code -eq 0 ]; then
        run_integration_tests || exit_code=$?
    fi
    
    if [ "$run_performance" = true ] && [ $exit_code -eq 0 ]; then
        run_performance_tests || exit_code=$?
    fi
    
    # 生成报告
    generate_test_report
    
    # 显示结果
    if [ $exit_code -eq 0 ]; then
        log_success "所有测试通过！"
    else
        log_error "测试失败，退出码: $exit_code"
    fi
    
    exit $exit_code
}

# 执行主函数
main "$@"