#!/bin/bash

################################################################################
# Athena工作平台 - Docker Compose配置迁移脚本
# 功能：自动迁移旧的docker-compose配置到新的统一配置
# 作者：Claude Code
# 日期：2026-04-20
# 版本：v1.0
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="/Users/xujian/Athena工作平台"
cd "$PROJECT_ROOT" || exit 1

# 备份目录
BACKUP_DIR=".docker_backup_$(date +%Y%m%d_%H%M%S)"

# 统计变量
BACKUP_COUNT=0
STOPPED_COUNT=0

################################################################################
# 工具函数
################################################################################

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

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
}

confirm() {
    read -p "$(echo -e ${YELLOW}[确认]${NC} $1 (y/N): )" -n 1 -r
    echo ""
    [[ $REPLY =~ ^[Yy]$ ]]
}

################################################################################
# 迁移步骤
################################################################################

backup_old_configs() {
    print_header "步骤 1/7: 备份现有配置"

    mkdir -p "$BACKUP_DIR"

    # 备份docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "$BACKUP_DIR/"
        log_success "已备份: docker-compose.yml"
        ((BACKUP_COUNT++))
    fi

    # 备份docker-compose.test.yml
    if [ -f "docker-compose.test.yml" ]; then
        cp docker-compose.test.yml "$BACKUP_DIR/"
        log_success "已备份: docker-compose.test.yml"
        ((BACKUP_COUNT++))
    fi

    # 备份生产环境配置
    if [ -f "config/docker/docker-compose.production.yml" ]; then
        mkdir -p "$BACKUP_DIR/config/docker"
        cp config/docker/docker-compose.production.yml "$BACKUP_DIR/config/docker/"
        log_success "已备份: config/docker/docker-compose.production.yml"
        ((BACKUP_COUNT++))
    fi

    # 备份核心监控配置
    if [ -f "core/observability/monitoring/docker-compose.yml" ]; then
        mkdir -p "$BACKUP_DIR/core/observability/monitoring"
        cp core/observability/monitoring/docker-compose.yml "$BACKUP_DIR/core/observability/monitoring/"
        log_success "已备份: core/observability/monitoring/docker-compose.yml"
        ((BACKUP_COUNT++))
    fi

    # 备份共享监控配置
    if [ -f "shared/observability/monitoring/docker-compose.yml" ]; then
        mkdir -p "$BACKUP_DIR/shared/observability/monitoring"
        cp shared/observability/monitoring/docker-compose.yml "$BACKUP_DIR/shared/observability/monitoring/"
        log_success "已备份: shared/observability/monitoring/docker-compose.yml"
        ((BACKUP_COUNT++))
    fi

    # 备份集成测试配置
    if [ -f "tests/integration/docker-compose.test.yml" ]; then
        mkdir -p "$BACKUP_DIR/tests/integration"
        cp tests/integration/docker-compose.test.yml "$BACKUP_DIR/tests/integration/"
        log_success "已备份: tests/integration/docker-compose.test.yml"
        ((BACKUP_COUNT++))
    fi

    log_info "备份完成: $BACKUP_COUNT 个文件已备份到 $BACKUP_DIR"
}

stop_running_containers() {
    print_header "步骤 2/7: 停止运行中的容器"

    log_info "正在停止所有Docker容器..."

    # 停止开发环境容器
    if docker-compose ps -q 2>/dev/null | grep -q .; then
        docker-compose down 2>/dev/null || true
        log_success "已停止开发环境容器"
        ((STOPPED_COUNT++))
    fi

    # 停止测试环境容器
    if [ -f "docker-compose.test.yml" ] && docker-compose -f docker-compose.test.yml ps -q 2>/dev/null | grep -q .; then
        docker-compose -f docker-compose.test.yml down 2>/dev/null || true
        log_success "已停止测试环境容器"
        ((STOPPED_COUNT++))
    fi

    # 停止生产环境容器
    if [ -f "config/docker/docker-compose.production.yml" ] && docker-compose -f config/docker/docker-compose.production.yml ps -q 2>/dev/null | grep -q .; then
        docker-compose -f config/docker/docker-compose.production.yml down 2>/dev/null || true
        log_success "已停止生产环境容器"
        ((STOPPED_COUNT++))
    fi

    # 停止监控服务
    if [ -f "core/observability/monitoring/docker-compose.yml" ] && docker-compose -f core/observability/monitoring/docker-compose.yml ps -q 2>/dev/null | grep -q .; then
        docker-compose -f core/observability/monitoring/docker-compose.yml down 2>/dev/null || true
        log_success "已停止核心监控服务"
        ((STOPPED_COUNT++))
    fi

    # 停止集成测试容器
    if [ -f "tests/integration/docker-compose.test.yml" ] && docker-compose -f tests/integration/docker-compose.test.yml ps -q 2>/dev/null | grep -q .; then
        docker-compose -f tests/integration/docker-compose.test.yml down 2>/dev/null || true
        log_success "已停止集成测试容器"
        ((STOPPED_COUNT++))
    fi

    log_info "容器停止完成: $STOPPED_COUNT 个环境已停止"
}

create_env_files() {
    print_header "步骤 3/7: 创建环境变量文件"

    # 创建开发环境变量
    cat > .env.dev << 'EOF'
# Redis配置
REDIS_PASSWORD=redis123

# Grafana配置
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin123
GRAFANA_ROOT_URL=http://localhost:3005
EOF
    log_success "已创建: .env.dev"

    # 创建测试环境变量
    cat > .env.test << 'EOF'
# 测试数据库配置
TEST_DATABASE_URL=postgresql://athena_test:athena_test_password_2024@localhost:5433/athena_test_db
TEST_REDIS_URL=redis://localhost:6380/0
TEST_QDRANT_URL=http://localhost:6334
TEST_NEO4J_URI=bolt://localhost:7688
TEST_NEO4J_USER=neo4j
TEST_NEO4J_PASSWORD=athena_test_2024
TEST_MINIO_ENDPOINT=http://localhost:9001
TEST_MINIO_ACCESS_KEY=minioadmin
TEST_MINIO_SECRET_KEY=minioadmin123
EOF
    log_success "已创建: .env.test"

    # 创建生产环境变量
    cat > .env.prod << 'EOF'
# 生产环境配置
REDIS_PASSWORD=CHANGE_ME_PRODUCTION
GRAFANA_ADMIN_PASSWORD=CHANGE_ME_SECURE_PASSWORD
EOF
    log_success "已创建: .env.prod"

    log_warning "⚠️  请修改 .env.prod 中的密码为安全密码！"
}

test_new_config() {
    print_header "步骤 4/7: 测试新配置"

    if [ ! -f "docker-compose.unified.yml" ]; then
        log_error "未找到 docker-compose.unified.yml 文件"
        exit 1
    fi

    log_info "测试开发环境配置..."
    if docker-compose -f docker-compose.unified.yml --profile dev config > /dev/null 2>&1; then
        log_success "✅ 开发环境配置测试通过"
    else
        log_error "❌ 开发环境配置测试失败"
        exit 1
    fi

    log_info "测试测试环境配置..."
    if docker-compose -f docker-compose.unified.yml --profile test config > /dev/null 2>&1; then
        log_success "✅ 测试环境配置测试通过"
    else
        log_error "❌ 测试环境配置测试失败"
        exit 1
    fi

    log_info "测试生产环境配置..."
    if docker-compose -f docker-compose.unified.yml --profile prod config > /dev/null 2>&1; then
        log_success "✅ 生产环境配置测试通过"
    else
        log_error "❌ 生产环境配置测试失败"
        exit 1
    fi

    log_info "测试监控服务配置..."
    if docker-compose -f docker-compose.unified.yml --profile monitoring config > /dev/null 2>&1; then
        log_success "✅ 监控服务配置测试通过"
    else
        log_error "❌ 监控服务配置测试失败"
        exit 1
    fi

    log_success "所有配置测试通过！"
}

start_dev_environment() {
    print_header "步骤 5/7: 启动开发环境"

    if ! confirm "是否启动开发环境进行验证？"; then
        log_warning "跳过开发环境启动"
        return
    fi

    log_info "正在启动开发环境..."
    docker-compose -f docker-compose.unified.yml --profile dev up -d

    log_info "等待容器启动..."
    sleep 10

    log_info "检查容器状态..."
    if docker-compose -f docker-compose.unified.yml --profile dev ps | grep -q "Up"; then
        log_success "✅ 开发环境启动成功"

        echo ""
        log_info "容器列表:"
        docker-compose -f docker-compose.unified.yml --profile dev ps
    else
        log_error "❌ 开发环境启动失败"
        log_error "请查看日志: docker-compose -f docker-compose.unified.yml --profile dev logs"
        exit 1
    fi
}

verify_services() {
    print_header "步骤 6/7: 验证服务"

    log_info "正在验证服务..."

    # 检查Redis
    if docker exec athena-redis-dev redis-cli -a redis123 ping 2>/dev/null | grep -q "PONG"; then
        log_success "✅ Redis 服务正常"
    else
        log_warning "⚠️  Redis 服务未响应"
    fi

    # 检查Qdrant
    if curl -s http://localhost:6333/ > /dev/null 2>&1; then
        log_success "✅ Qdrant 服务正常"
    else
        log_warning "⚠️  Qdrant 服务未响应"
    fi

    # 检查Neo4j
    if curl -s http://localhost:7474/ > /dev/null 2>&1; then
        log_success "✅ Neo4j 服务正常"
    else
        log_warning "⚠️  Neo4j 服务未响应"
    fi

    log_success "服务验证完成"
}

create_migration_report() {
    print_header "步骤 7/7: 生成迁移报告"

    cat << EOF > MIGRATION_REPORT_$(date +%Y%m%d).md
# Docker Compose配置迁移报告

**迁移日期**: $(date)
**备份目录**: $BACKUP_DIR
**备份文件数**: $BACKUP_COUNT
**停止环境数**: $STOPPED_COUNT

---

## ✅ 迁移完成

### 📊 迁移统计

- 备份文件: $BACKUP_COUNT 个
- 停止环境: $STOPPED_COUNT 个
- 新配置文件: docker-compose.unified.yml

### 🗂️ 旧配置文件位置

所有旧配置文件已备份到: \`$BACKUP_DIR/\`

### 🚀 新配置使用方法

\`\`\`bash
# 开发环境
docker-compose -f docker-compose.unified.yml --profile dev up -d

# 测试环境
docker-compose -f docker-compose.unified.yml --profile test up -d

# 生产环境
docker-compose -f docker-compose.unified.yml --profile prod up -d

# 监控服务
docker-compose -f docker-compose.unified.yml --profile monitoring up -d
\`\`\`

### 📖 详细文档

请查看 \`DOCKER_COMPOSE_MIGRATION_GUIDE.md\` 获取详细使用指南。

---

## ⚠️ 后续操作

1. **更新脚本**: 将所有脚本中的 docker-compose 命令更新为新格式
2. **更新文档**: 更新项目文档中的Docker命令
3. **测试验证**: 在各环境中测试新配置
4. **删除旧文件**: 确认无问题后，删除旧的docker-compose文件

---

## 🔄 回滚方案

如果迁移后出现问题：

\`\`\`bash
# 停止新配置
docker-compose -f docker-compose.unified.yml --profile dev down

# 恢复旧配置
cp $BACKUP_DIR/docker-compose.yml ./

# 重新启动
docker-compose up -d
\`\`\`

---

**迁移脚本版本**: v1.0
**维护者**: 徐健 (xujian519@gmail.com)
EOF

    log_success "迁移报告已生成: MIGRATION_REPORT_$(date +%Y%m%d).md"
}

################################################################################
# 主函数
################################################################################

main() {
    clear
    cat << 'EOF'
╔══════════════════════════════════════════════════════════════╗
║     Athena工作平台 - Docker Compose配置迁移                 ║
║     版本: v1.0                                               ║
║     日期: 2026-04-20                                         ║
╚══════════════════════════════════════════════════════════════╝
EOF

    log_warning "此脚本将执行以下操作："
    echo "  1. 备份所有旧的docker-compose文件"
    echo "  2. 停止所有运行中的容器"
    echo "  3. 创建新的环境变量文件"
    echo "  4. 测试新配置"
    echo "  5. 启动开发环境进行验证"
    echo "  6. 验证服务状态"
    echo "  7. 生成迁移报告"
    echo ""

    if ! confirm "是否继续迁移？"; then
        log_info "迁移已取消"
        exit 0
    fi

    # 执行迁移步骤
    backup_old_configs
    stop_running_containers
    create_env_files
    test_new_config
    start_dev_environment
    verify_services
    create_migration_report

    # 迁移完成
    print_header "迁移完成"
    cat << EOF

${GREEN}✅ Docker Compose配置迁移成功！${NC}

📊 迁移统计:
  - 备份文件: ${BACKUP_COUNT}个
  - 停止环境: ${STOPPED_COUNT}个
  - 备份位置: ${BACKUP_DIR}/

📖 下一步操作:
  1. 查看迁移报告: cat MIGRATION_REPORT_*.md
  2. 阅读迁移指南: cat DOCKER_COMPOSE_MIGRATION_GUIDE.md
  3. 更新项目脚本和文档
  4. 在各环境中测试新配置
  5. 确认无问题后删除旧配置文件

🔄 回滚命令:
  docker-compose -f docker-compose.unified.yml --profile dev down
  cp ${BACKUP_DIR}/docker-compose.yml ./
  docker-compose up -d

EOF
}

# 执行主函数
main "$@"
