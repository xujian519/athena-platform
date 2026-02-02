#!/bin/bash
# -*- coding: utf-8 -*-
# 批量处理系统测试脚本
# Batch Processing System Test Script - Controlled by Athena & 小诺

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

# 打印平台标识
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    ${PLATFORM_NAME}                       ║"
    echo "║                  批量处理系统测试脚本                        ║"
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
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_platform() {
    echo -e "${PURPLE}[PLATFORM]${NC} $1"
}

# 检查服务状态
check_service_status() {
    print_info "检查爬虫API服务状态..."

    if curl -s "$CRAWLER_API_URL/health" > /dev/null; then
        print_success "爬虫API服务运行正常"
        return 0
    else
        print_error "爬虫API服务未运行"
        return 1
    fi
}

# 启动爬虫API服务
start_crawler_service() {
    print_platform "启动爬虫API服务..."

    # 检查是否已经运行
    if check_service_status; then
        print_info "爬虫API服务已在运行中"
        return 0
    fi

    # 启动服务
    cd "$PROJECT_ROOT/services/crawler"
    export PYTHONPATH="$PROJECT_ROOT/services/crawler:$PYTHONPATH"

    # 后台启动服务
    python3 api/hybrid_crawler_api.py > "$PROJECT_ROOT/logs/crawler_api.log" 2>&1 &
    CRAWLER_PID=$!

    # 等待服务启动
    local count=0
    while [ $count -lt 30 ]; do
        if check_service_status; then
            print_success "爬虫API服务启动成功 (PID: $CRAWLER_PID)"
            echo $CRAWLER_PID > "$PROJECT_ROOT/tmp/crawler_api.pid"
            return 0
        fi
        sleep 2
        ((count++))
    done

    print_error "爬虫API服务启动失败"
    return 1
}

# 停止爬虫API服务
stop_crawler_service() {
    print_platform "停止爬虫API服务..."

    # 查找并终止进程
    if [ -f "$PROJECT_ROOT/tmp/crawler_api.pid" ]; then
        local pid=$(cat "$PROJECT_ROOT/tmp/crawler_api.pid")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            print_success "爬虫API服务已停止 (PID: $pid)"
        fi
        rm -f "$PROJECT_ROOT/tmp/crawler_api.pid"
    fi

    # 强制清理
    pkill -f "hybrid_crawler_api.py" 2>/dev/null || true
}

# 测试创建批量任务
test_create_batch_task() {
    print_platform "测试创建批量任务..."

    # 创建测试URL列表
    local urls='[
        "https://httpbin.org/html",
        "https://httpbin.org/json",
        "https://httpbin.org/robots.txt",
        "https://httpbin.org/delay/1",
        "https://httpbin.org/uuid"
    ]'

    # 发送创建任务请求
    local response=$(curl -s -X POST "$CRAWLER_API_URL/batch/create" \
        -H "Content-Type: application/json" \
        -d "{
            \"name\": \"测试批量任务\",
            \"urls\": $urls,
            \"crawler_type\": \"hybrid\",
            \"priority\": \"normal\",
            \"options\": {
                \"max_concurrent\": 3,
                \"timeout\": 30
            }
        }")

    # 提取任务ID
    local task_id=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('task_id', ''))
except:
    pass
")

    if [ -n "$task_id" ]; then
        print_success "批量任务创建成功 (ID: $task_id)"
        echo "$task_id" > "$PROJECT_ROOT/tmp/test_batch_task_id"
        return 0
    else
        print_error "批量任务创建失败"
        echo "$response"
        return 1
    fi
}

# 测试获取任务状态
test_get_task_status() {
    print_platform "测试获取任务状态..."

    if [ ! -f "$PROJECT_ROOT/tmp/test_batch_task_id" ]; then
        print_error "测试任务ID不存在"
        return 1
    fi

    local task_id=$(cat "$PROJECT_ROOT/tmp/test_batch_task_id")
    local response=$(curl -s "$CRAWLER_API_URL/batch/$task_id/status")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    status = data.get('status', 'unknown')
    progress = data.get('progress', 0)
    total_urls = data.get('total_urls', 0)
    processed_urls = data.get('processed_urls', 0)
    print(f'任务状态: {status}')
    print(f'进度: {progress}% ({processed_urls}/{total_urls})')
    print(f'创建时间: {data.get(\"created_at\", \"N/A\")}')
except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 测试获取任务结果
test_get_task_results() {
    print_platform "测试获取任务结果..."

    if [ ! -f "$PROJECT_ROOT/tmp/test_batch_task_id" ]; then
        print_error "测试任务ID不存在"
        return 1
    fi

    local task_id=$(cat "$PROJECT_ROOT/tmp/test_batch_task_id")
    local response=$(curl -s "$CRAWLER_API_URL/batch/$task_id/results")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    status = data.get('status', 'unknown')
    total_count = data.get('total_count', 0)
    success_count = data.get('success_count', 0)
    error_count = data.get('error_count', 0)
    cost = data.get('cost', 0.0)

    print(f'任务状态: {status}')
    print(f'总数量: {total_count}')
    print(f'成功: {success_count}')
    print(f'失败: {error_count}')
    print(f'成本: \${cost:.4f}')

    if status == 'completed' and 'results' in data:
        print()
        print('结果摘要:')
        for i, result in enumerate(data['results'][:3]):  # 只显示前3个结果
            url = result.get('url', 'N/A')
            success = result.get('success', False)
            crawler_type = result.get('crawler_type', 'N/A')
            print(f'  {i+1}. {url} - {crawler_type} - {\"成功\" if success else \"失败\"}')

        if len(data['results']) > 3:
            print(f'  ... 还有 {len(data[\"results\"]) - 3} 个结果')
except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 测试批量统计
test_batch_stats() {
    print_platform "测试批量处理统计..."

    local response=$(curl -s "$CRAWLER_API_URL/batch/stats")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)

    print('批量处理统计:')
    print(f'  总任务数: {data.get(\"total_tasks\", 0)}')
    print(f'  已完成: {data.get(\"completed_tasks\", 0)}')
    print(f'  失败: {data.get(\"failed_tasks\", 0)}')
    print(f'  等待中: {data.get(\"pending_tasks\", 0)}')
    print(f'  运行中: {data.get(\"running_tasks\", 0)}')
    print(f'  总URL数: {data.get(\"total_urls\", 0)}')
    print(f'  已处理URL: {data.get(\"processed_urls\", 0)}')
    print(f'  总成本: \${data.get(\"total_cost\", 0.0):.4f}')
    print(f'  平均成本/任务: \${data.get(\"average_cost_per_task\", 0.0):.4f}')
    print(f'  成功率: {data.get(\"success_rate\", 0.0):.1%}')
except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 测试健康检查
test_health_check() {
    print_platform "测试健康检查..."

    local response=$(curl -s "$CRAWLER_API_URL/health")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)

    print('系统健康状态:')
    print(f'  状态: {data.get(\"status\", \"unknown\")}')
    print(f'  版本: {data.get(\"version\", \"unknown\")}')
    print(f'  时间戳: {data.get(\"timestamp\", \"N/A\")}')

    # 爬虫状态
    if 'crawler_status' in data:
        print()
        print('爬虫状态:')
        for crawler, status in data['crawler_status'].items():
            print(f'  {crawler}: {status}')

    # 批量处理器状态
    if 'batch_processor' in data:
        print()
        print('批量处理器状态:')
        batch_info = data['batch_processor']
        print(f'  状态: {batch_info.get(\"status\", \"unknown\")}')

        if 'stats' in batch_info:
            stats = batch_info['stats']
            print(f'  总任务: {stats.get(\"total_tasks\", 0)}')
            print(f'  已完成: {stats.get(\"completed_tasks\", 0)}')

    # 配置验证
    if 'config_validated' in data:
        print()
        print(f'配置验证: {\"通过\" if data[\"config_validated\"] else \"失败\"}')

except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 等待任务完成
wait_for_task_completion() {
    if [ ! -f "$PROJECT_ROOT/tmp/test_batch_task_id" ]; then
        print_error "测试任务ID不存在"
        return 1
    fi

    local task_id=$(cat "$PROJECT_ROOT/tmp/test_batch_task_id")
    local timeout=300  # 5分钟超时
    local elapsed=0

    print_info "等待任务完成 (超时: ${timeout}s)..."

    while [ $elapsed -lt $timeout ]; do
        local response=$(curl -s "$CRAWLER_API_URL/batch/$task_id/status")
        local status=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('status', 'unknown'))
except:
    print('error')
")

        if [ "$status" = "completed" ]; then
            print_success "任务已完成"
            return 0
        elif [ "$status" = "failed" ]; then
            print_error "任务失败"
            return 1
        elif [ "$status" = "error" ] || [ "$status" = "unknown" ]; then
            print_error "获取任务状态失败"
            return 1
        fi

        # 显示进度
        local progress=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('progress', 0))
except:
    print(0)
")
        echo -ne "\r进度: ${progress}% (${elapsed}s)"

        sleep 5
        elapsed=$((elapsed + 5))
    done

    print_error "任务执行超时"
    return 1
}

# 清理测试文件
cleanup() {
    print_info "清理测试文件..."
    rm -f "$PROJECT_ROOT/tmp/test_batch_task_id"
    rm -f "$PROJECT_ROOT/tmp/crawler_api.pid"
}

# 显示使用帮助
show_help() {
    print_banner
    echo -e "${CYAN}用法:${NC} $0 [命令]"
    echo ""
    echo -e "${CYAN}命令:${NC}"
    echo "  start              启动服务并运行完整测试"
    echo "  status             显示当前任务状态"
    echo "  results            显示任务结果"
    echo "  stats              显示批量处理统计"
    echo "  health             显示系统健康状态"
    echo "  stop               停止服务"
    echo "  cleanup            清理测试文件"
    echo ""
    echo -e "${CYAN}示例:${NC}"
    echo "  $0 start           # 运行完整测试流程"
    echo "  $0 status          # 查看任务状态"
    echo "  $0 results         # 查看任务结果"
    echo ""
    echo -e "${PURPLE}控制者: $PLATFORM_OWNER${NC}"
}

# 主函数
main() {
    # 检查参数
    if [[ $# -eq 0 ]]; then
        show_help
        exit 1
    fi

    # 显示平台标识
    print_banner

    # 创建必要目录
    mkdir -p "$PROJECT_ROOT/tmp"
    mkdir -p "$PROJECT_ROOT/logs"

    # 解析命令
    case "$1" in
        start)
            print_platform "开始批量处理系统完整测试"

            # 启动服务
            if ! start_crawler_service; then
                print_error "启动服务失败"
                exit 1
            fi

            # 等待服务稳定
            sleep 3

            # 运行测试
            print_platform "开始功能测试"
            echo ""

            # 创建任务
            if test_create_batch_task; then
                echo ""

                # 等待任务完成
                if wait_for_task_completion; then
                    echo ""

                    # 显示结果
                    test_get_task_results
                    echo ""

                    # 显示统计
                    test_batch_stats
                fi
            fi

            echo ""
            print_success "批量处理系统测试完成"
            ;;

        status)
            test_get_task_status
            ;;

        results)
            test_get_task_results
            ;;

        stats)
            test_batch_stats
            ;;

        health)
            test_health_check
            ;;

        stop)
            stop_crawler_service
            print_success "服务已停止"
            ;;

        cleanup)
            cleanup
            print_success "测试文件已清理"
            ;;

        -h|--help)
            show_help
            ;;

        *)
            print_error "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"