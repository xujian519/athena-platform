#!/bin/bash
# Athena多模态文件系统 - 完整启动脚本（修复版）
# Fixed Complete Startup Script for Athena Multimodal File System
# 修复内容: 自动创建存储目录、检查端口占用、完整错误处理、支持后台运行、PID管理
# Author: Athena Team | Date: 2026-02-24 | Version: 2.1.0

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目路径
cd "/Users/xujian/Athena工作平台"
PROJECT_ROOT=$(pwd)
SERVICE_DIR="${PROJECT_ROOT}/services/multimodal"

# 配置（需要在SERVICE_DIR之后定义）
SERVICE_PORT=8021
SERVICE_NAME="athena-multimodal"
PYTHON_SCRIPT="multimodal_service_fixed.py"
PID_FILE="/tmp/${SERVICE_NAME}.pid"
LOG_FILE="${SERVICE_DIR}/logs/multimodal_startup.log"

echo -e "${BLUE}======================================${NC}"
echo -e "${BLUE}🚀 Athena多模态文件系统启动脚本${NC}"
echo -e "${BLUE}======================================${NC}"
echo ""

# 函数：打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# 函数：检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 函数：检查端口是否被占用
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 1  # 端口被占用
    else
        return 0  # 端口可用
    fi
}

# 函数：停止已运行的服务
stop_running_service() {
    if [ -f "$PID_FILE" ]; then
        local old_pid=$(cat "$PID_FILE")
        if ps -p "$old_pid" > /dev/null 2>&1; then
            print_info "发现运行中的服务 (PID: $old_pid)，正在停止..."
            kill "$old_pid" 2>/dev/null || true
            sleep 2
            if ps -p "$old_pid" > /dev/null 2>&1; then
                print_warning "进程无法正常终止，强制杀死..."
                kill -9 "$old_pid" 2>/dev/null || true
            fi
            print_success "旧服务已停止"
        fi
        rm -f "$PID_FILE"
    fi
}

# 函数：激活虚拟环境
activate_venv() {
    if [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
        print_info "激活Python虚拟环境..."
        source "${PROJECT_ROOT}/venv/bin/activate"
        print_success "虚拟环境已激活"
    elif [ -f "${PROJECT_ROOT}/.venv/bin/activate" ]; then
        print_info "激活Python虚拟环境 (.venv)..."
        source "${PROJECT_ROOT}/.venv/bin/activate"
        print_success "虚拟环境已激活"
    else
        print_warning "未找到虚拟环境，使用系统Python"
    fi
}

# 函数：检查依赖
check_dependencies() {
    print_info "检查Python依赖..."

    # 检查Python版本
    if ! command_exists python3; then
        print_error "未找到Python3"
        exit 1
    fi

    local python_version=$(python3 --version 2>&1 | awk '{print $2}')
    print_success "Python版本: $python_version"

    # 检查必要的Python包
    local required_packages=("fastapi" "uvicorn" "aiofiles" "python-multipart")
    local missing_packages=()

    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            missing_packages+=("$package")
        fi
    done

    if [ ${#missing_packages[@]} -gt 0 ]; then
        print_warning "缺少以下Python包: ${missing_packages[*]}"
        print_info "正在安装缺少的包..."
        pip3 install "${missing_packages[@]}" || {
            print_error "安装依赖失败"
            exit 1
        }
        print_success "依赖安装完成"
    else
        print_success "所有依赖已满足"
    fi
}

# 函数：创建必要的目录
create_directories() {
    print_info "创建必要的目录..."

    local dirs=(
        "storage-system/data/documents/multimodal"
        "storage-system/data/documents/thumbnails"
        "storage-system/data/documents/temp"
        "logs"
    )

    for dir in "${dirs[@]}"; do
        mkdir -p "${PROJECT_ROOT}/${dir}"
        print_success "创建目录: ${dir}"
    done
}

# 函数：检查端口
check_service_port() {
    print_info "检查端口 ${SERVICE_PORT}..."

    if ! check_port $SERVICE_PORT; then
        print_warning "端口 ${SERVICE_PORT} 已被占用"
        echo ""
        print_info "正在查找占用进程..."
        lsof -Pi :$SERVICE_PORT -sTCP:LISTEN || true
        echo ""
        read -p "是否要停止占用端口的进程? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            local pid=$(lsof -ti :$SERVICE_PORT)
            if [ -n "$pid" ]; then
                kill "$pid" 2>/dev/null || kill -9 "$pid" 2>/dev/null
                print_success "进程已停止"
                sleep 2
            fi
        else
            print_error "无法启动服务，端口被占用"
            exit 1
        fi
    fi

    print_success "端口 ${SERVICE_PORT} 可用"
}

# 函数：启动服务
start_service() {
    print_info "启动多模态文件系统服务..."

    cd "$SERVICE_DIR"

    # 启动服务（后台运行）
    nohup python3 "$PYTHON_SCRIPT" > "$LOG_FILE" 2>&1 &
    local service_pid=$!

    # 保存PID
    echo "$service_pid" > "$PID_FILE"

    # 等待服务启动
    print_info "等待服务启动..."
    local max_wait=10
    local wait_count=0

    while [ $wait_count -lt $max_wait ]; do
        if check_port $SERVICE_PORT; then
            break
        fi
        sleep 1
        wait_count=$((wait_count + 1))
        echo -n "."
    done
    echo ""

    # 验证服务是否启动成功
    if ps -p "$service_pid" > /dev/null 2>&1; then
        print_success "服务启动成功！"
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🎉 Athena多模态文件系统已启动${NC}"
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "📍 服务信息:"
        echo -e "   服务地址: ${BLUE}http://localhost:${SERVICE_PORT}${NC}"
        echo -e "   API文档: ${BLUE}http://localhost:${SERVICE_PORT}/docs${NC}"
        echo -e "   ReDoc文档: ${BLUE}http://localhost:${SERVICE_PORT}/redoc${NC}"
        echo -e "   健康检查: ${BLUE}http://localhost:${SERVICE_PORT}/health${NC}"
        echo ""
        echo -e "📝 进程信息:"
        echo -e "   PID: ${service_pid}"
        echo -e "   日志: ${LOG_FILE}"
        echo ""
        echo -e "🔧 常用命令:"
        echo -e "   健康检查: curl http://localhost:${SERVICE_PORT}/health"
        echo -e "   上传文件: curl -X POST -F 'file=@test.jpg' http://localhost:${SERVICE_PORT}/api/files/upload"
        echo -e "   文件列表: curl http://localhost:${SERVICE_PORT}/api/files/list"
        echo -e "   查看日志: tail -f ${LOG_FILE}"
        echo -e "   停止服务: kill $service_pid"
        echo ""
        echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    else
        print_error "服务启动失败"
        print_info "查看日志: cat ${LOG_FILE}"
        exit 1
    fi
}

# 函数：快速健康检查
health_check() {
    print_info "执行健康检查..."

    sleep 2  # 等待服务完全启动

    local response=$(curl -s "http://localhost:${SERVICE_PORT}/health" 2>/dev/null || echo "{}")

    if echo "$response" | grep -q '"status".*"healthy"'; then
        print_success "健康检查通过"

        # 显示服务信息
        echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
    else
        print_warning "健康检查未通过，但服务可能仍在启动中"
        echo "响应: $response"
    fi
}

# ==================== 主流程 ====================
main() {
    # 解析命令行参数
    local action="start"
    if [ $# -gt 0 ]; then
        action=$1
    fi

    case $action in
        start)
            stop_running_service
            activate_venv
            check_dependencies
            create_directories
            check_service_port
            start_service
            health_check
            ;;

        stop)
            print_info "停止多模态文件系统服务..."
            stop_running_service
            print_success "服务已停止"
            ;;

        restart)
            print_info "重启多模态文件系统服务..."
            stop_running_service
            sleep 2
            activate_venv
            check_dependencies
            create_directories
            check_service_port
            start_service
            health_check
            ;;

        status)
            print_info "服务状态:"
            if [ -f "$PID_FILE" ]; then
                local pid=$(cat "$PID_FILE")
                if ps -p "$pid" > /dev/null 2>&1; then
                    print_success "服务正在运行 (PID: $pid)"
                    echo ""
                    health_check
                else
                    print_warning "PID文件存在但进程未运行"
                    rm -f "$PID_FILE"
                fi
            else
                print_warning "服务未运行"
            fi
            ;;

        health)
            health_check
            ;;

        logs)
            if [ -f "$LOG_FILE" ]; then
                tail -f "$LOG_FILE"
            else
                print_error "日志文件不存在: $LOG_FILE"
            fi
            ;;

        *)
            echo "用法: $0 {start|stop|restart|status|health|logs}"
            echo ""
            echo "命令说明:"
            echo "  start   - 启动服务"
            echo "  stop    - 停止服务"
            echo "  restart - 重启服务"
            echo "  status  - 查看服务状态"
            echo "  health  - 健康检查"
            echo "  logs    - 查看实时日志"
            exit 1
            ;;
    esac
}

# 运行主流程
main "$@"
