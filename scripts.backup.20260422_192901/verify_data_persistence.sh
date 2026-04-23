#!/bin/bash
# 验证数据持久化脚本
# 用于验证Neo4j和Qdrant数据是否正确持久化

set -euo pipefail

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" >&2
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*"
}

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${PROJECT_ROOT}/data"

log "🔍 开始验证数据持久化配置"
log "========================================"

# 1. 检查数据目录是否存在
log "📁 [1/5] 检查数据目录..."
for dir in neo4j qdrant redis; do
    if [ -d "${DATA_DIR}/${dir}" ]; then
        size=$(du -sh "${DATA_DIR}/${dir}" | cut -f1)
        log "  ✅ ${dir}: ${size}"
    else
        error "  ❌ ${dir}: 目录不存在"
        exit 1
    fi
done

# 2. 检查Neo4j数据
log "📊 [2/5] 验证Neo4j数据..."
if [ -d "${DATA_DIR}/neo4j/databases" ]; then
    db_count=$(ls -1 "${DATA_DIR}/neo4j/databases" | wc -l)
    log "  ✅ Neo4j数据库目录存在，包含 ${db_count} 个数据库"
else
    error "  ❌ Neo4j数据库目录不存在"
    exit 1
fi

# 3. 检查Qdrant数据
log "📊 [3/5] 验证Qdrant数据..."
if [ -d "${DATA_DIR}/qdrant" ]; then
    log "  ✅ Qdrant数据目录存在"
else
    warn "  ⚠️  Qdrant数据目录为空（可能没有数据）"
fi

# 4. 检查备份文件
log "💾 [4/5] 检查备份文件..."
backup_count=$(find "${DATA_DIR}/neo4j" -name "*.tar.gz" | wc -l)
if [ ${backup_count} -gt 0 ]; then
    log "  ✅ 找到 ${backup_count} 个备份文件"
else
    warn "  ⚠️  没有找到备份文件"
fi

# 5. 验证Docker配置
log "🐳 [5/5] 验证Docker配置..."
cd "${PROJECT_ROOT}"
if grep -q "./data/neo4j:/data" docker-compose.yml; then
    log "  ✅ Neo4j使用物理挂载"
else
    error "  ❌ Neo4j未使用物理挂载"
    exit 1
fi

if grep -q "./data/qdrant:/qdrant/storage" docker-compose.yml; then
    log "  ✅ Qdrant使用物理挂载"
else
    error "  ❌ Qdrant未使用物理挂载"
    exit 1
fi

log "========================================"
log "✅ 数据持久化验证完成！"
log ""
log "📂 数据目录: ${DATA_DIR}"
log "💡 下一步: 重启容器以应用新配置"
log "   docker-compose -f docker-compose.unified.yml --profile dev down"
log "   docker-compose -f docker-compose.unified.yml --profile dev up -d"
