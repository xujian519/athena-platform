#!/bin/bash

# 专利行动层部署脚本
# Patent Action Layer Deployment Script
# Created by Athena + 小诺 (AI助手)
# Date: 2025-12-05

set -e

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

log_header() {
    echo -e "${PURPLE}[HEADER]${NC} $1"
}

log_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

# 项目配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
PATENT_ACTION_DIR="${PROJECT_ROOT}/patent-platform/workspace/src/action"
SERVICE_DIR="${PROJECT_ROOT}/patent-platform/workspace/src/action"
LOG_DIR="${PROJECT_ROOT}/patent-platform/workspace/documentation/logs/action_layer"
PID_DIR="${PROJECT_ROOT}/patent-platform/workspace/pids/action_layer"

# 端口配置
ACTION_SERVICE_PORT=9000

# 显示部署横幅
show_banner() {
    echo -e "${CYAN}"
    echo "============================================================"
    echo "        🚀 专利行动层部署脚本"
    echo "     Patent Action Layer Deployment Script"
    echo "    Created by Athena + 小诺 (AI助手)"
    echo "            Date: 2025-12-05"
    echo "============================================================"
    echo -e "${NC}"
}

# 检查先决条件
check_prerequisites() {
    log_header "检查系统先决条件..."

    # 检查Python版本
    python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    log_info "Python版本: $python_version"

    if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
        log_error "需要Python 3.8或更高版本"
        exit 1
    fi

    # 检查必要的Python包
    log_step "检查Python依赖包..."
    required_packages=("fastapi" "uvicorn" "pydantic" "networkx" "asyncio")

    for package in "${required_packages[@]}"; do
        if python3 -c "import $package" 2>/dev/null; then
            log_success "✓ $package"
        else
            log_warning "✗ $package (将自动安装)"
        fi
    done

    # 检查端口占用
    log_step "检查端口占用..."
    if lsof -i :$ACTION_SERVICE_PORT >/dev/null 2>&1; then
        log_warning "端口 $ACTION_SERVICE_PORT 已被占用"
        log_info "尝试停止占用进程..."
        lsof -ti:$ACTION_SERVICE_PORT | xargs kill -9 2>/dev/null || true
        sleep 2
    fi

    log_success "先决条件检查完成"
}

# 安装依赖
install_dependencies() {
    log_header "安装Python依赖包..."

    # 切换到action目录
    cd "$PATENT_ACTION_DIR"

    # 安装依赖
    log_step "安装FastAPI和相关依赖..."
    pip3 install fastapi uvicorn pydantic networkx --quiet

    # 安装其他可能需要的依赖
    log_step "安装其他依赖..."
    pip3 install aiofiles python-multipart --quiet

    log_success "依赖安装完成"
}

# 创建必要目录
create_directories() {
    log_header "创建部署目录..."

    # 创建日志目录
    if [[ ! -d "$LOG_DIR" ]]; then
        mkdir -p "$LOG_DIR"
        log_info "创建日志目录: $LOG_DIR"
    fi

    # 创建PID目录
    if [[ ! -d "$PID_DIR" ]]; then
        mkdir -p "$PID_DIR"
        log_info "创建PID目录: $PID_DIR"
    fi

    # 创建配置目录
    config_dir="${PROJECT_ROOT}/patent-platform/workspace/config/action"
    if [[ ! -d "$config_dir" ]]; then
        mkdir -p "$config_dir"
        log_info "创建配置目录: $config_dir"
    fi

    log_success "目录创建完成"
}

# 生成配置文件
generate_config() {
    log_header "生成配置文件..."

    config_file="${PROJECT_ROOT}/patent-platform/workspace/config/action/action_service_config.yaml"

    cat > "$config_file" << EOF
# 专利行动层服务配置
# Patent Action Layer Service Configuration

# 服务基础配置
service:
  name: "patent_action_service"
  version: "1.0.0"
  host: "0.0.0.0"
  port: $ACTION_SERVICE_PORT
  debug: false
  log_level: "INFO"

# 认知行动桥梁配置
cognitive_bridge:
  max_concurrent_decisions: 20
  decision_timeout: 300
  enable_caching: true
  cache_ttl: 3600

# 执行器工厂配置
executor_factory:
  max_concurrent_executions: 50
  default_timeout: 600
  retry_attempts: 3
  retry_delay: 30

# 智能调度器配置
scheduler:
  max_concurrent_tasks: 10
  default_strategy: "cognitive_guided"
  cognitive_weights:
    priority_weight: 0.3
    deadline_weight: 0.3
    cognitive_score_weight: 0.2
    resource_efficiency_weight: 0.2

# 工作流编排器配置
orchestrator:
  max_concurrent_workflows: 5
  default_parallel_steps: 3
  workflow_timeout: 7200
  step_retry_count: 3
  step_retry_delay: 30

# 数据库配置 (如果需要)
database:
  type: "sqlite"
  path: "${PROJECT_ROOT}/patent-platform/workspace/data/action_layer.db"

# 缓存配置
cache:
  type: "redis"
  host: "localhost"
  port: 6379
  db: 1
  default_ttl: 3600

# 监控配置
monitoring:
  enable_metrics: true
  metrics_port: 9001
  health_check_interval: 60
  performance_tracking: true

# 日志配置
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "${LOG_DIR}/action_service.log"
  max_size: "100MB"
  backup_count: 5

# 安全配置
security:
  enable_cors: true
  allowed_origins: ["*"]
  rate_limit: 100
  request_timeout: 300

# 集成配置
integration:
  cognitive_service_endpoint: "http://localhost:8080"
  patent_api_endpoint: "http://localhost:8000"
  enable_auto_discovery: true
EOF

    log_success "配置文件生成完成: $config_file"
}

# 启动专利行动层服务
start_action_service() {
    log_header "启动专利行动层服务..."

    # 切换到服务目录
    cd "$SERVICE_DIR"

    # 设置Python路径
    export PYTHONPATH="${PROJECT_ROOT}/patent-platform/workspace/src/action:${PROJECT_ROOT}/patent-platform/workspace/src:$PYTHONPATH"

    # 启动服务
    log_step "启动专利行动层API服务..."

    nohup python3 patent_action_service.py \
        > "${LOG_DIR}/action_service.log" 2>&1 &

    # 获取进程ID
    pid=$!
    echo $pid > "${PID_DIR}/patent_action_service.pid"

    log_info "服务进程ID: $pid"
    log_info "日志文件: ${LOG_DIR}/action_service.log"
    log_info "PID文件: ${PID_DIR}/patent_action_service.pid"

    # 等待服务启动
    log_step "等待服务启动..."
    sleep 5

    # 健康检查
    if curl -f -s "http://localhost:$ACTION_SERVICE_PORT/health" > /dev/null; then
        log_success "✓ 专利行动层服务启动成功"
        log_info "API文档: http://localhost:$ACTION_SERVICE_PORT/docs"
        log_info "健康检查: http://localhost:$ACTION_SERVICE_PORT/health"
    else
        log_error "✗ 服务启动失败，请检查日志"
        tail -n 20 "${LOG_DIR}/action_service.log"
        exit 1
    fi
}

# 运行系统测试
run_system_test() {
    log_header "运行系统测试..."

    # 测试API健康检查
    log_step "测试API健康检查..."
    health_response=$(curl -s "http://localhost:$ACTION_SERVICE_PORT/health")
    if echo "$health_response" | grep -q '"status":"healthy"'; then
        log_success "✓ 健康检查通过"
    else
        log_warning "⚠ 健康检查异常"
    fi

    # 测试组件状态
    log_step "测试组件状态..."
    components_response=$(curl -s "http://localhost:$ACTION_SERVICE_PORT/api/v1/status/components")
    if echo "$components_response" | grep -q '"cognitive_bridge"'; then
        log_success "✓ 组件状态正常"
    else
        log_warning "⚠ 组件状态异常"
    fi

    # 测试执行器列表
    log_step "测试执行器列表..."
    executors_response=$(curl -s "http://localhost:$ACTION_SERVICE_PORT/api/v1/executors")
    if echo "$executors_response" | grep -q '"patent_analysis"'; then
        log_success "✓ 执行器列表正常"
    else
        log_warning "⚠ 执行器列表异常"
    fi

    # 测试工作流定义
    log_step "测试工作流定义..."
    workflows_response=$(curl -s "http://localhost:$ACTION_SERVICE_PORT/api/v1/workflows/definitions")
    if echo "$workflows_response" | grep -q '"patent_analysis_standard"'; then
        log_success "✓ 工作流定义正常"
    else
        log_warning "⚠ 工作流定义异常"
    fi

    log_success "系统测试完成"
}

# 显示部署信息
show_deployment_info() {
    log_header "部署信息"

    echo -e "${GREEN}🎉 专利行动层部署成功！${NC}"
    echo
    echo -e "${CYAN}📍 服务信息:${NC}"
    echo -e "  服务名称: 专利行动层API服务"
    echo -e "  版本: v1.0.0"
    echo -e "  端口: $ACTION_SERVICE_PORT"
    echo -e "  进程ID: $(cat ${PID_DIR}/patent_action_service.pid)"
    echo
    echo -e "${CYAN}🔗 访问地址:${NC}"
    echo -e "  API文档: http://localhost:$ACTION_SERVICE_PORT/docs"
    echo -e "  ReDoc文档: http://localhost:$ACTION_SERVICE_PORT/redoc"
    echo -e "  健康检查: http://localhost:$ACTION_SERVICE_PORT/health"
    echo -e "  服务根路径: http://localhost:$ACTION_SERVICE_PORT/"
    echo
    echo -e "${CYAN}📋 主要功能:${NC}"
    echo -e "  ✓ 认知决策执行"
    echo -e "  ✓ 智能任务调度"
    echo -e "  ✓ 专利工作流编排"
    echo -e "  ✓ 专利专用执行器"
    echo -e "  ✓ 实时状态监控"
    echo
    echo -e "${CYAN}🗂️ 文件位置:${NC}"
    echo -e "  服务文件: ${SERVICE_DIR}/patent_action_service.py"
    echo -e "  配置文件: ${PROJECT_ROOT}/patent-platform/workspace/config/action/action_service_config.yaml"
    echo -e "  日志文件: ${LOG_DIR}/action_service.log"
    echo -e "  PID文件: ${PID_DIR}/patent_action_service.pid"
    echo
    echo -e "${CYAN}🛠️ 管理命令:${NC}"
    echo -e "  查看日志: tail -f ${LOG_DIR}/action_service.log"
    echo -e "  停止服务: bash ${PROJECT_ROOT}/scripts/stop_patent_action_layer.sh"
    echo -e "  重启服务: bash ${PROJECT_ROOT}/scripts/restart_patent_action_layer.sh"
    echo -e "  状态检查: curl http://localhost:$ACTION_SERVICE_PORT/health"
    echo
}

# 主函数
main() {
    show_banner

    log_info "开始部署专利行动层..."

    check_prerequisites
    install_dependencies
    create_directories
    generate_config
    start_action_service
    run_system_test
    show_deployment_info

    log_success "🚀 专利行动层部署完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查日志"; exit 1' ERR

# 执行主函数
main "$@"