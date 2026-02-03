#!/bin/bash
# PostgreSQL数据库备份脚本
# 功能：备份Athena工作平台的PostgreSQL数据库

set -euo pipefail

# 配置
BACKUP_DIR="/backup/postgres"
DB_NAME="${ATHENA_DB_NAME:-athena_db}"
DB_HOST="${ATHENA_DB_HOST:-localhost}"
DB_PORT="${ATHENA_DB_PORT:-5432}"
DB_USER="${ATHENA_DB_USER:-postgres}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p "${BACKUP_DIR}"

# 日志函数
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*"; }

log "开始PostgreSQL备份..."

# 1. 检查数据库连接
if ! pg_isready -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" > /dev/null 2>&1; then
    log "错误: 无法连接到PostgreSQL服务器"
    exit 1
fi

# 2. 逻辑备份 (SQL格式)
SQL_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.sql"
log "创建逻辑备份: ${SQL_FILE}"

if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=plain \
    --no-owner \
    --no-acl \
    --verbose \
    > "${SQL_FILE}" 2>/dev/null; then
    log "✅ 逻辑备份完成"
else
    log "❌ 逻辑备份失败"
    exit 1
fi

# 3. 二进制备份 (压缩)
DUMP_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.dump"
log "创建二进制备份: ${DUMP_FILE}"

if pg_dump -h "${DB_HOST}" -p "${DB_PORT}" -U "${DB_USER}" \
    -d "${DB_NAME}" \
    --format=custom \
    --compress=9 \
    -f "${DUMP_FILE}" 2>/dev/null; then
    log "✅ 二进制备份完成"
else
    log "❌ 二进制备份失败"
    exit 1
fi

# 4. 计算文件大小和校验和
SQL_SIZE=$(du -h "${SQL_FILE}" | cut -f1)
DUMP_SIZE=$(du -h "${DUMP_FILE}" | cut -f1)
SQL_CHECKSUM=$(shasum -a 256 "${SQL_FILE}" | cut -d' ' -f1)
DUMP_CHECKSUM=$(shasum -a 256 "${DUMP_FILE}" | cut -d' ' -f1)

# 5. 保存元数据
META_FILE="${BACKUP_DIR}/${DB_NAME}_${TIMESTAMP}.meta"
cat > "${META_FILE}" <<EOF
backup_timestamp: ${TIMESTAMP}
database: ${DB_NAME}
host: ${DB_HOST}
port: ${DB_PORT}
sql_file: ${SQL_FILE}
sql_size: ${SQL_SIZE}
sql_checksum: ${SQL_CHECKSUM}
dump_file: ${DUMP_FILE}
dump_size: ${DUMP_SIZE}
dump_checksum: ${DUMP_CHECKSUM}
backup_status: success
EOF

log "备份信息:"
log "  SQL文件: ${SQL_FILE} (${SQL_SIZE})"
log "  Dump文件: ${DUMP_FILE} (${DUMP_SIZE})"
log "  元数据: ${META_FILE}"

log "✅ PostgreSQL备份完成"

exit 0
