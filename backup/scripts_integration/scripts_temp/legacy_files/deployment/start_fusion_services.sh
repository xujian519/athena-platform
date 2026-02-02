#!/bin/bash

# 启动融合服务脚本
# 启动统一身份服务、协作中枢和通信系统

echo "🚀 启动Athena工作平台融合服务"
echo "================================"

# 设置工作目录
cd "$(dirname "$0")/.."

# 创建日志目录
mkdir -p logs/fusion

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
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

# 检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        log_warn "端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 启动服务
start_service() {
    local service_name=$1
    local service_script=$2
    local service_port=$3
    local log_file=$4

    log_info "启动 $service_name (端口: $service_port)"

    # 检查端口
    if ! check_port $service_port; then
        log_error "$service_name 启动失败 - 端口被占用"
        return 1
    fi

    # 启动服务
    nohup python3 $service_script > logs/fusion/$log_file 2>&1 &
    local pid=$!

    # 等待服务启动
    sleep 3

    # 检查服务是否成功启动
    if kill -0 $pid 2>/dev/null; then
        echo $pid > logs/fusion/${service_name}.pid
        log_info "$service_name 启动成功 (PID: $pid)"
        return 0
    else
        log_error "$service_name 启动失败"
        return 1
    fi
}

# 检查依赖
check_dependencies() {
    log_info "检查依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi

    # 检查必要的包
    python3 -c "import fastapi, uvicorn, websockets" 2>/dev/null
    if [ $? -ne 0 ]; then
        log_error "缺少必要的Python包，正在安装..."
        pip3 install fastapi uvicorn websockets httpx
    fi

    log_info "依赖检查完成"
}

# 清理旧进程
cleanup_old_processes() {
    log_info "清理旧进程..."

    # 杀死可能存在的服务进程
    for service in "unified-identity" "intelligent-collaboration" "websocket-server" "api-gateway-enhanced"; do
        if [ -f logs/fusion/${service}.pid ]; then
            local pid=$(cat logs/fusion/${service}.pid)
            if kill -0 $pid 2>/dev/null; then
                kill $pid
                log_info "已停止旧的 $service 进程 (PID: $pid)"
            fi
            rm -f logs/fusion/${service}.pid
        fi
    done

    # 等待进程完全退出
    sleep 2
}

# 启动所有融合服务
start_fusion_services() {
    log_info "启动融合服务..."

    # 1. 统一身份服务
    start_service "unified-identity" \
        "services/unified-identity/api_server.py" \
        8090 \
        "unified-identity.log"

    # 2. 智能协作中枢
    start_service "intelligent-collaboration" \
        "services/intelligent-collaboration/api_server.py" \
        8091 \
        "intelligent-collaboration.log"

    # 3. WebSocket通信服务
    start_service "websocket-server" \
        "services/communication-hub/websocket_server.py" \
        8092 \
        "websocket-server.log"

    # 4. 增强版API网关
    start_service "api-gateway-enhanced" \
        "services/api-gateway/src/main_enhanced.py" \
        8080 \
        "api-gateway-enhanced.log"
}

# 等待服务就绪
wait_for_services() {
    log_info "等待服务就绪..."

    local services=(
        "8090:统一身份服务"
        "8091:协作中枢"
        "8092:WebSocket服务"
        "8080:API网关"
    )

    for service_info in "${services[@]}"; do
        local port=${service_info%:*}
        local name=${service_info#*:}

        echo -n "等待 $name (端口 $port)..."
        local retries=0
        local max_retries=30

        while [ $retries -lt $max_retries ]; do
            if curl -s http://localhost:$port/health >/dev/null 2>&1; then
                echo " ✅"
                break
            fi
            echo -n "."
            sleep 1
            ((retries++))
        done

        if [ $retries -eq $max_retries ]; then
            echo " ❌"
            log_error "$name 启动超时"
            return 1
        fi
    done
}

# 验证服务
verify_services() {
    log_info "验证服务状态..."

    echo -e "\n${BLUE}服务状态检查${NC}"
    echo "================"

    # 检查各个服务的健康状态
    declare -A service_urls=(
        ["统一身份服务"]="http://localhost:8090/api/v1/health"
        ["协作中枢"]="http://localhost:8091/api/v1/health"
        ["WebSocket服务"]="http://localhost:8092/health"
        ["API网关"]="http://localhost:8080/health"
    )

    for service_name in "${!service_urls[@]}"; do
        local url=${service_urls[$service_name]}
        if curl -s $url >/dev/null 2>&1; then
            echo -e "${GREEN}✅${NC} $service_name - 运行正常"
        else
            echo -e "${RED}❌${NC} $service_name - 无法访问"
        fi
    done
}

# 显示服务信息
show_service_info() {
    echo -e "\n${BLUE}服务信息${NC}"
    echo "============"
    echo -e "\n📍 API端点:"
    echo "  • 统一身份服务: http://localhost:8090"
    echo "  • 智能协作中枢: http://localhost:8091"
    echo "  • API网关: http://localhost:8080"
    echo -e "\n🔌 WebSocket:"
    echo "  • 通信服务: ws://localhost:8092"
    echo -e "\n📚 API文档:"
    echo "  • 身份服务: http://localhost:8090/docs"
    echo "  • 协作中枢: http://localhost:8091/docs"
    echo "  • API网关: http://localhost:8080/docs"
    echo -e "\n🤖 AI家庭服务:"
    echo "  • POST /api/v1/family/collaborate - 创建协作任务"
    echo "  • GET  /api/v1/family/{task_id}/status - 查询任务状态"
    echo -e "\n📝 日志文件:"
    echo "  • 位置: logs/fusion/"
    echo "  • 查看命令: tail -f logs/fusion/[service].log"
}

# 主函数
main() {
    echo -e "${BLUE}Athena工作平台融合服务启动脚本${NC}"
    echo "===================================="
    echo

    # 检查依赖
    check_dependencies
    echo

    # 清理旧进程
    cleanup_old_processes
    echo

    # 启动服务
    start_fusion_services
    echo

    # 等待服务就绪
    wait_for_services
    echo

    # 验证服务
    verify_services
    echo

    # 显示服务信息
    show_service_info

    echo -e "\n${GREEN}🎉 融合服务启动完成！${NC}"
    echo -e "\n提示: 使用 'bash scripts/stop_fusion_services.sh' 停止所有服务"
}

# 错误处理
set -e
trap 'log_error "脚本执行失败，正在清理..."; cleanup_old_processes; exit 1' ERR

# 执行主函数
main "$@"