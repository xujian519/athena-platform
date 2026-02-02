#!/bin/bash
# -*- coding: utf-8 -*-
# 综合系统测试脚本
# Comprehensive System Test Script - Controlled by Athena & 小诺

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 平台信息
PLATFORM_NAME="Athena工作平台"
PLATFORM_OWNER="Athena & 小诺"

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 服务信息
CRAWLER_API_PORT=8002
CRAWLER_API_URL="http://localhost:$CRAWLER_API_PORT"
NGINX_URL="https://crawler.localhost"
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"

# 测试结果统计
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 打印平台标识
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ${PLATFORM_NAME}                       ║"
    echo "║                  综合系统测试脚本                            ║"
    echo "║                 控制者: ${PLATFORM_OWNER}                      ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 打印彩色信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    ((PASSED_TESTS++))
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((FAILED_TESTS++))
}

print_platform() {
    echo -e "${PURPLE}[PLATFORM]${NC} $1"
}

print_test_result() {
    ((TOTAL_TESTS++))
    echo -e "${CYAN}[TEST]${NC} $1"
}

# 检查端口是否开放
check_port() {
    local port=$1
    local service=$2

    if lsof -i :$port &> /dev/null; then
        print_success "$service 服务运行正常 (端口: $port)"
        return 0
    else
        print_error "$service 服务未运行 (端口: $port)"
        return 1
    fi
}

# 测试服务状态
test_service_status() {
    print_test_result "测试服务状态"

    echo ""
    echo "检查核心服务状态:"
    echo "================================"

    # 检查爬虫API服务
    if check_port $CRAWLER_API_PORT "爬虫API"; then
        # 测试API响应
        if curl -s "$CRAWLER_API_URL/health" | grep -q "healthy"; then
            print_success "爬虫API健康检查通过"
        else
            print_error "爬虫API健康检查失败"
        fi
    fi

    # 检查Nginx服务（如果配置了）
    if check_port 443 "Nginx HTTPS"; then
        if curl -s -k "$NGINX_URL/health" | grep -q "healthy"; then
            print_success "Nginx负载均衡器正常"
        else
            print_warning "Nginx运行但健康检查失败"
        fi
    fi

    # 检查Prometheus
    if check_port 9090 "Prometheus"; then
        print_info "Prometheus监控可访问: $PROMETHEUS_URL"
    fi

    # 检查Grafana
    if check_port 3000 "Grafana"; then
        print_info "Grafana仪表板可访问: $GRAFANA_URL"
    fi
}

# 测试爬虫核心功能
test_crawler_functionality() {
    print_test_result "测试爬虫核心功能"

    echo ""
    echo "测试爬虫核心功能:"
    echo "================================"

    # 测试单个URL爬取
    local test_urls='["https://httpbin.org/html"]'
    local crawl_request="{
        \"urls\": $test_urls,
        \"strategy\": \"auto\",
        \"max_concurrent\": 1,
        \"background\": false
    }"

    local response=$(curl -s -X POST "$CRAWLER_API_URL/crawl" \
        -H "Content-Type: application/json" \
        -d "$crawl_request")

    local success=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(1 if data.get('status') == 'completed' else 0)
except:
    print(0)
")

    if [ "$success" = "1" ]; then
        print_success "单个URL爬取测试通过"

        # 显示结果摘要
        echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    results = data.get('results', [])
    if results:
        result = results[0]
        print(f'  URL: {result.get(\"url\", \"N/A\")}')
        print(f'  成功: {result.get(\"success\", False)}')
        print(f'  爬虫类型: {result.get(\"crawler_used\", \"N/A\")}')
        print(f'  内容长度: {result.get(\"content_length\", 0)}')
except:
    pass
"
    else
        print_error "单个URL爬取测试失败"
    fi

    # 测试批量URL爬取
    local batch_urls='[
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/robots.txt"
    ]'
    local batch_request="{
        \"urls\": $batch_urls,
        \"strategy\": \"auto\",
        \"max_concurrent\": 3,
        \"background\": false
    }"

    response=$(curl -s -X POST "$CRAWLER_API_URL/crawl" \
        -H "Content-Type: application/json" \
        -d "$batch_request")

    success=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(1 if data.get('status') == 'completed' else 0)
except:
    print(0)
")

    if [ "$success" = "1" ]; then
        local result_count=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(len(data.get('results', [])))
except:
    print(0)
")
        print_success "批量URL爬取测试通过 (处理了 $result_count 个URL)"
    else
        print_error "批量URL爬取测试失败"
    fi
}

# 测试批量处理系统
test_batch_processing() {
    print_test_result "测试批量处理系统"

    echo ""
    echo "测试批量处理系统:"
    echo "================================"

    # 创建批量任务
    local urls='[
        "https://httpbin.org/html",
        "https://httpbin.org/json"
    ]'
    local batch_task_request="{
        \"name\": \"综合测试批量任务\",
        \"urls\": $urls,
        \"crawler_type\": \"hybrid\",
        \"priority\": \"normal\",
        \"options\": {
            \"max_concurrent\": 2
        }
    }"

    local response=$(curl -s -X POST "$CRAWLER_API_URL/batch/create" \
        -H "Content-Type: application/json" \
        -d "$batch_task_request")

    local task_id=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('task_id', '') if data.get('status') == 'created' else '')
except:
    print('')
")

    if [ -n "$task_id" ]; then
        print_success "批量任务创建成功 (ID: $task_id)"

        # 等待任务完成
        local max_wait=30
        local wait_time=0
        while [ $wait_time -lt $max_wait ]; do
            local status=$(curl -s "$CRAWLER_API_URL/batch/$task_id/status" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('status', 'unknown'))
except:
    print('error')
")

            if [ "$status" = "completed" ]; then
                print_success "批量任务执行成功"
                break
            elif [ "$status" = "failed" ]; then
                print_error "批量任务执行失败"
                break
            fi

            sleep 2
            ((wait_time += 2))
            echo -ne "\r等待任务完成... ${wait_time}s"
        done

        if [ $wait_time -ge $max_wait ]; then
            print_warning "批量任务等待超时"
        fi

    else
        print_error "批量任务创建失败"
    fi
}

# 测试数据存储系统
test_data_storage() {
    print_test_result "测试数据存储系统"

    echo ""
    echo "测试数据存储系统:"
    echo "================================"

    # 测试数据存储
    local test_data='{
        "task_id": "comprehensive_test_'$(date +%s)'",
        "url": "https://httpbin.org/html",
        "content": "<html><head><title>Comprehensive Test</title></head><body><h1>Test Content</h1></body></html>",
        "title": "Comprehensive Test",
        "crawler_used": "hybrid",
        "processing_time": 0.5,
        "status_code": 200
    }'

    local response=$(curl -s -X POST "$CRAWLER_API_URL/storage/store" \
        -H "Content-Type: application/json" \
        -d "$test_data")

    local data_id=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('data_id', '') if data.get('success') else '')
except:
    print('')
")

    if [ -n "$data_id" ]; then
        print_success "数据存储成功 (ID: $data_id)"

        # 测试数据检索
        response=$(curl -s "$CRAWLER_API_URL/storage/$data_id")
        local retrieved=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(1 if data.get('id') == '$data_id' else 0)
except:
    print(0)
")

        if [ "$retrieved" = "1" ]; then
            print_success "数据检索测试通过"
        else
            print_error "数据检索测试失败"
        fi

        # 测试数据搜索
        response=$(curl -s -X POST "$CRAWLER_API_URL/storage/search" \
            -H "Content-Type: application/json" \
            -d '{"url": "httpbin"}')

        local search_count=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('total', 0))
except:
    print(0)
")

        if [ "$search_count" -gt 0 ]; then
            print_success "数据搜索测试通过 (找到 $search_count 条记录)"
        else
            print_error "数据搜索测试失败"
        fi

    else
        print_error "数据存储失败"
    fi

    # 测试存储统计
    response=$(curl -s "$CRAWLER_API_URL/storage/stats")
    local stats_available=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(1 if 'total_records' in data or 'total_files' in data else 0)
except:
    print(0)
")

    if [ "$stats_available" = "1" ]; then
        print_success "存储统计功能正常"
    else
        print_error "存储统计功能异常"
    fi
}

# 测试监控告警系统
test_monitoring_system() {
    print_test_result "测试监控告警系统"

    echo ""
    echo "测试监控告警系统:"
    echo "================================"

    # 检查Prometheus指标
    if curl -s "$PROMETHEUS_URL/api/v1/query?query=up" | grep -q "result"; then
        print_success "Prometheus API可访问"
    else
        print_warning "Prometheus API不可访问"
    fi

    # 检查爬虫指标
    if curl -s "$CRAWLER_API_URL/metrics" | grep -q "http_requests"; then
        print_success "爬虫服务指标可访问"
    else
        print_warning "爬虫服务指标不可访问"
    fi

    # 检查系统统计
    response=$(curl -s "$CRAWLER_API_URL/stats")
    local stats_available=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(1 if 'task_stats' in data or 'crawler_stats' in data else 0)
except:
    print(0)
")

    if [ "$stats_available" = "1" ]; then
        print_success "系统统计功能正常"
    else
        print_error "系统统计功能异常"
    fi
}

# 测试SSL和安全配置
test_ssl_security() {
    print_test_result "测试SSL和安全配置"

    echo ""
    echo "测试SSL和安全配置:"
    echo "================================"

    # 检查HTTPS访问
    if curl -s -k "$NGINX_URL" | grep -q "Athena"; then
        print_success "HTTPS负载均衡器工作正常"
    else
        print_warning "HTTPS负载均衡器未配置或不可访问"
    fi

    # 检查证书文件
    if [ -f "$PROJECT_ROOT/ssl/crawler.crt" ] && [ -f "$PROJECT_ROOT/ssl/crawler.key" ]; then
        print_success "SSL证书文件存在"
    else
        print_warning "SSL证书文件不存在"
    fi

    # 检查Nginx配置
    if [ -f "$PROJECT_ROOT/nginx/nginx_crawler.conf" ]; then
        print_success "Nginx配置文件存在"
    else
        print_warning "Nginx配置文件不存在"
    fi
}

# 测试文件和目录结构
test_file_structure() {
    print_test_result "测试文件和目录结构"

    echo ""
    echo "检查系统文件结构:"
    echo "================================"

    # 核心目录
    local dirs=(
        "services/crawler/core"
        "services/crawler/api"
        "services/crawler/adapters"
        "services/crawler/config"
        "services/crawler/storage"
        "monitoring"
        "nginx"
        "ssl"
        "scripts"
        "data/crawler"
    )

    for dir in "${dirs[@]}"; do
        if [ -d "$PROJECT_ROOT/$dir" ]; then
            print_success "目录存在: $dir"
        else
            print_warning "目录不存在: $dir"
        fi
    done

    # 核心文件
    local files=(
        "services/crawler/core/universal_crawler.py"
        "services/crawler/core/hybrid_crawler_manager.py"
        "services/crawler/core/batch_processor.py"
        "services/crawler/api/hybrid_crawler_api.py"
        "services/crawler/storage/data_storage_manager.py"
        "monitoring/prometheus.yml"
        "monitoring/crawler_alerts.yml"
        "monitoring/grafana/crawler_dashboard.json"
    )

    for file in "${files[@]}"; do
        if [ -f "$PROJECT_ROOT/$file" ]; then
            print_success "文件存在: $file"
        else
            print_warning "文件不存在: $file"
        fi
    done
}

# 生成测试报告
generate_test_report() {
    echo ""
    echo -e "${PURPLE}========== 测试报告 ==========${NC}"
    echo ""

    echo -e "${CYAN}测试统计:${NC}"
    echo "总测试数: $TOTAL_TESTS"
    echo -e "${GREEN}通过: $PASSED_TESTS${NC}"
    echo -e "${RED}失败: $FAILED_TESTS${NC}"

    local success_rate=0
    if [ $TOTAL_TESTS -gt 0 ]; then
        success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))
    fi

    echo "成功率: ${success_rate}%"
    echo ""

    # 系统状态总结
    echo -e "${CYAN}系统状态总结:${NC}"
    echo "================================"

    if [ $success_rate -ge 80 ]; then
        echo -e "${GREEN}✅ 系统运行状态良好${NC}"
        echo "   - 核心功能正常"
        echo "   - 服务可用性高"
        echo "   - 可投入生产使用"
    elif [ $success_rate -ge 60 ]; then
        echo -e "${YELLOW}⚠️  系统存在部分问题${NC}"
        echo "   - 部分功能异常"
        echo "   - 建议检查失败项"
        echo "   - 可谨慎使用"
    else
        echo -e "${RED}❌ 系统存在严重问题${NC}"
        echo "   - 多项功能异常"
        echo "   - 需要立即修复"
        echo "   - 不建议生产使用"
    fi

    echo ""
    echo -e "${CYAN}关键服务状态:${NC}"
    echo "- 爬虫API: $(curl -s "$CRAWLER_API_URL/health" | grep -q "healthy" && echo "✅ 正常" || echo "❌ 异常")"
    echo "- 批量处理: $(curl -s "$CRAWLER_API_URL/batch/stats" | grep -q "total_tasks" && echo "✅ 正常" || echo "❌ 异常")"
    echo "- 数据存储: $(curl -s "$CRAWLER_API_URL/storage/stats" | grep -q "total_records\|total_files" && echo "✅ 正常" || echo "❌ 异常")"
    echo "- 监控系统: $(curl -s "$PROMETHEUS_URL/api/v1/query?query=up" | grep -q "result" && echo "✅ 正常" || echo "❌ 异常")"

    echo ""
    echo -e "${PURPLE}控制者: $PLATFORM_OWNER${NC}"
}

# 显示帮助信息
show_help() {
    print_banner
    echo -e "${CYAN}用法:${NC} $0 [选项]"
    echo ""
    echo -e "${CYAN}选项:${NC}"
    echo "  -h, --help          显示帮助信息"
    echo "  -q, --quick         快速测试（跳过耗时项）"
    echo "  --services-only     仅测试服务状态"
    echo "  --core-only         仅测试核心功能"
    echo ""
    echo -e "${CYAN}示例:${NC}"
    echo "  $0                  # 运行完整测试"
    echo "  $0 --quick          # 快速测试"
    echo "  $0 --services-only  # 只检查服务状态"
    echo ""
    echo -e "${PURPLE}控制者: $PLATFORM_OWNER${NC}"
}

# 主函数
main() {
    # 解析命令行参数
    QUICK_MODE=false
    SERVICES_ONLY=false
    CORE_ONLY=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -q|--quick)
                QUICK_MODE=true
                shift
                ;;
            --services-only)
                SERVICES_ONLY=true
                shift
                ;;
            --core-only)
                CORE_ONLY=true
                shift
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    # 显示平台标识
    print_banner

    echo -e "${CYAN}开始Athena工作平台综合系统测试...${NC}"
    echo "测试时间: $(date)"
    echo ""

    # 运行测试
    test_service_status

    if [ "$SERVICES_ONLY" = "true" ]; then
        generate_test_report
        exit 0
    fi

    if [ "$CORE_ONLY" = "false" ]; then
        test_file_structure
    fi

    test_crawler_functionality

    if [ "$QUICK_MODE" = "false" ]; then
        test_batch_processing
        test_data_storage
        test_monitoring_system
        test_ssl_security
    fi

    # 生成测试报告
    generate_test_report
}

# 运行主函数
main "$@"