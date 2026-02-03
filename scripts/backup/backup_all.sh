#!/bin/bash
# Athena工作平台全量备份脚本
# 功能：备份所有核心数据资产
# 作者：安全迁移系统
# 最后更新：2026-02-02

set -euo pipefail

# 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_ROOT="/backup"
LOG_DIR="${BACKUP_ROOT}/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/backup_${TIMESTAMP}.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "$LOG_FILE"
}

# 创建备份目录
mkdir -p "${BACKUP_ROOT}"/{postgres,neo4j,qdrant,legal_world_model,logs}
mkdir -p "${BACKUP_ROOT}/cloud_backup"

log "🚀 开始Athena工作平台全量备份"
log "========================================"

# 1. PostgreSQL数据库备份
log "📦 [1/5] 备份PostgreSQL数据库..."
if "${SCRIPT_DIR}/backup_postgres.sh"; then
    log "✅ PostgreSQL备份完成"
else
    error "❌ PostgreSQL备份失败"
    exit 1
fi

# 2. Neo4j知识图谱备份
log "📦 [2/5] 备份Neo4j知识图谱..."
if "${SCRIPT_DIR}/backup_neo4j.sh"; then
    log "✅ Neo4j备份完成"
else
    error "❌ Neo4j备份失败"
    exit 1
fi

# 3. Qdrant向量数据库备份
log "📦 [3/5] 备份Qdrant向量数据库..."
if "${SCRIPT_DIR}/backup_qdrant.sh"; then
    log "✅ Qdrant备份完成"
else
    error "❌ Qdrant备份失败"
    exit 1
fi

# 4. 法律世界模型备份
log "📦 [4/5] 备份法律世界模型..."
if "${SCRIPT_DIR}/backup_legal_model.sh"; then
    log "✅ 法律世界模型备份完成"
else
    error "❌ 法律世界模型备份失败"
    exit 1
fi

# 5. 个人安全存储备份
log "📦 [5/5] 备份个人安全存储..."
if "${SCRIPT_DIR}/backup_personal_storage.sh"; then
    log "✅ 个人安全存储备份完成"
else
    error "❌ 个人安全存储备份失败"
    exit 1
fi

# 6. 备份验证
log "🔍 验证备份完整性..."
if "${SCRIPT_DIR}/verify_backups.sh" "${TIMESTAMP}"; then
    log "✅ 备份验证通过"
else
    error "❌ 备份验证失败"
    exit 1
fi

# 7. 云备份（可选）
if command -v aws &> /dev/null; then
    log "☁️  上传到云存储..."
    if "${SCRIPT_DIR}/sync_to_cloud.sh" "${TIMESTAMP}"; then
        log "✅ 云备份完成"
    else
        warn "⚠️  云备份失败，但本地备份成功"
    fi
fi

# 8. 生成备份报告
log "📊 生成备份报告..."
"${SCRIPT_DIR}/backup_report.sh" "${TIMESTAMP}"

log "========================================"
log "✅ 全量备份完成！"
log "备份时间戳: ${TIMESTAMP}"
log "备份目录: ${BACKUP_ROOT}"
log "日志文件: ${LOG_FILE}"

# 9. 清理旧备份
log "🧹 清理旧备份（保留30天）..."
find "${BACKUP_ROOT}/postgres" -name "*.sql" -mtime +30 -delete 2>/dev/null || true
find "${BACKUP_ROOT}/neo4j" -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true
find "${BACKUP_ROOT}/qdrant" -name "*.tar.gz" -mtime +30 -delete 2>/dev/null || true
find "${BACKUP_ROOT}/logs" -name "*.log" -mtime +90 -delete 2>/dev/null || true

log "✅ 旧备份清理完成"

exit 0
