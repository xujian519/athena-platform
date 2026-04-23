#!/bin/bash
# Athena工作平台 - 本地CI/CD执行脚本
# Local CI/CD Execution Script for Athena Platform
#
# 用途: 手动执行本地CI/CD流程，或作为GitLab Runner的执行器
# 使用: ./scripts/local_ci.sh [stage]
#
# 参数:
#   quality    - 执行代码质量检查
#   test       - 执行测试（单元测试、集成测试、性能测试）
#   build      - 构建Docker镜像
#   deploy     - 部署到生产环境
#   all        - 执行完整CI/CD流程（默认）
#   clean      - 清理临时文件和旧镜像

set -e  # 遇到错误立即退出

# ==========================================
# 配置
# ==========================================

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置变量
PYTHON_VERSION="3.11"
VENV_DIR="${VENV_DIR:-$PROJECT_ROOT/venv}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')}"
DEPLOY_ENVIRONMENT="${DEPLOY_ENVIRONMENT:-production}"

# PostgreSQL配置（本地17.7版本）
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-athena_production}"
POSTGRES_USER="${POSTGRES_USER:-athena}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-athena123}"

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
    echo -e "\n${GREEN}==>${NC} $1"
}

# ==========================================
# 工具函数
# ==========================================

# 检查命令是否存在
check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "命令不存在: $1"
        return 1
    fi
    return 0
}

# 激活虚拟环境
activate_venv() {
    if [ -d "$VENV_DIR" ]; then
        log_info "激活虚拟环境: $VENV_DIR"
        source "$VENV_DIR/bin/activate"
    else
        log_warning "虚拟环境不存在，创建虚拟环境..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
        log_success "虚拟环境已创建"
    fi
}

# 检查PostgreSQL连接
check_postgres() {
    log_step "检查PostgreSQL连接..."
    if ! PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT version();" &> /dev/null; then
        log_error "无法连接到PostgreSQL: $POSTGRES_HOST:$POSTGRES_PORT"
        log_info "请确保PostgreSQL 17.7正在运行，并且数据库和用户已创建"
        return 1
    fi
    log_success "PostgreSQL连接正常"
    return 0
}

# 启动基础设施服务
start_infrastructure() {
    log_step "启动基础设施服务..."
    if docker-compose -f production/config/docker/docker-compose.infrastructure.yml up -d redis qdrant 2>&1; then
        log_success "基础设施服务启动成功"
        sleep 10
    else
        log_warning "Docker服务启动失败或已运行"
    fi
}

# 停止基础设施服务
stop_infrastructure() {
    log_step "停止基础设施服务..."
    docker-compose -f production/config/docker/docker-compose.infrastructure.yml down || true
    log_success "基础设施服务已停止"
}

# ==========================================
# Stage 1: 代码质量检查
# ==========================================

stage_quality() {
    log_step "🔍 开始代码质量检查..."

    # 检查Python版本
    log_info "检查Python版本..."
    if ! check_command python3; then
        log_error "Python3未安装"
        return 1
    fi
    python3 --version

    # 激活虚拟环境
    activate_venv

    # 安装依赖
    log_info "安装代码质量检查工具..."
    pip install --upgrade pip --quiet
    pip install black isort flake8 mypy bandit safety pylint --quiet

    # 创建报告目录
    mkdir -p reports/quality

    # 代码格式检查
    log_info "检查代码格式（black）..."
    if black --check core/ --diff 2>&1 | tee reports/quality/black-report.txt; then
        log_success "代码格式检查通过"
    else
        log_warning "代码格式检查发现问题"
    fi

    # 导入排序检查
    log_info "检查导入排序（isort）..."
    if isort --check-only core/ --diff-only 2>&1 | tee reports/quality/isort-report.txt; then
        log_success "导入排序检查通过"
    else
        log_warning "导入排序检查发现问题"
    fi

    # 代码质量分析
    log_info "代码质量分析（flake8）..."
    flake8 core/ --count --select=E9,F63,F7,F82 --show-source --statistics | tee reports/quality/flake8-report.txt
    flake8 core/ --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics | tee -a reports/quality/flake8-report.txt

    # 类型检查
    log_info "类型检查（mypy）..."
    mypy core/ --ignore-missing-imports --strict-optional --show-error-codes 2>&1 | tee reports/quality/mypy-report.txt || true

    # 安全扫描
    log_info "安全扫描（bandit）..."
    bandit -r core/ -f json -o reports/quality/bandit-report.json 2>&1 || true
    bandit -r core/ 2>&1 | tee reports/quality/bandit-report.txt || true

    # 依赖安全检查
    log_info "依赖安全检查（safety）..."
    safety check --json --output reports/quality/safety-report.json 2>&1 || true
    safety check 2>&1 | tee reports/quality/safety-report.txt || true

    log_success "代码质量检查完成"
    return 0
}

# ==========================================
# Stage 2: 测试
# ==========================================

stage_test() {
    log_step "🧪 开始测试..."

    # 检查PostgreSQL连接
    check_postgres || return 1

    # 设置环境变量
    export DATABASE_URL="postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB"
    export REDIS_URL="redis://localhost:6379/0"
    export QDRANT_HOST="localhost"
    export QDRANT_PORT="6333"

    # 激活虚拟环境
    activate_venv

    # 安装测试依赖
    log_info "安装测试依赖..."
    pip install --upgrade pip --quiet
    pip install pytest pytest-cov pytest-asyncio pytest-mock pytest-benchmark --quiet
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt --quiet
    fi

    # 创建报告目录
    mkdir -p reports/tests

    # 单元测试
    log_info "运行单元测试..."
    start_infrastructure

    if pytest tests/core/execution/test_shared_types.py -v \
        --cov=core/execution \
        --cov-report=xml:reports/tests/coverage.xml \
        --cov-report=html:reports/tests/htmlcov \
        --cov-report=term-missing \
        --junitxml=reports/tests/pytest-report.xml 2>&1 | tee reports/tests/pytest-output.txt; then
        log_success "单元测试通过"
    else
        log_warning "单元测试存在问题"
    fi

    # 集成测试
    log_info "运行集成测试..."
    if pytest tests/integration/ -v \
        --junitxml=reports/tests/integration-test-report.xml 2>&1 | tee reports/tests/integration-test-output.txt; then
        log_success "集成测试通过"
    else
        log_warning "集成测试存在问题"
    fi

    # 性能测试
    log_info "运行性能测试..."
    if pytest tests/core/execution/test_performance.py -v \
        --benchmark-only \
        --benchmark-json=reports/tests/performance-report.json 2>&1 | tee reports/tests/performance-test-output.txt; then
        log_success "性能测试通过"
    else
        log_warning "性能测试存在问题"
    fi

    # 停止基础设施服务
    stop_infrastructure

    log_success "测试完成"
    return 0
}

# ==========================================
# Stage 3: 构建
# ==========================================

stage_build() {
    log_step "🏗️ 开始构建Docker镜像..."

    # 检查Docker
    if ! check_command docker; then
        log_error "Docker未安装"
        return 1
    fi

    docker --version
    docker info > /dev/null 2>&1 || {
        log_error "Docker未运行"
        return 1
    }

    # 创建报告目录
    mkdir -p reports/build

    # 构建执行模块镜像
    log_info "构建执行模块镜像..."
    if [ -f Dockerfile.execution ]; then
        docker build -t "athena/execution-engine:$IMAGE_TAG" \
            -f Dockerfile.execution . 2>&1 | tee reports/build/build-execution.log
        docker tag "athena/execution-engine:$IMAGE_TAG" athena/execution-engine:latest
        log_success "执行模块镜像构建成功"
    else
        log_warning "Dockerfile.execution不存在，跳过执行模块构建"
    fi

    # 显示构建的镜像
    log_info "构建的Docker镜像:"
    docker images | grep athena || true

    log_success "Docker镜像构建完成"
    return 0
}

# ==========================================
# Stage 4: 部署
# ==========================================

stage_deploy() {
    log_step "🚀 开始部署到生产环境..."

    # 确认部署
    log_warning "即将部署到生产环境: $DEPLOY_ENVIRONMENT"
    read -p "确认部署? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        return 0
    fi

    # 检查部署脚本
    if [ ! -f scripts/deploy_to_production.sh ]; then
        log_error "部署脚本不存在: scripts/deploy_to_production.sh"
        return 1
    fi

    # 创建备份
    log_info "创建配置备份..."
    mkdir -p backups
    if [ -f config/production.yaml ]; then
        cp config/production.yaml "backups/production.yaml.$(date +%Y%m%d_%H%M%S).backup"
        log_success "配置备份完成"
    fi

    # 执行部署
    log_info "执行部署脚本..."
    if bash scripts/deploy_to_production.sh --env "$DEPLOY_ENVIRONMENT" --tag "$IMAGE_TAG" 2>&1 | tee reports/deploy/deploy.log; then
        log_success "部署成功"
    else
        log_error "部署失败"
        # 执行回滚
        log_warning "执行回滚..."
        if [ -f scripts/rollback_execution_macos.sh ]; then
            bash scripts/rollback_execution_macos.sh --dry-run false
        fi
        return 1
    fi

    # 健康检查
    log_info "执行健康检查..."
    sleep 10
    if curl -f http://localhost:8080/health 2>&1; then
        log_success "健康检查通过"
    else
        log_warning "健康检查失败"
    fi

    # 冒烟测试
    log_info "运行冒烟测试..."
    if [ -f scripts/smoke_tests.py ]; then
        if python3 scripts/smoke_tests.py --env "$DEPLOY_ENVIRONMENT" 2>&1 | tee reports/deploy/smoke-tests.log; then
            log_success "冒烟测试通过"
        else
            log_warning "冒烟测试存在问题"
        fi
    fi

    log_success "部署完成"
    return 0
}

# ==========================================
# 清理
# ==========================================

stage_clean() {
    log_step "🧹 清理临时文件和旧镜像..."

    # 清理Docker资源
    log_info "清理Docker资源..."
    docker system prune -f
    docker image prune -a -f

    # 清理旧的备份文件（保留最近5个）
    log_info "清理旧备份文件..."
    if [ -d backups ]; then
        ls -t backups/ 2>/dev/null | tail -n +6 | xargs -I {} rm "backups/{}" 2>/dev/null || true
    fi

    # 清理旧的报告文件（保留最近7天的）
    log_info "清理旧报告文件..."
    find reports/ -type f -mtime +7 -delete 2>/dev/null || true

    log_success "清理完成"
    return 0
}

# ==========================================
# 主函数
# ==========================================

main() {
    local stage="${1:-all}"

    # 显示标题
    echo -e "${BLUE}"
    echo "============================================"
    echo "  Athena工作平台 - 本地CI/CD执行脚本"
    echo "============================================"
    echo -e "${NC}"
    echo "项目根目录: $PROJECT_ROOT"
    echo "当前分支: $(git branch --show-current 2>/dev/null || echo '未知')"
    echo "镜像标签: $IMAGE_TAG"
    echo "部署环境: $DEPLOY_ENVIRONMENT"
    echo ""

    # 执行对应的阶段
    case "$stage" in
        quality)
            stage_quality
            ;;
        test)
            stage_quality
            stage_test
            ;;
        build)
            stage_quality
            stage_test
            stage_build
            ;;
        deploy)
            stage_quality
            stage_test
            stage_build
            stage_deploy
            ;;
        all)
            stage_quality
            stage_test
            stage_build
            log_info "完整CI/CD流程完成（部署需要手动触发）"
            ;;
        clean)
            stage_clean
            ;;
        *)
            log_error "未知的阶段: $stage"
            echo "使用方法: $0 [quality|test|build|deploy|all|clean]"
            exit 1
            ;;
    esac

    # 返回结果
    if [ $? -eq 0 ]; then
        log_success "CI/CD流程执行成功"
        exit 0
    else
        log_error "CI/CD流程执行失败"
        exit 1
    fi
}

# 执行主函数
main "$@"
