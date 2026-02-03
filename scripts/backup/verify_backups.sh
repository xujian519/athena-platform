#!/bin/bash
# 备份验证脚本
# 功能：验证备份的完整性和可恢复性

set -euo pipefail

# 配置
BACKUP_ROOT="/backup"
TIMESTAMP="${1:-$(date +%Y%m%d)}"
LOG_FILE="/backup/verification/verify_${TIMESTAMP}.log"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

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

# 创建验证日志目录
mkdir -p "$(dirname "$LOG_FILE")"

log "🔍 开始备份验证"
log "========================================"

VERIFY_RESULT=0

# 1. 验证PostgreSQL备份
log "📦 [1/5] 验证PostgreSQL备份..."
PG_BACKUP=$(find "${BACKUP_ROOT}/postgres" -name "*${TIMESTAMP}*.sql" | head -1)
if [ -n "$PG_BACKUP" ]; then
    if [ -f "$PG_BACKUP" ] && [ $(stat -f%z "$PG_BACKUP" 2>/dev/null || stat -c%s "$PG_BACKUP" 2>/dev/null) -gt 1000 ]; then
        # 尝试解析SQL文件头
        if head -1 "$PG_BACKUP" | grep -q "PostgreSQL database dump"; then
            log "✅ PostgreSQL备份文件有效: $PG_BACKUP"
        else
            error "❌ PostgreSQL备份文件格式错误"
            VERIFY_RESULT=1
        fi
    else
        error "❌ PostgreSQL备份文件为空或不存在"
        VERIFY_RESULT=1
    fi
else
    error "❌ 未找到PostgreSQL备份文件"
    VERIFY_RESULT=1
fi

# 2. 验证Neo4j备份
log "📦 [2/5] 验证Neo4j备份..."
NEO_BACKUP=$(find "${BACKUP_ROOT}/neo4j" -name "*${TIMESTAMP}*.tar.gz" | head -1)
if [ -n "$NEO_BACKUP" ]; then
    if tar -tzf "$NEO_BACKUP" > /dev/null 2>&1; then
        FILE_SIZE=$(du -h "$NEO_BACKUP" | cut -f1)
        log "✅ Neo4j备份文件有效: $NEO_BACKUP ($FILE_SIZE)"
    else
        error "❌ Neo4j备份文件损坏"
        VERIFY_RESULT=1
    fi
else
    warn "⚠️  未找到Neo4j备份文件"
fi

# 3. 验证Qdrant备份
log "📦 [3/5] 验证Qdrant备份..."
QDRANT_BACKUP=$(find "${BACKUP_ROOT}/qdrant" -name "*${TIMESTAMP}*.tar.gz" | head -1)
if [ -n "$QDRANT_BACKUP" ]; then
    if tar -tzf "$QDRANT_BACKUP" > /dev/null 2>&1; then
        FILE_SIZE=$(du -h "$QDRANT_BACKUP" | cut -f1)
        log "✅ Qdrant备份文件有效: $QDRANT_BACKUP ($FILE_SIZE)"
    else
        error "❌ Qdrant备份文件损坏"
        VERIFY_RESULT=1
    fi
else
    warn "⚠️  未找到Qdrant备份文件"
fi

# 4. 验证法律世界模型备份
log "📦 [4/5] 验证法律世界模型备份..."
LEGAL_BACKUP="${BACKUP_ROOT}/legal_world_model/${TIMESTAMP}"
if [ -d "$LEGAL_BACKUP" ]; then
    FILE_COUNT=$(find "$LEGAL_BACKUP" -type f | wc -l)
    if [ "$FILE_COUNT" -gt 0 ]; then
        # 验证校验和
        CHECKSUM_FILE="${LEGAL_BACKUP}/checksums.txt"
        if [ -f "$CHECKSUM_FILE" ]; then
            log "✅ 法律世界模型备份有效: $LEGAL_BACKUP ($FILE_COUNT 文件)"
            log "   校验和文件: $CHECKSUM_FILE"
        else
            warn "⚠️  法律世界模型备份缺少校验和文件"
        fi
    else
        error "❌ 法律世界模型备份目录为空"
        VERIFY_RESULT=1
    fi
else
    error "❌ 未找到法律世界模型备份目录"
    VERIFY_RESULT=1
fi

# 5. 验证Git备份
log "📦 [5/5] 验证Git备份..."
GIT_REPO="/backup/legal_world_model_git"
if [ -d "$GIT_REPO/.git" ]; then
    cd "$GIT_REPO"
    # 检查是否存在今天的备份标签
    if git tag -l "backup-${TIMESTAMP}*" | grep -q .; then
        TAG_NAME=$(git tag -l "backup-${TIMESTAMP}*" | head -1)
        COMMIT_COUNT=$(git rev-list --count "$TAG_NAME")
        log "✅ Git备份有效: $TAG_NAME ($COMMIT_COUNT commits)"
    else
        warn "⚠️  未找到今天的Git备份标签"
    fi
else
    warn "⚠️  Git备份仓库不存在"
fi

log "========================================"

# 6. 生成验证报告
if [ $VERIFY_RESULT -eq 0 ]; then
    log "✅ 所有备份验证通过！"
    echo "status=success" > "/backup/verification/status_${TIMESTAMP}.txt"
else
    error "❌ 备份验证失败！请检查错误信息。"
    echo "status=failed" > "/backup/verification/status_${TIMESTAMP}.txt"
fi

log "验证日志: $LOG_FILE"

exit $VERIFY_RESULT
