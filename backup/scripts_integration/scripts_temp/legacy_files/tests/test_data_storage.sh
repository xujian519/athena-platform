#!/bin/bash
# -*- coding: utf-8 -*-
# 数据存储系统测试脚本
# Data Storage System Test Script - Controlled by Athena & 小诺

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
    echo "║                  数据存储系统测试脚本                        ║"
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

# 测试数据存储
test_data_storage() {
    print_platform "测试数据存储功能..."

    # 创建测试数据
    local test_data='{
        "task_id": "test_'$(date +%s)'",
        "url": "https://httpbin.org/html",
        "content": "<html><head><title>Test Page</title></head><body><h1>Test Content</h1></body></html>",
        "title": "Test Page",
        "crawler_used": "hybrid",
        "processing_time": 1.23,
        "status_code": 200,
        "links": ["https://httpbin.org"],
        "images": ["https://httpbin.org/image"],
        "extracted_data": {"title": "Test Page", "headings": ["Test Content"]}
    }'

    # 发送存储请求
    local response=$(curl -s -X POST "$CRAWLER_API_URL/storage/store" \
        -H "Content-Type: application/json" \
        -d "$test_data")

    # 提取数据ID
    local data_id=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('success'):
        print(data.get('data_id', ''))
except:
    pass
")

    if [ -n "$data_id" ]; then
        print_success "数据存储成功 (ID: $data_id)"
        echo "$data_id" > "$PROJECT_ROOT/tmp/test_storage_data_id"
        return 0
    else
        print_error "数据存储失败"
        echo "$response"
        return 1
    fi
}

# 测试数据检索
test_data_retrieval() {
    print_platform "测试数据检索功能..."

    if [ ! -f "$PROJECT_ROOT/tmp/test_storage_data_id" ]; then
        print_error "测试数据ID不存在"
        return 1
    fi

    local data_id=$(cat "$PROJECT_ROOT/tmp/test_storage_data_id")
    local response=$(curl -s "$CRAWLER_API_URL/storage/$data_id")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'数据ID: {data.get(\"id\", \"N/A\")}')
    print(f'URL: {data.get(\"url\", \"N/A\")}')
    print(f'爬虫类型: {data.get(\"crawler_type\", \"N/A\")}')
    print(f'时间戳: {data.get(\"timestamp\", \"N/A\")}')
    print(f'内容大小: {data.get(\"size\", 0)} bytes')
    print(f'压缩大小: {data.get(\"compressed_size\", \"N/A\")} bytes')
    print(f'标题: {data.get(\"metadata\", {}).get(\"title\", \"N/A\")}')
except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 测试数据搜索
test_data_search() {
    print_platform "测试数据搜索功能..."

    # 创建搜索查询
    local query='{
        "url": "httpbin",
        "crawler_type": "hybrid"
    }'

    local response=$(curl -s -X POST "$CRAWLER_API_URL/storage/search" \
        -H "Content-Type: application/json" \
        -d "$query")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    total = data.get('total', 0)
    print(f'搜索结果: {total} 条记录')

    results = data.get('results', [])
    for i, result in enumerate(results[:3]):  # 只显示前3个结果
        print(f'  {i+1}. {result.get(\"url\", \"N/A\")} - {result.get(\"crawler_type\", \"N/A\")}')

    if total > 3:
        print(f'  ... 还有 {total - 3} 条结果')
except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 测试存储统计
test_storage_stats() {
    print_platform "测试存储统计功能..."

    local response=$(curl -s "$CRAWLER_API_URL/storage/stats")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)

    print('存储统计:')
    if 'total_records' in data:
        print(f'  总记录数: {data.get(\"total_records\", 0)}')
        print(f'  总大小: {data.get(\"total_size_bytes\", 0)} bytes')
        print(f'  压缩大小: {data.get(\"compressed_size_bytes\", 0)} bytes')
        print(f'  压缩比: {data.get(\"compression_ratio\", 0):.2%}')

    if 'by_crawler_type' in data:
        print()
        print('按爬虫类型统计:')
        for crawler_type, stats in data['by_crawler_type'].items():
            print(f'  {crawler_type}: {stats.get(\"count\", 0)} 条, {stats.get(\"size\", 0)} bytes')

    if 'daily_counts' in data:
        print()
        print('最近7天统计:')
        for date, count in data['daily_counts'].items():
            print(f'  {date}: {count} 条')

    if 'config' in data:
        print()
        print('配置信息:')
        config = data['config']
        print(f'  存储类型: {config.get(\"storage_type\", \"N/A\")}')
        print(f'  压缩方式: {config.get(\"compression\", \"N/A\")}')
        print(f'  保留天数: {config.get(\"retention_days\", \"N/A\")}')

except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 测试数据导出
test_data_export() {
    print_platform "测试数据导出功能..."

    # 创建导出查询
    local query='{
        "crawler_type": "hybrid"
    }'

    local response=$(curl -s -X POST "$CRAWLER_API_URL/storage/export?format=json" \
        -H "Content-Type: application/json" \
        -d "$query")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'导出完成:')
    print(f'  文件名: {data.get(\"filename\", \"N/A\")}')
    print(f'  文件路径: {data.get(\"file_path\", \"N/A\")}')
    print(f'  文件大小: {data.get(\"size\", 0)} bytes')
    print(f'  记录数量: {data.get(\"record_count\", 0)}')
except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 测试数据清理
test_data_cleanup() {
    print_platform "测试数据清理功能..."

    local response=$(curl -s -X POST "$CRAWLER_API_URL/storage/cleanup?days=365")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'清理结果:')
    print(f'  消息: {data.get(\"message\", \"N/A\")}')
    print(f'  保留天数: {data.get(\"retention_days\", \"N/A\")}')
    print(f'  删除数量: {data.get(\"deleted_count\", 0)}')
except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 测试数据删除
test_data_deletion() {
    print_platform "测试数据删除功能..."

    if [ ! -f "$PROJECT_ROOT/tmp/test_storage_data_id" ]; then
        print_error "测试数据ID不存在"
        return 1
    fi

    local data_id=$(cat "$PROJECT_ROOT/tmp/test_storage_data_id")
    local response=$(curl -s -X DELETE "$CRAWLER_API_URL/storage/$data_id")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'删除结果: {data.get(\"message\", \"N/A\")}')
except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 测试爬取结果自动存储
test_auto_storage() {
    print_platform "测试爬取结果自动存储..."

    # 创建简单的爬取请求
    local crawl_request='{
        "urls": ["https://httpbin.org/html"],
        "strategy": "auto",
        "max_concurrent": 1,
        "background": false
    }'

    local response=$(curl -s -X POST "$CRAWLER_API_URL/crawl" \
        -H "Content-Type: application/json" \
        -d "$crawl_request")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    status = data.get('status', 'unknown')
    results = data.get('results', [])

    print(f'爬取状态: {status}')
    print(f'结果数量: {len(results)}')

    if status == 'completed' and results:
        print()
        print('第一个结果摘要:')
        result = results[0]
        print(f'  URL: {result.get(\"url\", \"N/A\")}')
        print(f'  成功: {result.get(\"success\", False)}')
        print(f'  爬虫类型: {result.get(\"crawler_used\", \"N/A\")}')
        print(f'  内容长度: {result.get(\"content_length\", 0)}')
        print()
        print('注意: 成功的爬取结果应已自动存储到数据库中')
except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 测试健康检查中的存储状态
test_storage_in_health() {
    print_platform "测试健康检查中的存储状态..."

    local response=$(curl -s "$CRAWLER_API_URL/health")

    echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)

    print('系统健康状态:')
    print(f'  整体状态: {data.get(\"status\", \"unknown\")}')
    print(f'  版本: {data.get(\"version\", \"unknown\")}')

    if 'data_storage' in data:
        print()
        print('数据存储状态:')
        storage = data['data_storage']
        if 'error' in storage:
            print(f'  错误: {storage[\"error\"]}')
        else:
            if 'total_records' in storage:
                print(f'  总记录数: {storage.get(\"total_records\", 0)}')
            if 'total_size_bytes' in storage:
                print(f'  总大小: {storage.get(\"total_size_bytes\", 0)} bytes')
            if 'config' in storage:
                config = storage['config']
                print(f'  存储类型: {config.get(\"storage_type\", \"N/A\")}')
                print(f'  压缩方式: {config.get(\"compression\", \"N/A\")}')

except Exception as e:
    print(f'解析响应失败: {e}')
    print('原始响应:', sys.stdin.read())
"
}

# 清理测试文件
cleanup() {
    print_info "清理测试文件..."
    rm -f "$PROJECT_ROOT/tmp/test_storage_data_id"
}

# 显示使用帮助
show_help() {
    print_banner
    echo -e "${CYAN}用法:${NC} $0 [命令]"
    echo ""
    echo -e "${CYAN}命令:${NC}"
    echo "  all                运行所有存储功能测试"
    echo "  store              测试数据存储"
    echo "  retrieve           测试数据检索"
    echo "  search             测试数据搜索"
    echo "  stats              测试存储统计"
    echo "  export             测试数据导出"
    echo "  cleanup            测试数据清理"
    echo "  delete             测试数据删除"
    echo "  auto               测试自动存储"
    echo "  health             查看健康检查中的存储状态"
    echo "  cleanup-files      清理测试文件"
    echo ""
    echo -e "${CYAN}示例:${NC}"
    echo "  $0 all              # 运行完整测试"
    echo "  $0 store            # 只测试存储功能"
    echo "  $0 stats            # 查看存储统计"
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

    # 检查服务状态
    if ! check_service_status; then
        print_error "请先启动爬虫API服务"
        exit 1
    fi

    # 等待服务稳定
    sleep 2

    # 解析命令
    case "$1" in
        all)
            print_platform "开始数据存储系统完整测试"
            echo ""

            # 存储测试数据
            if test_data_storage; then
                echo ""

                # 测试检索
                test_data_retrieval
                echo ""

                # 测试搜索
                test_data_search
                echo ""

                # 测试统计
                test_storage_stats
                echo ""

                # 测试导出
                test_data_export
                echo ""

                # 测试自动存储
                test_auto_storage
                echo ""

                # 测试健康检查
                test_storage_in_health
                echo ""

                # 测试删除
                test_data_deletion
                echo ""

                # 测试清理
                test_data_cleanup
            fi

            echo ""
            print_success "数据存储系统测试完成"
            ;;

        store)
            test_data_storage
            ;;

        retrieve)
            test_data_retrieval
            ;;

        search)
            test_data_search
            ;;

        stats)
            test_storage_stats
            ;;

        export)
            test_data_export
            ;;

        cleanup)
            test_data_cleanup
            ;;

        delete)
            test_data_deletion
            ;;

        auto)
            test_auto_storage
            ;;

        health)
            test_storage_in_health
            ;;

        cleanup-files)
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