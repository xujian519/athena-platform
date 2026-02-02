#!/bin/bash
# ============================================================================
# Athena学习模块 - 本地CI/CD部署脚本
# ============================================================================
# 功能:
#   1. 运行完整测试套件
#   2. 提交代码到移动硬盘git仓库
#   3. 构建Docker镜像
#   4. 部署到生产环境
#   5. 运行烟雾测试
#
# 使用方法:
#   ./scripts/deploy_learning_module.sh [--skip-tests] [--skip-build] [--deploy-only]
#
# 作者: Athena Platform Team
# 版本: v1.1.0
# 创建时间: 2026-01-28
# ============================================================================

set -e  # 遇到错误立即退出

# ============================================================================
# 配置
# ============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 环境配置
ENVIRONMENT="${ENVIRONMENT:-production}"
CONFIG_FILE="config/athena_${ENVIRONMENT}.yaml"

# Git配置
REMOTE_NAME="origin"
REMOTE_PATH="/Volumes/AthenaData/Athena工作平台备份"
GIT_BRANCH="main"

# Docker配置
IMAGE_NAME="athena-learning-module"
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${REGISTRY:-localhost:5000}"

# 测试配置
TEST_COVERAGE_THRESHOLD=80
PYTEST_ARGS="-v --tb=short --cov=core.learning --cov-report=term-missing --cov-report=html"

# 部署配置
DEPLOY_HOST="${DEPLOY_HOST:-localhost}"
DEPLOY_PORT="${DEPLOY_PORT:-8000}"
HEALTH_CHECK_URL="http://${DEPLOY_HOST}:${DEPLOY_PORT}/health"
HEALTH_CHECK_TIMEOUT=60

# 日志文件
LOG_DIR="logs/deployments"
LOG_FILE="${LOG_DIR}/deploy_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$LOG_DIR"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================================================
# 辅助函数
# ============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo -e "[${timestamp}] [${level}] ${message}" | tee -a "$LOG_FILE"
}

log_info() {
    log "INFO" "${BLUE}$1${NC}"
}

log_success() {
    log "SUCCESS" "${GREEN}$1${NC}"
}

log_warning() {
    log "WARNING" "${YELLOW}$1${NC}"
}

log_error() {
    log "ERROR" "${RED}$1${NC}"
}

log_step() {
    log "STEP" "${PURPLE}$1${NC}"
}

print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

# ============================================================================
# 预检查
# ============================================================================

pre_flight_checks() {
    print_header "预检查"

    # 检查Python版本
    log_step "检查Python版本..."
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3未安装"
        exit 1
    fi
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log_info "Python版本: $PYTHON_VERSION"

    # 检查Docker
    log_step "检查Docker..."
    if ! command -v docker &> /dev/null; then
        log_warning "Docker未安装，将跳过Docker相关步骤"
        SKIP_DOCKER=true
    else
        log_info "Docker版本: $(docker --version)"
        SKIP_DOCKER=false
    fi

    # 检查移动硬盘
    log_step "检查移动硬盘..."
    if [ ! -d "$REMOTE_PATH" ]; then
        log_error "移动硬盘未挂载: $REMOTE_PATH"
        exit 1
    fi
    log_info "移动硬盘已挂载"

    # 检查远程仓库
    log_step "检查Git远程仓库..."
    if ! git remote | grep -q "$REMOTE_NAME"; then
        log_warning "远程仓库 '$REMOTE_NAME' 未配置"
        log_info "添加远程仓库: $REMOTE_PATH"
        git remote add "$REMOTE_NAME" "$REMOTE_PATH"
    fi
    log_info "Git远程仓库已配置"

    # 检查配置文件
    log_step "检查配置文件..."
    if [ ! -f "$CONFIG_FILE" ]; then
        log_error "配置文件不存在: $CONFIG_FILE"
        exit 1
    fi
    log_info "配置文件: $CONFIG_FILE"

    log_success "预检查完成"
}

# ============================================================================
# 运行测试
# ============================================================================

run_tests() {
    if [ "$SKIP_TESTS" = "true" ]; then
        log_warning "跳过测试 (SKIP_TESTS=true)"
        return 0
    fi

    print_header "运行测试套件"

    log_step "安装测试依赖..."
    pip install -q pytest pytest-cov pytest-asyncio pytest-benchmark pytest-timeout 2>&1 | tee -a "$LOG_FILE"

    log_step "运行单元测试..."
    if ! python3 -m pytest tests/core/learning/ -v --tb=short 2>&1 | tee -a "$LOG_FILE"; then
        log_error "单元测试失败"
        exit 1
    fi

    log_step "运行集成测试..."
    if ! python3 -m pytest tests/core/learning/integration/ -v --tb=short 2>&1 | tee -a "$LOG_FILE"; then
        log_error "集成测试失败"
        exit 1
    fi

    log_step "运行覆盖率测试..."
    COVERAGE_REPORT=$(python3 -m pytest tests/core/learning/ \
        --cov=core.learning \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        -q 2>&1 | tee -a "$LOG_FILE" | grep -E "TOTAL|core.learning")

    COVERAGE_PERCENT=$(echo "$COVERAGE_REPORT" | grep "TOTAL" | awk '{print $4}' | sed 's/%//')
    if [ -n "$COVERAGE_PERCENT" ] && [ "$COVERAGE_PERCENT" -lt "$TEST_COVERAGE_THRESHOLD" ]; then
        log_warning "覆盖率 ${COVERAGE_PERCENT}% 低于阈值 ${TEST_COVERAGE_THRESHOLD}%"
    fi

    log_success "所有测试通过"
}

# ============================================================================
# 提交代码
# ============================================================================

commit_code() {
    print_header "提交代码到远程仓库"

    log_step "检查Git状态..."
    if [ -z "$(git status --porcelain)" ]; then
        log_info "没有待提交的更改"
        return 0
    fi

    log_step "添加所有更改..."
    git add -A

    log_step "创建提交..."
    COMMIT_MESSAGE="chore: 自动部署 - $(date '+%Y-%m-%d %H:%M:%S')

- 自动提交学习模块更改
- 测试: $(python3 -m pytest tests/core/learning/ --collect-only -q 2>/dev/null | wc -l | tr -d ' ') 个测试
- 部署环境: ${ENVIRONMENT}"

    git commit -m "$COMMIT_MESSAGE" 2>&1 | tee -a "$LOG_FILE"

    log_step "推送到远程仓库..."
    if ! git push "$REMOTE_NAME" "$GIT_BRANCH" 2>&1 | tee -a "$LOG_FILE"; then
        log_error "推送失败"
        exit 1
    fi

    log_success "代码已提交到远程仓库"
}

# ============================================================================
# 构建Docker镜像
# ============================================================================

build_docker_image() {
    if [ "$SKIP_DOCKER" = "true" ] || [ "$SKIP_BUILD" = "true" ]; then
        log_warning "跳过Docker构建"
        return 0
    fi

    print_header "构建Docker镜像"

    log_step "创建Dockerfile..."
    cat > Dockerfile.learning <<'EOF'
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制学习模块
COPY core/learning/ /app/core/learning/
COPY tests/core/learning/ /app/tests/core/learning/

# 设置环境变量
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "pytest", "tests/core/learning/", "-v", "--tb=short"]
EOF

    log_step "构建镜像: ${IMAGE_NAME}:${IMAGE_TAG}"
    if ! docker build -f Dockerfile.learning -t "${IMAGE_NAME}:${IMAGE_TAG}" . 2>&1 | tee -a "$LOG_FILE"; then
        log_error "Docker构建失败"
        exit 1
    fi

    # 如果配置了registry，推送镜像
    if [ -n "$REGISTRY" ]; then
        log_step "推送镜像到registry..."
        docker tag "${IMAGE_NAME}:${IMAGE_TAG}" "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        docker push "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}" 2>&1 | tee -a "$LOG_FILE"
    fi

    log_success "Docker镜像构建完成"
}

# ============================================================================
# 部署到生产环境
# ============================================================================

deploy_to_production() {
    if [ "$DEPLOY_ONLY" != "true" ] && [ "$SKIP_DEPLOY" = "true" ]; then
        log_warning "跳过部署"
        return 0
    fi

    print_header "部署到生产环境"

    log_step "停止现有服务..."
    if pgrep -f "athena.*learning" > /dev/null; then
        pkill -f "athena.*learning" || true
        sleep 2
    fi

    log_step "清理旧日志..."
    find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true

    log_step "启动学习模块服务..."
    nohup python3 -m core.learning.autonomous_learning_system \
        --config "$CONFIG_FILE" \
        --log-level INFO \
        > logs/learning_module.log 2>&1 &

    LEARNING_PID=$!
    echo "$LEARNING_PID" > logs/learning_module.pid

    log_step "等待服务启动..."
    sleep 5

    if ps -p "$LEARNING_PID" > /dev/null; then
        log_success "学习模块服务已启动 (PID: $LEARNING_PID)"
    else
        log_error "服务启动失败"
        cat logs/learning_module.log | tail -20
        exit 1
    fi
}

# ============================================================================
# 健康检查
# ============================================================================

health_check() {
    print_header "健康检查"

    log_step "检查服务状态..."
    if [ ! -f logs/learning_module.pid ]; then
        log_error "PID文件不存在"
        return 1
    fi

    LEARNING_PID=$(cat logs/learning_module.pid)
    if ! ps -p "$LEARNING_PID" > /dev/null; then
        log_error "服务进程不存在 (PID: $LEARNING_PID)"
        return 1
    fi

    log_step "运行烟雾测试..."
    python3 -c "
import asyncio
import sys
sys.path.insert(0, '.')

async def smoke_test():
    from core.learning.autonomous_learning_system import AutonomousLearningSystem

    # 创建测试实例
    system = AutonomousLearningSystem(agent_id='smoke_test')

    # 测试基本功能
    await system.learn_from_experience(
        context={'task': 'smoke_test'},
        action='test_action',
        result={'status': 'success'},
        reward=0.8
    )

    metrics = await system.get_learning_metrics()
    assert metrics['learning']['total_experiences'] >= 1

    print('✓ 烟雾测试通过')

asyncio.run(smoke_test())
" 2>&1 | tee -a "$LOG_FILE"

    if [ $? -eq 0 ]; then
        log_success "健康检查通过"
        return 0
    else
        log_error "健康检查失败"
        return 1
    fi
}

# ============================================================================
# 生成部署报告
# ============================================================================

generate_report() {
    print_header "部署报告"

    local report_file="${LOG_DIR}/deploy_report_$(date +%Y%m%d_%H%M%S).txt"

    cat > "$report_file" <<EOF
================================================================================
Athena学习模块部署报告
================================================================================
部署时间: $(date '+%Y-%m-%d %H:%M:%S')
环境: ${ENVIRONMENT}
Git分支: ${GIT_BRANCH}
提交: $(git rev-parse --short HEAD)

--------------------------------------------------------------------------------
测试结果
--------------------------------------------------------------------------------
$(grep -E "passed|failed|ERROR" "$LOG_FILE" | tail -10)

--------------------------------------------------------------------------------
部署状态
--------------------------------------------------------------------------------
服务PID: $(cat logs/learning_module.pid 2>/dev/null || echo "N/A")
服务状态: $(ps -p $(cat logs/learning_module.pid 2>/dev/null) > /dev/null && echo "运行中" || echo "未运行")

--------------------------------------------------------------------------------
日志位置
--------------------------------------------------------------------------------
部署日志: ${LOG_FILE}
服务日志: logs/learning_module.log

================================================================================
EOF

    cat "$report_file" | tee -a "$LOG_FILE"
    log_success "部署报告已生成: $report_file"
}

# ============================================================================
# 回滚
# ============================================================================

rollback() {
    log_error "部署失败，执行回滚..."

    if [ -f logs/learning_module.pid.bak ]; then
        OLD_PID=$(cat logs/learning_module.pid.bak)
        if ps -p "$OLD_PID" > /dev/null; then
            log_info "旧服务仍在运行 (PID: $OLD_PID)"
        else
            log_info "尝试恢复旧服务..."
            # 这里可以添加恢复逻辑
        fi
    fi

    log_warning "回滚完成，请检查日志"
}

# ============================================================================
# 主流程
# ============================================================================

main() {
    print_header "Athena学习模块 - 本地CI/CD部署"
    log_info "开始时间: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "日志文件: $LOG_FILE"

    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tests)
                SKIP_TESTS=true
                shift
                ;;
            --skip-build)
                SKIP_BUILD=true
                shift
                ;;
            --deploy-only)
                DEPLOY_ONLY=true
                shift
                ;;
            --skip-deploy)
                SKIP_DEPLOY=true
                shift
                ;;
            *)
                log_error "未知参数: $1"
                echo "使用方法: $0 [--skip-tests] [--skip-build] [--deploy-only] [--skip-deploy]"
                exit 1
                ;;
        esac
    done

    # 保存当前PID用于回滚
    [ -f logs/learning_module.pid ] && cp logs/learning_module.pid logs/learning_module.pid.bak

    # 执行部署流程
    trap rollback ERR

    pre_flight_checks
    run_tests
    commit_code
    build_docker_image
    deploy_to_production

    # 等待服务稳定
    sleep 3

    if health_check; then
        generate_report
        log_success "🎉 部署成功完成！"
    else
        rollback
        exit 1
    fi

    log_info "结束时间: $(date '+%Y-%m-%d %H:%M:%S')"
}

# ============================================================================
# 执行主流程
# ============================================================================

main "$@"
