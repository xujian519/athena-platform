#!/bin/bash
# ============================================================================
# 向量维度迁移执行脚本
# Vector Dimension Migration Runner
#
# 将统一记忆系统的向量从768维迁移到1024维
# ============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 项目路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

# 日志函数
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_section() { echo -e "\n${CYAN}========== $1 ==========${NC}\n"; }

# 检查虚拟环境
VENV_PATH="$PROJECT_ROOT/athena_env"
if [ ! -d "$VENV_PATH" ]; then
    log_warning "虚拟环境不存在，使用系统Python"
else
    log_info "激活虚拟环境..."
    source "$VENV_PATH/bin/activate"
fi

# 检查依赖
log_info "检查依赖..."
python3 -c "import asyncpg" 2>/dev/null || {
    log_warning "安装缺失的依赖..."
    pip install asyncpg aiohttp sentence-transformers
}

log_success "依赖检查完成"

# 备份提醒
log_section "⚠️ 重要提醒"

echo "此脚本将执行以下操作："
echo "  1. 备份当前记忆数据"
echo "  2. 重建Qdrant集合（从768维改为1024维）"
echo "  3. 重新生成所有记忆的1024维向量"
echo "  4. 更新PostgreSQL数据库"
echo "  5. 同步数据到Qdrant"
echo ""
read -p "是否继续？(yes/no): " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log_warning "用户取消操作"
    exit 0
fi

# 备份数据库
log_section "📦 备份数据库"

BACKUP_DIR="$PROJECT_ROOT/production/backups"
BACKUP_FILE="$BACKUP_DIR/athena_memory_backup_$(date +%Y%m%d_%H%M%S).sql"

mkdir -p "$BACKUP_DIR"

log_info "备份数据库到: $BACKUP_FILE"
pg_dump -h localhost -p 5432 -U postgres athena_memory > "$BACKUP_FILE" 2>/dev/null || {
    log_error "数据库备份失败"
    exit 1
}

log_success "数据库备份完成"

# 执行迁移
log_section "🚀 开始迁移"

export PYTHONPATH="$PROJECT_ROOT"

python3 production/scripts/migrate_vector_dimensions.py

# 检查迁移结果
if [ $? -eq 0 ]; then
    log_section "✅ 迁移成功"

    log_info "迁移后的统计信息："
    log_info "  - 备份文件: $BACKUP_FILE"
    log_info "  - 日志文件: $PROJECT_ROOT/production/logs/vector_migration.log"

    echo ""
    log_info "如需回滚，可以使用以下命令："
    echo "  psql -h localhost -p 5432 -U postgres athena_memory < $BACKUP_FILE"

else
    log_section "❌ 迁移失败"

    log_warning "迁移过程中出现错误"
    log_info "您可以使用备份文件回滚："
    echo "  psql -h localhost -p 5432 -U postgres athena_memory < $BACKUP_FILE"

    exit 1
fi

log_success "所有操作完成！"
