#!/bin/bash
#
# 专利全文处理系统 - 生产环境启动脚本
# Patent Full Text Processing System - Production Startup Script
#
# 使用平台已有的数据库服务，只启动专利处理应用
#
# 作者: Athena平台团队
# 创建时间: 2025-12-25
#

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
PATENT_SYSTEM_DIR="${PROJECT_ROOT}/production/dev/scripts/patent_full_text"
PHASE3_DIR="${PATENT_SYSTEM_DIR}/phase3"

# 打印带颜色的消息
print_header() {
    echo ""
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}════════════════════════════════════════════════════════════════════════════════${NC}"
    echo ""
}

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

# 检查平台数据库服务
check_platform_services() {
    print_header "🔍 检查平台数据库服务"

    local all_ok=true

    # 检查Qdrant
    if docker ps --format '{{.Names}}' | grep -q "athena-qdrant"; then
        print_success "Qdrant向量数据库 (athena-qdrant) 运行中"
    elif docker ps --format '{{.Names}}' | grep -q "qdrant"; then
        print_success "Qdrant向量数据库 (qdrant) 运行中"
    else
        print_warning "Qdrant未检测到，将尝试使用localhost:6333"
    fi

    # 检查NebulaGraph
    if docker ps --format '{{.Names}}' | grep -q "athena_nebula_graph_min"; then
        print_success "NebulaGraph图数据库 (athena_nebula_graph_min) 运行中"
    elif docker ps --format '{{.Names}}' | grep -q "nebula"; then
        print_success "NebulaGraph图数据库 (nebula) 运行中"
    else
        print_warning "NebulaGraph未检测到，将尝试使用localhost:9669"
    fi

    # 检查Redis
    if docker ps --format '{{.Names}}' | grep -q "xiaonuo-redis"; then
        print_success "Redis缓存 (xiaonuo-redis) 运行中"
    elif docker ps --format '{{.Names}}' | grep -q "redis"; then
        print_success "Redis缓存 (redis) 运行中"
    else
        print_warning "Redis未检测到，将尝试使用localhost:6379"
    fi

    echo ""
}

# 验证环境配置
validate_config() {
    print_header "🔧 验证环境配置"

    if [ -f "${PATENT_SYSTEM_DIR}/.env" ]; then
        print_success ".env配置文件存在"
    else
        print_error ".env配置文件缺失"
        return 1
    fi

    # 检查必需目录
    local required_dirs=(
        "${PROJECT_ROOT}/apps/apps/patents/PDF"
        "${PROJECT_ROOT}/apps/apps/patents/checkpoints"
        "${PROJECT_ROOT}/apps/apps/patents/logs"
        "${PROJECT_ROOT}/models/patent"
    )

    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "目录存在: $dir"
        else
            print_warning "目录缺失: $dir，正在创建..."
            mkdir -p "$dir"
            print_success "已创建: $dir"
        fi
    done

    echo ""
}

# 启动专利处理应用
start_patent_app() {
    print_header "🚀 启动专利处理应用"

    cd "${PHASE3_DIR}"

    # 检查主程序
    if [ ! -f "pdf_monitor_service.py" ]; then
        print_error "PDF监控服务不存在: pdf_monitor_service.py"
        return 1
    fi

    print_info "启动PDF监控服务..."

    # 设置环境变量
    export PYTHONPATH="${PATENT_SYSTEM_DIR}:${PHASE3_DIR}:${PYTHONPATH}"
    export ATHENA_HOME="${PROJECT_ROOT}"
    export PATENT_PDF_PATH="${PROJECT_ROOT}/apps/apps/patents/PDF"
    export PATENT_LOG_PATH="${PROJECT_ROOT}/apps/apps/patents/logs"

    # 使用nohup在后台启动
    nohup /opt/homebrew/bin/python3 pdf_monitor_service.py \
        --watch-directory "${PATENT_PDF_PATH}" \
        --recursive \
        --interval 5.0 \
        > "${PROJECT_ROOT}/apps/apps/patents/logs/pdf_monitor.log" 2>&1 &

    local pid=$!
    echo $pid > "${PATENT_SYSTEM_DIR}/pids/patent_app.pid"

    # 等待启动
    sleep 3

    # 检查进程
    if ps -p $pid > /dev/null; then
        print_success "PDF监控服务启动成功 (PID: $pid)"
    else
        print_error "PDF监控服务启动失败"
        return 1
    fi

    echo ""
}

# 健康检查
health_check() {
    print_header "🔍 服务健康检查"

    # 检查应用进程
    local pid_file="${PATENT_SYSTEM_DIR}/pids/patent_app.pid"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            print_success "专利处理应用运行中 (PID: $pid)"
        else
            print_warning "专利处理应用未运行"
        fi
    else
        print_warning "未找到PID文件"
    fi

    # 检查日志
    local log_file="${PROJECT_ROOT}/apps/apps/patents/logs/patent_app.log"
    if [ -f "$log_file" ]; then
        print_success "日志文件: $log_file"
        echo ""
        echo "最近的日志:"
        tail -5 "$log_file" 2>/dev/null || true
    else
        print_warning "日志文件尚未生成"
    fi

    echo ""
}

# 显示访问信息
show_access_info() {
    print_header "📡 服务访问信息"

    echo "专利全文处理系统已启动！"
    echo ""
    echo "📊 服务状态:"
    echo "   应用进程: 查看日志 ${PROJECT_ROOT}/apps/apps/patents/logs/patent_app.log"
    echo ""
    echo "🗄️  数据库服务 (平台提供):"
    echo "   • Qdrant: http://localhost:6333"
    echo "   • NebulaGraph: localhost:9669"
    echo "   • Redis: localhost:6379"
    echo ""
    echo "📁 数据目录:"
    echo "   • PDF存储: ${PROJECT_ROOT}/apps/apps/patents/PDF"
    echo "   • 日志目录: ${PROJECT_ROOT}/apps/apps/patents/logs"
    echo ""
    echo "💡 使用方法:"
    echo "   查看状态: bash $0 status"
    echo "   停止服务: bash $0 stop"
    echo "   查看日志: tail -f ${PROJECT_ROOT}/apps/apps/patents/logs/patent_app.log"
    echo ""
}

# 停止服务
stop_services() {
    print_header "⏹️  停止专利处理应用"

    local pid_file="${PATENT_SYSTEM_DIR}/pids/patent_app.pid"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p $pid > /dev/null 2>&1; then
            print_info "停止进程 $pid..."
            kill $pid
            sleep 2
            if ps -p $pid > /dev/null 2>&1; then
                print_warning "进程未响应，强制停止..."
                kill -9 $pid
            fi
            print_success "专利处理应用已停止"
        else
            print_warning "进程未运行"
        fi
        rm -f "$pid_file"
    else
        print_warning "未找到PID文件"
    fi

    echo ""
}

# 主程序
main() {
    case "${1:-start}" in
        start)
            check_platform_services
            validate_config
            start_patent_app
            health_check
            show_access_info
            print_success "专利全文处理系统部署完成！"
            ;;
        stop)
            stop_services
            ;;
        status)
            health_check
            ;;
        restart)
            stop_services
            sleep 2
            main start
            ;;
        *)
            echo "用法: $0 {start|stop|status|restart}"
            exit 1
            ;;
    esac
}

# 执行主程序
main "$@"
