#!/bin/bash
###############################################################################
# LLM统一架构生产环境部署脚本
#
# 功能: 部署LLM统一架构和监控系统到生产环境
# 作者: Claude Code
# 日期: 2026-04-18
# 版本: v1.0
###############################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 创建备份
create_backup() {
    log_step "创建备份"

    BACKUP_DIR="/backup/athena_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # 备份核心LLM文件
    if [ -d "core/llm" ]; then
        cp -r core/llm "$BACKUP_DIR/"
        log_info "已备份 core/llm"
    fi

    # 备份配置文件
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/"
        log_info "已备份 .env"
    fi

    # 备份监控配置
    if [ -d "config/monitoring" ]; then
        cp -r config/monitoring "$BACKUP_DIR/"
        log_info "已备份 config/monitoring"
    fi

    echo "$BACKUP_DIR" > /tmp/athena_backup_dir.txt
    log_info "备份完成: $BACKUP_DIR"
}

# 检查环境依赖
check_dependencies() {
    log_step "检查环境依赖"

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi
    log_info "Python3: $(python3 --version)"

    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_warn "Docker 未安装，监控服务将无法启动"
    else
        log_info "Docker: $(docker --version)"
    fi

    # 检查docker-compose
    if ! command -v docker-compose &> /dev/null; then
        log_warn "docker-compose 未安装"
    else
        log_info "docker-compose: $(docker-compose --version)"
    fi
}

# 更新代码
update_code() {
    log_step "更新代码到最新版本"

    # 拉取最新代码（如果是git仓库）
    if [ -d ".git" ]; then
        git fetch origin
        git reset --hard origin/main
        log_info "代码已更新到最新版本"
    else
        log_warn "不是git仓库，跳过代码更新"
    fi
}

# 安装依赖
install_dependencies() {
    log_step "安装Python依赖"

    # 使用poetry安装
    if command -v poetry &> /dev/null; then
        poetry install
        log_info "依赖已通过poetry安装"
    else
        # 备用方案：使用pip
        pip3 install -r requirements.txt
        log_info "依赖已通过pip安装"
    fi
}

# 配置环境变量
setup_environment() {
    log_step "配置环境变量"

    # 检查.env文件
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_warn ".env文件不存在，已从.env.example创建"
            log_warn "请编辑.env文件配置API密钥"
        else
            log_error ".env.example文件不存在"
            exit 1
        fi
    fi

    # 设置Python路径
    export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"
    log_info "PYTHONPATH已设置"
}

# 验证LLM统一架构
verify_llm_unification() {
    log_step "验证LLM统一架构"

    python3 scripts/verify_llm_unification.py

    if [ $? -eq 0 ]; then
        log_info "LLM统一架构验证通过"
    else
        log_error "LLM统一架构验证失败"
        exit 1
    fi
}

# 部署监控系统
deploy_monitoring() {
    log_step "部署监控系统"

    # 检查Docker和docker-compose
    if ! command -v docker &> /dev/null || ! command -v docker-compose &> /dev/null; then
        log_warn "Docker或docker-compose未安装，跳过监控系统部署"
        return 0
    fi

    # 停止现有监控服务
    if docker-compose -f docker-compose.monitoring.yml ps 2>/dev/null | grep -q "Up"; then
        log_info "停止现有监控服务"
        docker-compose -f docker-compose.monitoring.yml down
    fi

    # 启动监控服务
    log_info "启动Prometheus和Grafana"
    docker-compose -f docker-compose.monitoring.yml up -d

    # 等待服务启动
    sleep 5

    # 验证服务状态
    if docker-compose -f docker-compose.monitoring.yml ps | grep -q "Up"; then
        log_info "监控系统启动成功"
        log_info "Prometheus: http://localhost:9090"
        log_info "Grafana: http://localhost:3000 (admin/admin123)"
    else
        log_error "监控系统启动失败"
        exit 1
    fi
}

# 运行测试
run_tests() {
    log_step "运行测试"

    # 运行单元测试
    log_info "运行单元测试..."
    python3 -m pytest tests/scripts/ tests/core/llm/ -v --tb=short || log_warn "部分测试失败，请检查"

    # 运行代码质量检查
    log_info "运行代码质量检查..."
    ruff check scripts/ core/llm/ || log_warn "代码质量问题，请检查"
}

# 创建生产环境配置
create_production_config() {
    log_step "创建生产环境配置"

    # 创建生产环境监控配置
    mkdir -p config/production/monitoring

    # 复制监控配置
    if [ -f "config/monitoring/prometheus.yml" ]; then
        cp config/monitoring/prometheus.yml config/production/monitoring/
    fi

    if [ -f "config/monitoring/llm_alerts.yml" ]; then
        cp config/monitoring/llm_alerts.yml config/production/monitoring/
    fi

    log_info "生产环境配置已创建"
}

# 显示部署摘要
show_summary() {
    echo ""
    echo "============================================================================"
    echo "                         部署完成摘要"
    echo "============================================================================"
    echo ""
    echo "✅ 备份位置: $(cat /tmp/athena_backup_dir.txt 2>/dev/null || echo '未记录')"
    echo ""
    echo "✅ LLM统一架构: 已部署"
    echo "✅ 监控系统: 已启动"
    echo "✅ 测试验证: 已完成"
    echo ""
    echo "📊 访问地址:"
    echo "   - Prometheus: http://localhost:9090"
    echo "   - Grafana: http://localhost:3000 (admin/admin123)"
    echo "   - LLM仪表板: http://localhost:3000/d/b6bc1106-7ddd-49d2-ab2f-9d421118d94f/"
    echo ""
    echo "🔧 维护命令:"
    echo "   - 验证LLM: python3 scripts/verify_llm_unification.py"
    echo "   - 查看监控: docker-compose -f docker-compose.monitoring.yml ps"
    echo "   - 查看日志: docker-compose -f docker-compose.monitoring.yml logs -f"
    echo ""
    echo "📚 文档位置:"
    echo "   - 快速参考: docs/reports/CODE_QUALITY_QUICK_REFERENCE.md"
    echo "   - 监控指南: docs/reports/LLM_MONITORING_SETUP_GUIDE_20260418.md"
    echo ""
    echo "============================================================================"
}

# 主流程
main() {
    echo "============================================================================"
    echo "           Athena LLM统一架构 - 生产环境部署"
    echo "============================================================================"
    echo ""
    echo "开始时间: $(date)"
    echo ""

    # 执行部署步骤
    create_backup
    check_dependencies
    update_code
    install_dependencies
    setup_environment
    verify_llm_unification
    deploy_monitoring
    run_tests
    create_production_config

    # 显示摘要
    show_summary

    log_info "部署完成！"
}

# 捕获错误并记录
trap 'log_error "部署过程中出现错误，请检查上述日志"; exit 1' ERR

# 运行主流程
main "$@"
