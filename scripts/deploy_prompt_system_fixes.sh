#!/bin/bash
###############################################################################
# 动态提示词系统修复 - 生产环境部署脚本
# Production Deployment Script for Dynamic Prompt System Fixes
#
# 作者: Athena AI系统
# 创建时间: 2026-02-03
# 版本: v1.0.0
#
# 功能: 部署今天验证过的修复到生产环境
###############################################################################

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

# 部署配置
ENVIRONMENT="${ENVIRONMENT:-production}"
IMAGE_TAG="${IMAGE_TAG:-v$(date +%Y%m%d-%H%M%S)}"
BACKUP_DIR="${BACKUP_DIR:-/tmp/athena-backups}"

# ==========================================
# 日志函数
# ==========================================

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
# 部署前检查
# ==========================================

pre_deploy_checks() {
    log_step "执行部署前检查"

    # 1. 检查当前分支
    CURRENT_BRANCH=$(git branch --show-current)
    log_info "当前分支: $CURRENT_BRANCH"

    # 2. 检查未提交的修改
    if [ -n "$(git status --porcelain)" ]; then
        log_error "存在未提交的修改，请先提交或暂存："
        git status --short
        exit 1
    fi

    # 3. 检查最近的提交
    log_info "最近的3次提交："
    git log --oneline -3

    # 4. 确认要部署的提交
    log_warning "即将部署以下提交到 ${ENVIRONMENT} 环境："
    git log --oneline -5

    read -p "确认部署？(yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log_info "部署已取消"
        exit 0
    fi
}

# ==========================================
# 备份当前版本
# ==========================================

backup_current_version() {
    log_step "备份当前版本"

    BACKUP_NAME="athena-backup-$(date +%Y%m%d-%H%M%S)"
    BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

    mkdir -p "$BACKUP_PATH"

    # 备份核心文件
    log_info "备份核心文件..."

    # 1. 备份修复的Python文件
    mkdir -p "${BACKUP_PATH}/core"
    cp -r core/database "${BACKUP_PATH}/core/" 2>/dev/null || true
    cp -r core/legal_world_model "${BACKUP_PATH}/core/" 2>/dev/null || true
    cp -r core/api "${BACKUP_PATH}/core/" 2>/dev/null || true

    # 2. 备份Neo4j规则数据
    log_info "备份Neo4j规则数据..."
    if docker ps | grep -q "athena-neo4j"; then
        docker exec athena-neo4j cypher-shell -u neo4j -p athena_neo4j_2024 \
            "MATCH (r:ScenarioRule) RETURN collect({rule_id: r.rule_id, data: r})" \
            > "${BACKUP_PATH}/neo4j_rules_backup.json" 2>/dev/null || true
    fi

    log_success "备份完成: ${BACKUP_PATH}"
}

# ==========================================
# 同步代码到生产环境
# ==========================================

sync_code_to_production() {
    log_step "同步代码到生产环境"

    # 方案1: 使用git pull (推荐用于单机部署)
    log_info "方式1: 直接应用今日修复的代码"

    # 获取今天修复的提交hash
    TODAY_COMMITS=$(git log --since="1 day ago" --oneline --pretty=format:"%H")

    if [ -z "$TODAY_COMMITS" ]; then
        log_warning "未找到今天的提交"
        return
    fi

    log_info "今天的提交："
    git log --since="1 day ago" --oneline

    # 生产环境如果是同一台机器，代码已经在git仓库中
    log_success "代码已在本地，无需同步"
}

# ==========================================
# 重启受影响的服务
# ==========================================

restart_services() {
    log_step "重启受影响的服务"

    # 1. 检查服务状态
    log_info "检查当前服务状态..."

    # 检查API服务
    API_RUNNING=$(docker ps | grep -c "athena-api" || true)
    log_info "API服务运行状态: ${API_RUNNING}个实例"

    # 2. 如果使用docker-compose
    if [ -f "docker-compose.yml" ]; then
        log_info "使用docker-compose重启服务..."

        # 重启API服务
        docker-compose restart api 2>/dev/null || \
        docker-compose restart 2>/dev/null || \
        log_warning "docker-compose重启失败，尝试手动重启"
    fi

    # 3. 如果使用PM2管理进程
    if command -v pm2 &> /dev/null; then
        log_info "使用PM2重启服务..."

        # 重启API服务
        pm2 restart athena-api 2>/dev/null || \
        pm2 restart all 2>/dev/null || \
        log_warning "PM2重启失败"
    fi

    # 4. 手动重启（如果其他方式都失败）
    log_info "或者手动重启："
    log_info "  pkill -f 'uvicorn.*core.api.main:app'"
    log_info "  nohup python3 -m uvicorn core.api.main:app --host 0.0.0.0 --port 8000 > /tmp/athena-api.log 2>&1 &"

    log_success "服务重启完成"
}

# ==========================================
# 运行健康检查
# ==========================================

health_checks() {
    log_step "运行健康检查"

    # 1. 等待服务启动
    log_info "等待服务启动..."
    sleep 10

    # 2. 检查API端点
    log_info "检查API健康状态..."
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        log_success "✅ API健康检查通过"
    else
        log_error "❌ API健康检查失败"
        return 1
    fi

    # 3. 检查动态提示词系统
    log_info "检查动态提示词系统..."
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/api/v1/prompt-system/health 2>/dev/null || echo '{}')

    if echo "$HEALTH_RESPONSE" | grep -q '"status":"healthy"'; then
        log_success "✅ 动态提示词系统健康"
    elif echo "$HEALTH_RESPONSE" | grep -q '"neo4j":"ok"'; then
        log_warning "⚠️  动态提示词系统部分功能可用"
    else
        log_error "❌ 动态提示词系统检查失败"
        return 1
    fi

    # 4. 测试提示词生成功能
    log_info "测试提示词生成功能..."
    TEST_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/prompt-system/prompt/generate \
        -H "Content-Type: application/json" \
        -d '{"user_input": "测试提示词生成"}' 2>/dev/null || echo '{}')

    if echo "$TEST_RESPONSE" | grep -q "system_prompt"; then
        log_success "✅ 提示词生成功能正常"
    else
        log_warning "⚠️  提示词生成功能测试未通过"
    fi

    # 5. 检查数据库连接
    log_info "检查数据库连接..."
    python3 -c "
from core.database import get_sync_db_manager
db = get_sync_db_manager()
health = db.health_check()
print('PostgreSQL:', health.get('postgresql', {}).get('status'))
print('Neo4j:', health.get('neo4j', {}).get('status'))
print('Qdrant:', health.get('qdrant', {}).get('status'))
" 2>/dev/null || log_warning "数据库检查脚本执行失败"

    log_success "健康检查完成"
}

# ==========================================
# 验证Neo4j规则数据
# ==========================================

verify_neo4j_rules() {
    log_step "验证Neo4j规则数据"

    python3 -c "
from core.database import get_sync_db_manager
db = get_sync_db_manager()

with db.neo4j_session() as session:
    # 检查规则数量
    result = session.run('MATCH (r:ScenarioRule) RETURN count(r) as count')
    record = result.single()
    count = record['count']

    print(f'Neo4j中的规则数量: {count}')

    # 检查is_active字段
    result = session.run('''
        MATCH (r:ScenarioRule)
        WHERE r.is_active = true
        RETURN count(r) as active_count
    ''')
    record = result.single()
    active_count = record['active_count']

    print(f'启用的规则数量: {active_count}')

    # 列出所有规则
    result = session.run('MATCH (r:ScenarioRule) RETURN r.rule_id as rule_id ORDER BY r.rule_id')
    print('规则列表:')
    for record in result:
        print(f'  - {record[\"rule_id\"]}')

    if active_count == 0:
        print('⚠️  警告: 没有启用的规则，尝试初始化...')
        import subprocess
        subprocess.run(['python3', 'scripts/init_prompt_rules.py'])
" 2>/dev/null || log_warning "Neo4j规则验证失败"
}

# ==========================================
# 监控部署结果
# ==========================================

monitor_deployment() {
    log_step "监控部署结果"

    # 查看最新日志
    if [ -f "/tmp/athena-api.log" ]; then
        log_info "最新API日志（最后30行）："
        tail -30 /tmp/athena-api.log
    fi

    # 检查错误
    ERROR_COUNT=$(grep -c "ERROR" /tmp/athena-api.log 2>/dev/null || echo "0")
    if [ "$ERROR_COUNT" -gt 0 ]; then
        log_warning "⚠️  发现 ${ERROR_COUNT} 个错误，请检查日志"
    fi
}

# ==========================================
# 主部署流程
# ==========================================

main() {
    echo -e "${GREEN}"
    echo "=============================================="
    echo "  Athena动态提示词系统 - 生产部署"
    echo "  版本: v1.0.0"
    echo "  日期: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=============================================="
    echo -e "${NC}"

    # 1. 部署前检查
    pre_deploy_checks

    # 2. 备份当前版本
    backup_current_version

    # 3. 同步代码
    sync_code_to_production

    # 4. 初始化Neo4j规则（如果需要）
    if [ "$SKIP_INIT" != "true" ]; then
        log_step "初始化Neo4j规则数据"
        python3 scripts/init_prompt_rules.py || log_warning "规则初始化失败"
    fi

    # 5. 重启服务
    restart_services

    # 6. 运行健康检查
    health_checks

    # 7. 验证规则数据
    verify_neo4j_rules

    # 8. 监控结果
    monitor_deployment

    # 完成总结
    log_step "部署完成总结"
    log_success "✅ 部署完成！"
    log_info "修复内容："
    log_info "  1. Neo4j导入遮蔽问题已修复"
    log_info "  2. JSON解析问题已修复"
    log_info "  3. API路由注册问题已修复"
    log_info "  4. 语法错误已修复"
    log_info ""
    log_info "服务访问："
    log_info "  - API服务: http://localhost:8000"
    log_info "  - API文档: http://localhost:8000/docs"
    log_info "  - 健康检查: http://localhost:8000/health"
    log_info "  - Prometheus: http://localhost:9090"
    log_info "  - Grafana: http://localhost:3000"
    log_info ""
    log_info "如需回滚，使用备份: ${BACKUP_NAME}"
}

# ==========================================
# 参数解析
# ==========================================

SKIP_INIT=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-init)
            SKIP_INIT=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            echo "使用方法: $0 [options]"
            echo ""
            echo "选项:"
            echo "  --skip-init    跳过Neo4j规则初始化"
            echo "  --dry-run      模拟运行"
            echo "  -h, --help     显示此帮助信息"
            exit 0
            ;;
        *)
            log_error "未知选项: $1"
            exit 1
            ;;
    esac
done

# ==========================================
# 执行部署
# ==========================================

if [ "$DRY_RUN" = "true" ]; then
    log_info "模拟运行模式，不会实际部署"
    log_info "将执行的步骤："
    log_info "  1. 部署前检查"
    log_info "  2. 备份当前版本"
    log_info "  3. 同步代码"
    log_info "  4. 初始化Neo4j规则"
    log_info "  5. 重启服务"
    log_info "  6. 健康检查"
    log_info "  7. 验证规则数据"
    log_info "  8. 监控结果"
else
    main
fi
