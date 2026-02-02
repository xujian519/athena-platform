#!/bin/bash
# Athena工作平台 MCP统一管理脚本
# Athena Work Platform MCP Unified Management Script
#
# 控制者: 小诺 & Athena
# 创建时间: 2025年12月11日
# 版本: 1.0.0

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLATFORM_ROOT="$(dirname "$SCRIPT_DIR")"
MCP_MANAGER_SCRIPT="$PLATFORM_ROOT/tools/mcp/athena_mcp_manager.py"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}=== $1 ===${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_failure() {
    echo -e "${RED}❌ $1${NC}"
}

# 显示帮助信息
show_help() {
    cat << EOF
Athena工作平台 MCP统一管理脚本 v1.0.0

用法: $0 [命令] [参数]

命令:
    start [服务器名]         启动MCP服务器 (不指定服务器名则启动所有可用服务器)
    stop [服务器名]          停止MCP服务器 (不指定服务器名则停止所有服务器)
    restart [服务器名]       重启MCP服务器
    status [服务器名]        查看服务器状态
    list                    列出所有可用的MCP服务器
    tools [服务器名]         列出指定服务器的工具
    call <服务器名> <工具名> [参数]  调用指定工具
    test                    测试所有可用的MCP服务器
    interactive             交互式管理模式
    help                    显示此帮助信息

可用的MCP服务器:
    jina-ai              Jina AI工具服务器 (Web读取、搜索、向量化、重排序)
    bing-cn-search       Bing中文搜索服务器 (中文搜索、图片、新闻)
    amap-mcp             高德地图服务器 (地理位置、路径规划、POI搜索)
    academic-search      学术搜索服务器 (论文、期刊搜索)

示例:
    $0 start                     # 启动所有可用的MCP服务器
    $0 start jina-ai            # 仅启动Jina AI服务器
    $0 status                    # 查看所有服务器状态
    $0 tools jina-ai            # 查看Jina AI服务器的工具
    $0 call jina-ai get_system_info  # 调用系统信息工具
    $0 test                      # 测试所有服务器

控制者: 小诺 & Athena
EOF
}

# 检查Python依赖
check_dependencies() {
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装或不在PATH中"
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        log_warn "Node.js 未安装，部分MCP服务器可能无法运行"
    fi
}

# 调用Python MCP管理器
call_mcp_manager() {
    local action=$1
    shift
    local args=("$@")

    cd "$PLATFORM_ROOT"

    # 设置环境变量
    export PYTHONPATH="$PLATFORM_ROOT:$PYTHONPATH"

    # 调用Python管理器
    python3 -c "
import asyncio
import sys
import json
sys.path.insert(0, '$PLATFORM_ROOT')

from tools.mcp.athena_mcp_manager import AthenaMCPManager

async def main():
    manager = AthenaMCPManager()

    try:
        if '$action' == 'start_all':
            result = await manager.start_all_servers()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif '$action' == 'stop_all':
            result = await manager.stop_all_servers()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif '$action' == 'get_all_status':
            result = await manager.get_all_status()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif '$action' == 'list_servers':
            servers = manager.list_all_servers()
            print(json.dumps(servers, ensure_ascii=False, indent=2))
        else:
            # 传递具体操作给Python
            result = await getattr(manager, '$action')(${args[@] if args else ''})
            if result is not None:
                print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
"
}

# 启动服务器
start_server() {
    local server_name=$1

    log_header "启动MCP服务器"

    if [ -z "$server_name" ]; then
        log_info "启动所有可用的MCP服务器..."
        call_mcp_manager "start_all" | python3 -m json.tool
    else
        log_info "启动MCP服务器: $server_name"
        call_mcp_manager "start_server" "'$server_name'" | python3 -m json.tool
    fi

    log_success "启动命令已执行"
}

# 停止服务器
stop_server() {
    local server_name=$1

    log_header "停止MCP服务器"

    if [ -z "$server_name" ]; then
        log_info "停止所有MCP服务器..."
        call_mcp_manager "stop_all" | python3 -m json.tool
    else
        log_info "停止MCP服务器: $server_name"
        call_mcp_manager "stop_server" "'$server_name'" | python3 -m json.tool
    fi

    log_success "停止命令已执行"
}

# 重启服务器
restart_server() {
    local server_name=$1

    log_header "重启MCP服务器"

    if [ -z "$server_name" ]; then
        log_error "请指定要重启的服务器名称"
        show_help
        exit 1
    fi

    log_info "重启MCP服务器: $server_name"
    call_mcp_manager "restart_server" "'$server_name'" | python3 -m json.tool

    log_success "重启命令已执行"
}

# 查看状态
show_status() {
    local server_name=$1

    log_header "MCP服务器状态"

    if [ -z "$server_name" ]; then
        log_info "获取所有MCP服务器状态..."
        call_mcp_manager "get_all_status" | python3 -m json.tool
    else
        log_info "获取MCP服务器状态: $server_name"
        call_mcp_manager "get_server_status" "'$server_name'" | python3 -m json.tool
    fi
}

# 列出服务器
list_servers() {
    log_header "可用的MCP服务器"

    call_mcp_manager "list_servers" | python3 -c "
import json
import sys
servers = json.load(sys.stdin)
print('可用的MCP服务器:')
for i, server in enumerate(servers, 1):
    print(f'  {i}. {server}')
"
}

# 列出工具
list_tools() {
    local server_name=$1

    if [ -z "$server_name" ]; then
        log_error "请指定服务器名称"
        show_help
        exit 1
    fi

    log_header "MCP服务器工具 - $server_name"

    cd "$PLATFORM_ROOT"
    export PYTHONPATH="$PLATFORM_ROOT:$PYTHONPATH"

    python3 -c "
import asyncio
import json
import sys
sys.path.insert(0, '$PLATFORM_ROOT')

from tools.mcp.athena_mcp_manager import AthenaMCPManager

async def main():
    manager = AthenaMCPManager()
    try:
        tools = await manager.list_tools('$server_name')
        print(f'服务器 {server_name} 的工具:')
        for tool in tools:
            print(f'  📦 {tool.name}')
            print(f'     描述: {tool.description}')
            print(f'     参数: {json.dumps(tool.input_schema, ensure_ascii=False, indent=6)}')
            print()
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
"
}

# 调用工具
call_tool() {
    local server_name=$1
    local tool_name=$2
    shift 2
    local tool_args="$*"

    if [ -z "$server_name" ] || [ -z "$tool_name" ]; then
        log_error "请指定服务器名称和工具名称"
        show_help
        exit 1
    fi

    log_header "调用MCP工具"
    log_info "服务器: $server_name"
    log_info "工具: $tool_name"
    if [ -n "$tool_args" ]; then
        log_info "参数: $tool_args"
    fi

    cd "$PLATFORM_ROOT"
    export PYTHONPATH="$PLATFORM_ROOT:$PYTHONPATH"

    # 解析参数为JSON格式
    if [ -n "$tool_args" ]; then
        # 简单的参数解析，这里可以扩展为更复杂的解析
        tool_args_json="{$tool_args}"
    else
        tool_args_json="{}"
    fi

    python3 -c "
import asyncio
import json
import sys
sys.path.insert(0, '$PLATFORM_ROOT')

from tools.mcp.athena_mcp_manager import AthenaMCPManager

async def main():
    manager = AthenaMCPManager()
    try:
        result = await manager.call_tool('$server_name', '$tool_name', $tool_args_json)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f'Error: {e}')
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
"
}

# 测试服务器
test_servers() {
    log_header "测试MCP服务器"

    log_info "测试所有可用的MCP服务器..."

    # 测试Jina AI
    log_info "测试Jina AI MCP服务器..."
    if [ -f "$PLATFORM_ROOT/mcp-servers/jina-ai-mcp-server/index.js" ]; then
        cd "$PLATFORM_ROOT/mcp-servers/jina-ai-mcp-server"
        if echo '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}' | node index.js > /dev/null 2>&1; then
            log_success "Jina AI MCP服务器测试通过"
        else
            log_failure "Jina AI MCP服务器测试失败"
        fi
    else
        log_warn "Jina AI MCP服务器文件不存在"
    fi

    # 测试Bing中文搜索
    log_info "测试Bing中文搜索MCP服务器..."
    if [ -f "$PLATFORM_ROOT/mcp-servers/bing-cn-mcp-server/index.js" ]; then
        cd "$PLATFORM_ROOT/mcp-servers/bing-cn-mcp-server"
        if echo '{"jsonrpc": "2.0", "method": "tools/list", "params": {}, "id": 1}' | node index.js > /dev/null 2>&1; then
            log_success "Bing中文搜索MCP服务器测试通过"
        else
            log_failure "Bing中文搜索MCP服务器测试失败"
        fi
    else
        log_warn "Bing中文搜索MCP服务器文件不存在"
    fi

    # 测试高德地图MCP
    log_info "测试高德地图MCP服务器..."
    if [ -f "$PLATFORM_ROOT/amap-mcp-server/amap_mcp_server.py" ]; then
        cd "$PLATFORM_ROOT"
        if python3 -c "
from amap_mcp_server import AmapMCPServer
import asyncio

async def test():
    try:
        server = AmapMCPServer()
        log_info('高德地图MCP服务器可以正常导入')
        return True
    except Exception as e:
        return False

result = asyncio.run(test())
print('PASS' if result else 'FAIL')
" 2>/dev/null | grep -q "PASS"; then
            log_success "高德地图MCP服务器测试通过"
        else
            log_failure "高德地图MCP服务器测试失败"
        fi
    else
        log_warn "高德地图MCP服务器文件不存在"
    fi

    log_info "MCP服务器测试完成"
}

# 交互式模式
interactive_mode() {
    log_header "MCP服务器交互式管理"

    while true; do
        echo
        echo -e "${CYAN}Athena MCP服务器管理器${NC}"
        echo "1. 启动所有服务器"
        echo "2. 停止所有服务器"
        echo "3. 查看服务器状态"
        echo "4. 列出可用工具"
        echo "5. 调用工具"
        echo "6. 测试服务器"
        echo "7. 退出"
        echo -n "请选择操作 [1-7]: "

        read choice

        case $choice in
            1)
                start_server
                ;;
            2)
                stop_server
                ;;
            3)
                show_status
                ;;
            4)
                echo -n "请输入服务器名称: "
                read server
                list_tools "$server"
                ;;
            5)
                echo -n "请输入服务器名称: "
                read server
                echo -n "请输入工具名称: "
                read tool
                echo -n "请输入工具参数 (JSON格式，可选): "
                read args
                call_tool "$server" "$tool" "$args"
                ;;
            6)
                test_servers
                ;;
            7)
                log_info "退出交互式模式"
                break
                ;;
            *)
                log_error "无效选择，请输入 1-7"
                ;;
        esac
    done
}

# 主函数
main() {
    local command=$1

    # 检查依赖
    check_dependencies

    case $command in
        start)
            start_server "$2"
            ;;
        stop)
            stop_server "$2"
            ;;
        restart)
            restart_server "$2"
            ;;
        status)
            show_status "$2"
            ;;
        list)
            list_servers
            ;;
        tools)
            list_tools "$2"
            ;;
        call)
            call_tool "$2" "$3" "${@:4}"
            ;;
        test)
            test_servers
            ;;
        interactive)
            interactive_mode
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"