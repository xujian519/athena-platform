#!/bin/bash
# Athena API Gateway 完整演示脚本
# 启动网关服务和示例微服务

set -euo pipefail

# 脚本配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DEMO_DIR="$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_command() {
    echo -e "${CYAN}[COMMAND]${NC} $1"
}

# 清理函数
cleanup() {
    log_info "清理演示环境..."
    
    # 停止所有相关进程
    pkill -f "athena_gateway.py" 2>/dev/null || true
    pkill -f "user_service.py" 2>/dev/null || true
    pkill -f "product_service.py" 2>/dev/null || true
    
    # 删除临时文件
    rm -f "$PROJECT_ROOT/data/gateway.pid" 2>/dev/null || true
    
    log_success "清理完成"
}

# 检查端口是否被占用
check_port() {
    local port=$1
    local service=$2
    
    if lsof -i ":$port" >/dev/null 2>&1; then
        log_warning "$service 端口 $port 已被占用"
        return 1
    fi
    return 0
}

# 等待服务启动
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=30
    local attempt=0
    
    log_info "等待 $service_name 启动..."
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            log_success "$service_name 已启动 (耗时 $((attempt * 2)) 秒)"
            return 0
        fi
        
        attempt=$((attempt + 1))
        sleep 2
    done
    
    log_error "$service_name 启动超时"
    return 1
}

# 检查依赖
check_dependencies() {
    log_step "检查系统依赖..."
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    
    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 未安装"
        exit 1
    fi
    
    # 检查curl
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安装"
        exit 1
    fi
    
    log_success "依赖检查通过"
}

# 安装Python依赖
install_dependencies() {
    log_step "安装Python依赖包..."
    
    cd "$DEMO_DIR"
    
    # 安装Gateway依赖
    if [[ -f "requirements.txt" ]]; then
        log_command "pip3 install -r requirements.txt"
        python3 -m pip install -r requirements.txt
        log_success "Gateway依赖安装完成"
    fi
    
    # 安装示例服务依赖
    if [[ -f "examples/requirements.txt" ]]; then
        log_command "pip3 install -r examples/requirements.txt"
        python3 -m pip install -r examples/requirements.txt
    else
        # 安装基本依赖
        log_command "pip3 install fastapi uvicorn aiohttp pydantic"
        python3 -m pip install fastapi uvicorn aiohttp pydantic
    fi
    
    log_success "Python依赖安装完成"
}

# 启动API Gateway
start_gateway() {
    log_step "启动 Athena API Gateway..."
    
    # 检查端口
    if ! check_port 8080 "API Gateway"; then
        log_error "无法启动 API Gateway，端口已被占用"
        return 1
    fi
    
    cd "$DEMO_DIR"
    log_command "./start_gateway.sh start"
    ./start_gateway.sh start
    
    # 等待Gateway启动
    if wait_for_service "http://localhost:8080/health" "API Gateway"; then
        log_success "API Gateway 启动成功"
        return 0
    else
        log_error "API Gateway 启动失败"
        return 1
    fi
}

# 启动示例服务
start_example_services() {
    log_step "启动示例微服务..."
    
    cd "$DEMO_DIR"
    
    # 启动用户服务
    log_info "启动用户服务..."
    if ! check_port 8001 "用户服务"; then
        log_warning "用户服务端口已被占用，跳过启动"
    else
        log_command "python3 examples/user_service.py > /tmp/user_service.log 2>&1 &"
        python3 examples/user_service.py > /tmp/user_service.log 2>&1 &
        
        if wait_for_service "http://localhost:8001/health" "用户服务"; then
            log_success "用户服务启动成功"
        else
            log_error "用户服务启动失败"
        fi
    fi
    
    # 启动产品服务
    log_info "启动产品服务..."
    if ! check_port 8002 "产品服务"; then
        log_warning "产品服务端口已被占用，跳过启动"
    else
        log_command "python3 examples/product_service.py > /tmp/product_service.log 2>&1 &"
        python3 examples/product_service.py > /tmp/product_service.log 2>&1 &
        
        if wait_for_service "http://localhost:8002/health" "产品服务"; then
            log_success "产品服务启动成功"
        else
            log_error "产品服务启动失败"
        fi
    fi
    
    # 等待服务注册
    log_info "等待服务注册..."
    sleep 10
}

# 配置路由
configure_routes() {
    log_step "配置API路由..."
    
    cd "$DEMO_DIR"
    log_command "python3 configure_routes.py"
    python3 configure_routes.py
    
    log_success "路由配置完成"
}

# 运行测试
run_tests() {
    log_step "运行功能测试..."
    
    cd "$DEMO_DIR"
    log_command "python3 test_gateway.py"
    python3 test_gateway.py
    
    if [ $? -eq 0 ]; then
        log_success "所有测试通过"
    else
        log_warning "部分测试失败，请检查日志"
    fi
}

# 显示服务状态
show_status() {
    log_step "显示服务状态..."
    
    echo
    echo "🔍 服务状态检查:"
    echo "───────────────────────────────────────────────────"
    
    # Gateway状态
    if curl -s "http://localhost:8080/health" >/dev/null 2>&1; then
        echo "✅ API Gateway (http://localhost:8080) - 运行中"
    else
        echo "❌ API Gateway (http://localhost:8080) - 未运行"
    fi
    
    # 用户服务状态
    if curl -s "http://localhost:8001/health" >/dev/null 2>&1; then
        echo "✅ 用户服务 (http://localhost:8001) - 运行中"
    else
        echo "❌ 用户服务 (http://localhost:8001) - 未运行"
    fi
    
    # 产品服务状态
    if curl -s "http://localhost:8002/health" >/dev/null 2>&1; then
        echo "✅ 产品服务 (http://localhost:8002) - 运行中"
    else
        echo "❌ 产品服务 (http://localhost:8002) - 未运行"
    fi
    
    echo
    echo "🌐 访问地址:"
    echo "───────────────────────────────────────────────────"
    echo "📋 API文档: http://localhost:8080/docs"
    echo "🔧 管理界面: http://localhost:8080/redoc"
    echo "🏥 健康检查: http://localhost:8080/health"
    echo
    echo "📝 API测试示例:"
    echo "───────────────────────────────────────────────────"
    echo "# 获取所有用户"
    echo "curl http://localhost:8080/api/users"
    echo
    echo "# 获取指定用户"
    echo "curl http://localhost:8080/api/users/1"
    echo
    echo "# 获取所有产品"
    echo "curl http://localhost:8080/api/products"
    echo
    echo "# 获取产品分类"
    echo "curl http://localhost:8080/api/categories"
    echo
}

# 显示帮助信息
show_help() {
    echo "Athena API Gateway 演示脚本"
    echo
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  start      - 启动完整演示环境"
    echo "  stop       - 停止所有服务"
    echo "  test       - 运行功能测试"
    echo "  test-auth  - 运行认证功能测试"
    echo "  status     - 显示服务状态"
    echo "  clean      - 清理环境"
    echo "  help       - 显示帮助信息"
    echo
    echo "示例:"
    echo "  $0 start      # 启动完整演示"
    echo "  $0 stop       # 停止所有服务"
    echo "  $0 test       # 运行功能测试"
    echo "  $0 test-auth  # 运行认证功能测试"
    echo
}

# 主演示流程
run_demo() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                          ║"
    echo "║                    🏛️ Athena API Gateway 演示系统                         ║"
    echo "║                     统一微服务接入和API管理平台                            ║"
    echo "║                                                                          ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    log_step "开始 Athena API Gateway 演示..."
    
    # 1. 检查依赖
    check_dependencies
    
    # 2. 清理环境
    cleanup
    
    # 3. 安装依赖
    install_dependencies
    
    # 4. 启动Gateway
    if ! start_gateway; then
        log_error "演示启动失败: API Gateway启动失败"
        exit 1
    fi
    
    # 5. 启动示例服务
    start_example_services
    
    # 6. 配置路由
    configure_routes
    
# 7. 运行测试
run_tests() {
    log_step "运行功能测试..."
    
    cd "$DEMO_DIR"
    
    # 基础功能测试
    log_command "python3 test_gateway.py"
    python3 test_gateway.py
    gateway_result=$?
    
    # 认证功能测试
    log_command "python3 test_auth.py"
    python3 test_auth.py
    auth_result=$?
    
    if [ $gateway_result -eq 0 ] && [ $auth_result -eq 0 ]; then
        log_success "所有测试通过"
    else
        log_warning "部分测试失败，请检查日志"
        if [ $gateway_result -ne 0 ]; then
            log_warning "基础功能测试失败"
        fi
        if [ $auth_result -ne 0 ]; then
            log_warning "认证功能测试失败"
        fi
    fi
}

# 信号处理
trap cleanup EXIT INT TERM

# 主函数
main() {
    local command=${1:-"help"}
    
    case "$command" in
        "start"|"demo")
            run_demo
            ;;
        "stop")
            cleanup
            log_success "所有服务已停止"
            ;;
        "test")
            cd "$DEMO_DIR"
            python3 test_gateway.py
            ;;
        "test-auth")
            cd "$DEMO_DIR"
            python3 test_auth.py
            ;;
        "status")
            show_status
            ;;
        "clean")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            log_error "未知命令: $command"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"