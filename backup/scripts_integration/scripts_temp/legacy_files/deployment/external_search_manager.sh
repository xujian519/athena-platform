#!/bin/bash
# -*- coding: utf-8 -*-
# Athena外部搜索引擎平台管理脚本
# Athena External Search Engine Platform Management Script
# 控制者: 小诺 & Athena

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目信息
PLATFORM_NAME="Athena外部搜索引擎平台"
PLATFORM_VERSION="1.0.0"
CONTROLLERS="小诺 & Athena"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 工具路径
EXTERNAL_SEARCH_PLATFORM_TOOL="$PROJECT_ROOT/tools/search/external_search_platform.py"
EXTERNAL_SEARCH_CLI_TOOL="$PROJECT_ROOT/tools/cli/search/external_search_cli.py"

# 打印平台标识
print_banner() {
    echo -e "${PURPLE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                  ${PLATFORM_NAME}                        ║"
    echo "║                管理脚本 v${PLATFORM_VERSION}                       ║"
    echo "║                    控制者: ${CONTROLLERS}                       ║"
    echo "╚════════════════════════════════════════════════════════════╝"
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

# 检查工具是否存在
check_tools() {
    if [[ ! -f "$EXTERNAL_SEARCH_PLATFORM_TOOL" ]]; then
        print_error "外部搜索平台工具不存在: $EXTERNAL_SEARCH_PLATFORM_TOOL"
        return 1
    fi

    if [[ ! -f "$EXTERNAL_SEARCH_CLI_TOOL" ]]; then
        print_error "外部搜索CLI工具不存在: $EXTERNAL_SEARCH_CLI_TOOL"
        return 1
    fi

    print_success "外部搜索工具检查通过"
    return 0
}

# 单引擎搜索功能
single_engine_search() {
    local query="$1"
    local engine="${2:-tavily}"
    local max_results="${3:-10}"

    print_platform "执行单引擎搜索: '$query' (引擎: $engine)"

    python3 "$EXTERNAL_SEARCH_CLI_TOOL" search "$query" --engine "$engine" --max-results "$max_results"
}

# 多引擎搜索功能
multi_engine_search() {
    local query="$1"
    local engines="${2:-tavily,metaso}"
    local max_results="${3:-10}"

    print_platform "执行多引擎搜索: '$query' (引擎: $engines)"

    python3 "$EXTERNAL_SEARCH_CLI_TOOL" multi "$query" --engines "$engines" --max-results "$max_results"
}

# 智能搜索功能
smart_search() {
    local query="$1"
    local optimize="${2:-relevance}"
    local max_results="${3:-10}"

    print_platform "执行智能搜索: '$query' (优化: $optimize)"

    python3 "$EXTERNAL_SEARCH_CLI_TOOL" smart "$query" --optimize "$optimize" --max-results "$max_results"
}

# 全面搜索功能
comprehensive_search() {
    local query="$1"
    local max_results="${2:-15}"

    print_platform "执行全面搜索: '$query'"

    python3 "$EXTERNAL_SEARCH_CLI_TOOL" comprehensive "$query" --max-results "$max_results"
}

# 平台状态检查
platform_status() {
    print_platform "检查外部搜索平台状态"

    python3 "$EXTERNAL_SEARCH_CLI_TOOL" status --verbose
}

# 显示使用手册
show_manual() {
    print_platform "显示外部搜索平台用户手册"

    python3 "$EXTERNAL_SEARCH_CLI_TOOL" manual --verbose
}

# 交互式搜索
interactive_search() {
    print_platform "进入交互式搜索模式"

    while true; do
        echo
        echo -e "${CYAN}Athena外部搜索平台 - 交互式模式${NC}"
        echo "1. 单引擎搜索"
        echo "2. 多引擎搜索"
        echo "3. 智能搜索"
        echo "4. 全面搜索"
        echo "5. 平台状态"
        echo "6. 使用手册"
        echo "7. 测试引擎"
        echo "8. 退出"
        echo
        read -p "请选择功能 (1-8): " choice

        case $choice in
            1)
                read -p "请输入搜索查询: " query
                echo "选择搜索引擎:"
                echo "  1) tavily (推荐)"
                echo "  2) bocha (中文优化)"
                echo "  3) metaso (AI增强)"
                read -p "请选择搜索引擎 (1-3, 默认1): " engine_choice

                case $engine_choice in
                    1) engine="tavily" ;;
                    2) engine="bocha" ;;
                    3) engine="metaso" ;;
                    *) engine="tavily" ;;
                esac

                read -p "最大结果数 (默认10): " max_results
                max_results=${max_results:-10}
                single_engine_search "$query" "$engine" "$max_results"
                ;;
            2)
                read -p "请输入搜索查询: " query
                echo "可用搜索引擎: tavily, bocha, metaso"
                read -p "请输入搜索引擎列表，逗号分隔 (默认: tavily,metaso): " engines
                engines=${engines:-"tavily,metaso"}
                read -p "最大结果数 (默认10): " max_results
                max_results=${max_results:-10}
                multi_engine_search "$query" "$engines" "$max_results"
                ;;
            3)
                read -p "请输入搜索查询: " query
                echo "优化目标选择:"
                echo "  1) relevance (相关性)"
                echo "  2) speed (速度)"
                echo "  3) completeness (完整性)"
                read -p "请选择优化目标 (1-3, 默认1): " optimize_choice

                case $optimize_choice in
                    1) optimize="relevance" ;;
                    2) optimize="speed" ;;
                    3) optimize="completeness" ;;
                    *) optimize="relevance" ;;
                esac

                read -p "最大结果数 (默认10): " max_results
                max_results=${max_results:-10}
                smart_search "$query" "$optimize" "$max_results"
                ;;
            4)
                read -p "请输入搜索查询: " query
                read -p "最大结果数 (默认15): " max_results
                max_results=${max_results:-15}
                comprehensive_search "$query" "$max_results"
                ;;
            5)
                platform_status
                ;;
            6)
                show_manual
                ;;
            7)
                test_engines
                ;;
            8)
                print_success "退出交互式搜索模式"
                break
                ;;
            *)
                print_error "无效选择，请输入1-8"
                ;;
        esac
    done
}

# 引擎测试
test_engines() {
    print_platform "测试外部搜索引擎"

    python3 "$EXTERNAL_SEARCH_CLI_TOOL" test
}

# 引擎性能对比
compare_engines() {
    local query="$1"

    print_platform "搜索引擎性能对比: '$query'"

    echo "🔄 开始性能对比测试..."
    echo "查询: '$query'"
    echo "测试引擎: tavily, metaso"
    echo "=" * 50

    # 测试Tavily
    echo -e "\n🔍 测试Tavily搜索引擎:"
    start_time=$(date +%s.%N)
    tavily_result=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
import asyncio
from tools.search.external_search_platform import ExternalSearchPlatform

async def test():
    platform = ExternalSearchPlatform()
    await platform.initialize()
    result = await platform.search_with_engine('$query', 'tavily', max_results=5)
    print(f'SUCCESS:{result.get(\"success\", False)}')
    print(f'TIME:{result.get(\"search_time\", 0):.2f}')
    print(f'COUNT:{len(result.get(\"results\", []))}')

asyncio.run(test())
" 2>/dev/null)
    end_time=$(date +%s.%N)
    tavily_time=$(echo "$end_time - $start_time" | bc)

    tavily_success=$(echo "$tavily_result" | grep "SUCCESS:" | cut -d: -f2)
    tavily_engine_time=$(echo "$tavily_result" | grep "TIME:" | cut -d: -f2)
    tavily_count=$(echo "$tavily_result" | grep "COUNT:" | cut -d: -f2)

    echo "状态: $tavily_success"
    echo "搜索耗时: ${tavily_engine_time}秒"
    echo "结果数量: $tavily_count"
    echo "总耗时: ${tavily_time}秒"

    # 测试秘塔
    echo -e "\n🔍 测试秘塔搜索引擎:"
    start_time=$(date +%s.%N)
    metaso_result=$(python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
import asyncio
from tools.search.external_search_platform import ExternalSearchPlatform

async def test():
    platform = ExternalSearchPlatform()
    await platform.initialize()
    result = await platform.search_with_engine('$query', 'metaso', max_results=5)
    print(f'SUCCESS:{result.get(\"success\", False)}')
    print(f'TIME:{result.get(\"search_time\", 0):.2f}')
    print(f'COUNT:{len(result.get(\"results\", []))}')

asyncio.run(test())
" 2>/dev/null)
    end_time=$(date +%s.%N)
    metaso_time=$(echo "$end_time - $start_time" | bc)

    metaso_success=$(echo "$metaso_result" | grep "SUCCESS:" | cut -d: -f2)
    metaso_engine_time=$(echo "$metaso_result" | grep "TIME:" | cut -d: -f2)
    metaso_count=$(echo "$metaso_result" | grep "COUNT:" | cut -d: -f2)

    echo "状态: $metaso_success"
    echo "搜索耗时: ${metaso_engine_time}秒"
    echo "结果数量: $metaso_count"
    echo "总耗时: ${metaso_time}秒"

    # 总结
    echo -e "\n📊 性能对比总结:"
    echo "================================"
    printf "%-15s %-10s %-10s %-10s %-10s\n" "引擎" "状态" "搜索耗时" "结果数" "总耗时"
    printf "%-15s %-10s %-10s %-10s %-10s\n" "Tavily" "$tavily_success" "${tavily_engine_time}s" "$tavily_count" "${tavily_time}s"
    printf "%-15s %-10s %-10s %-10s %-10s\n" "Metaso" "$metaso_success" "${metaso_engine_time}s" "$metaso_count" "${metaso_time}s"
}

# 显示帮助信息
show_help() {
    print_banner
    echo -e "${CYAN}用法:${NC} $0 [命令] [参数]"
    echo ""
    echo -e "${CYAN}命令:${NC}"
    echo "  search <query> [engine] [max_results]        - 执行单引擎搜索"
    echo "  multi <query> [engines] [max_results]         - 执行多引擎搜索"
    echo "  smart <query> [optimize] [max_results]        - 执行智能搜索"
    echo "  comprehensive <query> [max_results]             - 执行全面搜索"
    echo "  compare <query>                                - 搜索引擎性能对比"
    echo "  status                                         - 检查平台状态"
    echo "  manual                                         - 显示使用手册"
    echo "  interactive                                    - 进入交互式模式"
    echo "  test                                           - 测试搜索引擎功能"
    echo "  help                                           - 显示此帮助信息"
    echo ""
    echo -e "${CYAN}示例:${NC}"
    echo "  $0 search '人工智能' tavily 10"
    echo "  $0 multi '机器学习' 'tavily,metaso' 15"
    echo "  $0 smart '深度学习' relevance 10"
    echo "  $0 comprehensive '大数据分析' 20"
    echo "  $0 compare '人工智能最新发展'"
    echo "  $0 interactive"
    echo ""
    echo -e "${CYAN}搜索引擎选项:${NC}"
    echo "  tavily     - 全球AI搜索引擎，快速准确"
    echo "  bocha      - AI优化的中文搜索引擎"
    echo "  metaso     - 中国版Perplexity，智能AI搜索"
    echo ""
    echo -e "${PURPLE}控制者: $CONTROLLERS${NC}"
}

# 主函数
main() {
    local command="$1"
    shift || true

    case "$command" in
        search|s)
            if [[ $# -lt 1 ]]; then
                print_error "请提供搜索查询"
                echo "用法: $0 search <query> [engine] [max_results]"
                exit 1
            fi
            single_engine_search "$@"
            ;;
        multi|m)
            if [[ $# -lt 1 ]]; then
                print_error "请提供搜索查询"
                echo "用法: $0 multi <query> [engines] [max_results]"
                exit 1
            fi
            multi_engine_search "$@"
            ;;
        smart)
            if [[ $# -lt 1 ]]; then
                print_error "请提供搜索查询"
                echo "用法: $0 smart <query> [optimize] [max_results]"
                exit 1
            fi
            smart_search "$@"
            ;;
        comprehensive|comp)
            if [[ $# -lt 1 ]]; then
                print_error "请提供搜索查询"
                echo "用法: $0 comprehensive <query> [max_results]"
                exit 1
            fi
            comprehensive_search "$@"
            ;;
        compare|c)
            if [[ $# -lt 1 ]]; then
                print_error "请提供搜索查询"
                echo "用法: $0 compare <query>"
                exit 1
            fi
            compare_engines "$1"
            ;;
        status|st)
            platform_status
            ;;
        manual|man)
            show_manual
            ;;
        interactive|i)
            interactive_search
            ;;
        test|t)
            test_engines
            ;;
        help|h|--help|-h)
            show_help
            ;;
        "")
            print_error "请提供命令"
            show_help
            exit 1
            ;;
        *)
            print_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"