#!/bin/bash
# ==============================================================================
# Athena工作平台 - 生产环境启动脚本
# Athena Platform - Production Environment Startup Script
#
# 功能: 启动生产环境的所有组件
# Components:
#   1. 基础设施服务 (Docker Compose)
#   2. 记忆系统 (Memory System)
#   3. 知识图谱服务 (Legal World Model)
#   4. 动态提示词系统 (Dynamic Prompt System)
#   5. 小诺智能体 (Xiaonuo Agent)
#   6. Athena智能体 (Athena Agent)
#
# 作者: Athena开发团队
# 创建时间: 2026-02-06
# ==============================================================================

set -e  # 遇到错误立即退出

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
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════╗"
    echo "║                                                                  ║"
    echo "║          Athena工作平台 - 生产环境启动管理器                     ║"
    echo "║          Production Environment Startup Manager                  ║"
    echo "║                                                                  ║"
    echo "╚══════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${BLUE}启动时间: $(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo -e "${BLUE}项目路径: $PROJECT_ROOT${NC}"
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

check_port() {
    local port=$1
    local service_name=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        print_success "$service_name 已在运行 (端口 $port)"
        return 0
    else
        return 1
    fi
}

wait_for_port() {
    local port=$1
    local service_name=$2
    local max_wait=${3:-30}
    local count=0

    while [ $count -lt $max_wait ]; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
            print_success "$service_name 就绪 (端口 $port)"
            return 0
        fi
        sleep 1
        count=$((count + 1))
        if [ $((count % 5)) -eq 0 ]; then
            echo -n "."
        fi
    done
    print_error "$service_name 启动超时"
    return 1
}

# ==============================================================================
# 启动函数
# ==============================================================================

# 步骤1: 启动基础设施服务
start_infrastructure() {
    print_step 1 "启动基础设施服务 (Docker Compose)"

    print_info "检查Docker服务状态..."
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker未运行，请先启动Docker"
        return 1
    fi
    print_success "Docker服务正常"

    print_info "启动Docker Compose服务..."
    docker-compose -f docker-compose.unified.yml --profile dev up -d redis qdrant neo4j prometheus grafana alertmanager

    print_info "等待服务启动..."
    sleep 5

    # 验证服务
    local all_ok=true

    if check_port 6379 "Redis"; then
        echo "  📡 Redis: localhost:6379" >> "$LOG_DIR/infrastructure.log"
    else
        wait_for_port 6379 "Redis" 30 || all_ok=false
    fi

    if check_port 6333 "Qdrant"; then
        echo "  📡 Qdrant: http://localhost:6333" >> "$LOG_DIR/infrastructure.log"
    else
        wait_for_port 6333 "Qdrant" 30 || all_ok=false
    fi

    if check_port 7474 "Neo4j"; then
        echo "  📡 Neo4j: http://localhost:7474" >> "$LOG_DIR/infrastructure.log"
    else
        wait_for_port 7474 "Neo4j" 60 || all_ok=false
    fi

    if check_port 9090 "Prometheus"; then
        echo "  📡 Prometheus: http://localhost:9090" >> "$LOG_DIR/infrastructure.log"
    else
        wait_for_port 9090 "Prometheus" 30 || all_ok=false
    fi

    if check_port 3000 "Grafana"; then
        echo "  📡 Grafana: http://localhost:3000 (admin/admin123)" >> "$LOG_DIR/infrastructure.log"
    else
        wait_for_port 3000 "Grafana" 30 || all_ok=false
    fi

    if $all_ok; then
        print_success "基础设施服务启动完成"
        return 0
    else
        print_error "部分基础设施服务启动失败"
        return 1
    fi
}

# 步骤2: 启动记忆系统
start_memory_system() {
    print_step 2 "启动记忆系统 (Memory System)"

    local memory_script="$PROJECT_ROOT/core/memory/lyra_llm_service.py"
    local pid_file="$PID_DIR/memory_service.pid"
    local log_file="$LOG_DIR/memory_service.log"

    if [ ! -f "$memory_script" ]; then
        print_warning "记忆系统脚本不存在: $memory_script"
        return 1
    fi

    print_info "启动记忆系统服务..."

    # 检查是否已运行
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_success "记忆系统已在运行 (PID: $pid)"
            return 0
        fi
    fi

    # 启动记忆系统
    nohup python3 "$memory_script" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    sleep 3

    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "记忆系统启动成功 (PID: $pid)"
        return 0
    else
        print_error "记忆系统启动失败，请查看日志: $log_file"
        return 1
    fi
}

# 步骤3: 启动知识图谱服务（法律世界模型）
start_knowledge_graph() {
    print_step 3 "启动知识图谱服务 (Legal World Model)"

    local kg_script="$PROJECT_ROOT/services/knowledge-graph-service/api_server.py"
    local pid_file="$PID_DIR/knowledge_graph.pid"
    local log_file="$LOG_DIR/knowledge_graph.log"

    if [ ! -f "$kg_script" ]; then
        print_warning "知识图谱服务脚本不存在: $kg_script"
        return 1
    fi

    print_info "启动知识图谱服务..."

    # 检查是否已运行
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_success "知识图谱服务已在运行 (PID: $pid)"
            return 0
        fi
    fi

    # 检查端口
    if check_port 8002 "知识图谱服务"; then
        return 0
    fi

    # 启动服务
    cd "$PROJECT_ROOT/services/knowledge-graph-service"
    nohup python3 api_server.py > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    cd "$PROJECT_ROOT"

    sleep 3

    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "知识图谱服务启动成功 (PID: $pid)"
        return 0
    else
        print_error "知识图谱服务启动失败，请查看日志: $log_file"
        return 1
    fi
}

# 步骤4: 启动动态提示词系统
start_dynamic_prompt_system() {
    print_step 4 "启动动态提示词系统 (Dynamic Prompt System)"

    # 动态提示词系统集成在各个智能体中
    print_info "动态提示词系统集成在智能体中"
    print_info "将在启动智能体时自动加载"

    # 验证提示词规则文件
    local prompt_rules="$PROJECT_ROOT/core/prompts/unified_prompt_manager_production.py"
    if [ -f "$prompt_rules" ]; then
        print_success "提示词规则文件存在"
    else
        print_warning "提示词规则文件不存在"
    fi

    return 0
}

# 步骤5: 启动小诺智能体
start_xiaonuo_agent() {
    print_step 5 "启动小诺智能体 (Xiaonuo Agent)"

    local xiaonuo_script="$PROJECT_ROOT/services/intelligent-collaboration/xiaonuo_platform_controller.py"
    local pid_file="$PID_DIR/xiaonuo.pid"
    local log_file="$LOG_DIR/xiaonuo.log"

    if [ ! -f "$xiaonuo_script" ]; then
        # 尝试其他可能的位置
        xiaonuo_script=$(find "$PROJECT_ROOT/services" -name "*xiaonuo*.py" -type f | head -1)
        if [ -z "$xiaonuo_script" ]; then
            print_warning "小诺智能体脚本未找到"
            return 1
        fi
    fi

    print_info "启动小诺智能体..."

    # 检查是否已运行
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_success "小诺智能体已在运行 (PID: $pid)"
            return 0
        fi
    fi

    # 启动小诺
    nohup python3 "$xiaonuo_script" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    sleep 3

    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "小诺智能体启动成功 (PID: $pid)"
        return 0
    else
        print_error "小诺智能体启动失败，请查看日志: $log_file"
        return 1
    fi
}

# 步骤6: 启动Athena智能体
start_athena_agent() {
    print_step 6 "启动Athena智能体 (Athena Agent)"

    local athena_script="$PROJECT_CORE/agents/athena_agent.py"
    local pid_file="$PID_DIR/athena.pid"
    local log_file="$LOG_DIR/athena.log"

    # Athena可能集成在其他服务中
    print_info "Athena智能体可能集成在平台服务中"

    # 检查是否存在Athena脚本
    if [ -f "$athena_script" ]; then
        print_info "启动Athena智能体..."

        # 检查是否已运行
        if [ -f "$pid_file" ]; then
            local pid=$(cat "$pid_file")
            if ps -p "$pid" > /dev/null 2>&1; then
                print_success "Athena智能体已在运行 (PID: $pid)"
                return 0
            fi
        fi

        # 启动Athena
        nohup python3 "$athena_script" > "$log_file" 2>&1 &
        local pid=$!
        echo $pid > "$pid_file"

        sleep 3

        if ps -p "$pid" > /dev/null 2>&1; then
            print_success "Athena智能体启动成功 (PID: $pid)"
            return 0
        else
            print_error "Athena智能体启动失败，请查看日志: $log_file"
            return 1
        fi
    else
        print_info "Athena智能体功能集成在平台服务中"
        return 0
    fi
}

# 步骤7: 启动API网关
start_api_gateway() {
    print_step 7 "启动API网关 (API Gateway)"

    local gateway_script="$PROJECT_ROOT/services/api-gateway/main.py"
    local pid_file="$PID_DIR/api_gateway.pid"
    local log_file="$LOG_DIR/api_gateway.log"

    if [ ! -f "$gateway_script" ]; then
        print_warning "API网关脚本不存在"
        return 1
    fi

    print_info "启动API网关..."

    # 检查是否已运行
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_success "API网关已在运行 (PID: $pid)"
            return 0
        fi
    fi

    # 检查端口
    if check_port 8000 "API网关"; then
        return 0
    fi

    # 启动网关
    cd "$PROJECT_ROOT/services/api-gateway"
    nohup python3 main.py > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    cd "$PROJECT_ROOT"

    sleep 3

    if ps -p "$pid" > /dev/null 2>&1; then
        print_success "API网关启动成功 (PID: $pid)"
        return 0
    else
        print_error "API网关启动失败，请查看日志: $log_file"
        return 1
    fi
}

# 显示启动摘要
show_startup_summary() {
    echo ""
    echo -e "${PURPLE}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    生产环境启动摘要                              ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════════════════════════════╝${NC}"
    echo ""

    echo -e "${GREEN}📊 服务状态:${NC}"
    echo ""

    # 基础设施
    echo -e "${CYAN}基础设施服务:${NC}"
    check_port 6379 "Redis" && echo "  🟢 Redis (localhost:6379)" || echo "  🔴 Redis"
    check_port 6333 "Qdrant" && echo "  🟢 Qdrant (http://localhost:6333)" || echo "  🔴 Qdrant"
    check_port 7474 "Neo4j" && echo "  🟢 Neo4j (http://localhost:7474)" || echo "  🔴 Neo4j"
    check_port 9090 "Prometheus" && echo "  🟢 Prometheus (http://localhost:9090)" || echo "  🔴 Prometheus"
    check_port 3000 "Grafana" && echo "  🟢 Grafana (http://localhost:3000)" || echo "  🔴 Grafana"
    echo ""

    # 应用服务
    echo -e "${CYAN}应用服务:${NC}"
    check_port 8000 "API网关" && echo "  🟢 API网关 (http://localhost:8000)" || echo "  🔴 API网关"
    check_port 8002 "知识图谱" && echo "  🟢 知识图谱服务" || echo "  🔴 知识图谱服务"
    check_port 8005 "小诺" && echo "  🟢 小诺智能体" || echo "  🔴 小诺智能体"
    echo ""

    echo -e "${GREEN}📁 日志目录: $LOG_DIR${NC}"
    echo -e "${GREEN}📁 PID目录: $PID_DIR${NC}"
    echo ""

    echo -e "${YELLOW}💡 常用命令:${NC}"
    echo "  查看日志: tail -f $LOG_DIR/[service].log"
    echo "  停止服务: bash $PROJECT_ROOT/scripts/stop_production.sh"
    echo "  查看状态: bash $PROJECT_ROOT/scripts/check_status.sh"
    echo ""
}

# ==============================================================================
# 主流程
# ==============================================================================

main() {
    print_header

    local start_time=$(date +%s)

    # 执行启动步骤
    start_infrastructure || exit 1
    sleep 2

    start_memory_system || true
    sleep 1

    start_knowledge_graph || true
    sleep 1

    start_dynamic_prompt_system || true
    sleep 1

    start_xiaonuo_agent || true
    sleep 1

    start_athena_agent || true
    sleep 1

    start_api_gateway || true

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    show_startup_summary

    echo -e "${GREEN}✅ 生产环境启动完成！耗时: ${duration}秒${NC}"
    echo ""
}

# 运行主流程
main "$@"
