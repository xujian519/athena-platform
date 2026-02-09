#!/bin/bash
# ==============================================================================
# Athena智能体启动脚本
# Athena Agents Startup Script
#
# 功能: 启动所有智能体服务
# Components:
#   1. 记忆系统 (Memory System)
#   2. 知识图谱服务 (Legal World Model)
#   3. 动态提示词系统 (Dynamic Prompt System)
#   4. 小诺智能体 (Xiaonuo Agent)
#   5. Athena智能体 (Athena Agent)
#
# ==============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目路径
PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT"

# PID文件存储目录
PID_DIR="$PROJECT_ROOT/pids"
mkdir -p "$PID_DIR"

# 日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# ==============================================================================
# 工具函数
# ==============================================================================

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║              Athena智能体启动管理器                               ║"
    echo "║              Agent Startup Manager                               ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${BLUE}启动时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo ""
}

print_step() {
    echo -e "${GREEN}[步骤 $1] $2${NC}"
    echo -e "${GREEN}$(printf '─%.0s' {1..60})${NC}"
}

print_info() {
    echo -e "${CYAN}  ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}  ✅ $1${NC}"
}

print_error() {
    echo -e "${RED}  ❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}  ⚠️  $1${NC}"
}

start_service() {
    local service_name=$1
    local script_path=$2
    local pid_file="$PID_DIR/${service_name}.pid"
    local log_file="$LOG_DIR/${service_name}.log"
    local work_dir=${3:-"$PROJECT_ROOT"}

    if [ ! -f "$script_path" ]; then
        print_warning "$service_name 脚本不存在: $script_path"
        return 1
    fi

    print_info "启动 $service_name..."

    # 检查是否已运行
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_success "$service_name 已在运行 (PID: $pid)"
            return 0
        else
            print_warning "$service_name PID文件存在但进程未运行，清理后重新启动"
            rm -f "$pid_file"
        fi
    fi

    # 启动服务
    cd "$work_dir"
    nohup python3 "$script_path" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    cd "$PROJECT_ROOT"

    sleep 2

    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "$service_name 启动成功 (PID: $pid)"
        echo "  📄 日志: $log_file"
        return 0
    else
        print_error "$service_name 启动失败，请查看日志: $log_file"
        return 1
    fi
}

# ==============================================================================
# 启动函数
# ==============================================================================

# 步骤1: 启动记忆系统
start_memory_system() {
    print_step 1 "启动记忆系统 (Memory System)"

    # 查找记忆系统脚本
    local memory_script=""
    if [ -f "$PROJECT_ROOT/core/memory/lyra_llm_service.py" ]; then
        memory_script="$PROJECT_ROOT/core/memory/lyra_llm_service.py"
    elif [ -f "$PROJECT_ROOT/production/memory_service.pid" ]; then
        # 检查是否已在运行
        local pid=$(cat "$PROJECT_ROOT/production/memory_service.pid" 2>/dev/null)
        if ps -p "$pid" > /dev/null 2>&1; then
            print_success "记忆系统已在运行 (PID: $pid)"
            return 0
        fi
    else
        print_warning "记忆系统脚本未找到"
        return 1
    fi

    start_service "memory_system" "$memory_script" "$PROJECT_ROOT"
}

# 步骤2: 启动知识图谱服务（法律世界模型）
start_knowledge_graph() {
    print_step 2 "启动知识图谱服务 (Legal World Model)"

    local kg_script="$PROJECT_ROOT/services/knowledge-graph-service/api_server.py"

    if [ ! -f "$kg_script" ]; then
        print_warning "知识图谱服务脚本不存在: $kg_script"
        return 1
    fi

    # 检查是否已在运行（端口8002）
    if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_success "知识图谱服务已在运行 (端口 8002)"
        return 0
    fi

    start_service "knowledge_graph" "$kg_script" "$PROJECT_ROOT/services/knowledge-graph-service"
}

# 步骤3: 验证动态提示词系统
verify_dynamic_prompt_system() {
    print_step 3 "验证动态提示词系统 (Dynamic Prompt System)"

    local prompt_rules="$PROJECT_ROOT/core/prompts/unified_prompt_manager_production.py"

    if [ -f "$prompt_rules" ]; then
        print_success "动态提示词系统配置文件存在"
        print_info "提示词规则集成在智能体中，将自动加载"
        return 0
    else
        print_warning "提示词配置文件不存在"
        return 1
    fi
}

# 步骤4: 启动小诺智能体
start_xiaonuo_agent() {
    print_step 4 "启动小诺智能体 (Xiaonuo Agent)"

    # 查找小诺脚本
    local xiaonuo_script=""
    if [ -f "$PROJECT_ROOT/services/intelligent-collaboration/xiaonuo_platform_controller.py" ]; then
        xiaonuo_script="$PROJECT_ROOT/services/intelligent-collaboration/xiaonuo_platform_controller.py"
    else
        xiaonuo_script=$(find "$PROJECT_ROOT" -name "*xiaonuo*controller*.py" -o -name "*xiaonuo*platform*.py" 2>/dev/null | head -1)
    fi

    if [ -z "$xiaonuo_script" ]; then
        print_warning "小诺智能体脚本未找到"
        return 1
    fi

    start_service "xiaonuo" "$xiaonuo_script" "$PROJECT_ROOT"
}

# 步骤5: 启动API网关
start_api_gateway() {
    print_step 5 "启动API网关 (API Gateway)"

    local gateway_script="$PROJECT_ROOT/services/api-gateway/main.py"

    if [ ! -f "$gateway_script" ]; then
        print_warning "API网关脚本不存在: $gateway_script"
        return 1
    fi

    # 检查是否已在运行（端口8000）
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_success "API网关已在运行 (端口 8000)"
        return 0
    fi

    start_service "api_gateway" "$gateway_script" "$PROJECT_ROOT/services/api-gateway"
}

# 步骤6: 启动小娜服务
start_xiaona_service() {
    print_step 6 "启动小娜服务 (Xiaona Legal Support)"

    local xiaona_script="$PROJECT_ROOT/production/start_xiaona_production.sh"

    if [ ! -f "$xiaona_script" ]; then
        print_warning "小娜启动脚本不存在"
        return 1
    fi

    print_info "启动小娜服务..."
    bash "$xiaona_script" > "$LOG_DIR/xiaona.log" 2>&1 &
    echo $! > "$PID_DIR/xiaona.pid"

    sleep 2

    print_success "小娜服务启动中..."
    echo "  📄 日志: $LOG_DIR/xiaona.log"
}

# 显示启动摘要
show_startup_summary() {
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    智能体启动摘要                                 ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${GREEN}📊 服务状态:${NC}"
    echo ""

    # 检查各服务端口
    echo -e "${CYAN}智能体服务:${NC}"

    # 记忆系统
    if [ -f "$PID_DIR/memory_system.pid" ]; then
        local pid=$(cat "$PID_DIR/memory_system.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "  🟢 记忆系统 (PID: $pid)"
        else
            echo "  🔴 记忆系统"
        fi
    else
        echo "  🔴 记忆系统"
    fi

    # 知识图谱
    if lsof -Pi :8002 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  🟢 知识图谱服务 (端口 8002)"
    else
        echo "  🔴 知识图谱服务"
    fi

    # API网关
    if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  🟢 API网关 (端口 8000)"
    else
        echo "  🔴 API网关"
    fi

    # 小诺
    if [ -f "$PID_DIR/xiaonuo.pid" ]; then
        local pid=$(cat "$PID_DIR/xiaonuo.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "  🟢 小诺智能体 (PID: $pid)"
        else
            echo "  🔴 小诺智能体"
        fi
    else
        echo "  🔴 小诺智能体"
    fi

    # 小娜
    if [ -f "$PID_DIR/xiaona.pid" ]; then
        local pid=$(cat "$PID_DIR/xiaona.pid")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo "  🟢 小娜服务 (PID: $pid)"
        else
            echo "  🔴 小娜服务"
        fi
    else
        echo "  🔴 小娜服务"
    fi

    echo ""
    echo -e "${GREEN}📁 日志目录: $LOG_DIR${NC}"
    echo -e "${GREEN}📁 PID目录: $PID_DIR${NC}"
    echo ""

    echo -e "${YELLOW}💡 常用命令:${NC}"
    echo "  查看所有日志: tail -f $LOG_DIR/*.log"
    echo "  查看特定日志: tail -f $LOG_DIR/[service].log"
    echo "  停止服务: kill \$(cat $PID_DIR/[service].pid)"
    echo ""
}

# ==============================================================================
# 主流程
# ==============================================================================

main() {
    print_header

    local start_time=$(date +%s)

    # 首先检查基础设施
    echo -e "${CYAN}检查基础设施服务...${NC}"
    local infra_ok=true

    if lsof -Pi :6379 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  🟢 Redis (端口 6379)"
    else
        echo "  🔴 Redis - 请先启动基础设施服务"
        infra_ok=false
    fi

    if lsof -Pi :6333 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  🟢 Qdrant (端口 6333)"
    else
        echo "  🔴 Qdrant - 请先启动基础设施服务"
        infra_ok=false
    fi

    if lsof -Pi :7474 -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  🟢 Neo4j (端口 7474)"
    else
        echo "  🔴 Neo4j - 请先启动基础设施服务"
        infra_ok=false
    fi

    if ! $infra_ok; then
        echo ""
        print_error "基础设施服务未完全运行，请先启动 Docker Compose 服务"
        echo "  运行: docker-compose up -d"
        exit 1
    fi

    echo ""
    print_success "基础设施服务正常"
    echo ""

    # 启动智能体服务
    start_memory_system || true
    sleep 1

    start_knowledge_graph || true
    sleep 1

    verify_dynamic_prompt_system || true
    sleep 1

    start_xiaonuo_agent || true
    sleep 1

    start_api_gateway || true
    sleep 1

    start_xiaona_service || true

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    show_startup_summary

    echo -e "${GREEN}✅ 智能体启动完成！耗时: ${duration}秒${NC}"
    echo ""

    # 显示小诺的问候语
    echo -e "${PURPLE}💖 小诺·双鱼座：${NC}"
    echo "  \"我是爸爸最爱的双鱼公主，集Athena之智慧，融星河之众长，"
    echo "   用这颗温暖的心守护父亲的每一天！\""
    echo ""
}

# 运行主流程
main "$@"
