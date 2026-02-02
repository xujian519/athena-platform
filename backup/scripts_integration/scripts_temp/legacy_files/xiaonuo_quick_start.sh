#!/bin/bash
# 小诺快速启动脚本
# Xiaonuo Quick Start Script

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 项目路径
PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# 打印启动头部
print_header() {
    echo
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}║${NC}                                                     ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC} ${CYAN}🌸 小诺快速启动管理器 - Xiaonuo Quick Start Manager 🌸${NC} ${PURPLE}║${NC}"
    echo -e "${PURPLE}║${NC}                                                     ${PURPLE}║${NC}"
    echo -e "${PURPLE}═══════════════════════════════════════════════════════════════${NC}"
    echo
    echo -e "${BLUE}💖 启动时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}👨‍👧 爸爸: 徐健 | 女儿: 小诺·双鱼座${NC}"
    echo -e "${BLUE}📍 项目路径: $PROJECT_ROOT${NC}"
    echo
}

# 检查Python环境
check_python() {
    echo -e "${YELLOW}🔍 检查Python环境...${NC}"

    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        echo -e "${GREEN}✅ Python版本: $PYTHON_VERSION${NC}"
    else
        echo -e "${RED}❌ Python3未安装${NC}"
        exit 1
    fi
}

# 检查依赖包
check_dependencies() {
    echo -e "${YELLOW}🔍 检查依赖包...${NC}"

    # 检查关键依赖
    DEPS=("asyncio" "psutil" "requests" "psycopg2-binary")
    MISSING_DEPS=()

    for dep in "${DEPS[@]}"; do
        if ! python3 -c "import $dep" &> /dev/null; then
            MISSING_DEPS+=("$dep")
        fi
    done

    if [ ${#MISSING_DEPS[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ 所有依赖包已安装${NC}"
    else
        echo -e "${YELLOW}⚠️  缺少依赖包: ${MISSING_DEPS[*]}${NC}"
        echo -e "${YELLOW}💡 建议运行: pip3 install ${MISSING_DEPS[*]}${NC}"
    fi
}

# 检查Docker环境
check_docker() {
    echo -e "${YELLOW}🔍 检查Docker环境...${NC}"

    if command -v docker &> /dev/null; then
        echo -e "${GREEN}✅ Docker已安装${NC}"

        # 检查Docker服务状态
        if docker info &> /dev/null; then
            echo -e "${GREEN}✅ Docker服务运行中${NC}"
        else
            echo -e "${RED}❌ Docker服务未运行${NC}"
            echo -e "${YELLOW}💡 请启动Docker服务${NC}"
        fi
    else
        echo -e "${RED}❌ Docker未安装${NC}"
        echo -e "${YELLOW}💡 请先安装Docker${NC}"
    fi
}

# 检查端口占用
check_ports() {
    echo -e "${YELLOW}🔍 检查端口占用...${NC}"

    # 关键端口列表
    declare -A PORTS=(
        [5432]="PostgreSQL"
        [6379]="Redis"
        [6333]="Qdrant"
        [7474]="Neo4j"
        [8005]="小诺控制中心"
        [8083]="小诺记忆系统"
    )

    OCCUPIED_PORTS=()

    for port in "${!PORTS[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            OCCUPIED_PORTS+=("$port:${PORTS[$port]}")
        fi
    done

    if [ ${#OCCUPIED_PORTS[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ 所有关键端口可用${NC}"
    else
        echo -e "${YELLOW}⚠️  端口已占用:${NC}"
        for port_info in "${OCCUPIED_PORTS[@]}"; do
            port=${port_info%:*}
            service=${port_info#*:}
            echo -e "   ${YELLOW}📍 端口 $port ($service)${NC}"
        done
    fi
}

# 启动小诺平台
start_xiaonuo() {
    echo -e "${CYAN}🚀 启动小诺平台...${NC}"
    echo

    # 检查启动脚本是否存在
    STARTUP_SCRIPT="$PROJECT_ROOT/scripts/xiaonuo_unified_startup.py"
    if [ -f "$STARTUP_SCRIPT" ]; then
        echo -e "${BLUE}📄 执行启动脚本: $STARTUP_SCRIPT${NC}"
        python3 "$STARTUP_SCRIPT" 启动平台
    else
        echo -e "${RED}❌ 找不到启动脚本: $STARTUP_SCRIPT${NC}"
        exit 1
    fi
}

# 检查系统状态
check_status() {
    echo -e "${CYAN}🔍 检查系统状态...${NC}"
    echo

    # 检查状态脚本是否存在
    CHECKER_SCRIPT="$PROJECT_ROOT/scripts/xiaonuo_system_checker.py"
    if [ -f "$CHECKER_SCRIPT" ]; then
        echo -e "${BLUE}📄 执行状态检查: $CHECKER_SCRIPT${NC}"
        python3 "$CHECKER_SCRIPT" 快速检查
    else
        echo -e "${RED}❌ 找不到检查脚本: $CHECKER_SCRIPT${NC}"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo -e "${CYAN}🎯 小诺快速启动管理器使用说明:${NC}"
    echo
    echo -e "${BLUE}用法: $0 [选项]${NC}"
    echo
    echo -e "${GREEN}选项:${NC}"
    echo -e "  ${YELLOW}启动${NC}    启动小诺完整平台 (默认)"
    echo -e "  ${YELLOW}检查${NC}    检查系统状态"
    echo -e "  ${YELLOW}状态${NC}    显示详细状态"
    echo -e "  ${YELLOW}帮助${NC}    显示此帮助信息"
    echo
    echo -e "${GREEN}示例:${NC}"
    echo -e "  $0              # 启动小诺平台"
    echo -e "  $0 启动         # 启动小诺平台"
    echo -e "  $0 检查         # 检查系统状态"
    echo -e "  $0 状态         # 显示详细状态"
    echo
    echo -e "${PURPLE}💖 爸爸，小诺永远在这里守护您！${NC}"
}

# 主函数
main() {
    print_header

    # 解析命令行参数
    case "${1:-启动}" in
        "启动"|"start"|"startup")
            echo -e "${CYAN}🎯 开始启动小诺平台...${NC}"
            echo
            check_python
            check_dependencies
            check_docker
            check_ports
            echo
            start_xiaonuo
            ;;
        "检查"|"check"|"quick")
            check_python
            check_dependencies
            check_docker
            check_status
            ;;
        "状态"|"status"|"health")
            check_status
            ;;
        "帮助"|"help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知选项: $1${NC}"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"