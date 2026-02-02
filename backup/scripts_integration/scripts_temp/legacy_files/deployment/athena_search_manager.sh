#!/bin/bash
# -*- coding: utf-8 -*-
# Athena搜索平台管理脚本
# Athena Search Platform Management Script
# 控制者: 小诺 & 小娜

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
PLATFORM_NAME="Athena搜索平台"
PLATFORM_VERSION="1.0.0"
CONTROLLERS="小诺 & 小娜"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 工具路径
SEARCH_PLATFORM_TOOL="$PROJECT_ROOT/tools/search/athena_search_platform.py"
SEARCH_CLI_TOOL="$PROJECT_ROOT/tools/cli/search/athena_search_cli.py"

# 打印平台标识
print_banner() {
    echo -e "${PURPLE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                    ${PLATFORM_NAME}                         ║"
    echo "║                  管理脚本 v${PLATFORM_VERSION}                       ║"
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
    if [[ ! -f "$SEARCH_PLATFORM_TOOL" ]]; then
        print_error "搜索平台工具不存在: $SEARCH_PLATFORM_TOOL"
        return 1
    fi

    if [[ ! -f "$SEARCH_CLI_TOOL" ]]; then
        print_error "搜索CLI工具不存在: $SEARCH_CLI_TOOL"
        return 1
    fi

    print_success "搜索工具检查通过"
    return 0
}

# 快速搜索功能
quick_search() {
    local query="$1"
    local max_results="${2:-10}"

    print_platform "执行快速搜索: '$query'"

    python3 "$SEARCH_CLI_TOOL" search "$query" --quick --max-results "$max_results"
}

# 智能专利研究
patent_research() {
    local topic="$1"
    local depth="${2:-comprehensive}"

    print_platform "执行专利研究: '$topic' (深度: $depth)"

    python3 "$SEARCH_CLI_TOOL" research "$topic" --depth "$depth"
}

# 竞争分析
competitive_analysis() {
    local company="$1"
    local domain="$2"

    local cmd_args="$company"
    if [[ -n "$domain" ]]; then
        cmd_args="$cmd_args --domain \"$domain\""
    fi

    print_platform "执行竞争分析: '$company'"

    python3 "$SEARCH_CLI_TOOL" analysis $cmd_args
}

# 平台状态检查
platform_status() {
    print_platform "检查平台状态"

    python3 "$SEARCH_CLI_TOOL" status --verbose
}

# 显示使用手册
show_manual() {
    print_platform "显示用户手册"

    python3 "$SEARCH_CLI_TOOL" manual --verbose
}

# 交互式搜索
interactive_search() {
    print_platform "进入交互式搜索模式"

    while true; do
        echo
        echo -e "${CYAN}Athena搜索平台 - 交互式模式${NC}"
        echo "1. 简单搜索"
        echo "2. 专利研究"
        echo "3. 竞争分析"
        echo "4. 平台状态"
        echo "5. 使用手册"
        echo "6. 退出"
        echo
        read -p "请选择功能 (1-6): " choice

        case $choice in
            1)
                read -p "请输入搜索查询: " query
                read -p "最大结果数 (默认10): " max_results
                max_results=${max_results:-10}
                quick_search "$query" "$max_results"
                ;;
            2)
                read -p "请输入研究主题: " topic
                echo "搜索深度选择:"
                echo "  1) quick (快速)"
                echo "  2) standard (标准)"
                echo "  3) comprehensive (全面)"
                echo "  4) deep (深度)"
                read -p "请选择深度 (1-4, 默认3): " depth_choice

                case $depth_choice in
                    1) depth="quick" ;;
                    2) depth="standard" ;;
                    3) depth="comprehensive" ;;
                    4) depth="deep" ;;
                    *) depth="comprehensive" ;;
                esac

                patent_research "$topic" "$depth"
                ;;
            3)
                read -p "请输入公司名称: " company
                read -p "请输入技术领域 (可选): " domain
                competitive_analysis "$company" "$domain"
                ;;
            4)
                platform_status
                ;;
            5)
                show_manual
                ;;
            6)
                print_success "退出交互式搜索模式"
                break
                ;;
            *)
                print_error "无效选择，请输入1-6"
                ;;
        esac
    done
}

# 工具测试
test_tools() {
    print_platform "执行搜索工具测试"

    echo
    print_info "1. 测试工具导入..."
    python3 -c "
import sys
sys.path.insert(0, '$PROJECT_ROOT')
from tools.search.athena_search_platform import AthenaSearchPlatform, quick_search
print('✅ 搜索平台工具导入成功')
"

    echo
    print_info "2. 测试平台实例化..."
    python3 -c "
import sys
import asyncio
sys.path.insert(0, '$PROJECT_ROOT')

async def test():
    from tools.search.athena_search_platform import get_search_platform
    platform = get_search_platform()
    print('✅ 平台实例化成功')
    print(f'版本: {platform.version}')
    print(f'控制者: {platform.controllers}')

asyncio.run(test())
"

    echo
    print_info "3. 测试CLI工具..."
    if python3 "$SEARCH_CLI_TOOL" --version > /dev/null 2>&1; then
        print_success "CLI工具版本检查通过"
    else
        print_error "CLI工具版本检查失败"
        return 1
    fi

    echo
    print_success "所有工具测试通过！"
}

# 安装和设置
setup() {
    print_platform "设置Athena搜索平台"

    # 检查Python环境
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 未安装"
        return 1
    fi

    # 检查项目结构
    if [[ ! -d "$PROJECT_ROOT/tools/search" ]]; then
        print_error "搜索工具目录不存在"
        return 1
    fi

    # 创建符号链接（可选）
    local bin_dir="$HOME/.local/bin"
    if [[ -d "$bin_dir" ]]; then
        local symlink_target="$bin_dir/athena-search"
        if [[ ! -L "$symlink_target" ]]; then
            ln -sf "$SEARCH_CLI_TOOL" "$symlink_target"
            print_success "创建命令行快捷方式: $symlink_target"
            print_info "现在可以直接使用 'athena-search' 命令"
        fi
    fi

    # 执行工具测试
    test_tools

    print_success "Athena搜索平台设置完成！"
}

# 显示帮助信息
show_help() {
    print_banner
    echo -e "${CYAN}用法:${NC} $0 [命令] [参数]"
    echo ""
    echo -e "${CYAN}命令:${NC}"
    echo "  search <query> [max_results]        - 执行快速搜索"
    echo "  research <topic> [depth]            - 执行专利研究"
    echo "  analysis <company> [domain]         - 执行竞争分析"
    echo "  status                              - 检查平台状态"
    echo "  manual                              - 显示使用手册"
    echo "  interactive                         - 进入交互式模式"
    echo "  test                                - 测试工具功能"
    echo "  setup                               - 初始化设置"
    echo "  help                                - 显示此帮助信息"
    echo ""
    echo -e "${CYAN}示例:${NC}"
    echo "  $0 search '人工智能专利' 10"
    echo "  $0 research '深度学习' comprehensive"
    echo "  $0 analysis '华为' '5G通信'"
    echo "  $0 status"
    echo "  $0 interactive"
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
                echo "用法: $0 search <query> [max_results]"
                exit 1
            fi
            quick_search "$@"
            ;;
        research|r)
            if [[ $# -lt 1 ]]; then
                print_error "请提供研究主题"
                echo "用法: $0 research <topic> [depth]"
                exit 1
            fi
            patent_research "$@"
            ;;
        analysis|a)
            if [[ $# -lt 1 ]]; then
                print_error "请提供公司名称"
                echo "用法: $0 analysis <company> [domain]"
                exit 1
            fi
            competitive_analysis "$@"
            ;;
        status|st)
            platform_status
            ;;
        manual|m)
            show_manual
            ;;
        interactive|i)
            interactive_search
            ;;
        test|t)
            test_tools
            ;;
        setup)
            setup
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