#!/bin/bash

# Athena API Gateway - 测试脚本

set -euo pipefail

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TEST_RESULTS_DIR="$PROJECT_ROOT/test-results"

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# 准备测试环境
prepare_test_environment() {
    log_info "准备测试环境..."
    
    # 创建测试结果目录
    mkdir -p "$TEST_RESULTS_DIR"
    mkdir -p "$TEST_RESULTS_DIR/unit"
    mkdir -p "$TEST_RESULTS_DIR/integration"
    mkdir -p "$TEST_RESULTS_DIR/coverage"
    mkdir -p "$TEST_RESULTS_DIR/benchmark"
    
    # 启动测试依赖服务
    if [[ "${SKIP_INFRASTRUCTURE:-false}" != "true" ]]; then
        log_info "启动测试基础设施..."
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" up -d
        sleep 10
    fi
    
    log_success "测试环境准备完成"
}

# 清理测试环境
cleanup_test_environment() {
    log_info "清理测试环境..."
    
    # 停止测试依赖服务
    if [[ "${SKIP_INFRASTRUCTURE:-false}" != "true" ]]; then
        docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" down -v
    fi
    
    log_success "测试环境清理完成"
}

# 运行单元测试
run_unit_tests() {
    log_info "运行单元测试..."
    
    cd "$PROJECT_ROOT"
    
    # 运行单元测试并生成覆盖率报告
    go test -v \
        -tags=unit \
        -race \
        -coverprofile="$TEST_RESULTS_DIR/coverage/unit.out" \
        -covermode=atomic \
        ./... | tee "$TEST_RESULTS_DIR/unit/unit-test.log"
    
    # 生成HTML覆盖率报告
    go tool cover -html="$TEST_RESULTS_DIR/coverage/unit.out" -o "$TEST_RESULTS_DIR/coverage/unit.html"
    
    log_success "单元测试完成"
}

# 运行集成测试
run_integration_tests() {
    log_info "运行集成测试..."
    
    cd "$PROJECT_ROOT"
    
    # 设置测试环境变量
    export REDIS_HOST=localhost
    export REDIS_PORT=6379
    export ENVIRONMENT=test
    
    # 运行集成测试
    go test -v \
        -tags=integration \
        -timeout=30m \
        ./tests/integration/... | tee "$TEST_RESULTS_DIR/integration/integration-test.log"
    
    log_success "集成测试完成"
}

# 运行端到端测试
run_e2e_tests() {
    log_info "运行端到端测试..."
    
    # 启动完整的服务栈
    docker-compose -f "$PROJECT_ROOT/docker-compose.test.yml" up -d
    sleep 30
    
    # 等待服务就绪
    local max_attempts=60
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8080/health &>/dev/null; then
            break
        fi
        sleep 2
        ((attempt++))
    done
    
    if [[ $attempt -gt $max_attempts ]]; then
        log_error "服务启动超时，跳过端到端测试"
        return 1
    fi
    
    # 运行端到端测试
    cd "$PROJECT_ROOT"
    
    go test -v \
        -tags=e2e \
        -timeout=60m \
        ./tests/e2e/... | tee "$TEST_RESULTS_DIR/e2e/e2e-test.log"
    
    log_success "端到端测试完成"
}

# 运行性能测试
run_performance_tests() {
    log_info "运行性能测试..."
    
    cd "$PROJECT_ROOT"
    
    # 运行基准测试
    go test -v \
        -bench=. \
        -benchmem \
        -count=5 \
        -run=^$ \
        ./... | tee "$TEST_RESULTS_DIR/benchmark/benchmark.log"
    
    # 生成性能报告
    go test -v \
        -bench=. \
        -benchmem \
        -cpuprofile="$TEST_RESULTS_DIR/benchmark/cpu.prof" \
        -memprofile="$TEST_RESULTS_DIR/benchmark/mem.prof" \
        -run=^$ \
        ./...
    
    log_success "性能测试完成"
}

# 运行安全测试
run_security_tests() {
    log_info "运行安全测试..."
    
    # 运行Gosec安全扫描
    cd "$PROJECT_ROOT"
    gosec -fmt=json -out="$TEST_RESULTS_DIR/security/gosec.json" ./...
    
    # 运行敏感信息检测
    detect-secrets scan --all-files --baseline ".secrets.baseline" || true
    
    # 运行依赖漏洞扫描
    go list -json -m all | nancy sleuth --output=json > "$TEST_RESULTS_DIR/security/vulnerabilities.json" || true
    
    log_success "安全测试完成"
}

# 生成测试报告
generate_test_report() {
    log_info "生成测试报告..."
    
    cd "$PROJECT_ROOT"
    
    # 汇总测试结果
    local unit_passed=$(grep -c "PASS" "$TEST_RESULTS_DIR/unit/unit-test.log" || echo "0")
    local unit_failed=$(grep -c "FAIL" "$TEST_RESULTS_DIR/unit/unit-test.log" || echo "0")
    local integration_passed=$(grep -c "PASS" "$TEST_RESULTS_DIR/integration/integration-test.log" || echo "0")
    local integration_failed=$(grep -c "FAIL" "$TEST_RESULTS_DIR/integration/integration-test.log" || echo "0")
    
    # 生成HTML报告
    cat > "$TEST_RESULTS_DIR/test-report.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Athena API Gateway - 测试报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .summary { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .passed { color: green; font-weight: bold; }
        .failed { color: red; font-weight: bold; }
        .section { margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Athena API Gateway - 测试报告</h1>
    <div class="summary">
        <h2>测试摘要</h2>
        <div class="section">
            <strong>单元测试:</strong> 
            <span class="passed">$unit_passed 通过</span>, 
            <span class="failed">$unit_failed 失败</span>
        </div>
        <div class="section">
            <strong>集成测试:</strong>
            <span class="passed">$integration_passed 通过</span>,
            <span class="failed">$integration_failed 失败</span>
        </div>
        <div class="section">
            <p>生成时间: $(date)</p>
        </div>
    </div>
    <div class="section">
        <h2>详细报告</h2>
        <ul>
            <li><a href="coverage/unit.html">单元测试覆盖率报告</a></li>
            <li><a href="unit/unit-test.log">单元测试日志</a></li>
            <li><a href="integration/integration-test.log">集成测试日志</a></li>
            <li><a href="benchmark/benchmark.log">性能测试报告</a></li>
            <li><a href="security/gosec.json">安全扫描报告</a></li>
        </ul>
    </div>
</body>
</html>
EOF
    
    log_success "测试报告生成完成: $TEST_RESULTS_DIR/test-report.html"
}

# 运行所有测试
run_all_tests() {
    log_info "运行所有测试..."
    
    prepare_test_environment
    
    # 运行各类测试
    run_unit_tests
    run_integration_tests
    
    if [[ "${SKIP_E2E:-false}" != "true" ]]; then
        run_e2e_tests
    fi
    
    if [[ "${SKIP_PERFORMANCE:-false}" != "true" ]]; then
        run_performance_tests
    fi
    
    if [[ "${SKIP_SECURITY:-false}" != "true" ]]; then
        run_security_tests
    fi
    
    generate_test_report
    
    # 清理测试环境
    if [[ "${SKIP_CLEANUP:-false}" != "true" ]]; then
        cleanup_test_environment
    fi
    
    log_success "所有测试完成"
}

# 快速测试（仅单元测试）
run_quick_tests() {
    log_info "运行快速测试..."
    
    prepare_test_environment
    run_unit_tests
    generate_test_report
    
    log_success "快速测试完成"
}

# 信号处理
trap cleanup_test_environment EXIT INT TERM

# 主函数
main() {
    echo "🧪 Athena API Gateway - 测试脚本"
    echo ""
    
    local command=${1:-all}
    
    case $command in
        all)
            run_all_tests
            ;;
        
        unit)
            prepare_test_environment
            run_unit_tests
            ;;
        
        integration)
            prepare_test_environment
            run_integration_tests
            ;;
        
        e2e)
            prepare_test_environment
            run_e2e_tests
            ;;
        
        performance)
            prepare_test_environment
            run_performance_tests
            ;;
        
        security)
            run_security_tests
            ;;
        
        quick)
            run_quick_tests
            ;;
        
        cleanup)
            cleanup_test_environment
            ;;
        
        report)
            generate_test_report
            ;;
        
        help)
            echo "用法: $0 [command]"
            echo ""
            echo "命令:"
            echo "  all         运行所有测试 (默认)"
            echo "  unit        运行单元测试"
            echo "  integration 运行集成测试"
            echo "  e2e         运行端到端测试"
            echo "  performance 运行性能测试"
            echo "  security    运行安全测试"
            echo "  quick       快速测试（仅单元测试）"
            echo "  cleanup     清理测试环境"
            echo "  report      生成测试报告"
            echo "  help        显示帮助信息"
            echo ""
            echo "环境变量:"
            echo "  SKIP_INFRASTRUCTURE 跳过基础设施启动"
            echo "  SKIP_E2E            跳过端到端测试"
            echo "  SKIP_PERFORMANCE     跳过性能测试"
            echo "  SKIP_SECURITY        跳过安全测试"
            echo "  SKIP_CLEANUP         跳过环境清理"
            echo ""
            echo "示例:"
            echo "  $0 all                    # 运行所有测试"
            echo "  $0 unit                   # 仅运行单元测试"
            echo "  SKIP_E2E=true $0 all       # 跳过端到端测试"
            ;;
        
        *)
            log_error "未知命令: $command"
            main help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"